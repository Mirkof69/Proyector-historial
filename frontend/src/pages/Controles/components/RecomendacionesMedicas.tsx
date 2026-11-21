import React from 'react';
import { Card, Tag, Space, Typography, List, Avatar } from 'antd';
import { MedicineBoxFilled } from '@ant-design/icons';
import { RecomendacionMedica } from '../detalleControlUtils';

const { Title } = Typography;

interface RecomendacionesMedicasProps {
  recomendaciones: RecomendacionMedica[];
}

const RecomendacionesMedicas: React.FC<RecomendacionesMedicasProps> = ({ recomendaciones }) => (
  <Card className="u-mb-4 controles-recomendaciones">
    <Space direction="vertical" size="middle" className="u-ancho">
      <Space>
        <MedicineBoxFilled className="u-t-lg u-c-aviso" />
        <Title level={5} className="u-m-0">
          Recomendaciones Médicas ({recomendaciones.length})
        </Title>
      </Space>
      <List
        dataSource={recomendaciones}
        renderItem={(item) => (
          <List.Item>
            <List.Item.Meta
              avatar={
                <Avatar
                  icon={item.icono}
                  className={`controles-recomendacion__icono controles-recomendacion__icono--${item.tipo === 'urgente' ? 'peligro' : item.tipo === 'importante' ? 'aviso' : 'info'}`}
                />
              }
              title={
                <Space>
                  {item.titulo}
                  <Tag
                    color={
                      item.tipo === 'urgente'
                        ? 'error'
                        : item.tipo === 'importante'
                          ? 'warning'
                          : 'processing'
                    }
                  >
                    {item.tipo.toUpperCase()}
                  </Tag>
                </Space>
              }
              description={item.descripcion}
            />
          </List.Item>
        )}
      />
    </Space>
  </Card>
);

export default RecomendacionesMedicas;
