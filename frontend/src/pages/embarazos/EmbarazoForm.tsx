// ===========================================
// FORMULARIO DE EMBARAZO - CREAR/EDITAR
// ===========================================
// Componente completo para gestión de embarazos
// Incluye cálculo automático de FPP, validación y manejo de errores

import React, { useEffect, useState } from 'react';
import {
  Form,
  Input,
  Select,
  DatePicker,
  Button,
  Card,
  Row,
  Col,
  message,
  Spin,
  Divider,
  InputNumber,
  Switch
} from 'antd';
import { SaveOutlined, ArrowLeftOutlined, CalculatorOutlined } from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import { EmbarazosService, PacientesService } from '../../services/api';
import { Embarazo, Paciente } from '../../types';
import dayjs from 'dayjs';

const { Option } = Select;
const { TextArea } = Input;

// Componente principal del formulario
const EmbarazoForm: React.FC = () => {
  const [form] = Form.useForm();
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [pacientes, setPacientes] = useState<Paciente[]>([]);
  const isEditing = !!id;

  // Efecto para cargar datos iniciales
  useEffect(() => {
    fetchPacientes();
    if (isEditing) {
      fetchEmbarazo();
    }
  }, [id]);

  // Función para calcular FPP basado en FUM (Regla de Naegele)
  const calcularFPP = (fum: dayjs.Dayjs) => {
    // FPP = FUM + 280 días
    return fum.add(280, 'days');
  };

  // Handler para cambio de FUM
  const handleFUMChange = (date: dayjs.Dayjs | null) => {
    if (date) {
      const fpp = calcularFPP(date);
      form.setFieldsValue({ fecha_probable_parto: fpp });
    }
  };

  // Obtener lista de pacientes para el select
  const fetchPacientes = async () => {
    try {
      const response = await PacientesService.getAll({ genero: 'femenino' });
      setPacientes(response.data.results || response.data);
    } catch (error) {
      message.error('Error al cargar pacientes');
    }
  };

  // Obtener datos del embarazo al editar
  const fetchEmbarazo = async () => {
    setLoading(true);
    try {
      const response = await EmbarazosService.getById(Number(id));
      const embarazo: Embarazo = response.data;

      // Transformar los datos para el formulario
      form.setFieldsValue({
        ...embarazo,
        fecha_ultima_menstruacion: embarazo.fecha_ultima_menstruacion ?
          dayjs(embarazo.fecha_ultima_menstruacion) : null,
        fecha_probable_parto: embarazo.fecha_probable_parto ?
          dayjs(embarazo.fecha_probable_parto) : null,
        fecha_inicio_control: embarazo.fecha_inicio_control ?
          dayjs(embarazo.fecha_inicio_control) : null,
      });
    } catch (error) {
      message.error('Error al cargar datos del embarazo');
      navigate('/embarazos');
    } finally {
      setLoading(false);
    }
  };

  // Función para guardar (crear o actualizar)
  const handleSubmit = async (values: any) => {
    setSaving(true);
    try {
      // Preparar datos para enviar
      const data = {
        ...values,
        fecha_ultima_menstruacion: values.fecha_ultima_menstruacion ?
          values.fecha_ultima_menstruacion.format('YYYY-MM-DD') : null,
        fecha_probable_parto: values.fecha_probable_parto ?
          values.fecha_probable_parto.format('YYYY-MM-DD') : null,
        fecha_inicio_control: values.fecha_inicio_control ?
          values.fecha_inicio_control.format('YYYY-MM-DD') : null,
      };

      if (isEditing) {
        await EmbarazosService.update(Number(id), data);
        message.success('Embarazo actualizado exitosamente');
      } else {
        await EmbarazosService.create(data);
        message.success('Embarazo registrado exitosamente');
      }

      navigate('/embarazos');
    } catch (error: any) {
      console.error('Error al guardar:', error);

      // Manejo de errores específicos
      if (error.response?.data) {
        const errors = error.response.data;
        Object.keys(errors).forEach(key => {
          const errorMessage = Array.isArray(errors[key]) ? errors[key][0] : errors[key];
          message.error(`${key}: ${errorMessage}`);
        });
      } else {
        message.error('Error al guardar embarazo');
      }
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px' }}>
        <Spin size="large" />
      </div>
    );
  }

  return (
    <div style={{ padding: 24 }}>
      <Card
        title={
          <div>
            <Button
              icon={<ArrowLeftOutlined />}
              onClick={() => navigate('/embarazos')}
              style={{ marginRight: 16 }}
            />
            {isEditing ? 'Editar Embarazo' : 'Nuevo Embarazo'}
          </div>
        }
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={{
            tipo_embarazo: 'unico',
            riesgo_embarazo: 'bajo',
            estado: 'activo',
            numero_gesta: 1,
            numero_para: 0,
            numero_aborto: 0,
            numero_cesarea: 0,
            embarazo_planificado: false,
          }}
        >
          <Divider orientation="left">Información del Embarazo</Divider>

          <Row gutter={16}>
            <Col xs={24} md={12}>
              <Form.Item
                label="Paciente"
                name="paciente"
                rules={[{ required: true, message: 'Seleccione una paciente' }]}
              >
                <Select
                  showSearch
                  placeholder="Seleccione la paciente"
                  optionFilterProp="children"
                  filterOption={(input, option: any) =>
                    option.children.toLowerCase().includes(input.toLowerCase())
                  }
                  disabled={isEditing}
                >
                  {pacientes.map(p => (
                    <Option key={p.id} value={p.id}>
                      {p.nombre_completo} - {p.id_clinico}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>

            <Col xs={24} md={6}>
              <Form.Item
                label="Número de Gesta"
                name="numero_gesta"
                rules={[{ required: true, message: 'Campo requerido' }]}
              >
                <InputNumber min={1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>

            <Col xs={24} md={6}>
              <Form.Item
                label="Estado"
                name="estado"
                rules={[{ required: true, message: 'Campo requerido' }]}
              >
                <Select>
                  <Option value="activo">Activo</Option>
                  <Option value="finalizado">Finalizado</Option>
                  <Option value="perdida">Pérdida</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Divider orientation="left">Fechas y Cálculos</Divider>

          <Row gutter={16}>
            <Col xs={24} md={8}>
              <Form.Item
                label="Fecha Última Menstruación (FUM)"
                name="fecha_ultima_menstruacion"
                rules={[{ required: true, message: 'Campo requerido' }]}
              >
                <DatePicker
                  style={{ width: '100%' }}
                  format="DD/MM/YYYY"
                  placeholder="Seleccione fecha"
                  onChange={handleFUMChange}
                />
              </Form.Item>
            </Col>

            <Col xs={24} md={8}>
              <Form.Item
                label={
                  <span>
                    Fecha Probable de Parto (FPP) <CalculatorOutlined />
                  </span>
                }
                name="fecha_probable_parto"
              >
                <DatePicker
                  style={{ width: '100%' }}
                  format="DD/MM/YYYY"
                  placeholder="Calculado automáticamente"
                  disabled
                />
              </Form.Item>
            </Col>

            <Col xs={24} md={8}>
              <Form.Item
                label="Fecha Inicio Control"
                name="fecha_inicio_control"
              >
                <DatePicker
                  style={{ width: '100%' }}
                  format="DD/MM/YYYY"
                  placeholder="Seleccione fecha"
                />
              </Form.Item>
            </Col>
          </Row>

          <Divider orientation="left">Características del Embarazo</Divider>

          <Row gutter={16}>
            <Col xs={24} md={8}>
              <Form.Item
                label="Tipo de Embarazo"
                name="tipo_embarazo"
                rules={[{ required: true, message: 'Campo requerido' }]}
              >
                <Select>
                  <Option value="unico">Único</Option>
                  <Option value="gemelar">Gemelar</Option>
                  <Option value="multiple">Múltiple</Option>
                </Select>
              </Form.Item>
            </Col>

            <Col xs={24} md={8}>
              <Form.Item
                label="Riesgo del Embarazo"
                name="riesgo_embarazo"
                rules={[{ required: true, message: 'Campo requerido' }]}
              >
                <Select>
                  <Option value="bajo">Bajo</Option>
                  <Option value="medio">Medio</Option>
                  <Option value="alto">Alto</Option>
                </Select>
              </Form.Item>
            </Col>

            <Col xs={24} md={8}>
              <Form.Item
                label="Embarazo Planificado"
                name="embarazo_planificado"
                valuePropName="checked"
              >
                <Switch checkedChildren="Sí" unCheckedChildren="No" />
              </Form.Item>
            </Col>
          </Row>

          <Divider orientation="left">Antecedentes Obstétricos (GPAC)</Divider>

          <Row gutter={16}>
            <Col xs={24} md={6}>
              <Form.Item
                label="Número de Partos"
                name="numero_para"
              >
                <InputNumber min={0} style={{ width: '100%' }} />
              </Form.Item>
            </Col>

            <Col xs={24} md={6}>
              <Form.Item
                label="Número de Abortos"
                name="numero_aborto"
              >
                <InputNumber min={0} style={{ width: '100%' }} />
              </Form.Item>
            </Col>

            <Col xs={24} md={6}>
              <Form.Item
                label="Número de Cesáreas"
                name="numero_cesarea"
              >
                <InputNumber min={0} style={{ width: '100%' }} />
              </Form.Item>
            </Col>

            <Col xs={24} md={6}>
              <Form.Item
                label="Hijos Vivos"
                name="hijos_vivos"
              >
                <InputNumber min={0} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Divider orientation="left">Observaciones y Notas</Divider>

          <Form.Item
            label="Observaciones"
            name="observaciones"
          >
            <TextArea
              rows={4}
              placeholder="Observaciones sobre el embarazo, complicaciones previas, etc."
            />
          </Form.Item>

          <Form.Item
            label="Notas Adicionales"
            name="notas"
          >
            <TextArea
              rows={3}
              placeholder="Notas adicionales del médico"
            />
          </Form.Item>

          {/* Botones de acción */}
          <Form.Item>
            <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
              <Button onClick={() => navigate('/embarazos')}>
                Cancelar
              </Button>
              <Button
                type="primary"
                htmlType="submit"
                icon={<SaveOutlined />}
                loading={saving}
              >
                {isEditing ? 'Actualizar' : 'Registrar'} Embarazo
              </Button>
            </div>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
};

export default EmbarazoForm;
