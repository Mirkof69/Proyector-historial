import React from 'react';
import { Form, Input, Button, Space, Row, Col, Alert, Divider } from 'antd';
import { SaveOutlined, CloseOutlined, InfoCircleOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { FormularioCitaAction } from '../formularioCitaUtils';

const { TextArea } = Input;

interface StepDetallesProps {
  horaSeleccionada: dayjs.Dayjs | null;
  fechaSeleccionada: dayjs.Dayjs | null;
  loading: boolean;
  id?: string;
  handleCancel: () => void;
  dispatch: React.Dispatch<FormularioCitaAction>;
}

const StepDetalles: React.FC<StepDetallesProps> = ({
  horaSeleccionada, fechaSeleccionada, loading, id, handleCancel, dispatch,
}) => (
  <>
    {/* Resumen de Selección */}
    {horaSeleccionada && fechaSeleccionada && (
      <Alert
        message="Resumen de Cita"
        description={
          <>
            <strong>Fecha:</strong> {fechaSeleccionada.format('DD/MM/YYYY')} |
            <strong> Hora:</strong> {horaSeleccionada.format('HH:mm')}
          </>
        }
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
      />
    )}
    <Row gutter={16}>
      <Col xs={24}>
        <Form.Item
          label={
            <Space>
              <InfoCircleOutlined />
              <span>Motivo de la Cita</span>
            </Space>
          }
          name="motivo"
          rules={[
            { required: true, message: 'Ingrese el motivo de la cita' },
            { min: 10, message: 'El motivo debe tener al menos 10 caracteres' },
          ]}
        >
          <TextArea
            rows={4}
            placeholder="Describa el motivo de la cita según lo referido por el paciente"
            maxLength={500}
            showCount
          />
        </Form.Item>
      </Col>
    </Row>

    <Row gutter={16}>
      <Col xs={24}>
        <Form.Item
          label="Observaciones Adicionales (Opcional)"
          name="observaciones"
        >
          <TextArea
            rows={3}
            placeholder="Observaciones adicionales sobre la cita"
            maxLength={500}
            showCount
          />
        </Form.Item>
      </Col>
    </Row>

    <Divider />
    <Row justify="space-between">
      <Col>
        <Button onClick={() => dispatch({ type: 'SET_CURRENT_STEP', payload: 1 })}>
          Anterior
        </Button>
      </Col>
      <Col>
        <Space>
          <Button icon={<CloseOutlined />} onClick={handleCancel}>
            Cancelar
          </Button>
          <Button
            type="primary"
            htmlType="submit"
            loading={loading}
            icon={<SaveOutlined />}
          >
            {id ? 'Actualizar' : 'Crear'} Cita
          </Button>
        </Space>
      </Col>
    </Row>
  </>
);

export default StepDetalles;
