import React from 'react';
import { Drawer, Space, Form, Radio, Divider, Checkbox, Input, Button } from 'antd';
import { FilterOutlined } from '@ant-design/icons';
import { EmbarazosAction } from '../embarazosReducer';

const { TextArea } = Input;

interface FiltrosAvanzadosDrawerProps {
  visible: boolean;
  onClose: () => void;
  vistaComparacion: 'tabla' | 'tarjetas';
  mostrarFinalizados: boolean;
  dispatch: React.Dispatch<EmbarazosAction>;
  message: { success: (m: string) => void };
}

const FiltrosAvanzadosDrawer: React.FC<FiltrosAvanzadosDrawerProps> = ({
  visible, onClose, vistaComparacion, mostrarFinalizados, dispatch, message,
}) => (
  <Drawer
    title={
      <Space>
        <FilterOutlined />
        <span>Filtros Avanzados</span>
      </Space>
    }
    placement="right"
    width={400}
    open={visible}
    onClose={onClose}
  >
    <Form layout="vertical">
      <Form.Item label="Vista de Tabla">
        <Radio.Group
          value={vistaComparacion}
          onChange={(e) => dispatch({ type: 'SET_VISTA_COMPARACION', payload: e.target.value })}
          buttonStyle="solid"
        >
          <Radio.Button value="tabla">Tabla</Radio.Button>
          <Radio.Button value="tarjetas">Tarjetas</Radio.Button>
        </Radio.Group>
      </Form.Item>

      <Form.Item label="Mostrar embarazos">
        <Radio.Group
          value={mostrarFinalizados}
          onChange={(e) => dispatch({ type: 'SET_MOSTRAR_FINALIZADOS', payload: e.target.value })}
        >
          <Space direction="vertical">
            <Radio value={false}>Solo Activos</Radio>
            <Radio value={true}>Incluir Finalizados</Radio>
          </Space>
        </Radio.Group>
      </Form.Item>

      <Divider />

      <Form.Item label="Filtrar por Trimestre">
        <Checkbox.Group>
          <Space direction="vertical">
            <Checkbox value="1">Primer Trimestre (0-13 semanas)</Checkbox>
            <Checkbox value="2">Segundo Trimestre (14-27 semanas)</Checkbox>
            <Checkbox value="3">Tercer Trimestre (28-40 semanas)</Checkbox>
          </Space>
        </Checkbox.Group>
      </Form.Item>

      <Form.Item label="Notas Adicionales">
        <TextArea
          rows={3}
          placeholder="Agregue notas sobre los filtros aplicados..."
        />
      </Form.Item>

      <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
        <Button onClick={onClose}>
          Cancelar
        </Button>
        <Button type="primary" onClick={() => {
          message.success('Filtros aplicados');
          dispatch({ type: 'SET_FILTROS_AVANZADOS_VISIBLE', payload: false });
        }}>
          Aplicar Filtros
        </Button>
      </Space>
    </Form>
  </Drawer>
);

export default FiltrosAvanzadosDrawer;
