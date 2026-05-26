import React from 'react';
import { Row, Col, Input, DatePicker, Select, Button } from 'antd';
import { SearchOutlined, ReloadOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';

const { Option } = Select;

interface FiltrosState {
  searchText: string;
  filterType: string;
  filterDate: dayjs.Dayjs | null;
}

interface EvolucionesFiltersProps {
  filtros: FiltrosState;
  onSearchChange: (value: string) => void;
  onTypeChange: (value: string) => void;
  onDateChange: (value: dayjs.Dayjs | null) => void;
  onReset: () => void;
}

const EvolucionesFilters: React.FC<EvolucionesFiltersProps> = ({
  filtros,
  onSearchChange,
  onTypeChange,
  onDateChange,
  onReset,
}) => (
  <div style={{ background: '#f8fafc', padding: '20px', borderRadius: '12px', marginBottom: 24, border: '1px solid #e2e8f0' }}>
    <Row gutter={[16, 16]} align="middle">
      <Col xs={24} lg={10}>
        <Input
          placeholder="Buscar por paciente, médico o diagnóstico..."
          prefix={<SearchOutlined style={{ color: '#94a3b8' }} />}
          value={filtros.searchText}
          onChange={(e) => onSearchChange(e.target.value)}
          size="large"
          className="custom-search"
          allowClear
        />
      </Col>
      <Col xs={12} sm={8} lg={5}>
        <Select
          placeholder="Filtrar por tipo"
          value={filtros.filterType}
          onChange={onTypeChange}
          style={{ width: '100%' }}
          size="large"
        >
          <Option value="todos">Todos los tipos</Option>
          <Option value="consulta">Consulta General</Option>
          <Option value="control">Control Prenatal</Option>
          <Option value="urgencia">Urgencia Médica</Option>
        </Select>
      </Col>
      <Col xs={12} sm={8} lg={5}>
        <DatePicker
          value={filtros.filterDate}
          onChange={onDateChange}
          placeholder="Filtrar por fecha"
          style={{ width: '100%' }}
          size="large"
          format="DD/MM/YYYY"
        />
      </Col>
      <Col xs={24} sm={8} lg={4}>
        <Button block size="large" icon={<ReloadOutlined />} onClick={onReset}>
          Reiniciar
        </Button>
      </Col>
    </Row>
  </div>
);

export default EvolucionesFilters;
