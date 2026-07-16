import React from 'react';
import { Drawer, Space, Badge, Form, Typography, DatePicker, Select, Button } from 'antd';
import type { FormInstance } from 'antd';
import { FiltrosAction } from '../controlesReducers';
import { UIAction } from '../controlesReducers';

const { Text } = Typography;
const { Option } = Select;
const { RangePicker } = DatePicker;

interface FiltrosDrawerProps {
  filtrosDrawerVisible: boolean;
  formHasChanges: boolean;
  form: FormInstance;
  onClose: () => void;
  handleFormChange: () => void;
  dispatchFiltros: React.Dispatch<FiltrosAction>;
  dispatchUI: React.Dispatch<UIAction>;
}

const FiltrosDrawer: React.FC<FiltrosDrawerProps> = ({
  filtrosDrawerVisible, formHasChanges, form, onClose,
  handleFormChange, dispatchFiltros, dispatchUI,
}) => (
  <Drawer
    title={
      <Space>
        Filtros Avanzados
        {formHasChanges && <Badge status="processing" text="Modificado" />}
      </Space>
    }
    placement="right"
    onClose={onClose}
    open={filtrosDrawerVisible}
    width={320}
  >
    <Form form={form} layout="vertical" onValuesChange={handleFormChange}>
      <Space direction="vertical" style={{ width: '100%' }} size="large">
        <div>
          <Text strong>Rango de Fechas</Text>
          <RangePicker
            style={{ width: '100%', marginTop: 8 }}
            onChange={(dates) => {
              handleFormChange();
              dispatchFiltros({ type: 'SET_FECHA_DESDE', payload: dates ? dates[0] || undefined : undefined });
              dispatchFiltros({ type: 'SET_FECHA_HASTA', payload: dates ? dates[1] || undefined : undefined });
            }}
          />
        </div>

        <div>
          <Text strong>Estado de Alerta</Text>
          <Select
            style={{ width: '100%', marginTop: 8 }}
            placeholder="Todos"
            allowClear
            onChange={(val) => {
              handleFormChange();
              dispatchFiltros({ type: 'SET_CON_ALERTAS', payload: val });
            }}
          >
            <Option value={true}>Con Alertas</Option>
            <Option value={false}>Sin Alertas</Option>
          </Select>
        </div>

        <div>
          <Text strong>Trimestre</Text>
          <Select
            style={{ width: '100%', marginTop: 8 }}
            placeholder="Todos"
            allowClear
            onChange={(val) => {
              handleFormChange();
              dispatchFiltros({ type: 'SET_TRIMESTRE', payload: val });
            }}
          >
            <Option value={1}>1° Trimestre (&lt;13 sem)</Option>
            <Option value={2}>2° Trimestre (13-28 sem)</Option>
            <Option value={3}>3° Trimestre (&gt;28 sem)</Option>
          </Select>
        </div>

        <Button
          block
          onClick={() => {
            dispatchFiltros({ type: 'RESET' });
            dispatchUI({ type: 'SET_SEARCH_TEXT', payload: '' });
            form.resetFields();
            dispatchUI({ type: 'SET_FORM_HAS_CHANGES', payload: false });
          }}
        >
          Limpiar Filtros
        </Button>
      </Space>
    </Form>
  </Drawer>
);

export default FiltrosDrawer;
