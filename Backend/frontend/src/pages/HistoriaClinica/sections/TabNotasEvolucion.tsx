import React from 'react';
import { Card, List, Space, Tag, Typography, Button, Empty, Divider, Avatar } from 'antd';
import { FileTextOutlined, UserOutlined, EditOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { NotaEvolucion } from '../types';

const { Text } = Typography;

const userIcon = <UserOutlined />;
const verticalDivider = <Divider type="vertical" />;

interface TabNotasEvolucionProps {
  notas: NotaEvolucion[];
  setDrawerNotasVisible: (visible: boolean) => void;
}

const TabNotasEvolucion: React.FC<TabNotasEvolucionProps> = ({ notas, setDrawerNotasVisible }) => {
  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <Space>
          <FileTextOutlined style={{ fontSize: 20 }} />
          <Text strong style={{ fontSize: 16 }}>Notas de Evolución Clínica</Text>
        </Space>
        <Button type="primary" icon={<FileTextOutlined />} onClick={() => setDrawerNotasVisible(true)}>
          Nueva Nota
        </Button>
      </div>

      <List
        dataSource={notas.slice().sort((a, b) => dayjs(b.fecha_hora).diff(dayjs(a.fecha_hora)))}
        renderItem={(nota) => (
          <Card
            key={nota.id}
            style={{ marginBottom: 16, borderRadius: 8, boxShadow: '0 2px 8px rgba(0,0,0,0.05)' }}
            bodyStyle={{ padding: 0 }}
          >
            <div style={{ padding: '12px 16px', background: '#fafafa', borderBottom: '1px solid #f0f0f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Space>
                <Tag color={
                  nota.tipo === 'URGENCIA' ? 'red' :
                  nota.tipo === 'JUNTA_MEDICA' ? 'purple' :
                  nota.tipo === 'TELECONSULTA' ? 'cyan' : 'blue'
                }>
                  {nota.tipo}
                </Tag>
                <Text strong>{dayjs(nota.fecha_hora).format('DD/MM/YYYY HH:mm')}</Text>
              </Space>
              <Space>
                <Avatar size="small" icon={userIcon} />
                <Text type="secondary">{nota.autor?.nombre_completo || nota.autor?.username || 'Médico'}</Text>
              </Space>
            </div>
            <div style={{ padding: 16 }}>
              <div style={{ marginBottom: 12 }}>
                <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>SUBJETIVO / MOTIVO:</Text>
                <Text>{nota.subjetivo}</Text>
              </div>
              <div style={{ marginBottom: 12 }}>
                <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>OBJETIVO / HALLAZGOS:</Text>
                <Text>{nota.objetivo}</Text>
              </div>
              <div style={{ marginBottom: 12 }}>
                <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>ANÁLISIS / DIAGNÓSTICO:</Text>
                <Text strong>{nota.analisis}</Text>
              </div>
              <div>
                <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>PLAN DE MANEJO:</Text>
                <div style={{ background: '#f6ffed', padding: '8px 12px', borderRadius: 4, boxShadow: 'inset 3px 0 0 #b7eb8f' }}>
                  <Text italic>{nota.plan}</Text>
                </div>
              </div>
            </div>
            <Card variant="borderless" style={{ background: '#f9f9f9', borderTop: '1px solid #f0f0f0', padding: '8px 16px' }}>
              <Space split={verticalDivider} size="large" wrap>
                <Space direction="vertical" size={0}>
                  <Text type="secondary">Signos Vitales:</Text>
                  <Text strong>
                    {nota.presion_arterial || 'N/D'} | {nota.frecuencia_cardiaca ? `${nota.frecuencia_cardiaca} lpm` : 'N/D'} | {nota.temperatura ? `${nota.temperatura} °C` : 'N/D'}
                  </Text>
                </Space>

                {nota.fecha_modificacion && nota.fecha_modificacion !== nota.fecha_hora && (
                  <Space direction="vertical" size={0}>
                    <Text type="secondary">Última modificación:</Text>
                    <Text strong>
                      <EditOutlined /> {dayjs(nota.fecha_modificacion).format('DD/MM/YYYY HH:mm:ss')}
                    </Text>
                  </Space>
                )}

                {nota.semanas_gestacion && (
                  <Space direction="vertical" size={0}>
                    <Text type="secondary">Edad gestacional:</Text>
                    <Text strong style={{ color: '#722ed1' }}>
                      {nota.semanas_gestacion} semanas
                    </Text>
                    {nota.dias_gestacion && (
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        + {nota.dias_gestacion} días
                      </Text>
                    )}
                  </Space>
                )}

                {nota.numero_consulta && (
                  <Space direction="vertical" size={0}>
                    <Text type="secondary">Consulta N°:</Text>
                    <Text strong>{nota.numero_consulta}</Text>
                  </Space>
                )}
              </Space>
            </Card>
          </Card>
        )}
      />

      {notas.length === 0 && (
        <Empty
          description="No hay notas de evolución registradas"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        >
          <Button type="primary" icon={<FileTextOutlined />} onClick={() => setDrawerNotasVisible(true)}>
            Crear Primera Nota
          </Button>
        </Empty>
      )}
    </div>
  );
};

export default TabNotasEvolucion;
