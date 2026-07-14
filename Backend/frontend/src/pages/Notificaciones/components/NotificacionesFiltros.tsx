import React from 'react';
import { Card, DatePicker, Select, Input, Row, Col, Typography } from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import type { FiltrosNotifState, FiltrosNotifAction } from '../notificacionesUtils';

const { Text } = Typography;
const { Option } = Select;
const { RangePicker } = DatePicker;

interface NotificacionesFiltrosProps {
  filtros: FiltrosNotifState;
  dispatchFiltros: React.Dispatch<FiltrosNotifAction>;
  filteredCount: number;
  total: number;
}

const NotificacionesFiltros: React.FC<NotificacionesFiltrosProps> = ({
  filtros, dispatchFiltros, filteredCount, total,
}) => (
  <Card className="filters-card" styles={{ body: { padding: '16px 24px' } }}>
    <Row gutter={[16, 16]} align="middle">
      <Col xs={24} md={6}>
        <Input
          prefix={<SearchOutlined style={{ color: 'var(--text-tertiary)' }} />}
          placeholder="Buscar en notificaciones..."
          value={filtros.searchText}
          onChange={e => dispatchFiltros({ type: 'SET_SEARCH', payload: e.target.value })}
          allowClear
        />
      </Col>
      <Col xs={24} md={6}>
        <RangePicker
          style={{ width: '100%' }}
          placeholder={['Fecha inicio', 'Fecha fin']}
          value={filtros.dateRange}
          onChange={(dates) => dispatchFiltros({ type: 'SET_DATE_RANGE', payload: dates })}
          format="DD/MM/YYYY"
        />
      </Col>
      <Col xs={24} md={4}>
        <Select
          placeholder="Tipo"
          style={{ width: '100%' }}
          allowClear
          value={filtros.filterType}
          onChange={(val) => dispatchFiltros({ type: 'SET_TYPE', payload: val })}
        >
          <Option value="info">Información</Option>
          <Option value="warning">Advertencia</Option>
          <Option value="error">Alerta</Option>
          <Option value="success">Éxito</Option>
          <Option value="cita">Citas</Option>
          <Option value="examen">Exámenes</Option>
        </Select>
      </Col>
      <Col xs={24} md={4}>
        <Select
          placeholder="Estado"
          style={{ width: '100%' }}
          value={filtros.filterRead}
          onChange={(val) => dispatchFiltros({ type: 'SET_READ', payload: val })}
        >
          <Option value="todas">Todas</Option>
          <Option value="nuevas">No leídas</Option>
          <Option value="leidas">Leídas</Option>
        </Select>
      </Col>
      <Col xs={24} md={4} style={{ textAlign: 'right' }}>
        <Text type="secondary">
          Mostrando {filteredCount} de {total}
        </Text>
      </Col>
    </Row>
  </Card>
);

export default NotificacionesFiltros;
