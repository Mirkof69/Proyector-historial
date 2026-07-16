import React from 'react';
import { Card, Row, Col, Button, Space, List } from 'antd';
import { Consultorio, EstadoConsultorio } from '../../../services/consultoriosService';

interface VistaPorEstadoTabProps {
  consultorios: Consultorio[];
  handleCambiarEstado: (consultorioId: number, nuevoEstado: EstadoConsultorio) => void;
  handleAbrirReservas: (consultorio: Consultorio) => void;
}

const VistaPorEstadoTab: React.FC<VistaPorEstadoTabProps> = ({
  consultorios, handleCambiarEstado, handleAbrirReservas,
}) => (
  <Space direction="vertical" style={{ width: '100%' }} size="large">
    <Row gutter={16}>
      <Col span={12}>
        <Card title="Disponibles" size="small">
          <List
            dataSource={consultorios.filter(c => c.estado === 'disponible')}
            renderItem={(item) => (<List.Item key={item.id} actions={[
                  <Button key={`btn-ocupado-${item.id}`} size="small" onClick={() => handleCambiarEstado(item.id!, 'ocupado')}>Marcar Ocupado</Button>
                ]}
              >
                <List.Item.Meta title={item.nombre} description={item.codigo} />
              </List.Item>
            )}
          />
        </Card>
      </Col>
      <Col span={12}>
        <Card title="En Mantenimiento" size="small">
          <List
            dataSource={consultorios.filter(c => c.estado === 'mantenimiento')}
            renderItem={(item) => (<List.Item key={item.id} actions={[
                  <Button key={`btn-disponible-${item.id}`} size="small" onClick={() => handleCambiarEstado(item.id!, 'disponible')}>Marcar Disponible</Button>
                ]}
              >
                <List.Item.Meta title={item.nombre} description={item.codigo} />
              </List.Item>
            )}
          />
        </Card>
      </Col>
    </Row>
    <Row gutter={16}>
      <Col span={12}>
        <Card title="Ocupados" size="small">
          <List
            dataSource={consultorios.filter(c => c.estado === 'ocupado')}
            renderItem={(item) => (<List.Item key={item.id} actions={[
                  <Button key={`btn-liberar-${item.id}`} size="small" onClick={() => handleCambiarEstado(item.id!, 'disponible')}>Liberar</Button>
                ]}
              >
                <List.Item.Meta title={item.nombre} description={item.codigo} />
              </List.Item>
            )}
          />
        </Card>
      </Col>
      <Col span={12}>
        <Card title="Reservados" size="small">
          <List
            dataSource={consultorios.filter(c => c.estado === 'reservado')}
            renderItem={(item) => (<List.Item key={item.id} actions={[
                  <Button key={`btn-reservas-${item.id}`} size="small" onClick={() => handleAbrirReservas(item)}>Ver Reservas</Button>
                ]}
              >
                <List.Item.Meta title={item.nombre} description={item.codigo} />
              </List.Item>
            )}
          />
        </Card>
      </Col>
    </Row>
  </Space>
);

export default VistaPorEstadoTab;
