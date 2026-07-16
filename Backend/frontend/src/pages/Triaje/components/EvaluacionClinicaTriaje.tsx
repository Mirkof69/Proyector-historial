import React from 'react';
import { Descriptions, Tag, Space, Divider, Typography } from 'antd';
import { UserOutlined, HeartOutlined, DashboardOutlined, MedicineBoxOutlined } from '@ant-design/icons';
import { TriajeEnfermeria } from '../../../services/triajeService';
import { Clasificacion } from './triajeUtils';

const { Title, Text } = Typography;

interface EvaluacionClinicaTriajeProps {
  triaje: TriajeEnfermeria;
  clasificacionIMC: Clasificacion | null;
  clasificacionPresion: Clasificacion;
}

const EvaluacionClinicaTriaje: React.FC<EvaluacionClinicaTriajeProps> = ({
  triaje,
  clasificacionIMC,
  clasificacionPresion,
}) => (
  <section className="detail-section">
    <Title level={4}><UserOutlined /> Identificación del Paciente</Title>
    <Descriptions bordered column={{ xs: 1, sm: 2 }} className="custom-descriptions">
      <Descriptions.Item label="Nombre Completo" span={2}>
        <Text strong style={{ fontSize: '1.1em' }}>
          {triaje.paciente_info?.nombre_completo || triaje.paciente_nombre || 'No especificado'}
        </Text>
      </Descriptions.Item>
      <Descriptions.Item label="Nro. Historia">
        {(triaje.paciente_info as any)?.id_clinico || (triaje.paciente_info as any)?.ci || '-'}
      </Descriptions.Item>
      <Descriptions.Item label="Responsable Triaje">
        {triaje.enfermera_info?.nombre || 'Personal de Enfermería'}
      </Descriptions.Item>
    </Descriptions>

    <Divider />

    <Title level={4}><HeartOutlined /> Evaluación de Signos Vitales</Title>
    <Descriptions bordered column={{ xs: 1, sm: 2 }} className="custom-descriptions">
      <Descriptions.Item label="Presión Arterial">
        <Space>
          <Text strong>{triaje.presion_sistolica}/{triaje.presion_diastolica} mmHg</Text>
          <Tag color={clasificacionPresion.color}>{clasificacionPresion.text}</Tag>
        </Space>
      </Descriptions.Item>
      <Descriptions.Item label="Temperatura">
        <Text strong>{triaje.temperatura}°C</Text>
        {triaje.temperatura >= 38 && <Tag color="red" style={{ marginLeft: 8 }}>Febrícula/Fiebre</Tag>}
      </Descriptions.Item>
      <Descriptions.Item label="Frecuencia Cardíaca">
        <Text strong>{triaje.frecuencia_cardiaca} bpm</Text>
      </Descriptions.Item>
      <Descriptions.Item label="Frecuencia Respiratoria">
        <Text strong>{triaje.frecuencia_respiratoria} rpm</Text>
      </Descriptions.Item>
      {triaje.saturacion_oxigeno && (
        <Descriptions.Item label="Saturación O₂">
          <Text strong>{triaje.saturacion_oxigeno}%</Text>
          {triaje.saturacion_oxigeno < 95 && <Tag color="red">Hipoxia</Tag>}
        </Descriptions.Item>
      )}
      {triaje.dolor_escala !== null && triaje.dolor_escala !== undefined && (
        <Descriptions.Item label="Escala de Dolor">
          <Text strong>{triaje.dolor_escala}/10</Text>
          <Tag color={triaje.dolor_escala! >= 7 ? 'red' : triaje.dolor_escala! >= 4 ? 'orange' : 'green'}>
            {triaje.dolor_escala! >= 7 ? 'Severo' : triaje.dolor_escala! >= 4 ? 'Moderado' : 'Leve'}
          </Tag>
        </Descriptions.Item>
      )}
    </Descriptions>

    <Divider />

    <Title level={4}><DashboardOutlined /> Antropometría</Title>
    <Descriptions bordered column={{ xs: 1, sm: 3 }} className="custom-descriptions">
      <Descriptions.Item label="Peso Antropomético">
        <Text strong>{triaje.peso_kg}</Text> kg
      </Descriptions.Item>
      <Descriptions.Item label="Talla/Estatura">
        <Text strong>{triaje.talla_cm}</Text> cm
      </Descriptions.Item>
      {triaje.perimetro_abdominal_cm && (
        <Descriptions.Item label="P. Abdominal">
          {triaje.perimetro_abdominal_cm} cm
        </Descriptions.Item>
      )}
      {triaje.imc && (
        <Descriptions.Item label="Estado Nutricional (IMC)" span={3}>
          <Space size="large">
            <Text strong style={{ fontSize: '1.2em' }}>{Number(triaje.imc).toFixed(2)}</Text>
            {clasificacionIMC && (
              <Tag color={clasificacionIMC.color} style={{ padding: '4px 12px', fontSize: '1em' }}>
                {clasificacionIMC.text.toUpperCase()}
              </Tag>
            )}
          </Space>
        </Descriptions.Item>
      )}
    </Descriptions>

    <Divider />

    <Title level={4}><MedicineBoxOutlined /> Evaluación Subjetiva y Motivo</Title>
    <Descriptions bordered column={1} className="custom-descriptions">
      <Descriptions.Item label="Motivo de la Visita">
        <div style={{ whiteSpace: 'pre-wrap', minHeight: '60px' }}>
          {triaje.motivo_visita || triaje.motivo_consulta || 'Sin especificar'}
        </div>
      </Descriptions.Item>
      <Descriptions.Item label="Nivel de Conciencia">
        <Tag color="geekblue" style={{ fontSize: '1.1em', padding: '5px 15px' }}>
          {(triaje.nivel_conciencia || 'alerta').toUpperCase()}
        </Tag>
      </Descriptions.Item>
      {triaje.observaciones && (
        <Descriptions.Item label="Observaciones de Enfermería">
          <div style={{ fontStyle: 'italic' }}>{triaje.observaciones}</div>
        </Descriptions.Item>
      )}
    </Descriptions>
  </section>
);

export default EvaluacionClinicaTriaje;
