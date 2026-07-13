import React from 'react';
import { Card, Row, Col, Input, Select, DatePicker, Button } from 'antd';
import { SearchOutlined, FilterOutlined } from '@ant-design/icons';

interface TriajeFiltrosProps {
  searchText: string;
  filterState: string;
  filterPriority: string;
  filterDate: any;
  onSearchChange: (v: string) => void;
  onStateChange: (v: string) => void;
  onPriorityChange: (v: string) => void;
  onDateChange: (v: any) => void;
  onLimpiar: () => void;
}

const TriajeFiltros: React.FC<TriajeFiltrosProps> = ({
  searchText, filterState, filterPriority, filterDate,
  onSearchChange, onStateChange, onPriorityChange, onDateChange, onLimpiar,
}) => (
  <Card className="shadow-card" style={{ marginBottom: '24px' }}>
    <Row gutter={[16, 16]} align="middle">
      <Col xs={24} md={8}>
        <Input
          placeholder="Buscar por paciente, motivo..."
          prefix={<SearchOutlined />}
          value={searchText}
          onChange={(e) => onSearchChange(e.target.value)}
          size="large"
          allowClear
        />
      </Col>
      <Col xs={12} md={4}>
        <Select
          placeholder="Estado"
          value={filterState}
          onChange={onStateChange}
          style={{ width: '100%' }}
          allowClear
          size="large"
          options={[
            { label: 'Pendiente', value: 'pendiente' },
            { label: 'Completado', value: 'completado' },
          ]}
        />
      </Col>
      <Col xs={12} md={4}>
        <Select
          placeholder="Prioridad"
          value={filterPriority}
          onChange={onPriorityChange}
          style={{ width: '100%' }}
          allowClear
          size="large"
          options={[
            { label: 'Urgente', value: 'urgente' },
            { label: 'Alto', value: 'alto' },
            { label: 'Normal', value: 'normal' },
            { label: 'Bajo', value: 'bajo' },
          ]}
        />
      </Col>
      <Col xs={24} md={4}>
        <DatePicker
          value={filterDate}
          onChange={onDateChange}
          placeholder="Fecha"
          style={{ width: '100%' }}
          format="DD/MM/YYYY"
          size="large"
        />
      </Col>
      <Col xs={24} md={4}>
        <Button
          icon={<FilterOutlined />}
          onClick={onLimpiar}
          block
          size="large"
        >
          Limpiar
        </Button>
      </Col>
    </Row>
  </Card>
);

export default TriajeFiltros;
