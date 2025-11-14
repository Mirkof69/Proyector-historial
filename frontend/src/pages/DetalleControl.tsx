import React, { useState, useEffect } from 'react';
import { 
  Card, Descriptions, Tag, Alert, Spin, Row, Col, Statistic, 
  Timeline, Progress, Space, Divider, Badge, Button, Empty, Tooltip
} from 'antd';
import { 
  WarningOutlined, CheckCircleOutlined, HeartOutlined, 
  MedicineBoxOutlined, UserOutlined, CalendarOutlined,
  RiseOutlined, FallOutlined, LineChartOutlined,
  FileTextOutlined, AlertOutlined, CloseCircleOutlined
} from '@ant-design/icons';
import axios from 'axios';
import { authService } from '../services/authService';
import dayjs from 'dayjs';
import 'dayjs/locale/es';

dayjs.locale('es');

interface DetalleControlProps {
  controlId: number;
  onClose: () => void;
}

interface Alerta {
  tipo: string;
  categoria: string;
  mensaje: string;
  valor: string;
  recomendacion?: string;
}

interface RiesgoPreeclampsia {
  nivel: string;
  puntuacion: number;
  factores: string[];
}

interface EstadoNutricional {
  imc: number;
  clasificacion: string;
  ganancia_peso: number;
  ganancia_semanal: number;
  ganancia_esperada: [number, number];
  estado: string;
}

interface CrecimientoFetal {
  altura_uterina: number;
  esperada: [number, number];
  diferencia: number;
  estado: string;
}

interface ControlDetalle {
  id: number;
  numero_control: number;
  fecha_control: string;
  fecha_control_formatted: string;
  paciente_nombre: string;
  edad_gestacional: string;
  semanas_gestacion: number;
  dias_gestacion: number;
  peso_actual: number;
  peso_pregestacional: number;
  talla: number;
  presion_arterial_sistolica: number;
  presion_arterial_diastolica: number;
  presion_arterial: string;
  presion_arterial_media: number;
  frecuencia_cardiaca: number;
  temperatura: number;
  altura_uterina: number;
  frecuencia_cardiaca_fetal: number;
  presentacion_fetal: string;
  movimientos_fetales: string;
  edema: string;
  proteinuria: string;
  observaciones: string;
  imc_actual: number;
  clasificacion_imc: string;
  ganancia_peso: number;
  alertas: Alerta[];
  tiene_alertas: boolean;
}

interface Reporte {
  control: {
    numero: number;
    fecha: string;
    edad_gestacional: string;
    trimestre: number;
  };
  paciente: {
    nombre: string;
    id_clinico: string;
  };
  signos_vitales: {
    presion_arterial: string;
    pam: number;
    fc_materna: number;
    temperatura: number;
  };
  mediciones_obstetricas: {
    altura_uterina: number;
    fcf: number;
    presentacion: string;
    movimientos: string;
  };
  estado_nutricional: EstadoNutricional;
  evaluacion_crecimiento: CrecimientoFetal;
  riesgo_preeclampsia: RiesgoPreeclampsia;
  alertas: Alerta[];
  observaciones: string;
}

