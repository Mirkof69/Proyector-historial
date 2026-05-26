import React from 'react';
import { Row, Col, Input, Select, Button, DatePicker } from 'antd';
import { SearchOutlined, FilterOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';

const { RangePicker } = DatePicker;
const { Option } = Select;

interface CitasFilterBarProps {
  busqueda: string;
  filtroEstado: string;
  filtroTipo: string;
  filtroFecha: [dayjs.Dayjs, dayjs.Dayjs] | null;
  onBusquedaChange: (value: string) => void;
  onFiltroEstadoChange: (value: string) => void;
  onFiltroTipoChange: (value: string) => void;
  onFiltroFechaChange: (dates: [dayjs.Dayjs, dayjs.Dayjs] | null) => void;
  onLimpiar: () => void;
}

const CitasFilterBar: React.FC<CitasFilterBarProps> = ({
  busqueda, filtroEstado, filtroTipo, filtroFecha,
  onBusquedaChange, onFiltroEstadoChange, onFiltroTipoChange, onFiltroFechaChange, onLimpiar,
}) => (
  <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
    <Col xs={24} sm={12} md={8}>
      <Input placeholder="Buscar por paciente, médico, motivo, ID clínico..." prefix={<SearchOutlined />} value={busqueda} onChange={(e) => onBusquedaChange(e.target.value)} allowClear />
    </Col>
    <Col xs={24} sm={12} md={4}>
      <Select placeholder="Estado" style={{ width: '100%' }} value={filtroEstado || undefined} onChange={onFiltroEstadoChange} allowClear>
        <Option value="agendada">Agendada</Option>
        <Option value="confirmada">Confirmada</Option>
        <Option value="en_espera">En Espera</Option>
        <Option value="en_consulta">En Consulta</Option>
        <Option value="completada">Completada</Option>
        <Option value="cancelada">Cancelada</Option>
        <Option value="no_asistio">No Asistió</Option>
      </Select>
    </Col>
    <Col xs={24} sm={12} md={4}>
      <Select placeholder="Tipo" style={{ width: '100%' }} value={filtroTipo || undefined} onChange={onFiltroTipoChange} allowClear>
        <Option value="primera_vez">Primera Vez</Option>
        <Option value="control">Control</Option>
        <Option value="urgencia">Urgencia</Option>
        <Option value="seguimiento">Seguimiento</Option>
      </Select>
    </Col>
    <Col xs={24} sm={12} md={6}>
      <RangePicker style={{ width: '100%' }} format="DD/MM/YYYY" value={filtroFecha} onChange={(dates) => onFiltroFechaChange(dates as [dayjs.Dayjs, dayjs.Dayjs])} placeholder={['Desde', 'Hasta']} />
    </Col>
    <Col xs={24} sm={12} md={2}>
      <Button icon={<FilterOutlined />} onClick={onLimpiar} block>Limpiar</Button>
    </Col>
  </Row>
);

export default CitasFilterBar;
