import React, { useState, useEffect } from 'react';
import { Form, Input, DatePicker, Button, Card, message, Row, Col, Select } from 'antd';
import { SaveOutlined, CloseOutlined } from '@ant-design/icons';
import axios from 'axios';
import { authService } from '../services/authService';
import dayjs from 'dayjs';
import 'dayjs/locale/es';

dayjs.locale('es');

interface FormularioEmbarazoProps {
  onCancel: () => void;
  onSuccess: () => void;
}

interface Paciente {
  id: number;
  nombre: string;
  apellido_paterno: string;
  apellido_materno: string;
  id_clinico: string;
  genero: string;
}

const FormularioEmbarazo: React.FC<FormularioEmbarazoProps> = ({ onCancel, onSuccess }) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [pacientes, setPacientes] = useState<Paciente[]>([]);
  const [fpp, setFpp] = useState<string>('');

  useEffect(() => {
    fetchPacientes();
  }, []);

  const fetchPacientes = async () => {
    try {
      const token = authService.getToken();
      const response = await axios.get('http://127.0.0.1:8000/api/pacientes/', {
        headers: { Authorization: `Bearer ${token}` }
      });
      const pacientesFemeninos = response.data.filter((p: Paciente) => p.genero === 'femenino');
      setPacientes(pacientesFemeninos);
    } catch (error) {
      console.error('Error al cargar pacientes:', error);
      message.error('Error al cargar lista de pacientes');
    }
  };

  const calcularFPP = (fum: any) => {
    if (fum) {
      const fechaFPP = dayjs(fum).add(280, 'day');
      setFpp(fechaFPP.format('DD/MM/YYYY'));
      form.setFieldsValue({ fecha_probable_parto: fechaFPP });
    }
  };

  const translateError = (msg: string): string => {
    const translations: any = {
      'This field is required.': 'Este campo es obligatorio',
      'This field may not be blank.': 'Este campo no puede estar en blanco',
      'Enter a valid date.': 'Ingrese una fecha válida'
    };
    return translations[msg] || msg;
  };

  const onFinish = async (values: any) => {
    setLoading(true);
    
    try {
      const token = authService.getToken();
      await axios.post('http://127.0.0.1:8000/api/embarazos/', {
        paciente: values.paciente,
        numero_gesta: values.numero_gesta,
        fecha_ultima_menstruacion: dayjs(values.fecha_ultima_menstruacion).format('YYYY-MM-DD'),
        fecha_probable_parto: values.fecha_probable_parto ? dayjs(values.fecha_probable_parto).format('YYYY-MM-DD') : null,
        tipo_embarazo: values.tipo_embarazo || 'simple',
        riesgo_embarazo: values.riesgo_embarazo || 'bajo',
        estado: values.estado || 'activo',
        notas: values.notas || ''
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      message.success('Embarazo registrado exitosamente');
      form.resetFields();
      setFpp('');
      onSuccess();
    } catch (error: any) {
      console.error('Error al crear embarazo:', error.response?.data);
      
      const errorData = error.response?.data;
      
      if (errorData?.errores) {
        const fieldErrors: any = {};
        
        Object.keys(errorData.errores).forEach(key => {
          const errorArray = errorData.errores[key];
          let errorMessage = Array.isArray(errorArray) ? errorArray[0] : errorArray;
          errorMessage = translateError(errorMessage);
          
          const fieldMap: any = {
            'paciente': 'paciente',
            'numero_gesta': 'numero_gesta',
            'fecha_ultima_menstruacion': 'fecha_ultima_menstruacion',
            'fecha_probable_parto': 'fecha_probable_parto',
            'tipo_embarazo': 'tipo_embarazo',
            'riesgo_embarazo': 'riesgo_embarazo',
            'estado': 'estado'
          };
          
          const frontendField = fieldMap[key] || key;
          fieldErrors[frontendField] = errorMessage;
        });
        
        form.setFields(
          Object.keys(fieldErrors).map(field => ({
            name: field,
            errors: [fieldErrors[field]]
          }))
        );
        
        message.error('Por favor corrija los errores en el formulario');
      } else if (errorData?.error) {
        message.error(translateError(errorData.error));
      } else {
        message.error('Error al registrar embarazo');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card title="Nuevo Embarazo">
      <Form
        form={form}
        layout="vertical"
        onFinish={onFinish}
      >
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              name="paciente"
              label="Paciente"
              rules={[{ required: true, message: 'Este campo es obligatorio' }]}
            >
              <Select
                placeholder="Seleccionar paciente"
                showSearch
                optionFilterProp="children"
                filterOption={(input, option: any) =>
                  option.children.toLowerCase().includes(input.toLowerCase())
                }
              >
                {pacientes.map(p => (
                  <Select.Option key={p.id} value={p.id}>
                    {`${p.id_clinico} - ${p.nombre} ${p.apellido_paterno} ${p.apellido_materno || ''}`}
                  </Select.Option>
                ))}
              </Select>
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              name="numero_gesta"
              label="Número de Gesta"
              initialValue={1}
              rules={[
                { required: true, message: 'Este campo es obligatorio' },
                { type: 'number', min: 1, max: 20, message: 'Debe ser entre 1 y 20' }
              ]}
            >
              <Input type="number" min={1} max={20} placeholder="1" />
            </Form.Item>
          </Col>
        </Row>

        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              name="fecha_ultima_menstruacion"
              label="Fecha Última Menstruación (FUM)"
              rules={[{ required: true, message: 'Este campo es obligatorio' }]}
            >
              <DatePicker 
                style={{ width: '100%' }} 
                format="DD/MM/YYYY"
                placeholder="Seleccionar cualquier fecha"
                onChange={calcularFPP}
              />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              name="fecha_probable_parto"
              label="Fecha Probable de Parto (FPP)"
            >
              <DatePicker 
                style={{ width: '100%' }} 
                format="DD/MM/YYYY"
                placeholder="Editable manualmente"
              />
            </Form.Item>
            {fpp && <div style={{ color: '#52c41a', marginTop: -16 }}>✓ FPP calculada: {fpp}</div>}
          </Col>
        </Row>

        <Row gutter={16}>
          <Col span={8}>
            <Form.Item
              name="tipo_embarazo"
              label="Tipo de Embarazo"
              initialValue="simple"
              rules={[{ required: true, message: 'Este campo es obligatorio' }]}
            >
              <Select>
                <Select.Option value="simple">Simple</Select.Option>
                <Select.Option value="gemelar">Gemelar</Select.Option>
                <Select.Option value="multiple">Múltiple</Select.Option>
              </Select>
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item
              name="riesgo_embarazo"
              label="Nivel de Riesgo"
              initialValue="bajo"
              rules={[{ required: true, message: 'Este campo es obligatorio' }]}
            >
              <Select>
                <Select.Option value="bajo">Bajo</Select.Option>
                <Select.Option value="medio">Medio</Select.Option>
                <Select.Option value="alto">Alto</Select.Option>
              </Select>
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item
              name="estado"
              label="Estado"
              initialValue="activo"
              rules={[{ required: true, message: 'Este campo es obligatorio' }]}
            >
              <Select>
                <Select.Option value="activo">Activo</Select.Option>
                <Select.Option value="finalizado">Finalizado</Select.Option>
                <Select.Option value="perdida">Pérdida</Select.Option>
              </Select>
            </Form.Item>
          </Col>
        </Row>

        <Row gutter={16}>
          <Col span={24}>
            <Form.Item
              name="notas"
              label="Notas / Observaciones"
            >
              <Input.TextArea rows={4} placeholder="Observaciones del embarazo..." />
            </Form.Item>
          </Col>
        </Row>

        <Form.Item>
          <Button type="primary" htmlType="submit" loading={loading} icon={<SaveOutlined />}>
            Guardar
          </Button>
          <Button style={{ marginLeft: 8 }} onClick={onCancel} icon={<CloseOutlined />}>
            Cancelar
          </Button>
        </Form.Item>
      </Form>
    </Card>
  );
};

export default FormularioEmbarazo;