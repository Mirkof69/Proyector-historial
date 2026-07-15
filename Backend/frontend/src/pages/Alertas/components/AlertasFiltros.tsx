import React from 'react';
import { Card, Row, Col, Button, Space, Select, Input, DatePicker, Tooltip } from 'antd';
import {
  WarningOutlined, ExclamationCircleOutlined, BellOutlined,
  FireOutlined, InfoCircleOutlined, SyncOutlined, FilterOutlined, SearchOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { AlertAction } from '../sistemaAlertasUtils';

const { Option } = Select;
const { Search } = Input;
const { RangePicker } = DatePicker;

interface AlertasFiltrosProps {
  busqueda: string;
  filtroTipo: string;
  filtroEstado: string;
  rangoFechas: [dayjs.Dayjs | null, dayjs.Dayjs | null];
  loading: boolean;
  dispatch: React.Dispatch<AlertAction>;
  cargarAlertas: () => void;
}

const AlertasFiltros: React.FC<AlertasFiltrosProps> = ({
  busqueda, filtroTipo, filtroEstado, rangoFechas, loading, dispatch, cargarAlertas,
}) => (
  <Card style={{ marginBottom: 24 }}>
    <Row gutter={16} style={{ marginBottom: 16 }}>
      <Col xs={24} md={8}>
        <Search
          placeholder="Buscar alertas..."
          value={busqueda}
          onChange={(e) => dispatch({ type: 'SET_BUSQUEDA', payload: e.target.value })}
          prefix={<SearchOutlined />}
          allowClear
        />
      </Col>
      <Col xs={24} md={5}>
        <Select
          placeholder="Tipo de Alerta"
          value={filtroTipo}
          onChange={(val) => dispatch({ type: 'SET_FILTRO_TIPO', payload: val })}
          allowClear
          style={{ width: '100%' }}
        >
          <Option value="critica">
            <FireOutlined /> Crítica
          </Option>
          <Option value="alta">
            <WarningOutlined /> Alta
          </Option>
          <Option value="media">
            <ExclamationCircleOutlined /> Media
          </Option>
          <Option value="baja">
            <InfoCircleOutlined /> Baja
          </Option>
          <Option value="info">
            <BellOutlined /> Información
          </Option>
        </Select>
      </Col>
      <Col xs={24} md={5}>
        <Select
          placeholder="Estado"
          value={filtroEstado}
          onChange={(val) => dispatch({ type: 'SET_FILTRO_ESTADO', payload: val })}
          allowClear
          style={{ width: '100%' }}
        >
          <Option value="activa">Activas</Option>
          <Option value="en_proceso">En Proceso</Option>
          <Option value="resuelta">Resueltas</Option>
          <Option value="descartada">Descartadas</Option>
        </Select>
      </Col>
      <Col xs={24} md={6}>
        <Space>
          <Tooltip title="Actualizar alertas en tiempo real">
            <Button
              icon={<SyncOutlined />}
              onClick={cargarAlertas}
              loading={loading}
            >
              Actualizar
            </Button>
          </Tooltip>
          <Tooltip title="Limpiar todos los filtros">
            <Button
              icon={<FilterOutlined />}
              onClick={() => dispatch({ type: 'CLEAR_FILTERS' })}
            >
              Limpiar
            </Button>
          </Tooltip>
        </Space>
      </Col>
    </Row>
    <Row gutter={16}>
      <Col xs={24} md={12}>
        <RangePicker
          style={{ width: '100%' }}
          placeholder={['Fecha inicio', 'Fecha fin']}
          value={rangoFechas}
          onChange={(dates) => dispatch({ type: 'SET_RANGO_FECHAS', payload: dates || [null, null] })}
          format="DD/MM/YYYY"
        />
      </Col>
    </Row>
  </Card>
);

export default AlertasFiltros;
