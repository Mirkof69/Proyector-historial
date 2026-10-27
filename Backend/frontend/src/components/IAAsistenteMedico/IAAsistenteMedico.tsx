/**
 * =============================================================================
 * IA ASISTENTE MÉDICO - COMPONENTE VISIBLE
 * =============================================================================
 * Asistente médico inteligente con IA visible para análisis y recomendaciones
 * =============================================================================
 */

import { authService } from '../../services/authService';
import React, { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAntdApp } from "../../hooks/useMessage";
import {Card,
  Button,
  Avatar,
  Space,
  Tag,
  Typography,
  Alert,
  Tooltip,
  Divider,
  Switch} from "antd";
import {
  RobotOutlined,
  DeleteOutlined,
  BulbOutlined,
  BugOutlined,
  CloseCircleOutlined,
  EyeOutlined,
  ReadOutlined,
} from '@ant-design/icons';
import useSystemDiagnostics from '../../hooks/useSystemDiagnostics';
import statisticsService, { DashboardStats } from '../../services/statisticsService';
import './IAAsistenteMedico.css';
import { CLAVE_HISTORIAL, Mensaje, crearMensajeBienvenida, loadInitialMessages, procesarConsultaLocal } from './iaAsistenteUtils';
import IAStatsPanel from './components/IAStatsPanel';
import IAAnalisisRapidos from './components/IAAnalisisRapidos';
import IAChatMessages from './components/IAChatMessages';
import IAChatInput from './components/IAChatInput';
import IAErroresCollapse from './components/IAErroresCollapse';

const { Text, Title } = Typography;

const MONITOR_ON_ICON = <EyeOutlined />;
const MONITOR_OFF_ICON = <CloseCircleOutlined />;

