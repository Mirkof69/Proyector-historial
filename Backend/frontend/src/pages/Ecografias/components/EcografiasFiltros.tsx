import React from 'react';
import { Button, Space, Input, Select, DatePicker, Row, Col } from 'antd';
import { SearchOutlined, FilterOutlined } from '@ant-design/icons';
import { FiltrosEcografiaState, FiltrosEcografiaAction } from '../ecografiasUtils';
import dayjs from 'dayjs';

const { RangePicker } = DatePicker;
const { Option } = Select;

interface EcografiasFiltrosProps {
  filtros: FiltrosEcografiaState;
  dispatchFiltros: React.Dispatch<FiltrosEcografiaAction>;
  limpiarFiltros: () => void;
}

const EcografiasFiltros: React.FC<EcografiasFiltrosProps> = ({ filtros, dispatchFiltros, limpiarFiltros }) => (
  <Space direction="vertical" size="middle" style={{ width: '100%', marginBottom: 16 }}>
    <Row gutter={[16, 16]}>
      <Col xs={24} sm={12} md={8}>
        <Input
          placeholder="Buscar..."
          prefix={<SearchOutlined />}
          value={filtros.busqueda}
          onChange={(e) => dispatchFiltros({ type: 'SET_BUSQUEDA', payload: e.target.value })}
          allowClear
        />
      </Col>
      <Col xs={24} sm={12} md={6}>
        <Select
          placeholder="Filtrar por tipo"
          style={{ width: '100%' }}
          value={filtros.filtroTipo}
          onChange={(val) => dispatchFiltros({ type: 'SET_TIPO', payload: val })}
          allowClear
        >
          <Option value="primer_trimestre">Primer Trimestre</Option>
          <Option value="segundo_trimestre">Segundo Trimestre</Option>
          <Option value="tercer_trimestre">Tercer Trimestre</Option>
          <Option value="morfologica">Morfológica</Option>
          <Option value="doppler">Doppler</Option>
          <Option value="genetica">Genética</Option>
          <Option value="4d">4D</Option>
        </Select>
      </Col>
      <Col xs={24} sm={12} md={8}>
        <RangePicker
          style={{ width: '100%' }}
          format="DD/MM/YYYY"
          value={filtros.filtroFecha}
          onChange={(dates) => dispatchFiltros({ type: 'SET_FECHA', payload: dates as [dayjs.Dayjs, dayjs.Dayjs] })}
        />
      </Col>
      <Col xs={24} sm={12} md={2}>
        <Button icon={<FilterOutlined />} onClick={limpiarFiltros} block>
          Limpiar
        </Button>
      </Col>
    </Row>
  </Space>
);

export default EcografiasFiltros;
