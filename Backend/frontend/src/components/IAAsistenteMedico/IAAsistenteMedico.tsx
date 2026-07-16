/**
 * =============================================================================
 * IA ASISTENTE MÉDICO - COMPONENTE VISIBLE
 * =============================================================================
 * Asistente médico inteligente con IA visible para análisis y recomendaciones
 * =============================================================================
 */

import React, { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import { useAntdApp } from "../../hooks/useMessage";
import {Card,
  Button,
  Avatar,
  Space,
  Tag,
  Typography,
  Alert,
  Tooltip,
  Badge,
  Divider,
  Switch} from "antd";
import {
  RobotOutlined,
  ThunderboltOutlined,
  SafetyOutlined,
  DeleteOutlined,
  LineChartOutlined,
  BulbOutlined,
  BugOutlined,
  CloseCircleOutlined,
  EyeOutlined
} from '@ant-design/icons';
import useSystemDiagnostics from '../../hooks/useSystemDiagnostics';
import statisticsService, { DashboardStats } from '../../services/statisticsService';
import './IAAsistenteMedico.css';
import { Mensaje, loadInitialMessages, procesarConsultaLocal } from './iaAsistenteUtils';
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
  const [estadisticasIA, setEstadisticasIA] = useState({
    analisisRealizados: 0,
    alertasGeneradas: 0,
    recomendacionesDadas: 0,
    precision: 94.5
  });
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
      try {
        const stats = await statisticsService.getDashboardStatistics();
        dashboardContextRef.current = stats;
      } catch (error) {
        console.error("Error cargando contexto para IA:", error);
      }
    };
    loadContext();
  }, []);

  const persistAndScroll = useCallback((msgs: Mensaje[]) => {
    if (msgs.length > 0) {
      localStorage.setItem('ia_chat_history:v1', JSON.stringify(msgs));
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, []);

  useEffect(() => {
    if (systemErrors.length > 0 && isMonitoring) {
      const lastError = systemErrors[systemErrors.length - 1];
      const interpretation = interpretError(lastError);

      const errorMessage: Mensaje = {
        id: `sistema-error-${Date.now()}`,
        tipo: 'sistema',
        contenido: `🔧 **ERROR DETECTADO AUTOMÁTICAMENTE**\n\n${interpretation}`,
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
  }, [systemErrors, isMonitoring, interpretError, persistAndScroll]);

  // Función para limpiar el historial
  const limpiarHistorial = () => {
    localStorage.removeItem('ia_chat_history');
    setMensajes([]);
    setTimeout(() => {
      const mensajeBienvenida: Mensaje = {
        id: `ia-${Date.now()}`,
        tipo: 'ia',
        contenido: `¡Historial limpiado! 🧹

¿En qué puedo ayudarte ahora?`,
        timestamp: new Date(),
        categoria: 'informacion',
        confianza: 100,
      };
      setMensajes(prev => {
        const newMessages = [mensajeBienvenida];
        persistAndScroll(newMessages);
        return newMessages;
      });
    }, 100);
  };

  const procesarConsultaIA = async (consulta: string): Promise<{
    respuesta: string;
    consultaId?: number;
    confianza?: number;
    tiempoRespuesta?: number;
  }> => {
    const { iaMedicaService } = await import('../../services/iaMedicaService');

    try {
      const pathParts = window.location.pathname.split('/');
      const pacienteIdString = pathParts[pathParts.indexOf('pacientes') + 1];
      const paciente_id = !isNaN(Number(pacienteIdString)) ? Number(pacienteIdString) : undefined;

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

      let respuestaFormateada = resultado.consulta.respuesta_ia;

      if (resultado.nlp_info && resultado.nlp_info.keywords.length > 0) {
        respuestaFormateada += `\n\n---\n📊 **Información de Procesamiento:**\n`;
        respuestaFormateada += `• Confianza técnica: ${resultado.nlp_info.confianza.toFixed(1)}%\n`;
        respuestaFormateada += `• Etiquetas: ${resultado.nlp_info.keywords.join(', ')}`;
      }

      return {
        respuesta: respuestaFormateada,
        consultaId: resultado.consulta.id,
        confianza: resultado.consulta.confianza,
        tiempoRespuesta: resultado.consulta.tiempo_respuesta_ms
      };
    } catch (error) {
      console.error('Error al consultar IA:', error);
      const consultaLower = consulta.toLowerCase();
      return {
        respuesta: procesarConsultaLocal(consultaLower),
        confianza: 85
      };
    }
  };


  const enviarMensaje = async () => {
    if (!inputTexto.trim()) return;

    const mensajeUsuario: Mensaje = {
      id: `user-${Date.now()}`,
      tipo: 'usuario',
      contenido: inputTexto,
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
      const resultadoIA = await procesarConsultaIA(inputTexto);

      const mensajeIA: Mensaje = {
        id: `ia-${Date.now()}`,
        tipo: 'ia',
        contenido: resultadoIA.respuesta,
        timestamp: new Date(),
        categoria: 'analisis',
        confianza: resultadoIA.confianza || 88,
        consultaId: resultadoIA.consultaId,
        tiempoRespuesta: resultadoIA.tiempoRespuesta
      };

      setMensajes(prev => {
        const newMessages = [...prev, mensajeIA];
        persistAndScroll(newMessages);
        return newMessages;
      });

      setEstadisticasIA(prev => ({
        ...prev,
        analisisRealizados: prev.analisisRealizados + 1,
        recomendacionesDadas: prev.recomendacionesDadas + (resultadoIA.respuesta.includes('Recomend') ? 1 : 0),
        alertasGeneradas: prev.alertasGeneradas + (resultadoIA.respuesta.includes('⚠️') || resultadoIA.respuesta.includes('🚨') ? 1 : 0),
        precision: resultadoIA.confianza || prev.precision
      }));

    } catch (error) {
      console.error('Error procesando IA:', error);
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

    setInputTexto(consultas[tipo] || '');
    setTimeout(() => enviarMensaje(), 100);
  };

  const collapseErrorLabel = useMemo(
    () => (
      <Space>
        <BugOutlined style={{ color: '#ff4d4f' }} />
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
          <Badge dot status="processing">
            <Avatar
              icon={<RobotOutlined />}
              style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}
            />
          </Badge>
          <div>
            <Title level={5} style={{ margin: 0 }}>Asistente Médico IA</Title>
            <Text type="secondary" style={{ fontSize: 12 }}>
              <ThunderboltOutlined /> Análisis en tiempo real
            </Text>
          </div>
        </Space>
      }
      extra={
        <Space>
          <Tag icon={<SafetyOutlined />} color="success">
            Precisión {estadisticasIA.precision}%
          </Tag>
          <Tag icon={<LineChartOutlined />} color="processing">
            {estadisticasIA.analisisRealizados} análisis
          </Tag>
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
              <Text type="secondary" style={{ fontSize: '12px' }}>
                {isMonitoring ? 'Monitor ON' : 'Monitor OFF'}
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
      style={{ height: '100%', display: 'flex', flexDirection: 'column' }}
    >
      {hasErrors && (
        <IAErroresCollapse systemErrors={systemErrors} collapseErrorLabel={collapseErrorLabel} />
      )}

      <IAStatsPanel estadisticasIA={estadisticasIA} />

      <Divider style={{ margin: '12px 0' }} />

      <IAAnalisisRapidos analizarRapido={analizarRapido} />

      <IAChatMessages mensajes={mensajes} cargando={cargando} messagesEndRef={messagesEndRef} />

      <IAChatInput
        inputTexto={inputTexto}
        setInputTexto={setInputTexto}
        enviarMensaje={enviarMensaje}
        cargando={cargando}
      />

      <Alert
        message="IA Experimental"
        description="Este asistente usa algoritmos de IA para análisis médico. Siempre verificar con criterio clínico profesional."
        type="info"
        showIcon
        icon={<BulbOutlined />}
        style={{ marginTop: 12 }}
      />
    </Card>
  );
};

export default IAAsistenteMedico;