export const IAAsistenteMedico: React.FC = () => {
  const [mensajes, setMensajes] = useState<Mensaje[]>(loadInitialMessages);
  const { message } = useAntdApp();
  const [inputTexto, setInputTexto] = useState('');
  const [cargando, setCargando] = useState(false);
  // Solo se cuentan las consultas: antes había una «precisión 94,5 %» fija.
  const [consultasSesion, setConsultasSesion] = useState(0);
  const navigate = useNavigate();
  const dashboardContextRef = useRef<DashboardStats | null>(null);

  const {
    errors: systemErrors,
    isMonitoring,
    toggleMonitoring,
    interpretError,
    clearErrors,
    hasErrors,
    criticalErrors,
    highErrors
  } = useSystemDiagnostics();

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const loadContext = async () => {
      // Enfermería y recepción no leen /reportes/: pedirlo era un 403 en cada Panel.
      if (['enfermera', 'recepcion'].includes(authService.getCurrentUser()?.rol ?? '')) return;
      try {
        const stats = await statisticsService.getDashboardStatistics();
        dashboardContextRef.current = stats;
      } catch {
        // Sin contexto del panel la consulta sigue funcionando.
      }
    };
    loadContext();
  }, []);

  const persistAndScroll = useCallback((msgs: Mensaje[]) => {
    if (msgs.length > 0) {
      try { localStorage.setItem(CLAVE_HISTORIAL, JSON.stringify(msgs)); } catch { /* almacenamiento bloqueado */ }
      messagesEndRef.current?.scrollIntoView?.({ behavior: 'smooth' });
    }
  }, []);

  useEffect(() => {
    if (systemErrors.length > 0 && isMonitoring) {
      const lastError = systemErrors[systemErrors.length - 1];
      const interpretation = interpretError(lastError);

      const errorMessage: Mensaje = {
        id: `sistema-error-${Date.now()}`,
        tipo: 'sistema',
        contenido: `Error detectado automáticamente\n\n${interpretation}`,
        timestamp: new Date(),
        categoria: 'alerta'
      };

      setMensajes(prev => {
        const newMessages = [...prev, errorMessage];
        persistAndScroll(newMessages);
        return newMessages;
      });
      message.error(`Error ${lastError.details.status || 'del sistema'} detectado - Ver IA Assistant`);
    }
  }, [systemErrors, isMonitoring, interpretError, persistAndScroll, message]);

  // Función para limpiar el historial
  const limpiarHistorial = () => {
    // Antes borraba «ia_chat_history» y el historial se guarda en «ia_chat_history:v1».
    try { localStorage.removeItem(CLAVE_HISTORIAL); } catch { /* almacenamiento bloqueado */ }
    const bienvenida = [crearMensajeBienvenida()];
    setMensajes(bienvenida);
    persistAndScroll(bienvenida);
  };

  const procesarConsultaIA = async (consulta: string): Promise<{
    respuesta: string;
    fuente: 'base_conocimiento' | 'sin_conexion';
    tema?: string;
    consultaId?: number;
    tiempoRespuesta?: number;
  }> => {
    const { iaMedicaService } = await import('../../services/iaMedicaService');

    try {
      // Solo dentro de la ficha de una paciente (/pacientes/:id). Antes, fuera de
      // ella, indexOf daba -1, se leía el primer tramo vacío y Number('') = 0:
      // se mandaba paciente_id = 0 y el backend respondía 500 en cada consulta.
      const pathParts = window.location.pathname.split('/');
      const pos = pathParts.indexOf('pacientes');
      const pacienteIdString = pos >= 0 ? pathParts[pos + 1] : '';
      const paciente_id = /^\d+$/.test(pacienteIdString ?? '') && Number(pacienteIdString) > 0
        ? Number(pacienteIdString) : undefined;

      const contextoRico = {
        total_pacientes: dashboardContextRef.current?.total_pacientes || 0,
        total_embarazos_activos: dashboardContextRef.current?.embarazos_activos || 0,
        total_notificaciones_pendientes: dashboardContextRef.current?.citas_pendientes || 0,
        fecha_sistema: new Date().toLocaleDateString(),
        usuario_rol: 'Doctor'
      };

      const resultado = await iaMedicaService.consultarIA({
        consulta,
        paciente_id,
        contexto: contextoRico
      });

      // El backend responde 200 con `fallback: true` cuando el microservicio no está.
      if (resultado.fallback) {
        return { respuesta: procesarConsultaLocal(consulta), fuente: 'sin_conexion' };
      }
      return {
        respuesta: resultado.consulta.respuesta_ia,
        fuente: 'base_conocimiento',
        tema: resultado.consulta.categoria,
        consultaId: resultado.consulta.id,
        tiempoRespuesta: resultado.consulta.tiempo_respuesta_ms,
      };
    } catch {
      return { respuesta: procesarConsultaLocal(consulta), fuente: 'sin_conexion' };
    }
  };


  // Recibe el texto: las «consultas rápidas» lo pasan directo. Antes ponían el
  // texto en el campo y llamaban a enviarMensaje con un setTimeout, pero esa
  // función ya había leído el campo vacío y no enviaba nada.
  const enviarMensaje = async (texto: string = inputTexto) => {
    const consulta = texto.trim();
    if (!consulta) return;

    const mensajeUsuario: Mensaje = {
      id: `user-${Date.now()}`,
      tipo: 'usuario',
      contenido: consulta,
      timestamp: new Date()
    };

    setMensajes(prev => {
      const newMessages = [...prev, mensajeUsuario];
      persistAndScroll(newMessages);
      return newMessages;
    });
    setInputTexto('');
    setCargando(true);

    try {
      const resultadoIA = await procesarConsultaIA(consulta);

      const mensajeIA: Mensaje = {
        id: `ia-${Date.now()}`,
        tipo: 'ia',
        contenido: resultadoIA.respuesta,
        timestamp: new Date(),
        categoria: 'analisis',
        fuente: resultadoIA.fuente,
        tema: resultadoIA.tema,
        consultaId: resultadoIA.consultaId,
        tiempoRespuesta: resultadoIA.tiempoRespuesta
      };

      setMensajes(prev => {
        const newMessages = [...prev, mensajeIA];
        persistAndScroll(newMessages);
        return newMessages;
      });

      if (resultadoIA.fuente === 'base_conocimiento') setConsultasSesion((n) => n + 1);
    } finally {
      setCargando(false);
    }
  };

  const analizarRapido = (tipo: string) => {
    const consultas: { [key: string]: string } = {
      preeclampsia: '¿Cómo detectar preeclampsia?',
      diabetes: 'Protocolo de diabetes gestacional',
      rciu: 'Evaluación de restricción de crecimiento',
      laboratorio: 'Interpretación de laboratorios prenatal'
    };

    if (consultas[tipo]) enviarMensaje(consultas[tipo]);
  };

  const collapseErrorLabel = useMemo(
    () => (
      <Space>
        <BugOutlined className="mensaje-icono alarma" />
        <Text strong>Errores Capturados ({systemErrors.length})</Text>
        {criticalErrors > 0 && <Tag color="error">CRÍTICOS: {criticalErrors}</Tag>}
        {highErrors > 0 && <Tag color="warning">ALTOS: {highErrors}</Tag>}
      </Space>
    ),
    [systemErrors.length, criticalErrors, highErrors]
  );

  return (
    <Card
      className="ia-asistente-medico"
      title={
        <Space>
          <Avatar icon={<RobotOutlined />} className="ia-asistente-avatar" />
          <div>
            <Title level={5} className="ia-asistente-titulo">Asistente de consulta</Title>
            <Text type="secondary" className="ia-asistente-subtitulo">
              Base de conocimiento obstétrica
            </Text>
          </div>
        </Space>
      }
      extra={
        <Space wrap>
          <Tooltip title="Qué modelos de IA tiene el sistema y cuánto aciertan">
            <Button size="small" icon={<ReadOutlined />} onClick={() => navigate('/dashboard/ia-guia')}>
              Guía de IA
            </Button>
          </Tooltip>
          <Tooltip title="Borrar historial de chat">
            <Button
              type="text"
              icon={<DeleteOutlined />}
              size="small"
              onClick={limpiarHistorial}
              danger
            />
          </Tooltip>
          <Divider type="vertical" />
          {hasErrors && (
            <Tooltip title={`Limpiar ${systemErrors.length} errores`}>
              <Button
                type="text"
                danger
                icon={<CloseCircleOutlined />}
                size="small"
                onClick={() => {
                  clearErrors();
                  message.success('Errores de diagnóstico limpiados');
                }}
              />
            </Tooltip>
          )}
          <Tooltip title={isMonitoring ? 'Desactivar monitoreo' : 'Activar monitoreo de sistema'}>
            <Space>
              <Text type="secondary" className="ia-asistente-subtitulo">
                {isMonitoring ? 'Monitor activo' : 'Monitor apagado'}
              </Text>
              <Switch
                checked={isMonitoring}
                onChange={toggleMonitoring}
                size="small"
                checkedChildren={MONITOR_ON_ICON}
                unCheckedChildren={MONITOR_OFF_ICON}
              />
            </Space>
          </Tooltip>
        </Space>
      }
    >
      {hasErrors && (
        <IAErroresCollapse systemErrors={systemErrors} collapseErrorLabel={collapseErrorLabel} />
      )}

      <IAStatsPanel consultas={consultasSesion} />

      <Divider className="ia-asistente-divisor" />

      <IAAnalisisRapidos analizarRapido={analizarRapido} />

      <IAChatMessages mensajes={mensajes} cargando={cargando} messagesEndRef={messagesEndRef} />

      <IAChatInput
        inputTexto={inputTexto}
        setInputTexto={setInputTexto}
        enviarMensaje={enviarMensaje}
        cargando={cargando}
      />

      <Alert
        message="Apoyo, no diagnóstico"
        description="Las respuestas resumen guías clínicas. La decisión es del médico (Ley 3131)."
        type="info"
        showIcon
        icon={<BulbOutlined />}
      />
    </Card>
  );
};

export default IAAsistenteMedico;
