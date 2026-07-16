import React from 'react';
import { Card, Row, Col, Button, Space } from 'antd';
import { Consultorio, EstadoConsultorio } from '../../../services/consultoriosService';

interface PanelControlTabProps {
  consultorios: Consultorio[];
  handleCambiarEstado: (consultorioId: number, nuevoEstado: EstadoConsultorio) => void;
}

const PanelControlTab: React.FC<PanelControlTabProps> = ({ consultorios, handleCambiarEstado }) => (
  <Space direction="vertical" style={{ width: '100%' }} size="middle">
    <Card title="Cambio Rápido de Estado" size="small">
      <Row gutter={16}>
        <Col span={24}>
          <Space direction="vertical" style={{ width: '100%' }}>
            {consultorios.slice(0, 10).map(c => (
              <Card key={c.id} size="small">
                <Row align="middle">
                  <Col flex="auto">
                    <strong>{c.nombre}</strong> - {c.codigo}
                  </Col>
                  <Col>
                    <Space>
                      <Button size="small" type={c.estado === 'disponible' ? 'primary' : 'default'} onClick={() => handleCambiarEstado(c.id!, 'disponible')}>Disponible</Button>
                      <Button size="small" type={c.estado === 'ocupado' ? 'primary' : 'default'} onClick={() => handleCambiarEstado(c.id!, 'ocupado')}>Ocupado</Button>
                      <Button size="small" type={c.estado === 'mantenimiento' ? 'primary' : 'default'} onClick={() => handleCambiarEstado(c.id!, 'mantenimiento')}>Mantenimiento</Button>
                      <Button size="small" type={c.estado === 'reservado' ? 'primary' : 'default'} onClick={() => handleCambiarEstado(c.id!, 'reservado')}>Reservado</Button>
                    </Space>
                  </Col>
                </Row>
              </Card>
            ))}
          </Space>
        </Col>
      </Row>
    </Card>
  </Space>
);

export default PanelControlTab;
