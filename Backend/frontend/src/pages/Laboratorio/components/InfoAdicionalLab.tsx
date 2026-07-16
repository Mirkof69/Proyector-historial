import React from 'react';
import { Card, Space, Tag, Descriptions, Badge } from 'antd';
import { InfoCircleOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';

interface InfoAdicionalLabProps {
  examen: any;
}

const InfoAdicionalLab: React.FC<InfoAdicionalLabProps> = ({ examen }) => (
  <Card
    title={
      <Space>
        <InfoCircleOutlined />
        Información Adicional
      </Space>
    }
  >
    <Descriptions column={1} bordered size="small">
      {examen.dias_desde_solicitud !== undefined && (
        <Descriptions.Item label="Días desde solicitud">
          <Badge count={examen.dias_desde_solicitud} showZero color={examen.dias_desde_solicitud > 3 ? 'red' : 'blue'} />
        </Descriptions.Item>
      )}
      {examen.esta_vencido !== undefined && (
        <Descriptions.Item label="Estado de tiempo">
          {examen.esta_vencido ? (
            <Tag color="red">Vencido</Tag>
          ) : (
            <Tag color="green">A tiempo</Tag>
          )}
        </Descriptions.Item>
      )}
      <Descriptions.Item label="Fecha de Registro">
        {examen.fecha_creacion
          ? dayjs(examen.fecha_creacion).format('DD/MM/YYYY HH:mm')
          : '-'}
      </Descriptions.Item>
      <Descriptions.Item label="Última Modificación">
        {examen.fecha_actualizacion
          ? dayjs(examen.fecha_actualizacion).format('DD/MM/YYYY HH:mm')
          : '-'}
      </Descriptions.Item>
    </Descriptions>
  </Card>
);

export default InfoAdicionalLab;
