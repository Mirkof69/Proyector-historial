import React, { useState, useEffect } from 'react';
import { Card, Descriptions, Button, Tag, Spin, message, Alert, Row, Col, Statistic } from 'antd';
import { ArrowLeftOutlined, EditOutlined, WarningOutlined } from '@ant-design/icons';
import axios from 'axios';
import { authService } from '../services/authService';
import dayjs from 'dayjs';

interface DetalleControlProps {
  controlId: number;
  onBack: () => void;
  onEdit: (id: number) => void;
}

interface Control {
  id: number;
  embarazo_id: number;
  paciente: number;
  paciente_nombre?: string;
  numero_control: number;
  fecha_control: string;
  semanas_gestacion: number;
  dias_gestacion?: number;
  edad_gestacional?: string;
  peso_actual: number;
  peso_pregestacional?: number;
  ganancia_peso?: number;
  talla?: number;
  imc_actual?: number;
  clasificacion_imc?: string;
  presion_arterial?: string;
  presion_arterial_sistolica?: number;
  presion_arterial_diastolica?: number;
  presion_arterial_media?: number;
  frecuencia_cardiaca?: number;
  temperatura?: number;
  altura_uterina: number;
  frecuencia_cardiaca_fetal: number;
  presentacion_fetal?: string;
  movimientos_fetales?: string;
  edema?: string;
  proteinuria?: string;
  observaciones?: string;
  fecha_registro: string;
}

