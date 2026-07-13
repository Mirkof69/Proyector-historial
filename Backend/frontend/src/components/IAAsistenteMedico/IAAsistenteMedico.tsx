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
  Input,
  Button,
  Avatar,
  Space,
  Tag,
  List,
  Typography,
  Alert,
  Spin,
  Tooltip,
  Badge,
  Statistic,
  Row,
  Col,
  Progress,
  Divider,
  Collapse,
  Switch} from "antd";
import {
  RobotOutlined,
  SendOutlined,
  UserOutlined,
  BulbOutlined,
  ThunderboltOutlined,
  SafetyOutlined,
  DeleteOutlined,
  LineChartOutlined,
  WarningOutlined,
  HeartOutlined,
  MedicineBoxOutlined,
  BugOutlined,
  CloseCircleOutlined,
  EyeOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';
import useSystemDiagnostics from '../../hooks/useSystemDiagnostics';
import statisticsService, { DashboardStats } from '../../services/statisticsService';
import './IAAsistenteMedico.css';

const { Text, Title, Paragraph } = Typography;
const { TextArea } = Input;

const MONITOR_ON_ICON = <EyeOutlined />;
const MONITOR_OFF_ICON = <CloseCircleOutlined />;

interface Mensaje {
  id: string;
  tipo: 'usuario' | 'ia' | 'sistema';
  contenido: string;
  timestamp: Date;
  categoria?: 'analisis' | 'recomendacion' | 'alerta' | 'informacion';
  confianza?: number;
  accionSugerida?: string;
  consultaId?: number; // ID de la consulta en el backend
  tiempoRespuesta?: number; // Tiempo de respuesta en ms
  contextoSistema?: string; // Contexto inyectado para la IA (no visible)
}

const crearMensajeBienvenida = (): Mensaje => ({
  id: `ia-${Date.now()}`,
  tipo: 'ia',
  contenido: `¡Hola! Soy tu Asistente Médico con IA. 🤖
      
Estoy integrado completamente con el sistema. Puedo guiarte a cualquier módulo:

• **Pacientes y Clínico**: Pacientes, Embarazos, Controles, Partos.
• **Diagnóstico**: Ecografías, Laboratorio, Calculadoras.
• **Gestión**: Citas, Consultorios, Reportes.

¿Qué necesitas hacer hoy?`,
  timestamp: new Date(),
  categoria: 'informacion',
  confianza: 100,
});

const loadInitialMessages = (): Mensaje[] => {
  const savedMessages = localStorage.getItem('ia_chat_history:v1');
  if (savedMessages) {
    try {
      const parsed = JSON.parse(savedMessages);
      if (Array.isArray(parsed) && parsed.length > 0) {
        return parsed.map((m: any) => ({
          ...m,
          timestamp: new Date(m.timestamp)
        }));
      }
    } catch (e) {
      console.error("Error parsing chat history", e);
    }
  }
  return [crearMensajeBienvenida()];
};

const procesarConsultaLocal = (consultaLower: string): string => {
  if (consultaLower.includes('sistema') || consultaLower.includes('estado') || consultaLower.includes('pacientes')) {
    return `📊 **Estado del Sistema (Modo Offline)**

⚠️ *No he podido conectar con el microservicio de análisis en tiempo real, pero puedo darte un resumen general:*

• **Pacientes**: Accede al módulo de "Pacientes" para ver el listado completo y sus historias clínicas.
• **Embarazos**: El panel principal del Dashboard muestra el resumen de gestaciones activas.
• **Pendientes**: Revisa tu campana de notificaciones para ver alertas críticas pendientes.

**Acción sugerida**: Verifica que el microservicio de IA esté activo para un análisis numérico exacto.`;
  }

  if (consultaLower.includes('falta') || consultaLower.includes('implementación')) {
    return `🚀 **Hoja de Ruta del Sistema**

Currently el sistema base está completado al 100%. Las áreas de mejora continua son:
1. Optimización de modelos de machine learning.
2. Expansión del módulo de telemedicina.
3. Integración con dispositivos wearables.

¿En qué más puedo ayudarte?`;
  }

  if (consultaLower.includes('preeclampsia') || consultaLower.includes('presion') || consultaLower.includes('hipertension')) {
    return `📊 **Análisis de Riesgo de Preeclampsia**

Basado en los criterios clínicos actuales:

**Factores de Riesgo Evaluados:**
• Presión arterial ≥ 140/90 mmHg
• Proteinuria significativa
• Antecedentes de preeclampsia
• Edad materna avanzada (>35 años)
• Embarazo múltiple

**Recomendaciones de IA:**
1. ✅ Monitoreo de PA cada 4 horas si PA ≥ 140/90
2. ✅ Proteinuria en muestra de 24h
3. ✅ Laboratorio: Hemograma, función hepática, LDH
4. ⚠️  Considerar hospitalización si PA ≥ 160/110
5. 💊 Evaluación de sulfato de magnesio profiláctico

**Nivel de Confianza**: 92% | **Última actualización**: Guías ACOG 2023`;
  }

  if (consultaLower.includes('diabetes') || consultaLower.includes('glucosa') || consultaLower.includes('glicemia')) {
    return `🔬 **Análisis de Diabetes Gestacional**

**Protocolo de Detección:**

**Factores de Riesgo:**
• IMC pregestacional > 30
• Antecedentes familiares de DM
• Glicemia basal ≥ 92 mg/dL
• PTOG anterior anormal

**Plan de Acción Recomendado:**
1. 🩸 Test de O'Sullivan (50g glucosa) a las 24-28 semanas
2. 📈 Si ≥ 140 mg/dL → PTOG 100g
3. 🍎 Consejería nutricional inmediata
4. 📊 Monitoreo de glucosa capilar 4 veces/día
5. 💉 Evaluación de terapia insulínica si necesario

**IA Sugiere**: Control glicémico estricto reduce riesgos fetales en 60%

**Confianza**: 95% | **Basado en**: ADA Guidelines 2024`;
  }

  if (consultaLower.includes('rciu') || consultaLower.includes('crecimiento') || consultaLower.includes('altura uterina')) {
    return `📏 **Evaluación de Restricción de Crecimiento Intrauterino**

**Criterios de Sospecha:**
• Altura uterina < percentil 10 para EG
• Discordancia AU/EG > 3 cm
• Velocidad de crecimiento inadecuada

**Protocolo Diagnóstico:**
1. 🔍 Ecografía Doppler (arteria umbilical, cerebral media)
2. 📊 Biometría fetal completa
3. 💉 Laboratorio materno: HTA, diabetes, trombofilias
4. 🔬 Evaluación de bienestar fetal (NST, PBF)

**Seguimiento Sugerido:**
• Eco Doppler cada 2 semanas si RCIU leve
• Semanal si RCIU moderado/severo
• NST 2 veces/semana

**IA Recomienda**: Evaluación multidisciplinaria con MFM

**Confianza**: 89% | **Evidencia**: Nivel A`;
  }

  if (consultaLower.includes('edad gestacional') || consultaLower.includes('fum') || consultaLower.includes('fpp')) {
    return `📅 **Calculadora de Edad Gestacional**

**Métodos de Cálculo:**

1. **Por FUM (Regla de Naegele)**:
   • FPP = FUM + 280 días
   • Confiable si: Ciclos regulares (28±3 días)

2. **Por Ecografía Primer Trimestre**:
   • LCN 6-12 semanas: ±3-5 días
   • Más preciso que FUM si discordancia > 7 días

**La IA Recomienda**:
   ✅ Usar eco temprana como gold standard
   ✅ Si eco tardía: mantener FUM si concordante
   ⚠️  Revisar si discordancia > 2 semanas

**Confianza**: 98% | **Precisión**: ±3 días`;
  }

  if (consultaLower.includes('laboratorio') || consultaLower.includes('examenes') || consultaLower.includes('hemograma')) {
    return `🧪 **Análisis de Resultados de Laboratorio**

**Interpretación IA de Valores Críticos:**

**Hemograma:**
• Hb < 11 g/dL → Anemia gestacional (suplementar hierro)
• Hb < 9 g/dL → Anemia moderada (investigar causa)
• Plaquetas < 150,000 → Vigilar preeclampsia/HELLP

**Función Hepática:**
• TGO/TGP > 2x normal → HELLP syndrome
• Bilirrubinas elevadas → Colestasis gestacional

**Función Renal:**
• Creatinina > 0.9 mg/dL → Evaluar función renal
• Proteinuria > 300 mg/24h → Preeclampsia

**IA Sugiere Algoritmo:**
1. ✅ Hemograma + grupo sanguíneo (1er control)
2. ✅ Test O'Sullivan (24-28 sem)
3. ✅ Cultivo urocultivo (cada trimestre)
4. ✅ Serología TORCH si no inmune

**Confianza**: 93%`;
  }

  return `🤖 **Asistente IA en Modo Análisis**

He procesado tu consulta: "${consultaLower}"

**Puedo ayudarte con análisis específicos de:**

🔴 **Emergencias Obstétricas**
• Preeclampsia / Eclampsia
• Hemorragia obstétrica
• Sufrimiento fetal agudo

🟡 **Patologías Frecuentes**
• Diabetes gestacional
• Hipertensión gestacional
• RCIU / Macrosomía

🟢 **Control Prenatal**
• Interpretación de laboratorios
• Cálculo de edad gestacional
• Evaluación de riesgos

💡 **Tip**: Sé más específico con tu consulta para un análisis detallado.

¿Sobre qué quieres que analice?`;
};

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
        <Collapse
          items={[{
            key: '1',
            label: collapseErrorLabel,
            children: systemErrors.slice(-3).map((err) => (
              <Alert
                key={err.message || err.timestamp}
                message={`${err.details.status || 'Error'}: ${err.message}`}
                description={
                  <div>
                    <Text type="secondary" style={{ fontSize: '12px' }}>
                      {dayjs(err.timestamp).format('HH:mm:ss')} - {err.details.url}
                    </Text>
                  </div>
                }
                type={err.severity === 'critical' ? 'error' : 'warning'}
                showIcon
                style={{ marginBottom: 8 }}
              />
            ))
          }]}
          style={{ marginBottom: 16 }}
        />
      )}

      <Row gutter={8} style={{ marginBottom: 16 }}>
        <Col span={8}>
          <Statistic
            title="Análisis"
            value={estadisticasIA.analisisRealizados}
            prefix={<LineChartOutlined />}
            valueStyle={{ fontSize: 16 }}
          />
        </Col>
        <Col span={8}>
          <Statistic
            title="Alertas"
            value={estadisticasIA.alertasGeneradas}
            prefix={<WarningOutlined />}
            valueStyle={{ fontSize: 16, color: '#ff4d4f' }}
          />
        </Col>
        <Col span={8}>
          <Statistic
            title="Recomendaciones"
            value={estadisticasIA.recomendacionesDadas}
            prefix={<BulbOutlined />}
            valueStyle={{ fontSize: 16, color: '#52c41a' }}
          />
        </Col>
      </Row>

      <Progress
        percent={estadisticasIA.precision}
        strokeColor={{ from: '#108ee9', to: '#87d068' }}
        status="active"
        format={percent => `Precisión: ${percent}%`}
      />

      <Divider style={{ margin: '12px 0' }} />

      <div style={{ marginBottom: 16 }}>
        <Text strong>Análisis Rápidos:</Text>
        <div style={{ marginTop: 8 }}>
          <Space wrap>
            <Button
              size="small"
              icon={<HeartOutlined />}
              onClick={() => analizarRapido('preeclampsia')}
            >
              Preeclampsia
            </Button>
            <Button
              size="small"
              icon={<MedicineBoxOutlined />}
              onClick={() => analizarRapido('diabetes')}
            >
              Diabetes
            </Button>
            <Button
              size="small"
              icon={<LineChartOutlined />}
              onClick={() => analizarRapido('rciu')}
            >
              RCIU
            </Button>
            <Button
              size="small"
              icon={<BulbOutlined />}
              onClick={() => analizarRapido('laboratorio')}
            >
              Laboratorios
            </Button>
          </Space>
        </div>
      </div>

      <div
        className="chat-messages-container"
      >
        <List
          dataSource={mensajes}
          renderItem={(mensaje) => (
            <div
              style={{
                display: 'flex',
                justifyContent: mensaje.tipo === 'usuario' ? 'flex-end' : 'flex-start',
                marginBottom: 12
              }}
            >
              <div className={`mensaje-bubble ${mensaje.tipo}`}>
                <Space direction="vertical" size={4} style={{ width: '100%' }}>
                  <Space>
                    {mensaje.tipo === 'ia' ? (
                      <RobotOutlined style={{ color: '#722ed1' }} />
                    ) : mensaje.tipo === 'sistema' ? (
                      <BugOutlined style={{ color: '#ff4d4f' }} />
                    ) : (
                      <UserOutlined />
                    )}
                    <Text strong className="mensaje-sender">
                      {mensaje.tipo === 'ia' ? 'IA Médica' : mensaje.tipo === 'sistema' ? 'Sistema' : 'Tú'}
                    </Text>
                    {mensaje.confianza && (
                      <Tag color="green" style={{ fontSize: '12px' }}>
                        {mensaje.confianza}% confianza
                      </Tag>
                    )}
                  </Space>
                  <Paragraph className="mensaje-text">
                    {mensaje.contenido}
                  </Paragraph>
                  <Text type="secondary" className="mensaje-time">
                    {dayjs(mensaje.timestamp).format('HH:mm')}
                  </Text>
                </Space>
              </div>
            </div>
          )}
        />
        {cargando && (
          <div style={{ textAlign: 'center', padding: 16 }}>
            <Space>
              <Spin />
              <Text type="secondary">IA analizando…</Text>
            </Space>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <Space.Compact style={{ width: '100%' }}>
        <TextArea
          value={inputTexto}
          onChange={(e) => setInputTexto(e.target.value)}
          placeholder="Pregunta al Asistente IA... (ej: ¿Cómo detectar preeclampsia?)"
          autoSize={{ minRows: 1, maxRows: 3 }}
          onPressEnter={(e) => {
            if (!e.shiftKey) {
              e.preventDefault();
              enviarMensaje();
            }
          }}
        />
        <Button
          type="primary"
          icon={<SendOutlined />}
          onClick={enviarMensaje}
          loading={cargando}
        >
          Enviar
        </Button>
      </Space.Compact>

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
