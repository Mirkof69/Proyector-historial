import React from 'react';
import { Card, Tag, Space, Typography, List, Avatar } from 'antd';
import { MedicineBoxFilled } from '@ant-design/icons';
import { RecomendacionMedica } from '../detalleControlUtils';

const { Title } = Typography;

interface RecomendacionesMedicasProps {
  recomendaciones: RecomendacionMedica[];
}

const RecomendacionesMedicas: React.FC<RecomendacionesMedicasProps> = ({ recomendaciones }) => (
  <Card style={{ marginBottom: 16, borderColor: '#faad14' }}>
    <Space direction="vertical" size="middle" style={{ width: '100%' }}>
      <Space>
        <MedicineBoxFilled style={{ fontSize: 20, color: '#faad14' }} />
        <Title level={5} style={{ margin: 0 }}>
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
                  style={{
                    backgroundColor:
                      item.tipo === 'urgente'
                        ? '#ff4d4f'
                        : item.tipo === 'importante'
                          ? '#faad14'
                          : '#1890ff',
                  }}
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
