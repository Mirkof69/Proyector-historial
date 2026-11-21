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
          <Badge count={examen.dias_desde_solicitud} showZero className={`laboratorio-page__dias ${examen.dias_desde_solicitud > 3 ? 'laboratorio-page__dias--vencido' : 'laboratorio-page__dias--a-tiempo'}`} />
        </Descriptions.Item>
      )}
      {examen.esta_vencido !== undefined && (
        <Descriptions.Item label="Estado de tiempo">
          {examen.esta_vencido ? (
            <Tag color="error">Vencido</Tag>
          ) : (
            <Tag color="success">A tiempo</Tag>
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
