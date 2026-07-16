import React from 'react';
import { Space, Row, Col, Input, Select, DatePicker, Button } from 'antd';
import { SearchOutlined, FilterOutlined } from '@ant-design/icons';
import type { Dayjs } from 'dayjs';
import { FiltrosState, FiltrosAction } from './laboratorioFiltrosReducer';

const { RangePicker } = DatePicker;
const { Option } = Select;

interface LaboratorioFiltrosProps {
  filtros: FiltrosState;
  dispatchFiltros: React.Dispatch<FiltrosAction>;
  onLimpiar: () => void;
}

const LaboratorioFiltros: React.FC<LaboratorioFiltrosProps> = ({ filtros, dispatchFiltros, onLimpiar }) => (
  <Space direction="vertical" size="middle" style={{ width: '100%', marginBottom: 16 }}>
    <Row gutter={[16, 16]}>
      <Col xs={24} sm={12} md={8}>
        <Input
          placeholder="Buscar paciente o examen..."
          prefix={<SearchOutlined />}
          value={filtros.busqueda}
          onChange={(e) => dispatchFiltros({ type: 'SET_BUSQUEDA', payload: e.target.value })}
          allowClear
        />
      </Col>
      <Col xs={24} sm={12} md={5}>
        <Select
          placeholder="Categoría"
          style={{ width: '100%' }}
          value={filtros.filtroCategoria}
          onChange={(val) => dispatchFiltros({ type: 'SET_CATEGORIA', payload: val })}
          allowClear
        >
          <Option value="hematologia">Hematología</Option>
          <Option value="bioquimica">Bioquímica</Option>
          <Option value="inmunologia">Inmunología</Option>
          <Option value="microbiologia">Microbiología</Option>
          <Option value="urinalisis">Urianálisis</Option>
          <Option value="serologia">Serología</Option>
          <Option value="hormonal">Hormonal</Option>
        </Select>
      </Col>
      <Col xs={24} sm={12} md={5}>
        <Select
          placeholder="Estado"
          style={{ width: '100%' }}
          value={filtros.filtroEstado}
          onChange={(val) => dispatchFiltros({ type: 'SET_ESTADO', payload: val })}
          allowClear
        >
          <Option value="solicitado">Solicitado</Option>
          <Option value="en_proceso">En Proceso</Option>
          <Option value="completado">Completado</Option>
          <Option value="cancelado">Cancelado</Option>
        </Select>
      </Col>
      <Col xs={24} sm={12} md={5}>
        <RangePicker
          style={{ width: '100%' }}
          format="DD/MM/YYYY"
          value={filtros.filtroFecha}
          onChange={(dates) => dispatchFiltros({ type: 'SET_FECHA', payload: dates as [Dayjs, Dayjs] })}
        />
      </Col>
      <Col xs={24} sm={12} md={1}>
        <Button icon={<FilterOutlined />} onClick={onLimpiar} block>
          Limpiar
        </Button>
      </Col>
    </Row>
  </Space>
);

export default LaboratorioFiltros;
