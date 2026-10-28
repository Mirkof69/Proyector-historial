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
  <Space direction="vertical" size="middle" className="laboratorio-ancho laboratorio-separado">
    <Row gutter={[16, 16]}>
      <Col xs={24} sm={12} lg={6}>
        <Input
          placeholder="Buscar paciente o examen..."
          prefix={<SearchOutlined />}
          value={filtros.busqueda}
          onChange={(e) => dispatchFiltros({ type: 'SET_BUSQUEDA', payload: e.target.value })}
          allowClear
        />
      </Col>
      <Col xs={24} sm={12} lg={4}>
        <Select
          placeholder="Categoría"
          className="laboratorio-ancho"
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
      <Col xs={24} sm={12} lg={4}>
        <Select
          placeholder="Estado"
          className="laboratorio-ancho"
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
      <Col xs={24} sm={12} lg={7}>
        <RangePicker
          className="laboratorio-ancho"
          format={{ format: 'DD/MM/YYYY', type: 'mask' }}
          value={filtros.filtroFecha}
          onChange={(dates) => dispatchFiltros({ type: 'SET_FECHA', payload: dates as [Dayjs, Dayjs] })}
        />
      </Col>
      <Col xs={24} sm={12} lg={3}>
        <Button icon={<FilterOutlined />} onClick={onLimpiar} block>
          Limpiar
        </Button>
      </Col>
    </Row>
  </Space>
);

export default LaboratorioFiltros;