const DetalleControl: React.FC<DetalleControlProps> = ({ controlId, onClose }) => {
  const [control, setControl] = useState<ControlDetalle | null>(null);
  const [reporte, setReporte] = useState<Reporte | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingReporte, setLoadingReporte] = useState(false);

  useEffect(() => {
    fetchControl();
    fetchReporte();
  }, [controlId]);

  const fetchControl = async () => {
    try {
      const token = authService.getToken();
      const response = await axios.get(`http://127.0.0.1:8000/api/controles/${controlId}/`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setControl(response.data);
    } catch (error) {
      console.error('Error al cargar control:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchReporte = async () => {
    setLoadingReporte(true);
    try {
      const token = authService.getToken();
      const response = await axios.get(`http://127.0.0.1:8000/api/controles/${controlId}/reporte/`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setReporte(response.data.reporte);
    } catch (error) {
      console.error('Error al cargar reporte:', error);
    } finally {
      setLoadingReporte(false);
    }
  };

  const obtenerColorRiesgo = (nivel: string) => {
    switch (nivel) {
      case 'ALTO': return 'red';
      case 'MODERADO': return 'orange';
      case 'BAJO': return 'yellow';
      case 'MÍNIMO': return 'green';
      default: return 'blue';
    }
  };

  const obtenerIconoAlerta = (tipo: string) => {
    switch (tipo) {
      case 'critico': return <CloseCircleOutlined />;
      case 'advertencia': return <WarningOutlined />;
      default: return <AlertOutlined />;
    }
  };

  const calcularPorcentajePA = (sistolica: number, diastolica: number) => {
    // PA normal: 120/80
    const porcentajeSistolica = (sistolica / 140) * 100;
    const porcentajeDiastolica = (diastolica / 90) * 100;
    const promedio = (porcentajeSistolica + porcentajeDiastolica) / 2;
    return Math.min(promedio, 100);
  };

  const calcularPorcentajeFCF = (fcf: number) => {
    // FCF normal: 110-160, óptimo: 120-150
    if (fcf < 110) return 50;
    if (fcf > 160) return 50;
    if (fcf >= 120 && fcf <= 150) return 100;
    return 80;
  };

  const calcularPorcentajeIMC = (imc: number) => {
    // IMC normal: 18.5-24.9
    if (imc < 18.5) return 60;
    if (imc >= 18.5 && imc < 25) return 100;
    if (imc >= 25 && imc < 30) return 70;
    return 40;
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" tip="Cargando detalles del control..." />
      </div>
    );
  }

  if (!control) {
    return <Empty description="No se encontraron datos del control" />;
  }

  const alertasCriticas = control.alertas.filter(a => a.tipo === 'critico');
  const alertasAdvertencia = control.alertas.filter(a => a.tipo === 'advertencia');

  return (
    <div>
      {/* HEADER CON ALERTAS CRÍTICAS */}
      {alertasCriticas.length > 0 && (
        <Alert
          message={`🚨 ${alertasCriticas.length} ALERTA(S) CRÍTICA(S) DETECTADA(S)`}
          description={
            <Space direction="vertical" style={{ width: '100%' }}>
              {alertasCriticas.map((alerta, index) => (
                <div key={index}>
                  <strong>{alerta.mensaje}</strong>
                  <br />
                  <span style={{ fontSize: '12px' }}>
                    Valor: {alerta.valor} | {alerta.recomendacion}
                  </span>
                </div>
              ))}
            </Space>
          }
          type="error"
          showIcon
          icon={<WarningOutlined />}
          style={{ marginBottom: 16 }}
        />
      )}

      {/* ESTADÍSTICAS PRINCIPALES */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Control N°"
              value={control.numero_control}
              prefix={<FileTextOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Edad Gestacional"
              value={control.edad_gestacional}
              suffix="semanas"
              prefix={<CalendarOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Presión Arterial"
              value={control.presion_arterial}
              suffix="mmHg"
              prefix={<HeartOutlined />}
              valueStyle={{ 
                color: (control.presion_arterial_sistolica >= 140 || control.presion_arterial_diastolica >= 90) 
                  ? '#ff4d4f' : '#52c41a' 
              }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="FCF"
              value={control.frecuencia_cardiaca_fetal}
              suffix="lpm"
              prefix={<HeartOutlined />}
              valueStyle={{ 
                color: (control.frecuencia_cardiaca_fetal < 110 || control.frecuencia_cardiaca_fetal > 160)
                  ? '#ff4d4f' : '#52c41a'
              }}
            />
          </Card>
        </Col>
      </Row>

      {/* INDICADORES VISUALES */}
      <Card title="📊 Indicadores Clínicos" style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col span={8}>
            <div style={{ marginBottom: 8 }}>
              <strong>Presión Arterial</strong>
              <Tooltip title={`Sistólica: ${control.presion_arterial_sistolica} / Diastólica: ${control.presion_arterial_diastolica}`}>
                <Progress 
                  percent={calcularPorcentajePA(control.presion_arterial_sistolica, control.presion_arterial_diastolica)}
                  status={(control.presion_arterial_sistolica >= 140 || control.presion_arterial_diastolica >= 90) ? 'exception' : 'success'}
                  strokeColor={(control.presion_arterial_sistolica >= 140 || control.presion_arterial_diastolica >= 90) ? '#ff4d4f' : '#52c41a'}
                />
              </Tooltip>
              <div style={{ fontSize: '12px', color: '#666' }}>
                PAM: {control.presion_arterial_media} mmHg
              </div>
            </div>
          </Col>
          <Col span={8}>
            <div style={{ marginBottom: 8 }}>
              <strong>Frecuencia Cardíaca Fetal</strong>
              <Progress 
                percent={calcularPorcentajeFCF(control.frecuencia_cardiaca_fetal)}
                status={(control.frecuencia_cardiaca_fetal < 110 || control.frecuencia_cardiaca_fetal > 160) ? 'exception' : 'success'}
                strokeColor={(control.frecuencia_cardiaca_fetal < 110 || control.frecuencia_cardiaca_fetal > 160) ? '#ff4d4f' : '#52c41a'}
              />
              <div style={{ fontSize: '12px', color: '#666' }}>
                Rango normal: 110-160 lpm
              </div>
            </div>
          </Col>
          <Col span={8}>
            <div style={{ marginBottom: 8 }}>
              <strong>Estado Nutricional (IMC)</strong>
              <Progress 
                percent={calcularPorcentajeIMC(control.imc_actual)}
                status={(control.imc_actual < 18.5 || control.imc_actual >= 30) ? 'exception' : 'success'}
                strokeColor={(control.imc_actual < 18.5 || control.imc_actual >= 30) ? '#ff4d4f' : '#52c41a'}
              />
              <div style={{ fontSize: '12px', color: '#666' }}>
                IMC: {control.imc_actual} - {control.clasificacion_imc}
              </div>
            </div>
          </Col>
        </Row>
      </Card>

      {/* INFORMACIÓN DEL PACIENTE */}
      <Card title={<><UserOutlined /> Información del Paciente</>} style={{ marginBottom: 16 }}>
        <Descriptions column={2} bordered size="small">
          <Descriptions.Item label="Paciente" span={2}>
            <strong style={{ fontSize: '16px' }}>{control.paciente_nombre}</strong>
          </Descriptions.Item>
          <Descriptions.Item label="Fecha del Control">
            {control.fecha_control_formatted}
          </Descriptions.Item>
          <Descriptions.Item label="N° Control">
            <Badge count={control.numero_control} style={{ backgroundColor: '#1890ff' }} />
          </Descriptions.Item>
        </Descriptions>
      </Card>

      {/* EDAD GESTACIONAL Y TRIMESTRE */}
      <Card title={<><CalendarOutlined /> Edad Gestacional</>} style={{ marginBottom: 16 }}>
        <Descriptions column={3} bordered size="small">
          <Descriptions.Item label="Semanas">
            <Tag color="blue" style={{ fontSize: '14px' }}>{control.semanas_gestacion} semanas</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Días adicionales">
            <Tag color="cyan">{control.dias_gestacion} días</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Edad Gestacional">
            <Tag color="purple" style={{ fontSize: '14px' }}>{control.edad_gestacional}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Trimestre" span={3}>
            {reporte ? (
              <Tag color={reporte.control.trimestre === 1 ? 'cyan' : reporte.control.trimestre === 2 ? 'blue' : 'purple'}>
                {reporte.control.trimestre}° Trimestre
              </Tag>
            ) : (
              <Tag color="blue">Calculando...</Tag>
            )}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      {/* MEDICIONES ANTROPOMÉTRICAS */}
      <Card title={<><RiseOutlined /> Mediciones Antropométricas</>} style={{ marginBottom: 16 }}>
        <Descriptions column={2} bordered size="small">
          <Descriptions.Item label="Peso Actual">
            <strong>{control.peso_actual} kg</strong>
          </Descriptions.Item>
          <Descriptions.Item label="Peso Pre-gestacional">
            {control.peso_pregestacional ? `${control.peso_pregestacional} kg` : 'No registrado'}
          </Descriptions.Item>
          <Descriptions.Item label="Ganancia de Peso">
            {control.ganancia_peso ? (
              <Space>
                <Tag color={control.ganancia_peso > 0 ? 'green' : 'red'}>
                  {control.ganancia_peso > 0 ? <RiseOutlined /> : <FallOutlined />}
                  {control.ganancia_peso > 0 ? '+' : ''}{control.ganancia_peso} kg
                </Tag>
                {reporte?.estado_nutricional && (
                  <span style={{ fontSize: '12px', color: '#666' }}>
                    ({reporte.estado_nutricional.estado})
                  </span>
                )}
              </Space>
            ) : 'No calculado'}
          </Descriptions.Item>
          <Descriptions.Item label="Talla">
            {control.talla} cm
          </Descriptions.Item>
          <Descriptions.Item label="IMC">
            <Space>
              <Tag color={control.imc_actual < 18.5 || control.imc_actual >= 30 ? 'red' : control.imc_actual >= 25 ? 'orange' : 'green'}>
                {control.imc_actual}
              </Tag>
              <span>{control.clasificacion_imc}</span>
            </Space>
          </Descriptions.Item>
          <Descriptions.Item label="Ganancia Semanal">
            {reporte?.estado_nutricional?.ganancia_semanal ? (
              `${reporte.estado_nutricional.ganancia_semanal} kg/semana`
            ) : 'No calculado'}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      {/* SIGNOS VITALES MATERNOS */}
      <Card title={<><HeartOutlined /> Signos Vitales Maternos</>} style={{ marginBottom: 16 }}>
        <Descriptions column={2} bordered size="small">
          <Descriptions.Item label="Presión Arterial">
            <Space>
              <Tag color={(control.presion_arterial_sistolica >= 140 || control.presion_arterial_diastolica >= 90) ? 'red' : 'green'}>
                {control.presion_arterial} mmHg
              </Tag>
              {(control.presion_arterial_sistolica >= 140 || control.presion_arterial_diastolica >= 90) && (
                <Tag color="red">HIPERTENSIÓN</Tag>
              )}
            </Space>
          </Descriptions.Item>
          <Descriptions.Item label="PAM">
            {control.presion_arterial_media} mmHg
          </Descriptions.Item>
          <Descriptions.Item label="FC Materna">
            {control.frecuencia_cardiaca ? `${control.frecuencia_cardiaca} lpm` : 'No registrado'}
          </Descriptions.Item>
          <Descriptions.Item label="Temperatura">
            {control.temperatura ? (
              <Space>
                <span>{control.temperatura} °C</span>
                {control.temperatura >= 38 && <Tag color="red">FIEBRE</Tag>}
              </Space>
            ) : 'No registrada'}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      {/* MEDICIONES OBSTÉTRICAS */}
      <Card title={<><MedicineBoxOutlined /> Mediciones Obstétricas</>} style={{ marginBottom: 16 }}>
        <Descriptions column={2} bordered size="small">
          <Descriptions.Item label="Altura Uterina">
            <Space>
              <strong>{control.altura_uterina} cm</strong>
              {reporte?.evaluacion_crecimiento && (
                <span style={{ fontSize: '12px', color: '#666' }}>
                  (Esperado: {reporte.evaluacion_crecimiento.esperada[0]}-{reporte.evaluacion_crecimiento.esperada[1]} cm)
                </span>
              )}
            </Space>
          </Descriptions.Item>
          <Descriptions.Item label="Diferencia AU">
            {reporte?.evaluacion_crecimiento?.diferencia ? (
              <Tag color={Math.abs(reporte.evaluacion_crecimiento.diferencia) > 3 ? 'red' : 'green'}>
                {reporte.evaluacion_crecimiento.diferencia > 0 ? '+' : ''}{reporte.evaluacion_crecimiento.diferencia} cm
              </Tag>
            ) : 'No calculado'}
          </Descriptions.Item>
          <Descriptions.Item label="FCF">
            <Space>
              <Tag color={(control.frecuencia_cardiaca_fetal < 110 || control.frecuencia_cardiaca_fetal > 160) ? 'red' : 'green'}>
                {control.frecuencia_cardiaca_fetal} lpm
              </Tag>
              {(control.frecuencia_cardiaca_fetal < 110 || control.frecuencia_cardiaca_fetal > 160) && (
                <Tag color="red">ANORMAL</Tag>
              )}
            </Space>
          </Descriptions.Item>
          <Descriptions.Item label="Rango Normal FCF">
            <span style={{ color: '#666' }}>110-160 lpm</span>
          </Descriptions.Item>
          <Descriptions.Item label="Presentación Fetal">
            {control.presentacion_fetal ? (
              <Tag color="blue">{control.presentacion_fetal.charAt(0).toUpperCase() + control.presentacion_fetal.slice(1)}</Tag>
            ) : 'No registrada'}
          </Descriptions.Item>
          <Descriptions.Item label="Movimientos Fetales">
            <Tag color={control.movimientos_fetales === 'ausentes' ? 'red' : control.movimientos_fetales === 'disminuidos' ? 'orange' : 'green'}>
              {control.movimientos_fetales?.charAt(0).toUpperCase() + control.movimientos_fetales?.slice(1)}
            </Tag>
          </Descriptions.Item>
        </Descriptions>
      </Card>

      {/* EVALUACIÓN CLÍNICA */}
      <Card title="🩺 Evaluación Clínica" style={{ marginBottom: 16 }}>
        <Descriptions column={2} bordered size="small">
          <Descriptions.Item label="Edema">
            <Tag color={control.edema === 'severo' || control.edema === 'generalizado' ? 'red' : control.edema === 'moderado' ? 'orange' : 'green'}>
              {control.edema.charAt(0).toUpperCase() + control.edema.slice(1)}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Proteinuria">
            <Tag color={control.proteinuria !== 'negativa' && control.proteinuria !== 'trazas' ? 'red' : 'green'}>
              {control.proteinuria.charAt(0).toUpperCase() + control.proteinuria.slice(1)}
            </Tag>
          </Descriptions.Item>
        </Descriptions>
      </Card>

      {/* RIESGO DE PREECLAMPSIA */}
      {reporte?.riesgo_preeclampsia && (
        <Card 
          title={<><AlertOutlined /> Evaluación de Riesgo de Preeclampsia</>} 
          style={{ marginBottom: 16 }}
        >
          <Space direction="vertical" style={{ width: '100%' }}>
            <div>
              <strong>Nivel de Riesgo: </strong>
              <Tag color={obtenerColorRiesgo(reporte.riesgo_preeclampsia.nivel)} style={{ fontSize: '16px', padding: '5px 15px' }}>
                {reporte.riesgo_preeclampsia.nivel}
              </Tag>
              <span style={{ marginLeft: 10 }}>
                Puntuación: {reporte.riesgo_preeclampsia.puntuacion} puntos
              </span>
            </div>
            {reporte.riesgo_preeclampsia.factores.length > 0 && (
              <div>
                <strong>Factores de Riesgo Identificados:</strong>
                <ul>
                  {reporte.riesgo_preeclampsia.factores.map((factor, index) => (
                    <li key={index}>{factor}</li>
                  ))}
                </ul>
              </div>
            )}
          </Space>
        </Card>
      )}

      {/* ALERTAS */}
      {control.alertas && control.alertas.length > 0 && (
        <Card title={<><WarningOutlined /> Alertas Clínicas ({control.alertas.length})</>} style={{ marginBottom: 16 }}>
          <Timeline>
            {control.alertas.map((alerta, index) => (
              <Timeline.Item 
                key={index}
                color={alerta.tipo === 'critico' ? 'red' : 'orange'}
                dot={obtenerIconoAlerta(alerta.tipo)}
              >
                <div>
                  <Space>
                    <Tag color={alerta.tipo === 'critico' ? 'red' : 'orange'}>
                      {alerta.tipo === 'critico' ? 'CRÍTICO' : 'ADVERTENCIA'}
                    </Tag>
                    <Tag color="blue">{alerta.categoria}</Tag>
                  </Space>
                  <div style={{ marginTop: 8 }}>
                    <strong>{alerta.mensaje}</strong>
                  </div>
                  <div style={{ color: '#666', fontSize: '12px', marginTop: 4 }}>
                    Valor: {alerta.valor}
                  </div>
                  {alerta.recomendacion && (
                    <Alert
                      message="Recomendación"
                      description={alerta.recomendacion}
                      type="info"
                      showIcon
                      style={{ marginTop: 8 }}
                    />
                  )}
                </div>
              </Timeline.Item>
            ))}
          </Timeline>
        </Card>
      )}

      {/* OBSERVACIONES */}
      {control.observaciones && (
        <Card title={<><FileTextOutlined /> Observaciones</>} style={{ marginBottom: 16 }}>
          <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.8 }}>
            {control.observaciones}
          </div>
        </Card>
      )}

      {/* RESUMEN DE EVALUACIÓN */}
      {reporte && (
        <Card title="📋 Resumen de Evaluación" loading={loadingReporte}>
          <Row gutter={16}>
            <Col span={8}>
              <Card size="small" title="Estado Nutricional">
                <Descriptions column={1} size="small">
                  <Descriptions.Item label="Estado">
                    <Tag color={reporte.estado_nutricional.estado === 'Normal' ? 'green' : 'orange'}>
                      {reporte.estado_nutricional.estado}
                    </Tag>
                  </Descriptions.Item>
                  <Descriptions.Item label="Ganancia">
                    {reporte.estado_nutricional.ganancia_peso ? `${reporte.estado_nutricional.ganancia_peso} kg` : 'N/A'}
                  </Descriptions.Item>
                  {reporte.estado_nutricional.ganancia_esperada && (
                    <Descriptions.Item label="Esperada">
                      {reporte.estado_nutricional.ganancia_esperada[0]}-{reporte.estado_nutricional.ganancia_esperada[1]} kg
                    </Descriptions.Item>
                  )}
                </Descriptions>
              </Card>
            </Col>
            <Col span={8}>
              <Card size="small" title="Crecimiento Fetal">
                <Descriptions column={1} size="small">
                  <Descriptions.Item label="Estado">
                    <Tag color={reporte.evaluacion_crecimiento.estado === 'Normal' ? 'green' : 'orange'}>
                      {reporte.evaluacion_crecimiento.estado}
                    </Tag>
                  </Descriptions.Item>
                  <Descriptions.Item label="AU Actual">
                    {reporte.evaluacion_crecimiento.altura_uterina} cm
                  </Descriptions.Item>
                  {reporte.evaluacion_crecimiento.esperada && (
                    <Descriptions.Item label="AU Esperada">
                      {reporte.evaluacion_crecimiento.esperada[0]}-{reporte.evaluacion_crecimiento.esperada[1]} cm
                    </Descriptions.Item>
                  )}
                </Descriptions>
              </Card>
            </Col>
            <Col span={8}>
              <Card size="small" title="Riesgo Preeclampsia">
                <Descriptions column={1} size="small">
                  <Descriptions.Item label="Nivel">
                    <Tag color={obtenerColorRiesgo(reporte.riesgo_preeclampsia.nivel)}>
                      {reporte.riesgo_preeclampsia.nivel}
                    </Tag>
                  </Descriptions.Item>
                  <Descriptions.Item label="Puntuación">
                    {reporte.riesgo_preeclampsia.puntuacion} puntos
                  </Descriptions.Item>
                  <Descriptions.Item label="Factores">
                    {reporte.riesgo_preeclampsia.factores.length}
                  </Descriptions.Item>
                </Descriptions>
              </Card>
            </Col>
          </Row>
        </Card>
      )}

      {/* BOTÓN CERRAR */}
      <div style={{ textAlign: 'center', marginTop: 24 }}>
        <Button type="primary" size="large" onClick={onClose}>
          Cerrar Detalle
        </Button>
      </div>
    </div>
  );
};

export default DetalleControl;