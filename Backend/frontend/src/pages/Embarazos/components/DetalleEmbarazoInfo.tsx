import React from 'react';
import { Card, Descriptions, Tag, Space, Typography, Progress, Tooltip, Badge } from 'antd';
import {
  HeartOutlined, CalendarOutlined, WarningOutlined, UserOutlined, InfoCircleOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { Embarazo } from '../../../services/embarazosService';
import { Paciente } from '../../../services/pacientesService';

const { Title, Text, Paragraph } = Typography;

interface DetalleEmbarazoInfoProps {
  embarazo: Embarazo;
  paciente: Paciente | null;
  nombrePaciente: string;
  estadoConfig: { color: string; icon: React.ReactNode; texto: string };
  riesgoConfig: { color: string; texto: string };
  formulaObstetrica: string;
  eg: { semanas: number; dias: number; texto: string };
  trimestre: { numero: number; texto: string; color: string };
  diasRestantes: number;
  progreso: number;
  imcClasificacion: { texto: string; color: string } | null;
}

const DetalleEmbarazoInfo: React.FC<DetalleEmbarazoInfoProps> = ({
  embarazo, paciente, nombrePaciente, estadoConfig, riesgoConfig, formulaObstetrica,
  eg, trimestre, diasRestantes, progreso, imcClasificacion,
}) => (
  <Card
    title={
      <Space>
        <HeartOutlined style={{ fontSize: 20, color: '#ff4d4f' }} />
        <Title level={4} style={{ margin: 0 }}>
          Embarazo #{embarazo.id}
        </Title>
      </Space>
    }
    extra={
      <Space>
        <Tag color={estadoConfig.color} icon={estadoConfig.icon}>
          {estadoConfig.texto}
        </Tag>
        <Tag color={riesgoConfig.color} icon={embarazo.riesgo_embarazo === 'alto' ? <WarningOutlined /> : undefined}>
          {riesgoConfig.texto}
        </Tag>
      </Space>
    }
  >
    <Descriptions bordered column={2} size="middle">
      {/* INFORMACIÓN DE LA PACIENTE */}
      <Descriptions.Item label={<><UserOutlined /> Paciente</>} span={2}>
        <Space>
          <Text strong style={{ fontSize: 16 }}>
            {nombrePaciente}
          </Text>
          {paciente && <Tag color="blue">{paciente.id_clinico}</Tag>}
        </Space>
      </Descriptions.Item>

      {/* DATOS OBSTÉTRICOS */}
      <Descriptions.Item label="Número de Gesta">
        <Tag color="geekblue" style={{ fontSize: 14 }}>
          G{embarazo.numero_gesta}
        </Tag>
      </Descriptions.Item>

      <Descriptions.Item label="Fórmula Obstétrica">
        <Tooltip title="Gesta-Partos-Cesáreas-Abortos">
          <Tag color="purple" style={{ fontSize: 14 }}>
            {formulaObstetrica}
          </Tag>
        </Tooltip>
      </Descriptions.Item>

      <Descriptions.Item label="Tipo de Embarazo">
        <Tag color={embarazo.tipo_embarazo === 'multiple' || embarazo.tipo_embarazo === 'gemelar' ? 'orange' : 'default'}>
          {embarazo.tipo_embarazo ? (embarazo.tipo_embarazo.charAt(0).toUpperCase() +
            embarazo.tipo_embarazo.slice(1)) : 'Simple'}
        </Tag>
      </Descriptions.Item>

      <Descriptions.Item label="Hijos Vivos">
        <Badge count={embarazo.hijos_vivos || 0} showZero style={{ backgroundColor: '#52c41a' }} />
      </Descriptions.Item>

      {/* FECHAS IMPORTANTES */}
      <Descriptions.Item label={<><CalendarOutlined /> Fecha Última Menstruación (FUM)</>}>
        <Text strong>{dayjs(embarazo.fecha_ultima_menstruacion).format('DD/MM/YYYY')}</Text>
      </Descriptions.Item>

      <Descriptions.Item label={<><CalendarOutlined /> Fecha Probable de Parto (FPP)</>}>
        <Space>
          <Text strong>{dayjs(embarazo.fecha_probable_parto).format('DD/MM/YYYY')}</Text>
          <Tag color={diasRestantes < 30 ? 'error' : 'success'}>
            {diasRestantes} días
          </Tag>
        </Space>
      </Descriptions.Item>

      {/* EDAD GESTACIONAL */}
      <Descriptions.Item label="Edad Gestacional Actual" span={2}>
        <Space size="large">
          <Text strong style={{ fontSize: '18px', color: '#1890ff' }}>
            {eg.texto}
          </Text>
          <Tag color={trimestre.color} style={{ fontSize: 14 }}>
            {trimestre.texto}
          </Tag>
        </Space>
      </Descriptions.Item>

      {/* PROGRESO */}
      <Descriptions.Item label="Progreso del Embarazo" span={2}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Progress
            percent={progreso}
            status="active"
            strokeColor={{
              '0%': '#87d068',
              '50%': '#1890ff',
              '100%': '#722ed1',
            }}
          />
          <Space>
            <Text>
              <strong>{diasRestantes} días restantes</strong> hasta la FPP
            </Text>
            {diasRestantes < 30 && (
              <Tag color="orange" icon={<InfoCircleOutlined />}>
                Término cercano
              </Tag>
            )}
          </Space>
        </Space>
      </Descriptions.Item>

      {/* DATOS ANTROPOMÉTRICOS */}
      {embarazo.peso_pregestacional && (
        <Descriptions.Item label="Peso Pregestacional">
          {embarazo.peso_pregestacional} kg
        </Descriptions.Item>
      )}

      {embarazo.talla_materna && (
        <Descriptions.Item label="Talla Materna">
          {embarazo.talla_materna} cm
        </Descriptions.Item>
      )}

      {embarazo.imc_pregestacional && imcClasificacion && (
        <Descriptions.Item label="IMC Pregestacional" span={2}>
          <Space>
            <Text strong>{embarazo.imc_pregestacional.toFixed(2)}</Text>
            <Tag color={imcClasificacion.color}>{imcClasificacion.texto}</Tag>
          </Space>
        </Descriptions.Item>
      )}

      {/* OTROS DATOS */}
      {embarazo.grupo_sanguineo_pareja && (
        <Descriptions.Item label="Grupo Sanguíneo Pareja" span={2}>
          <Tag color="red">{embarazo.grupo_sanguineo_pareja}</Tag>
        </Descriptions.Item>
      )}

      {embarazo.medico_responsable && (
        <Descriptions.Item label="Médico Responsable" span={2}>
          <Text>{embarazo.medico_responsable}</Text>
        </Descriptions.Item>
      )}

      {embarazo.notas && (
        <Descriptions.Item label="Observaciones Clínicas" span={2}>
          <Paragraph style={{ marginBottom: 0, whiteSpace: 'pre-wrap' }}>
            {embarazo.notas}
          </Paragraph>
        </Descriptions.Item>
      )}

      {/* METADATOS */}
      <Descriptions.Item label="Fecha de Registro" span={2}>
        <Space>
          <CalendarOutlined />
          {embarazo.fecha_registro
            ? dayjs(embarazo.fecha_registro).format('DD/MM/YYYY HH:mm')
            : 'No disponible'}
        </Space>
      </Descriptions.Item>
    </Descriptions>
  </Card>
);

export default DetalleEmbarazoInfo;
