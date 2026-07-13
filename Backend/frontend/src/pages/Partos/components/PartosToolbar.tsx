import React from 'react';
import { Card, Row, Col, Space, Input, DatePicker, Select, Button } from 'antd';
import { SearchOutlined, ReloadOutlined, FileExcelOutlined, PlusOutlined } from '@ant-design/icons';
import type { Dayjs } from 'dayjs';
import { FiltrosPartosState, FiltrosPartosAction } from './partosFiltrosReducer';

const { RangePicker } = DatePicker;
const { Option } = Select;

interface PartosToolbarProps {
  filtros: FiltrosPartosState;
  dispatchFiltros: React.Dispatch<FiltrosPartosAction>;
  onReload: () => void;
  onExport: () => void;
  onNew: () => void;
  canAdd: boolean;
}

const PartosToolbar: React.FC<PartosToolbarProps> = ({ filtros, dispatchFiltros, onReload, onExport, onNew, canAdd }) => (
  <Card className="toolbar-card" style={{ marginBottom: 16 }}>
    <Row gutter={[16, 16]} justify="space-between" align="middle">
      <Col xs={24} md={16}>
        <Space wrap>
          <Input
            placeholder="Buscar paciente..."
            prefix={<SearchOutlined />}
            value={filtros.searchText}
            onChange={(e) => dispatchFiltros({ type: 'SET_SEARCH', payload: e.target.value })}
            style={{ width: 200 }}
          />
          <RangePicker
            onChange={(dates) => dispatchFiltros({ type: 'SET_DATE_RANGE', payload: dates as [Dayjs, Dayjs] | null })}
            placeholder={['Desde', 'Hasta']}
          />
          <Select
            placeholder="Tipo de parto"
            allowClear
            style={{ width: 180 }}
            value={filtros.tipoPartoFilter}
            onChange={(val) => dispatchFiltros({ type: 'SET_TIPO_PARTO', payload: val })}
          >
            <Option value="vaginal_espontaneo">Vaginal Espontáneo</Option>
            <Option value="vaginal_instrumentado">Vaginal Instrumentado</Option>
            <Option value="cesarea_electiva">Cesárea Electiva</Option>
            <Option value="cesarea_urgencia">Cesárea Urgencia</Option>
            <Option value="cesarea_emergencia">Cesárea Emergencia</Option>
          </Select>
          <Button icon={<ReloadOutlined />} onClick={onReload} title="Recargar datos" />
          <Button
            icon={<FileExcelOutlined />}
            onClick={onExport}
            title="Exportar a Excel"
            type="primary"
            ghost
          >
            Exportar Excel
          </Button>
        </Space>
      </Col>
      <Col xs={24} md={8} style={{ textAlign: 'right' }}>
        {canAdd && (
          <Button type="primary" icon={<PlusOutlined />} onClick={onNew} size="large">
            Registrar Nuevo Parto
          </Button>
        )}
      </Col>
    </Row>
  </Card>
);

export default PartosToolbar;
