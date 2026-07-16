import React from 'react';
import { Card, Descriptions, Space, Tag, Badge, Typography } from 'antd';
import {
  CalendarOutlined, UserOutlined, HeartOutlined, CheckCircleOutlined, ScanOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { Ecografia } from '../../../services/ecografiasService';

const { Text } = Typography;

interface DetalleEcoDatosGeneralesProps {
  ecografia: Ecografia;
}

const DetalleEcoDatosGenerales: React.FC<DetalleEcoDatosGeneralesProps> = ({ ecografia }) => (
  <Card
    title={
      <Space>
        <ScanOutlined />
        Datos Generales
      </Space>
    }
    style={{ marginBottom: 16 }}
  >
    <Descriptions column={{ xs: 1, sm: 2 }} bordered>
      <Descriptions.Item label="Paciente">
        {ecografia.paciente_nombre || `ID: ${ecografia.paciente}`}
      </Descriptions.Item>
      <Descriptions.Item label="Médico">
        <Space>
          <UserOutlined style={{ color: '#1890ff' }} />
          {ecografia.medico_nombre || '-'}
          {ecografia.medico_nombre && <CheckCircleOutlined style={{ color: '#52c41a' }} />}
        </Space>
      </Descriptions.Item>
      <Descriptions.Item label="Fecha del Estudio">
        <Space>
          <CalendarOutlined />
          {dayjs(ecografia.fecha_ecografia).format('DD/MM/YYYY')}
        </Space>
      </Descriptions.Item>
      <Descriptions.Item label="Tipo de Ecografía">
        <Tag color="blue">
          {ecografia.tipo_ecografia?.replace('_', ' ').toUpperCase()}
        </Tag>
      </Descriptions.Item>
      <Descriptions.Item label="Edad Gestacional">
        <Text strong>{ecografia.edad_gestacional_texto}</Text>
      </Descriptions.Item>
      <Descriptions.Item label="Número de Fetos">
        {ecografia.numero_fetos || 1}
      </Descriptions.Item>
      <Descriptions.Item label="Vitalidad Fetal">
        {ecografia.vitalidad_fetal ? (
          <Badge status="success" text="Presente" />
        ) : (
          <Badge status="error" text="Ausente" />
        )}
      </Descriptions.Item>
      {ecografia.frecuencia_cardiaca_fetal && (
        <Descriptions.Item label="FCF">
          <Space>
            <HeartOutlined style={{ color: '#ff4d4f' }} />
            {ecografia.frecuencia_cardiaca_fetal} lpm
          </Space>
        </Descriptions.Item>
      )}
    </Descriptions>
  </Card>
);

export default DetalleEcoDatosGenerales;
