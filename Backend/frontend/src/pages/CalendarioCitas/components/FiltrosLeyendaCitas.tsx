import React from 'react';
import { Row, Col, Select, Button, Alert, Space, Badge, Typography } from 'antd';
import { FilterOutlined } from '@ant-design/icons';

const { Option } = Select;
const { Text } = Typography;

interface FiltrosLeyendaCitasProps {
  filtroEstado: string;
  filtroTipo: string;
  onEstadoChange: (val: string) => void;
  onTipoChange: (val: string) => void;
  onClearFilters: () => void;
}

const FiltrosLeyendaCitas: React.FC<FiltrosLeyendaCitasProps> = ({
  filtroEstado, filtroTipo, onEstadoChange, onTipoChange, onClearFilters,
}) => (
  <>
    {/* FILTROS */}
    <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
      <Col xs={24} sm={12} md={8}>
        <Select
          placeholder="Filtrar por estado"
          style={{ width: '100%' }}
          value={filtroEstado}
          onChange={onEstadoChange}
          allowClear
        >
          <Option value="pendiente">Pendiente</Option>
          <Option value="confirmada">Confirmada</Option>
          <Option value="completada">Completada</Option>
          <Option value="cancelada">Cancelada</Option>
        </Select>
      </Col>
      <Col xs={24} sm={12} md={8}>
        <Select
          placeholder="Filtrar por tipo"
          style={{ width: '100%' }}
          value={filtroTipo}
          onChange={onTipoChange}
          allowClear
        >
          <Option value="control_prenatal">Control Prenatal</Option>
          <Option value="ecografia">Ecografía</Option>
          <Option value="consulta_general">Consulta General</Option>
          <Option value="emergencia">Emergencia</Option>
          <Option value="seguimiento">Seguimiento</Option>
          <Option value="laboratorio">Laboratorio</Option>
          <Option value="procedimiento">Procedimiento</Option>
        </Select>
      </Col>
      <Col xs={24} sm={12} md={8}>
        <Button icon={<FilterOutlined />} onClick={onClearFilters} block>
          Limpiar Filtros
        </Button>
      </Col>
    </Row>

    {/* LEYENDA */}
    <Alert
      message="Leyenda del Calendario"
      description={
        <Space direction="vertical" size="small">
          <Space>
            <Badge status="warning" />
            <Text>Pendiente</Text>
            <Badge status="processing" />
            <Text>Confirmada</Text>
            <Badge status="success" />
            <Text>Completada</Text>
            <Badge status="error" />
            <Text>Cancelada</Text>
          </Space>
          <Text type="secondary" style={{ fontSize: 12 }}>
            Haga clic en cualquier día para ver las citas programadas
          </Text>
        </Space>
      }
      type="info"
      showIcon
      style={{ marginBottom: 16 }}
    />
  </>
);

export default FiltrosLeyendaCitas;
