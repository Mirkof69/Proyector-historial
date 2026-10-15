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
  <Drawer rootClassName="capa-clinica"
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
      <Space direction="vertical" className="u-ancho" size="large">
        <div>
          <Text strong>Rango de Fechas</Text>
          {/* Dentro de Form.Item para que «Limpiar Filtros» (form.resetFields)
              también borre lo que se ve; antes quedaba el valor viejo en
              pantalla aunque el filtro ya no se aplicara. */}
          <Form.Item name="rangoFechas" noStyle>
            <RangePicker
              className="u-ancho u-mt-2"
              format="DD/MM/YYYY"
              onChange={(dates) => {
                handleFormChange();
                dispatchFiltros({ type: 'SET_FECHA_DESDE', payload: dates ? dates[0] || undefined : undefined });
                dispatchFiltros({ type: 'SET_FECHA_HASTA', payload: dates ? dates[1] || undefined : undefined });
              }}
            />
          </Form.Item>
        </div>

        <div>
          <Text strong>Estado de Alerta</Text>
          <Form.Item name="conAlertas" noStyle>
            <Select
              className="u-ancho u-mt-2"
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
          </Form.Item>
        </div>

        <div>
          <Text strong>Trimestre</Text>
          {/* Mismos cortes que el servidor (`?trimestre=`): 1.º hasta la
              semana 13, 2.º de 14 a 27, 3.º desde 28. Las etiquetas viejas
              («<13», «13-28», «>28») no coincidían en las semanas 13 y 28. */}
          <Form.Item name="trimestre" noStyle>
            <Select
              className="u-ancho u-mt-2"
              placeholder="Todos"
              allowClear
              onChange={(val) => {
                handleFormChange();
                dispatchFiltros({ type: 'SET_TRIMESTRE', payload: val ?? null });
              }}
            >
              <Option value={1}>1° Trimestre (hasta 13 sem)</Option>
              <Option value={2}>2° Trimestre (14-27 sem)</Option>
              <Option value={3}>3° Trimestre (28 sem o más)</Option>
            </Select>
          </Form.Item>
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
