/**
 * =============================================================================
 * CONSULTORIOS - FORMULARIO CREAR/EDITAR
 * =============================================================================
 * Formulario completo para crear o editar consultorios
 * =============================================================================
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Card, Form, Input, Select, InputNumber, Button, Switch,
  Row, Col, message, Divider, Space
} from 'antd';
import { SaveOutlined, ArrowLeftOutlined } from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import { consultoriosService } from '../../services/consultoriosService';

const { Option } = Select;
const { TextArea } = Input;

const FormularioConsultorio: React.FC = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [cargando, setCargando] = useState(false);
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const esEdicion = Boolean(id);

  const cargarConsultorio = useCallback(async (consultorioId: number) => {
    setCargando(true);
    try {
      const data = await consultoriosService.getById(consultorioId);
      form.setFieldsValue(data);
    } catch (error) {
      message.error('Error cargando consultorio');
    } finally {
      setCargando(false);
    }
  }, [form]);

  useEffect(() => {
    if (esEdicion && id) {
      cargarConsultorio(parseInt(id));
    }
  }, [id, esEdicion, cargarConsultorio]);

  const handleSubmit = async (values: any) => {
    setLoading(true);
    try {
      if (esEdicion && id) {
        await consultoriosService.update(parseInt(id), values);
        message.success('Consultorio actualizado exitosamente');
      } else {
        await consultoriosService.create(values);
        message.success('Consultorio creado exitosamente');
      }
      navigate('/consultorios');
    } catch (error) {
      message.error(esEdicion ? 'Error actualizando consultorio' : 'Error creando consultorio');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '24px' }}>
      <Card
        title={
          <Space>
            <Button
              icon={<ArrowLeftOutlined />}
              onClick={() => navigate('/consultorios')}
            />
            {esEdicion ? 'Editar Consultorio' : 'Nuevo Consultorio'}
          </Space>
        }
        loading={cargando}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={{
            activo: true,
            tiene_camilla: false,
            tiene_escritorio: false,
            tiene_computadora: false,
            tiene_lavamanos: false,
            tiene_oxigeno: false,
            tiene_aspirador: false,
            estado: 'disponible',
            capacidad: 1,
          }}
        >
          {/* Información Básica */}
          <Divider orientation="left">Información Básica</Divider>
          <Row gutter={16}>
            <Col xs={24} md={8}>
              <Form.Item
                label="Código"
                name="codigo"
                rules={[
                  { required: true, message: 'El código es requerido' },
                  { max: 20, message: 'Máximo 20 caracteres' },
                ]}
              >
                <Input placeholder="Ej: CONS-001" />
              </Form.Item>
            </Col>
            <Col xs={24} md={16}>
              <Form.Item
                label="Nombre"
                name="nombre"
                rules={[
                  { required: true, message: 'El nombre es requerido' },
                  { max: 100, message: 'Máximo 100 caracteres' },
                ]}
              >
                <Input placeholder="Ej: Consultorio de Ginecología 1" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col xs={24} md={12}>
              <Form.Item
                label="Tipo"
                name="tipo"
                rules={[{ required: true, message: 'El tipo es requerido' }]}
              >
                <Select placeholder="Seleccione tipo">
                  <Option value="consulta">Consulta</Option>
                  <Option value="procedimientos">Procedimientos</Option>
                  <Option value="emergencia">Emergencia</Option>
                  <Option value="multifuncional">Multifuncional</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item
                label="Estado"
                name="estado"
              >
                <Select placeholder="Seleccione estado">
                  <Option value="disponible">Disponible</Option>
                  <Option value="ocupado">Ocupado</Option>
                  <Option value="mantenimiento">Mantenimiento</Option>
                  <Option value="limpieza">Limpieza</Option>
                  <Option value="reservado">Reservado</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col xs={24} md={8}>
              <Form.Item
                label="Área"
                name="area"
              >
                <Input placeholder="Ej: Maternidad" />
              </Form.Item>
            </Col>
            <Col xs={24} md={8}>
              <Form.Item
                label="Piso"
                name="piso"
              >
                <InputNumber min={0} max={20} style={{ width: '100%' }} placeholder="0" />
              </Form.Item>
            </Col>
            <Col xs={24} md={8}>
              <Form.Item
                label="Capacidad"
                name="capacidad"
              >
                <InputNumber min={1} max={20} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          {/* Equipamiento */}
          <Divider orientation="left">Equipamiento</Divider>
          <Row gutter={16}>
            <Col xs={24} md={12}>
              <Form.Item
                label="Tipo de Equipamiento"
                name="equipamiento"
              >
                <Select placeholder="Seleccione equipamiento" allowClear>
                  <Option value="basico">Básico</Option>
                  <Option value="intermedio">Intermedio</Option>
                  <Option value="avanzado">Avanzado</Option>
                  <Option value="quirurgico">Quirúrgico</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col xs={12} md={6}>
              <Form.Item label="Tiene Camilla" name="tiene_camilla" valuePropName="checked">
                <Switch />
              </Form.Item>
            </Col>
            <Col xs={12} md={6}>
              <Form.Item label="Tiene Escritorio" name="tiene_escritorio" valuePropName="checked">
                <Switch />
              </Form.Item>
            </Col>
            <Col xs={12} md={6}>
              <Form.Item label="Tiene Computadora" name="tiene_computadora" valuePropName="checked">
                <Switch />
              </Form.Item>
            </Col>
            <Col xs={12} md={6}>
              <Form.Item label="Tiene Lavamanos" name="tiene_lavamanos" valuePropName="checked">
                <Switch />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col xs={12} md={6}>
              <Form.Item label="Tiene Oxígeno" name="tiene_oxigeno" valuePropName="checked">
                <Switch />
              </Form.Item>
            </Col>
            <Col xs={12} md={6}>
              <Form.Item label="Tiene Aspirador" name="tiene_aspirador" valuePropName="checked">
                <Switch />
              </Form.Item>
            </Col>
          </Row>

          {/* Descripción y Observaciones */}
          <Divider orientation="left">Descripción y Observaciones</Divider>
          <Row gutter={16}>
            <Col xs={24}>
              <Form.Item
                label="Descripción"
                name="descripcion"
              >
                <TextArea rows={3} placeholder="Descripción del consultorio" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col xs={24}>
              <Form.Item
                label="Observaciones"
                name="observaciones"
              >
                <TextArea rows={3} placeholder="Notas adicionales sobre el consultorio" />
              </Form.Item>
            </Col>
          </Row>

          {/* Estado Activo */}
          <Row gutter={16}>
            <Col xs={24}>
              <Form.Item label="Activo" name="activo" valuePropName="checked">
                <Switch />
              </Form.Item>
            </Col>
          </Row>

          {/* Botones */}
          <Form.Item>
            <Space>
              <Button
                type="primary"
                htmlType="submit"
                icon={<SaveOutlined />}
                loading={loading}
              >
                {esEdicion ? 'Actualizar' : 'Crear'} Consultorio
              </Button>
              <Button onClick={() => navigate('/consultorios')}>
                Cancelar
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
};

export default FormularioConsultorio;
