import React, { useState, useEffect } from 'react';
import { Form, Input, InputNumber, DatePicker, Button, Card, message, Row, Col, Select } from 'antd';
import { SaveOutlined, CloseOutlined } from '@ant-design/icons';
import axios from 'axios';
import { authService } from '../services/authService';
import dayjs from 'dayjs';
import 'dayjs/locale/es';

dayjs.locale('es');

interface FormularioControlProps {
  onCancel: () => void;
  onSuccess: () => void;
}

interface Embarazo {
  id: number;
  paciente: number;
  paciente_nombre: string;
  numero_gesta: number;
  fecha_ultima_menstruacion: string;
  estado: string;
}

const FormularioControl: React.FC<FormularioControlProps> = ({ onCancel, onSuccess }) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [embarazos, setEmbarazos] = useState<Embarazo[]>([]);
  const [imcCalculado, setImcCalculado] = useState<string>('');
  const [pamCalculada, setPamCalculada] = useState<string>('');
  const [gananciaCalculada, setGananciaCalculada] = useState<string>('');

  useEffect(() => {
    fetchEmbarazos();
  }, []);

  const fetchEmbarazos = async () => {
    try {
      const token = authService.getToken();
      const response = await axios.get('http://127.0.0.1:8000/api/embarazos/?estado=activo', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setEmbarazos(response.data);
    } catch (error) {
      console.error('Error al cargar embarazos:', error);
      message.error('Error al cargar lista de embarazos');
    }
  };

  const calcularSemanasGestacion = (embarazoId: number) => {
    const embarazo = embarazos.find(e => e.id === embarazoId);
    if (embarazo) {
      const hoy = dayjs();
      const fum = dayjs(embarazo.fecha_ultima_menstruacion);
      const diasDiferencia = hoy.diff(fum, 'day');
      const semanas = Math.floor(diasDiferencia / 7);
      const dias = diasDiferencia % 7;
      
      form.setFieldsValue({ 
        semanas_gestacion: semanas,
        dias_gestacion: dias
      });
    }
  };

  const calcularIMC = () => {
    const peso = form.getFieldValue('peso_actual');
    const talla = form.getFieldValue('talla');
    
    if (peso && talla) {
      const tallaM = talla / 100;
      const imc = peso / (tallaM * tallaM);
      let clasificacion = '';
      
      if (imc < 18.5) clasificacion = 'Bajo peso';
      else if (imc < 25) clasificacion = 'Normal';
      else if (imc < 30) clasificacion = 'Sobrepeso';
      else clasificacion = 'Obesidad';
      
      setImcCalculado(`${imc.toFixed(2)} - ${clasificacion}`);
    }
  };

  const calcularGananciaPeso = () => {
    const pesoActual = form.getFieldValue('peso_actual');
    const pesoPregestacional = form.getFieldValue('peso_pregestacional');
    
    if (pesoActual && pesoPregestacional) {
      const ganancia = pesoActual - pesoPregestacional;
      setGananciaCalculada(`${ganancia > 0 ? '+' : ''}${ganancia.toFixed(1)} kg`);
    }
  };

  const calcularPAM = () => {
    const sistolica = form.getFieldValue('presion_arterial_sistolica');
    const diastolica = form.getFieldValue('presion_arterial_diastolica');
    
    if (sistolica && diastolica) {
      const pam = (sistolica + (2 * diastolica)) / 3;
      setPamCalculada(`PAM: ${pam.toFixed(2)} mmHg`);
    }
  };

  const translateError = (msg: string): string => {
    const translations: any = {
      'This field is required.': 'Este campo es obligatorio',
      'This field may not be blank.': 'Este campo no puede estar en blanco',
      'Enter a valid date.': 'Ingrese una fecha válida',
      'Enter a valid number.': 'Ingrese un número válido'
    };
    return translations[msg] || msg;
  };

  const onFinish = async (values: any) => {
    setLoading(true);
    
    try {
      const token = authService.getToken();
      const user = authService.getCurrentUser();
      const embarazoSeleccionado = embarazos.find(e => e.id === values.embarazo);
      
      await axios.post('http://127.0.0.1:8000/api/controles/', {
        embarazo_id: values.embarazo,
        paciente: embarazoSeleccionado?.paciente,
        numero_control: values.numero_control,
        fecha_control: dayjs(values.fecha_control).format('YYYY-MM-DD'),
        semanas_gestacion: values.semanas_gestacion,
        dias_gestacion: values.dias_gestacion || 0,
        peso_actual: values.peso_actual,
        peso_pregestacional: values.peso_pregestacional,
        talla: values.talla,
        presion_arterial_sistolica: values.presion_arterial_sistolica,
        presion_arterial_diastolica: values.presion_arterial_diastolica,
        frecuencia_cardiaca: values.frecuencia_cardiaca,
        temperatura: values.temperatura,
        altura_uterina: values.altura_uterina,
        frecuencia_cardiaca_fetal: values.frecuencia_cardiaca_fetal,
        presentacion_fetal: values.presentacion_fetal,
        movimientos_fetales: values.movimientos_fetales,
        edema: values.edema || 'no',
        proteinuria: values.proteinuria || 'negativa',
        observaciones: values.observaciones || '',
        medico_id: user?.id || 1
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      message.success('Control prenatal registrado exitosamente');
      form.resetFields();
      setImcCalculado('');
      setPamCalculada('');
      setGananciaCalculada('');
      onSuccess();
    } catch (error: any) {
      console.error('Error al crear control:', error.response?.data);
      
      const errorData = error.response?.data;
      
      if (errorData?.errores) {
        const fieldErrors: any = {};
        
        Object.keys(errorData.errores).forEach(key => {
          const errorArray = errorData.errores[key];
          let errorMessage = Array.isArray(errorArray) ? errorArray[0] : errorArray;
          errorMessage = translateError(errorMessage);
          fieldErrors[key] = errorMessage;
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
        message.error('Error al registrar control');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card title="Nuevo Control Prenatal">
      <Form
        form={form}
        layout="vertical"
        onFinish={onFinish}
        initialValues={{
          fecha_control: dayjs(),
          numero_control: 1,
          dias_gestacion: 0,
          edema: 'no',
          proteinuria: 'negativa',
          movimientos_fetales: 'presentes'
        }}
      >
        {/* FILA 1: Embarazo, N° Control, Fecha */}
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              name="embarazo"
              label="Embarazo"
              rules={[{ required: true, message: 'Este campo es obligatorio' }]}
            >
              <Select
                placeholder="Seleccionar embarazo activo"
                showSearch
                optionFilterProp="children"
                onChange={calcularSemanasGestacion}
                filterOption={(input, option: any) =>
                  option.children.toLowerCase().includes(input.toLowerCase())
                }
              >
                {embarazos.map(e => (
                  <Select.Option key={e.id} value={e.id}>
                    {e.paciente_nombre || `Embarazo #${e.id} - Paciente #${e.paciente}`}
                  </Select.Option>
                ))}
              </Select>
            </Form.Item>
          </Col>
          <Col span={6}>
            <Form.Item
              name="numero_control"
              label="N° Control"
              rules={[{ required: true, message: 'Obligatorio' }]}
            >
              <InputNumber style={{ width: '100%' }} min={1} placeholder="1" />
            </Form.Item>
          </Col>
          <Col span={6}>
            <Form.Item
              name="fecha_control"
              label="Fecha Control"
              rules={[{ required: true, message: 'Obligatorio' }]}
            >
              <DatePicker 
                style={{ width: '100%' }} 
                format="DD/MM/YYYY"
                placeholder="Seleccionar fecha"
              />
            </Form.Item>
          </Col>
        </Row>

        {/* FILA 2: Semanas de Gestación */}
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              name="semanas_gestacion"
              label="Semanas Gestación"
              rules={[{ required: true, message: 'Obligatorio' }]}
            >
              <InputNumber 
                style={{ width: '100%' }} 
                min={0} 
                max={42}
                disabled
                placeholder="Se calcula automáticamente"
              />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              name="dias_gestacion"
              label="Días adicionales (0-6)"
            >
              <InputNumber 
                style={{ width: '100%' }} 
                min={0} 
                max={6}
                disabled
                placeholder="0-6"
              />
            </Form.Item>
          </Col>
        </Row>

        {/* FILA 3: Peso Actual, Peso Pre-gestacional, Talla */}
        <Row gutter={16}>
          <Col span={8}>
            <Form.Item
              name="peso_actual"
              label="Peso Actual (kg)"
              rules={[{ required: true, message: 'Este campo es obligatorio' }]}
            >
              <InputNumber 
                style={{ width: '100%' }} 
                min={30} 
                max={200} 
                step={0.1}
                onChange={() => {
                  calcularIMC();
                  calcularGananciaPeso();
                }}
                placeholder="Ej: 65.5"
              />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item
              name="peso_pregestacional"
              label="Peso Pre-gestacional (kg)"
            >
              <InputNumber 
                style={{ width: '100%' }} 
                min={30} 
                max={200} 
                step={0.1}
                onChange={calcularGananciaPeso}
                placeholder="Opcional"
              />
            </Form.Item>
            {gananciaCalculada && (
              <div style={{ color: '#52c41a', marginTop: -16, marginBottom: 16 }}>
                ✓ Ganancia: {gananciaCalculada}
              </div>
            )}
          </Col>
          <Col span={8}>
            <Form.Item
              name="talla"
              label="Talla (cm)"
              rules={[{ required: true, message: 'Este campo es obligatorio' }]}
            >
              <InputNumber 
                style={{ width: '100%' }} 
                min={130} 
                max={200}
                onChange={calcularIMC}
                placeholder="Ej: 165"
              />
            </Form.Item>
            {imcCalculado && (
              <div style={{ color: '#52c41a', marginTop: -16, marginBottom: 16 }}>
                ✓ IMC: {imcCalculado}
              </div>
            )}
          </Col>
        </Row>

        {/* FILA 4: Presión Arterial y FC Materna */}
        <Row gutter={16}>
          <Col span={6}>
            <Form.Item
              name="presion_arterial_sistolica"
              label="PA Sistólica (mmHg)"
              rules={[{ required: true, message: 'Obligatorio' }]}
            >
              <InputNumber 
                style={{ width: '100%' }} 
                min={70} 
                max={220}
                onChange={calcularPAM}
                placeholder="Ej: 120"
              />
            </Form.Item>
          </Col>
          <Col span={6}>
            <Form.Item
              name="presion_arterial_diastolica"
              label="PA Diastólica (mmHg)"
              rules={[{ required: true, message: 'Obligatorio' }]}
            >
              <InputNumber 
                style={{ width: '100%' }} 
                min={40} 
                max={130}
                onChange={calcularPAM}
                placeholder="Ej: 80"
              />
            </Form.Item>
            {pamCalculada && (
              <div style={{ color: '#52c41a', marginTop: -16, marginBottom: 16 }}>
                ✓ {pamCalculada}
              </div>
            )}
          </Col>
          <Col span={6}>
            <Form.Item
              name="frecuencia_cardiaca"
              label="FC Materna (lpm)"
            >
              <InputNumber 
                style={{ width: '100%' }} 
                min={40} 
                max={200}
                placeholder="Ej: 80"
              />
            </Form.Item>
          </Col>
          <Col span={6}>
            <Form.Item
              name="temperatura"
              label="Temperatura (°C)"
            >
              <InputNumber 
                style={{ width: '100%' }} 
                min={35} 
                max={42} 
                step={0.1}
                placeholder="Ej: 36.5"
              />
            </Form.Item>
          </Col>
        </Row>

        {/* FILA 5: Mediciones Obstétricas */}
        <Row gutter={16}>
          <Col span={8}>
            <Form.Item
              name="altura_uterina"
              label="Altura Uterina (cm)"
              rules={[{ required: true, message: 'Obligatorio' }]}
            >
              <InputNumber 
                style={{ width: '100%' }} 
                min={0} 
                max={50}
                placeholder="Ej: 28"
              />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item
              name="frecuencia_cardiaca_fetal"
              label="FCF (lpm)"
              rules={[{ required: true, message: 'Obligatorio' }]}
              tooltip="Rango normal: 110-160 lpm"
            >
              <InputNumber 
                style={{ width: '100%' }} 
                min={100} 
                max={180}
                placeholder="110-160"
              />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item
              name="presentacion_fetal"
              label="Presentación Fetal"
            >
              <Select placeholder="Seleccionar">
                <Select.Option value="cefalica">Cefálica</Select.Option>
                <Select.Option value="podalica">Podálica</Select.Option>
                <Select.Option value="transversa">Transversa</Select.Option>
              </Select>
            </Form.Item>
          </Col>
        </Row>

        {/* FILA 6: Evaluación Clínica */}
        <Row gutter={16}>
          <Col span={8}>
            <Form.Item
              name="movimientos_fetales"
              label="Movimientos Fetales"
            >
              <Select placeholder="Seleccionar">
                <Select.Option value="presentes">Presentes</Select.Option>
                <Select.Option value="ausentes">Ausentes</Select.Option>
                <Select.Option value="disminuidos">Disminuidos</Select.Option>
              </Select>
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item
              name="edema"
              label="Edema"
            >
              <Select placeholder="Seleccionar">
                <Select.Option value="no">No</Select.Option>
                <Select.Option value="leve">Leve</Select.Option>
                <Select.Option value="moderado">Moderado</Select.Option>
                <Select.Option value="severo">Severo</Select.Option>
              </Select>
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item
              name="proteinuria"
              label="Proteinuria"
            >
              <Select placeholder="Seleccionar">
                <Select.Option value="negativa">Negativa</Select.Option>
                <Select.Option value="trazas">Trazas</Select.Option>
                <Select.Option value="positiva_1">+</Select.Option>
                <Select.Option value="positiva_2">++</Select.Option>
                <Select.Option value="positiva_3">+++</Select.Option>
              </Select>
            </Form.Item>
          </Col>
        </Row>

        {/* FILA 7: Observaciones */}
        <Row gutter={16}>
          <Col span={24}>
            <Form.Item
              name="observaciones"
              label="Observaciones / Hallazgos"
            >
              <Input.TextArea 
                rows={4} 
                placeholder="Observaciones del control prenatal, hallazgos relevantes, indicaciones..."
              />
            </Form.Item>
          </Col>
        </Row>

        {/* BOTONES */}
        <Form.Item>
          <Button type="primary" htmlType="submit" loading={loading} icon={<SaveOutlined />}>
            Guardar Control
          </Button>
          <Button style={{ marginLeft: 8 }} onClick={onCancel} icon={<CloseOutlined />}>
            Cancelar
          </Button>
        </Form.Item>
      </Form>
    </Card>
  );
};

export default FormularioControl;