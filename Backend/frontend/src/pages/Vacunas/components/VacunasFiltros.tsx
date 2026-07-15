import React from 'react';
import { Input, DatePicker, Select, Row, Col } from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import { FiltrosVacunasState, FiltrosVacunasAction, FULL_WIDTH_STYLE } from '../vacunasUtils';

const { RangePicker } = DatePicker;
const { Option } = Select;

interface VacunasFiltrosProps {
  filtros: FiltrosVacunasState;
  dispatchFiltros: React.Dispatch<FiltrosVacunasAction>;
}

const VacunasFiltros: React.FC<VacunasFiltrosProps> = ({ filtros, dispatchFiltros }) => (
  <div style={{ background: '#f8fafc', padding: '20px', borderRadius: '12px', marginBottom: 24, border: '1px solid #e2e8f0' }}>
    <Row gutter={[16, 16]} align="middle">
      <Col xs={24} lg={8}>
        <Input
          placeholder="Buscar por paciente, vacuna, lote o lab..."
          prefix={<SearchOutlined style={{ color: '#94a3b8' }} />}
          value={filtros.searchText}
          onChange={(e) => dispatchFiltros({ type: 'SET_SEARCH', payload: e.target.value })}
          size="large"
          className="custom-search"
          allowClear
        />
      </Col>
      <Col xs={24} sm={12} lg={6}>
        <RangePicker
          style={{ width: '100%' }}
          size="large"
          format="DD/MM/YYYY"
          value={filtros.dateRange}
          onChange={(dates) => dispatchFiltros({ type: 'SET_DATE_RANGE', payload: dates as any })}
        />
      </Col>
      <Col xs={12} sm={6} lg={5}>
        <Select
          style={FULL_WIDTH_STYLE}
          size="large"
          value={filtros.filtroVacuna}
          onChange={(val) => dispatchFiltros({ type: 'SET_FILTRO_VACUNA', payload: val })}
        >
          <Option value="todas">Todas las vacunas</Option>
          <Option value="covid">Refuerzos COVID</Option>
          <Option value="influenza">Influenza</Option>
          <Option value="hepatitis">Hepatitis B</Option>
        </Select>
      </Col>
      <Col xs={12} sm={6} lg={5}>
        <Select
          style={FULL_WIDTH_STYLE}
          size="large"
          value={filtros.filtroEstado}
          onChange={(val) => dispatchFiltros({ type: 'SET_FILTRO_ESTADO', payload: val })}
        >
          <Option value="todas">Todos los estados</Option>
          <Option value="pendientes">Pendientes</Option>
          <Option value="vencidas">Vencidas</Option>
          <Option value="completas">Esquema Completo</Option>
        </Select>
      </Col>
    </Row>
  </div>
);

export default VacunasFiltros;
