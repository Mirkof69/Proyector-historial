import React from 'react';
import { Card, Button, Space, Input, Select, DatePicker } from 'antd';
import {
  CheckCircleOutlined, SearchOutlined, PlusOutlined, ReloadOutlined, FilterOutlined,
} from '@ant-design/icons';
import { AlertaMedica } from '../../../services/reportesService';
import { AlertasState } from '../alertasMedicasUtils';

const { RangePicker } = DatePicker;

interface AlertasMedicasFiltrosProps {
  searchText: string;
  filterSeveridad: string;
  filterEstado: string;
  dateRange: any;
  setState: React.Dispatch<React.SetStateAction<AlertasState>>;
  cargarAlertas: () => void;
  filteredAlertas: AlertaMedica[];
  filtrosAvanzadosVisibleRef: React.MutableRefObject<boolean>;
  handleResolverTodas: () => void;
}

const AlertasMedicasFiltros: React.FC<AlertasMedicasFiltrosProps> = ({
  searchText, filterSeveridad, filterEstado, dateRange, setState, cargarAlertas,
  filteredAlertas, filtrosAvanzadosVisibleRef, handleResolverTodas,
}) => (
  <Card style={{ marginBottom: 16 }}>
    <Space wrap>
      <Input
        placeholder="Buscar por paciente, tipo o mensaje..."
        prefix={<SearchOutlined />}
        value={searchText}
        onChange={e => setState(prev => ({ ...prev, searchText: e.target.value }))}
        style={{ width: 300 }}
      />
      <Select
        value={filterSeveridad}
        onChange={val => setState(prev => ({ ...prev, filterSeveridad: val }))}
        style={{ width: 150 }}
      >
        <Select.Option value="all">Todas las severidades</Select.Option>
        <Select.Option value="baja">Baja</Select.Option>
        <Select.Option value="media">Media</Select.Option>
        <Select.Option value="alta">Alta</Select.Option>
        <Select.Option value="critica">Crítica</Select.Option>
      </Select>
      <Select
        value={filterEstado}
        onChange={val => setState(prev => ({ ...prev, filterEstado: val }))}
        style={{ width: 150 }}
      >
        <Select.Option value="all">Todos los estados</Select.Option>
        <Select.Option value="activa">Activas</Select.Option>
        <Select.Option value="revisada">Revisadas</Select.Option>
        <Select.Option value="resuelta">Resueltas</Select.Option>
        <Select.Option value="descartada">Descartadas</Select.Option>
        <Select.Option value="escalada">Escaladas</Select.Option>
      </Select>
      <RangePicker
        value={dateRange}
        onChange={val => setState(prev => ({ ...prev, dateRange: val }))}
        format="DD/MM/YYYY"
      />
      <Button
        icon={<ReloadOutlined />}
        onClick={cargarAlertas}
      >
        Recargar
      </Button>
      <Button
        type="primary"
        icon={<PlusOutlined />}
        onClick={() => setState(prev => ({ ...prev, modalNuevaAlerta: true }))}
      >
        Nueva Alerta
      </Button>
      <Button
        icon={<FilterOutlined />}
        onClick={() => { filtrosAvanzadosVisibleRef.current = !filtrosAvanzadosVisibleRef.current; }}
      >
        Filtros Avanzados
      </Button>
      {filteredAlertas.length > 0 && filteredAlertas.some(a => a.estado !== 'resuelta' && a.estado !== 'descartada') && (
        <Button
          type="default"
          icon={<CheckCircleOutlined />}
          onClick={handleResolverTodas}
        >
          Resolver Todas
        </Button>
      )}
    </Space>
  </Card>
);

export default AlertasMedicasFiltros;
