import React from 'react';
import { Card, Descriptions, Space, Tag, Typography } from 'antd';
import { InfoCircleOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { Ecografia } from '../../../services/ecografiasService';

const { Text } = Typography;

interface DetalleEcoInfoAdicionalProps {
  ecografia: Ecografia;
}

const DetalleEcoInfoAdicional: React.FC<DetalleEcoInfoAdicionalProps> = ({ ecografia }) => (
  <Card
    title={
      <Space>
        <InfoCircleOutlined />
        Información Adicional
      </Space>
    }
  >
    <Descriptions column={1} bordered size="small">
      <Descriptions.Item label="Calidad del Estudio">
        <Tag>{ecografia.calidad_estudio || 'No especificada'}</Tag>
      </Descriptions.Item>
      {ecografia.limitaciones_tecnicas && (
        <Descriptions.Item label="Limitaciones">
          {ecografia.limitaciones_tecnicas}
        </Descriptions.Item>
      )}
      <Descriptions.Item label="Fecha de Registro">
        {ecografia.fecha_registro
          ? dayjs(ecografia.fecha_registro).format('DD/MM/YYYY HH:mm')
          : '-'}
      </Descriptions.Item>
      <Descriptions.Item label="Registrado por">
        {ecografia.created_by_nombre || <Text type="secondary">No registrado</Text>}
      </Descriptions.Item>
      <Descriptions.Item label="Última Modificación">
        {ecografia.fecha_modificacion
          ? dayjs(ecografia.fecha_modificacion).format('DD/MM/YYYY HH:mm')
          : '-'}
      </Descriptions.Item>
      <Descriptions.Item label="Modificado por">
        {ecografia.updated_by_nombre || <Text type="secondary">No registrado</Text>}
      </Descriptions.Item>
    </Descriptions>
  </Card>
);

export default DetalleEcoInfoAdicional;
