import React from 'react';
import { Form, Select, DatePicker, TimePicker, Button, Space, Row, Col, Alert, Divider } from 'antd';
import { CalendarOutlined, ClockCircleOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { FormularioCitaAction } from '../formularioCitaUtils';
import { HorarioDisponible } from '../../../services/citasService';
import HorariosDisponibles from './HorariosDisponibles';

const { Option } = Select;

interface StepFechaHoraProps {
  medicoSeleccionado: number | null;
  fechaSeleccionada: dayjs.Dayjs | null;
  loadingHorarios: boolean;
  horariosDisponibles: HorarioDisponible[];
  handleFechaChange: (date: dayjs.Dayjs | null) => void;
  handleHoraChange: (time: dayjs.Dayjs | null) => void;
  handleHoraSelect: (hora: string) => void;
  isHorarioDisponible: (hora: dayjs.Dayjs) => boolean;
  dispatch: React.Dispatch<FormularioCitaAction>;
}

const StepFechaHora: React.FC<StepFechaHoraProps> = ({
  medicoSeleccionado, fechaSeleccionada, loadingHorarios, horariosDisponibles,
  handleFechaChange, handleHoraChange, handleHoraSelect, isHorarioDisponible, dispatch,
}) => (
  <>
    <Alert
      message="Programación de Cita"
      description="Seleccione la fecha y hora de la cita. Los horarios disponibles se mostrarán automáticamente."
      type="info"
      showIcon
      style={{ marginBottom: 16 }}
    />

    <Row gutter={16}>
      <Col xs={24} md={8}>
        <Form.Item
          label={
            <Space>
              <CalendarOutlined />
              <span>Fecha de la Cita</span>
            </Space>
          }
          name="fecha_cita"
          rules={[{ required: true, message: 'Seleccione la fecha' }]}
        >
          <DatePicker
            style={{ width: '100%' }}
            format="DD/MM/YYYY"
            disabledDate={(current) => current && current < dayjs().startOf('day')}
            onChange={handleFechaChange}
          />
        </Form.Item>
      </Col>

      <Col xs={24} md={8}>
        <Form.Item
          label={
            <Space>
              <ClockCircleOutlined />
              <span>Hora de la Cita</span>
            </Space>
          }
          name="hora_cita"
          rules={[
            { required: true, message: 'Seleccione la hora' },
            {
              validator: (_, value) => {
                if (!value) return Promise.resolve();
                if (isHorarioDisponible(value)) {
                  return Promise.resolve();
                }
                return Promise.reject(new Error('Este horario no está disponible'));
              },
            },
          ]}
        >
          <TimePicker
            style={{ width: '100%' }}
            format="HH:mm"
            minuteStep={15}
            disabled={!medicoSeleccionado || !fechaSeleccionada}
            onChange={handleHoraChange}
          />
        </Form.Item>
      </Col>

      <Col xs={24} md={8}>
        <Form.Item
          label="Duración (minutos)"
          name="duracion"
          tooltip="Duración estimada de la consulta"
        >
          <Select>
            <Option value={15}>15 minutos</Option>
            <Option value={30}>30 minutos</Option>
            <Option value={45}>45 minutos</Option>
            <Option value={60}>1 hora</Option>
            <Option value={90}>1.5 horas</Option>
            <Option value={120}>2 horas</Option>
          </Select>
        </Form.Item>
      </Col>
    </Row>

    <HorariosDisponibles
      medicoSeleccionado={medicoSeleccionado}
      fechaSeleccionada={fechaSeleccionada}
      loadingHorarios={loadingHorarios}
      horariosDisponibles={horariosDisponibles}
      onHoraSelect={handleHoraSelect}
    />

    <Divider />
    <Row justify="space-between">
      <Col>
        <Button onClick={() => dispatch({ type: 'SET_CURRENT_STEP', payload: 0 })}>
          Anterior
        </Button>
      </Col>
      <Col>
        <Button type="primary" onClick={() => dispatch({ type: 'SET_CURRENT_STEP', payload: 2 })}>
          Siguiente
        </Button>
      </Col>
    </Row>
  </>
);

export default StepFechaHora;
