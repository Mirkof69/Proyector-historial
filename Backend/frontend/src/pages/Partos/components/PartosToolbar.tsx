import React from 'react';
import { Card, Space, Input, DatePicker, Select, Button } from 'antd';
import { SearchOutlined, ReloadOutlined, FileExcelOutlined } from '@ant-design/icons';
import type { Dayjs } from 'dayjs';
import { FiltrosPartosState, FiltrosPartosAction } from './partosFiltrosReducer';

const { RangePicker } = DatePicker;
const { Option } = Select;

interface PartosToolbarProps {
  filtros: FiltrosPartosState;
  dispatchFiltros: React.Dispatch<FiltrosPartosAction>;
  onReload: () => void;
  onExport: () => void;
}

const PartosToolbar: React.FC<PartosToolbarProps> = ({ filtros, dispatchFiltros, onReload, onExport }) => (
  <Card>
    <div className="partos-page__barra">
        <Space wrap>
          <Input
            placeholder="Buscar paciente..."
            prefix={<SearchOutlined />}
            value={filtros.searchText}
            onChange={(e) => dispatchFiltros({ type: 'SET_SEARCH', payload: e.target.value })}
            className="partos-page__buscar"
          />
          <RangePicker format={{ format: 'DD/MM/YYYY', type: 'mask' }}
            onChange={(dates) => dispatchFiltros({ type: 'SET_DATE_RANGE', payload: dates as [Dayjs, Dayjs] | null })}
            placeholder={['Desde', 'Hasta']}
          />
          <Select
            placeholder="Tipo de parto"
            allowClear
            className="partos-page__selector"
            value={filtros.tipoPartoFilter}
            onChange={(val) => dispatchFiltros({ type: 'SET_TIPO_PARTO', payload: val })}
          >
            <Option value="vaginal_espontaneo">Vaginal Espontáneo</Option>
            <Option value="vaginal_instrumentado">Vaginal Instrumentado</Option>
            <Option value="cesarea_electiva">Cesárea Electiva</Option>
            <Option value="cesarea_urgencia">Cesárea Urgencia</Option>
            <Option value="cesarea_emergencia">Cesárea Emergencia</Option>
          </Select>
          <Button icon={<ReloadOutlined />} onClick={onReload} title="Recargar datos" aria-label="Recargar datos" />
        </Space>
        <Button
          icon={<FileExcelOutlined />}
          onClick={onExport}
          title="Exportar a Excel"
        >
          Exportar Excel
        </Button>
    </div>
  </Card>
);

export default PartosToolbar;
