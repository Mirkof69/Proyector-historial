// ===========================================
// FORMULARIO DE PARTO - CREAR/EDITAR
// ===========================================
// Componente completo para registro de partos
// Incluye información del parto, recién nacidos y complicaciones

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
  TimePicker,
  Switch
} from 'antd';
import { SaveOutlined, ArrowLeftOutlined } from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import { PartosService, EmbarazosService } from '../../services/api';
import { Parto, Embarazo } from '../../types';
import dayjs from 'dayjs';

const { Option } = Select;
const { TextArea } = Input;

// Componente principal del formulario
const PartoForm: React.FC = () => {
  const [form] = Form.useForm();
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [embarazos, setEmbarazos] = useState<Embarazo[]>([]);
  const isEditing = !!id;

  // Efecto para cargar datos iniciales
  useEffect(() => {
    fetchEmbarazosActivos();
    if (isEditing) {
      fetchParto();
    }
  }, [id]);

  // Obtener embarazos activos para el select
  const fetchEmbarazosActivos = async () => {
    try {
      const response = await EmbarazosService.getAll({ estado: 'activo' });
      setEmbarazos(response.data.results || response.data);
    } catch (error) {
      message.error('Error al cargar embarazos');
    }
  };

  // Obtener datos del parto al editar
  const fetchParto = async () => {
    setLoading(true);
    try {
      const response = await PartosService.getById(Number(id));
      const parto: Parto = response.data;

      // Transformar los datos para el formulario
      form.setFieldsValue({
        ...parto,
        fecha_parto: parto.fecha_parto ? dayjs(parto.fecha_parto) : null,
        hora_inicio_trabajo_parto: parto.hora_inicio_trabajo_parto ?
          dayjs(parto.hora_inicio_trabajo_parto, 'HH:mm:ss') : null,
        hora_nacimiento: parto.hora_nacimiento ?
          dayjs(parto.hora_nacimiento, 'HH:mm:ss') : null,
      });
    } catch (error) {
      message.error('Error al cargar datos del parto');
      navigate('/partos');
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
        fecha_parto: values.fecha_parto ? values.fecha_parto.format('YYYY-MM-DD') : null,
        hora_inicio_trabajo_parto: values.hora_inicio_trabajo_parto ?
          values.hora_inicio_trabajo_parto.format('HH:mm:ss') : null,
        hora_nacimiento: values.hora_nacimiento ?
          values.hora_nacimiento.format('HH:mm:ss') : null,
      };

      if (isEditing) {
        await PartosService.update(Number(id), data);
        message.success('Parto actualizado exitosamente');
      } else {
        await PartosService.create(data);
        message.success('Parto registrado exitosamente');
      }

      navigate('/partos');
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
        message.error('Error al guardar parto');
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
              onClick={() => navigate('/partos')}
              style={{ marginRight: 16 }}
            />
            {isEditing ? 'Editar Parto' : 'Nuevo Parto'}
          </div>
        }
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={{
            tipo_parto: 'eutocico',
            via_parto: 'vaginal',
            estado: 'en_curso',
            complicaciones: false,
            edad_gestacional_semanas: 40,
            edad_gestacional_dias: 0,
          }}
        >
          <Divider orientation="left">Información Básica</Divider>

          <Row gutter={16}>
            <Col xs={24} md={12}>
              <Form.Item
                label="Embarazo"
                name="embarazo"
                rules={[{ required: true, message: 'Seleccione un embarazo' }]}
              >
                <Select
                  showSearch
                  placeholder="Seleccione el embarazo"
                  optionFilterProp="children"
                  filterOption={(input, option: any) =>
                    option.children.toLowerCase().includes(input.toLowerCase())
                  }
                  disabled={isEditing}
                >
                  {embarazos.map(e => (
                    <Option key={e.id} value={e.id}>
                      {e.paciente_nombre} - Gesta {e.numero_gesta}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>

            <Col xs={24} md={6}>
              <Form.Item
                label="Fecha del Parto"
                name="fecha_parto"
                rules={[{ required: true, message: 'Campo requerido' }]}
              >
                <DatePicker
                  style={{ width: '100%' }}
                  format="DD/MM/YYYY"
                  placeholder="Seleccione fecha"
                />
              </Form.Item>
            </Col>

            <Col xs={24} md={6}>
              <Form.Item
                label="Estado"
                name="estado"
                rules={[{ required: true, message: 'Campo requerido' }]}
              >
                <Select>
                  <Option value="en_curso">En Curso</Option>
                  <Option value="finalizado">Finalizado</Option>
                  <Option value="complicado">Complicado</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Divider orientation="left">Tipo de Parto</Divider>

          <Row gutter={16}>
            <Col xs={24} md={8}>
              <Form.Item
                label="Tipo de Parto"
                name="tipo_parto"
                rules={[{ required: true, message: 'Campo requerido' }]}
              >
                <Select>
                  <Option value="eutocico">Eutócico (Normal)</Option>
                  <Option value="cesarea">Cesárea</Option>
                  <Option value="forceps">Fórceps</Option>
                  <Option value="ventosa">Ventosa</Option>
                  <Option value="distocico">Distócico</Option>
                </Select>
              </Form.Item>
            </Col>

            <Col xs={24} md={8}>
              <Form.Item
                label="Vía del Parto"
                name="via_parto"
                rules={[{ required: true, message: 'Campo requerido' }]}
              >
                <Select>
                  <Option value="vaginal">Vaginal</Option>
                  <Option value="cesarea">Cesárea</Option>
                  <Option value="vaginal_instrumentado">Vaginal Instrumentado</Option>
                </Select>
              </Form.Item>
            </Col>

            <Col xs={24} md={8}>
              <Form.Item
                label="Presentación Fetal"
                name="presentacion_fetal"
              >
                <Select placeholder="Seleccione presentación">
                  <Option value="cefalica">Cefálica</Option>
                  <Option value="podalica">Podálica</Option>
                  <Option value="transversa">Transversa</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Divider orientation="left">Horarios</Divider>

          <Row gutter={16}>
            <Col xs={24} md={8}>
              <Form.Item
                label="Hora Inicio Trabajo de Parto"
                name="hora_inicio_trabajo_parto"
              >
                <TimePicker
                  style={{ width: '100%' }}
                  format="HH:mm"
                  placeholder="Seleccione hora"
                />
              </Form.Item>
            </Col>

            <Col xs={24} md={8}>
              <Form.Item
                label="Hora de Nacimiento"
                name="hora_nacimiento"
              >
                <TimePicker
                  style={{ width: '100%' }}
                  format="HH:mm"
                  placeholder="Seleccione hora"
                />
              </Form.Item>
            </Col>

            <Col xs={24} md={8}>
              <Form.Item
                label="Duración Trabajo Parto (min)"
                name="duracion_trabajo_parto"
              >
                <InputNumber
                  min={0}
                  style={{ width: '100%' }}
                  placeholder="Minutos"
                />
              </Form.Item>
            </Col>
          </Row>

          <Divider orientation="left">Edad Gestacional</Divider>

          <Row gutter={16}>
            <Col xs={24} md={8}>
              <Form.Item
                label="Semanas de Gestación"
                name="edad_gestacional_semanas"
                rules={[{ required: true, message: 'Campo requerido' }]}
              >
                <InputNumber min={20} max={42} style={{ width: '100%' }} />
              </Form.Item>
            </Col>

            <Col xs={24} md={8}>
              <Form.Item
                label="Días Adicionales"
                name="edad_gestacional_dias"
                rules={[{ required: true, message: 'Campo requerido' }]}
              >
                <InputNumber min={0} max={6} style={{ width: '100%' }} />
              </Form.Item>
            </Col>

            <Col xs={24} md={8}>
              <Form.Item
                label="Método Determinación EG"
                name="metodo_determinacion_eg"
              >
                <Select placeholder="Seleccione método">
                  <Option value="fum">FUM</Option>
                  <Option value="ecografia">Ecografía</Option>
                  <Option value="clinico">Clínico</Option>
                  <Option value="capurro">Capurro</Option>
                  <Option value="ballard">Ballard</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Divider orientation="left">Líquido Amniótico y Placenta</Divider>

          <Row gutter={16}>
            <Col xs={24} md={8}>
              <Form.Item
                label="Aspecto Líquido Amniótico"
                name="liquido_amniotico"
              >
                <Select placeholder="Seleccione aspecto">
                  <Option value="claro">Claro</Option>
                  <Option value="meconial">Meconial</Option>
                  <Option value="hemático">Hemático</Option>
                  <Option value="purulento">Purulento</Option>
                </Select>
              </Form.Item>
            </Col>

            <Col xs={24} md={8}>
              <Form.Item
                label="Alumbramiento Placenta"
                name="alumbramiento_placenta"
              >
                <Select placeholder="Tipo de alumbramiento">
                  <Option value="espontaneo">Espontáneo</Option>
                  <Option value="manual">Manual</Option>
                  <Option value="instrumental">Instrumental</Option>
                </Select>
              </Form.Item>
            </Col>

            <Col xs={24} md={8}>
              <Form.Item
                label="Peso Placenta (g)"
                name="peso_placenta"
              >
                <InputNumber
                  min={0}
                  style={{ width: '100%' }}
                  placeholder="Gramos"
                />
              </Form.Item>
            </Col>
          </Row>

          <Divider orientation="left">Complicaciones</Divider>

          <Row gutter={16}>
            <Col xs={24} md={6}>
              <Form.Item
                label="¿Hubo Complicaciones?"
                name="complicaciones"
                valuePropName="checked"
              >
                <Switch checkedChildren="Sí" unCheckedChildren="No" />
              </Form.Item>
            </Col>

            <Col xs={24} md={18}>
              <Form.Item
                label="Descripción de Complicaciones"
                name="descripcion_complicaciones"
              >
                <TextArea
                  rows={2}
                  placeholder="Describa las complicaciones si las hubo"
                />
              </Form.Item>
            </Col>
          </Row>

          <Divider orientation="left">Observaciones</Divider>

          <Form.Item
            label="Observaciones Generales"
            name="observaciones"
          >
            <TextArea
              rows={4}
              placeholder="Observaciones sobre el parto, procedimientos realizados, etc."
            />
          </Form.Item>

          <Form.Item
            label="Notas del Médico"
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
              <Button onClick={() => navigate('/partos')}>
                Cancelar
              </Button>
              <Button
                type="primary"
                htmlType="submit"
                icon={<SaveOutlined />}
                loading={saving}
              >
                {isEditing ? 'Actualizar' : 'Registrar'} Parto
              </Button>
            </div>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
};

export default PartoForm;