const DetalleControl: React.FC<DetalleControlProps> = ({ controlId, onBack, onEdit }) => {
  const [control, setControl] = useState<Control | null>(null);
  const [loading, setLoading] = useState(true);
  const [alertas, setAlertas] = useState<string[]>([]);

  useEffect(() => {
    fetchControl();
  }, [controlId]);

  const fetchControl = async () => {
    setLoading(true);
    try {
      const token = authService.getToken();
      const response = await axios.get(`http://127.0.0.1:8000/api/controles/${controlId}/`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setControl(response.data);
      evaluarAlertas(response.data);
    } catch (error) {
      message.error('Error al cargar datos del control');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const evaluarAlertas = (control: Control) => {
    const alertasEncontradas: string[] = [];

    // Alerta de hipertensión
    if (control.presion_arterial_sistolica && control.presion_arterial_diastolica) {
      if (control.presion_arterial_sistolica >= 140 || control.presion_arterial_diastolica >= 90) {
        alertasEncontradas.push('🔴 HIPERTENSIÓN DETECTADA - Requiere evaluación urgente para descartar preeclampsia');
      } else if (control.presion_arterial_sistolica >= 120 || control.presion_arterial_diastolica >= 80) {
        alertasEncontradas.push('🟠 Pre-hipertensión - Monitoreo cercano recomendado');
      }
    }

    // Alerta de FCF anormal
    if (control.frecuencia_cardiaca_fetal) {
      if (control.frecuencia_cardiaca_fetal < 110 || control.frecuencia_cardiaca_fetal > 160) {
        alertasEncontradas.push('🔴 FCF ANORMAL - Frecuencia cardíaca fetal fuera de rango (110-160 lpm). Realizar NST.');
      }
    }

    // Alerta de edema severo
    if (control.edema === 'severo') {
      alertasEncontradas.push('🔴 EDEMA SEVERO - Evaluar preeclampsia. Solicitar proteinuria 24h.');
    }

    // Alerta de proteinuria
    if (control.proteinuria && ['positiva_1', 'positiva_2', 'positiva_3'].includes(control.proteinuria)) {
      alertasEncontradas.push('🔴 PROTEINURIA POSITIVA - Evaluar función renal y preeclampsia inmediatamente');
    }

    // Alerta de IMC
    if (control.imc_actual) {
      if (control.imc_actual < 18.5) {
        alertasEncontradas.push('🟠 Bajo peso - Evaluación nutricional y suplementación recomendada');
      } else if (control.imc_actual >= 30) {
        alertasEncontradas.push('🟠 Obesidad - Control de peso, seguimiento nutricional y mayor riesgo de complicaciones');
      }
    }

    // Alerta de movimientos fetales ausentes
    if (control.movimientos_fetales === 'ausentes') {
      alertasEncontradas.push('🔴 MOVIMIENTOS FETALES AUSENTES - EVALUACIÓN INMEDIATA. Realizar NST y ecografía.');
    } else if (control.movimientos_fetales === 'disminuidos') {
      alertasEncontradas.push('🟠 Movimientos fetales disminuidos - Realizar conteo de movimientos y NST');
    }

    setAlertas(alertasEncontradas);
  };

  const evaluarPresionArterial = (sistolica?: number, diastolica?: number) => {
    if (!sistolica || !diastolica) return { estado: 'Sin datos', color: 'default' };
    
    if (sistolica >= 140 || diastolica >= 90) {
      return { estado: 'HIPERTENSIÓN', color: 'red' };
    } else if (sistolica >= 120 || diastolica >= 80) {
      return { estado: 'Pre-hipertensión', color: 'orange' };
    } else {
      return { estado: 'Normal', color: 'green' };
    }
  };

  const evaluarFCF = (fcf?: number) => {
    if (!fcf) return { estado: 'Sin datos', color: 'default' };
    if (fcf < 110 || fcf > 160) {
      return { estado: 'ANORMAL', color: 'red' };
    } else {
      return { estado: 'Normal', color: 'green' };
    }
  };

  const evaluarIMC = (imc?: number) => {
    if (!imc) return { color: 'default' };
    if (imc < 18.5) return { color: 'orange' };
    if (imc < 25) return { color: 'green' };
    if (imc < 30) return { color: 'orange' };
    return { color: 'red' };
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!control) {
    return (
      <div style={{ padding: 24 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={onBack} style={{ marginBottom: 16 }}>
          Volver a la lista
        </Button>
        <Card>
          <p>Control no encontrado</p>
        </Card>
      </div>
    );
  }

  const paEval = evaluarPresionArterial(control.presion_arterial_sistolica, control.presion_arterial_diastolica);
  const fcfEval = evaluarFCF(control.frecuencia_cardiaca_fetal);
  const imcEval = evaluarIMC(control.imc_actual);

  return (
    <div style={{ padding: 24 }}>
      <Button icon={<ArrowLeftOutlined />} onClick={onBack} style={{ marginBottom: 16 }}>
        Volver a la lista
      </Button>

      {alertas.length > 0 && (
        <Alert
          message="⚠️ ALERTAS CLÍNICAS DETECTADAS"
          description={
            <ul style={{ marginBottom: 0, paddingLeft: 20 }}>
              {alertas.map((alerta, index) => (
                <li key={index} style={{ marginBottom: 8 }}>{alerta}</li>
              ))}
            </ul>
          }
          type="error"
          showIcon
          icon={<WarningOutlined />}
          style={{ marginBottom: 16 }}
        />
      )}

      <Card
        title={`Control Prenatal #${control.numero_control}`}
        extra={
          <Button 
            type="primary" 
            icon={<EditOutlined />}
            onClick={() => onEdit(control.id)}
          >
            Editar
          </Button>
        }
      >
        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col span={6}>
            <Statistic 
              title="Edad Gestacional" 
              value={`${control.semanas_gestacion}+${control.dias_gestacion || 0}`}
              suffix="semanas"
            />
          </Col>
          <Col span={6}>
            <Statistic 
              title="Peso Actual" 
              value={control.peso_actual || 0}
              suffix="kg"
              precision={1}
            />
          </Col>
          <Col span={6}>
            <Statistic 
              title="Presión Arterial" 
              value={`${control.presion_arterial_sistolica}/${control.presion_arterial_diastolica}`}
              valueStyle={{ color: paEval.color === 'red' ? '#cf1322' : paEval.color === 'orange' ? '#faad14' : '#3f8600' }}
            />
          </Col>
          <Col span={6}>
            <Statistic 
              title="FCF" 
              value={control.frecuencia_cardiaca_fetal || 0}
              suffix="lpm"
              valueStyle={{ color: fcfEval.color === 'red' ? '#cf1322' : '#3f8600' }}
            />
          </Col>
        </Row>

        <Descriptions bordered column={2}>
          <Descriptions.Item label="Paciente" span={2}>
            {control.paciente_nombre || `ID: ${control.paciente}`}
          </Descriptions.Item>

          <Descriptions.Item label="Embarazo ID">
            {control.embarazo_id}
          </Descriptions.Item>
          <Descriptions.Item label="Fecha Control">
            {dayjs(control.fecha_control).format('DD/MM/YYYY')}
          </Descriptions.Item>

          <Descriptions.Item label="Semanas Gestación">
            <strong>{control.semanas_gestacion} + {control.dias_gestacion || 0} días</strong>
          </Descriptions.Item>
          <Descriptions.Item label="Peso Pregestacional">
            {control.peso_pregestacional ? `${control.peso_pregestacional} kg` : 'No registrado'}
          </Descriptions.Item>

          <Descriptions.Item label="Ganancia de Peso">
            {control.ganancia_peso ? (
              <Tag color={control.ganancia_peso > 0 ? 'green' : 'red'}>
                {control.ganancia_peso > 0 ? '+' : ''}{control.ganancia_peso} kg
              </Tag>
            ) : 'No calculada'}
          </Descriptions.Item>
          <Descriptions.Item label="Talla">
            {control.talla ? `${control.talla} cm` : 'No registrada'}
          </Descriptions.Item>

          <Descriptions.Item label="IMC">
            {control.imc_actual ? (
              <>
                {control.imc_actual.toFixed(2)} <Tag color={imcEval.color}>{control.clasificacion_imc}</Tag>
              </>
            ) : 'No calculado'}
          </Descriptions.Item>
          <Descriptions.Item label="Presión Arterial">
            {control.presion_arterial_sistolica && control.presion_arterial_diastolica ? (
              <>
                {control.presion_arterial_sistolica}/{control.presion_arterial_diastolica} mmHg <Tag color={paEval.color}>{paEval.estado}</Tag>
              </>
            ) : 'No registrada'}
          </Descriptions.Item>

          <Descriptions.Item label="PAM">
            {control.presion_arterial_media ? `${control.presion_arterial_media.toFixed(2)} mmHg` : 'No calculada'}
          </Descriptions.Item>
          <Descriptions.Item label="FC Materna">
            {control.frecuencia_cardiaca ? `${control.frecuencia_cardiaca} lpm` : 'No registrada'}
          </Descriptions.Item>

          <Descriptions.Item label="Temperatura">
            {control.temperatura ? `${control.temperatura} °C` : 'No registrada'}
          </Descriptions.Item>
          <Descriptions.Item label="Altura Uterina">
            {control.altura_uterina ? `${control.altura_uterina} cm` : 'No registrada'}
          </Descriptions.Item>

          <Descriptions.Item label="FCF">
            {control.frecuencia_cardiaca_fetal ? (
              <>
                {control.frecuencia_cardiaca_fetal} lpm <Tag color={fcfEval.color}>{fcfEval.estado}</Tag>
              </>
            ) : 'No registrada'}
          </Descriptions.Item>
          <Descriptions.Item label="Presentación Fetal">
            {control.presentacion_fetal ? (
              <Tag>{control.presentacion_fetal.charAt(0).toUpperCase() + control.presentacion_fetal.slice(1)}</Tag>
            ) : 'No registrada'}
          </Descriptions.Item>

          <Descriptions.Item label="Movimientos Fetales">
            {control.movimientos_fetales ? (
              <Tag color={control.movimientos_fetales === 'presentes' ? 'green' : control.movimientos_fetales === 'ausentes' ? 'red' : 'orange'}>
                {control.movimientos_fetales.charAt(0).toUpperCase() + control.movimientos_fetales.slice(1)}
              </Tag>
            ) : 'No registrado'}
          </Descriptions.Item>
          <Descriptions.Item label="Edema">
            {control.edema ? (
              <Tag color={control.edema === 'no' ? 'green' : control.edema === 'severo' ? 'red' : 'orange'}>
                {control.edema.charAt(0).toUpperCase() + control.edema.slice(1)}
              </Tag>
            ) : 'No registrado'}
          </Descriptions.Item>

          <Descriptions.Item label="Proteinuria" span={2}>
            {control.proteinuria ? (
              <Tag color={control.proteinuria === 'negativa' ? 'green' : 'red'}>
                {control.proteinuria.replace('positiva_1', '+').replace('positiva_2', '++').replace('positiva_3', '+++').replace('_', ' ').toUpperCase()}
              </Tag>
            ) : 'No registrada'}
          </Descriptions.Item>

          <Descriptions.Item label="Fecha Registro" span={2}>
            {dayjs(control.fecha_registro).format('DD/MM/YYYY HH:mm')}
          </Descriptions.Item>

          {control.observaciones && (
            <Descriptions.Item label="Observaciones" span={2}>
              {control.observaciones}
            </Descriptions.Item>
          )}
        </Descriptions>
      </Card>

      <Card title="Interpretación Clínica" style={{ marginTop: 16 }}>
        <Row gutter={16}>
          <Col span={12}>
            <h4>Signos Vitales Maternos:</h4>
            <ul>
              <li><strong>Presión Arterial:</strong> {paEval.estado} ({control.presion_arterial_sistolica}/{control.presion_arterial_diastolica} mmHg)</li>
              {control.presion_arterial_media && (
                <li><strong>PAM:</strong> {control.presion_arterial_media.toFixed(2)} mmHg</li>
              )}
              {control.frecuencia_cardiaca && (
                <li><strong>FC Materna:</strong> {control.frecuencia_cardiaca} lpm</li>
              )}
              {control.temperatura && (
                <li><strong>Temperatura:</strong> {control.temperatura} °C</li>
              )}
            </ul>
          </Col>
          <Col span={12}>
            <h4>Evaluación Fetal:</h4>
            <ul>
              <li><strong>FCF:</strong> {fcfEval.estado} ({control.frecuencia_cardiaca_fetal} lpm)</li>
              <li><strong>Edad Gestacional:</strong> {control.semanas_gestacion}+{control.dias_gestacion || 0} semanas</li>
              <li><strong>Altura Uterina:</strong> {control.altura_uterina} cm</li>
              {control.presentacion_fetal && (
                <li><strong>Presentación:</strong> {control.presentacion_fetal}</li>
              )}
              {control.movimientos_fetales && (
                <li><strong>Movimientos:</strong> {control.movimientos_fetales}</li>
              )}
            </ul>
          </Col>
        </Row>

        {control.imc_actual && (
          <>
            <h4>Estado Nutricional:</h4>
            <ul>
              <li><strong>IMC:</strong> {control.imc_actual.toFixed(2)} - {control.clasificacion_imc}</li>
              {control.ganancia_peso && (
                <li><strong>Ganancia de Peso:</strong> {control.ganancia_peso > 0 ? '+' : ''}{control.ganancia_peso} kg</li>
              )}
            </ul>
          </>
        )}

        {(control.edema !== 'no' || control.proteinuria !== 'negativa') && (
          <>
            <h4>Hallazgos Importantes:</h4>
            <ul>
              {control.edema && control.edema !== 'no' && (
                <li><strong>Edema:</strong> {control.edema}</li>
              )}
              {control.proteinuria && control.proteinuria !== 'negativa' && (
                <li><strong>Proteinuria:</strong> {control.proteinuria.replace('positiva_1', '+').replace('positiva_2', '++').replace('positiva_3', '+++')}</li>
              )}
            </ul>
          </>
        )}
      </Card>
    </div>
  );
};

export default DetalleControl;