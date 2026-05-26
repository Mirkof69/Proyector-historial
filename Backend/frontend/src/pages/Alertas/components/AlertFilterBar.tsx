import React from 'react';
import { Card, Row, Col, Select, Input, Button, Tooltip, Space } from 'antd';
import { SearchOutlined, FilterOutlined, SyncOutlined } from '@ant-design/icons';

const { Option } = Select;
const { Search } = Input;

interface AlertFilterBarProps {
  busqueda: string;
  filtroTipo: string;
  filtroEstado: string;
  loading: boolean;
  onBusquedaChange: (value: string) => void;
  onFiltroTipoChange: (value: string) => void;
  onFiltroEstadoChange: (value: string) => void;
  onRefresh: () => void;
  onClearFilters: () => void;
}

const AlertFilterBar: React.FC<AlertFilterBarProps> = ({
  busqueda, filtroTipo, filtroEstado, loading,
  onBusquedaChange, onFiltroTipoChange, onFiltroEstadoChange,
  onRefresh, onClearFilters,
}) => (
  <Card style={{ marginBottom: 24 }}>
    <Row gutter={16} style={{ marginBottom: 16 }}>
      <Col xs={24} md={8}>
        <Search placeholder="Buscar alertas..." value={busqueda} onChange={(e) => onBusquedaChange(e.target.value)} prefix={<SearchOutlined />} allowClear />
      </Col>
      <Col xs={24} md={5}>
        <Select placeholder="Tipo de Alerta" value={filtroTipo} onChange={onFiltroTipoChange} allowClear style={{ width: '100%' }}>
          <Option value="critica">Crítica</Option>
          <Option value="alta">Alta</Option>
          <Option value="media">Media</Option>
          <Option value="baja">Baja</Option>
          <Option value="info">Información</Option>
        </Select>
      </Col>
      <Col xs={24} md={5}>
        <Select placeholder="Estado" value={filtroEstado} onChange={onFiltroEstadoChange} allowClear style={{ width: '100%' }}>
          <Option value="activa">Activas</Option>
          <Option value="en_proceso">En Proceso</Option>
          <Option value="resuelta">Resueltas</Option>
          <Option value="descartada">Descartadas</Option>
        </Select>
      </Col>
      <Col xs={24} md={6}>
        <Space>
          <Tooltip title="Actualizar alertas en tiempo real">
            <Button icon={<SyncOutlined />} onClick={onRefresh} loading={loading}>Actualizar</Button>
          </Tooltip>
          <Tooltip title="Limpiar todos los filtros">
            <Button icon={<FilterOutlined />} onClick={onClearFilters}>Limpiar</Button>
          </Tooltip>
        </Space>
      </Col>
    </Row>
  </Card>
);

export default AlertFilterBar;
