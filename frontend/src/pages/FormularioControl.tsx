import React, { useState, useEffect } from 'react';
import { Form, Input, InputNumber, DatePicker, Button, Card, message, Row, Col, Select, Divider, Alert } from 'antd';
import { SaveOutlined, CloseOutlined, WarningOutlined } from '@ant-design/icons';
import axios from 'axios';
import { authService } from '../services/authService';
import dayjs from 'dayjs';
import 'dayjs/locale/es';

dayjs.locale('es');

interface FormularioControlProps {
  onCancel: () => void;
  onSuccess: () => void;
  controlId?: number | null;
}

interface Embarazo {
  id: number;
  paciente: number;
  paciente_nombre: string;
  numero_gesta: number;
  fecha_ultima_menstruacion: string;
  fecha_probable_parto: string;
  estado: string;
}

const FormularioControl: React.FC<FormularioControlProps> = ({ onCancel, onSuccess, controlId }) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [embarazos, setEmbarazos] = useState<Embarazo[]>([]);
  const [imcCalculado, setImcCalculado] = useState<string>('');
  const [pamCalculada, setPamCalculada] = useState<string>('');
  const [gananciaCalculada, setGananciaCalculada] = useState<string>('');
  const [alertasPreliminares, setAlertasPreliminares] = useState<string[]>([]);
  const [modoEdicion, setModoEdicion] = useState(false);

  useEffect(() => {
    fetchEmbarazos();
    if (controlId) {
      setModoEdicion(true);
      cargarControl(controlId);
    }
  }, [controlId]);

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

  const cargarControl = async (id: number) => {
    try {
      const token = authService.getToken();
      const response = await axios.get(`http://127.0.0.1:8000/api/controles/${id}/`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      const control = response.data;
      form.setFieldsValue({
        embarazo_id: control.embarazo_id,
        numero_control: control.numero_control,
        fecha_control: dayjs(control.fecha_control),
        semanas_gestacion: control.semanas_gestacion,
        dias_gestacion: control.dias_gestacion || 0,
        peso_actual: control.peso_actual,
        peso_pregestacional: control.peso_pregestacional,
        talla: control.talla,
        presion_arterial_sistolica: control.presion_arterial_sistolica,
        presion_arterial_diastolica: control.presion_arterial_diastolica,
        frecuencia_cardiaca: control.frecuencia_cardiaca,
        temperatura: control.temperatura,
        altura_uterina: control.altura_uterina,
        frecuencia_cardiaca_fetal: control.frecuencia_cardiaca_fetal,
        presentacion_fetal: control.presentacion_fetal,
        movimientos_fetales: control.movimientos_fetales,
        edema: control.edema,
        proteinuria: control.proteinuria,
        observaciones: control.observaciones || ''
      });

      recalcularTodo();
    } catch (error) {
      message.error('Error al cargar datos del control');
      console.error(error);
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
      
      if (imc < 18.5) {
        clasificacion = 'Bajo peso';
      } else if (imc < 25) {
        clasificacion = 'Normal';
      } else if (imc < 30) {
        clasificacion = 'Sobrepeso';
      } else {
        clasificacion = 'Obesidad';
      }
      
      setImcCalculado(`${imc.toFixed(2)} - ${clasificacion}`);
      return { valor: imc, clasificacion };
    }
    return null;
  };

  const calcularGananciaPeso = () => {
    const pesoActual = form.getFieldValue('peso_actual');
    const pesoPregestacional = form.getFieldValue('peso_pregestacional');
    
    if (pesoActual && pesoPregestacional) {
      const ganancia = pesoActual - pesoPregestacional;
      const signo = ganancia > 0 ? '+' : '';
      setGananciaCalculada(`${signo}${ganancia.toFixed(1)} kg`);
      return ganancia;
    }
    return null;
  };

  const calcularPAM = () => {
    const sistolica = form.getFieldValue('presion_arterial_sistolica');
    const diastolica = form.getFieldValue('presion_arterial_diastolica');
    
    if (sistolica && diastolica) {
      const pam = (sistolica + (2 * diastolica)) / 3;
      setPamCalculada(`PAM: ${pam.toFixed(2)} mmHg`);
      return pam;
    }
    return null;
  };

  const evaluarAlertas = () => {
    const alertas: string[] = [];
    
    const sistolica = form.getFieldValue('presion_arterial_sistolica');
    const diastolica = form.getFieldValue('presion_arterial_diastolica');
    if (sistolica >= 140 || diastolica >= 90) {
      alertas.push('⚠️ Hipertensión detectada');
    } else if (sistolica >= 120 || diastolica >= 80) {
      alertas.push('⚠️ Pre-hipertensión');
    }
    
    const fcf = form.getFieldValue('frecuencia_cardiaca_fetal');
    if (fcf && (fcf < 110 || fcf > 160)) {
      alertas.push('⚠️ FCF fuera de rango normal');
    }
    
    const edema = form.getFieldValue('edema');
    if (edema === 'severo' || edema === 'generalizado') {
      alertas.push('⚠️ Edema severo');
    }
    
    const proteinuria = form.getFieldValue('proteinuria');
    if (proteinuria && proteinuria !== 'negativa' && proteinuria !== 'trazas') {
      alertas.push('⚠️ Proteinuria positiva');
    }
    
    const movimientos = form.getFieldValue('movimientos_fetales');
    if (movimientos === 'ausentes') {
      alertas.push('🔴 Movimientos fetales ausentes');
    }
    
    const imc = calcularIMC();
    if (imc) {
      if (imc.valor < 18.5) {
        alertas.push('⚠️ Bajo peso materno');
      } else if (imc.valor >= 30) {
        alertas.push('⚠️ Obesidad materna');
      }
    }
    
    setAlertasPreliminares(alertas);
  };

  const recalcularTodo = () => {
    calcularIMC();
    calcularGananciaPeso();
    calcularPAM();
    evaluarAlertas();
  };

  const translateError = (msg: string): string => {
    const translations: any = {
      'This field is required.': 'Este campo es obligatorio',
      'This field may not be blank.': 'Este campo no puede estar en blanco',
      'Enter a valid date.': 'Ingrese una fecha válida',
      'Enter a valid number.': 'Ingrese un número válido',
      'PA sistólica debe ser mayor que diastólica': 'La presión sistólica debe ser mayor que la diastólica'
    };
    return translations[msg] || msg;
  };

  const onFinish = async (values: any) => {
    setLoading(true);
    
    try {
      const token = authService.getToken();
      const user = authService.getCurrentUser();
      
      const payload: any = {
        numero_control: values.numero_control,
        fecha_control: dayjs(values.fecha_control).format('YYYY-MM-DD'),
        semanas_gestacion: values.semanas_gestacion,
        dias_gestacion: values.dias_gestacion || 0,
        peso_actual: values.peso_actual,
        peso_pregestacional: values.peso_pregestacional || null,
        talla: values.talla,
        presion_arterial_sistolica: values.presion_arterial_sistolica,
        presion_arterial_diastolica: values.presion_arterial_diastolica,
        frecuencia_cardiaca: values.frecuencia_cardiaca || null,
        temperatura: values.temperatura || null,
        altura_uterina: values.altura_uterina,
        frecuencia_cardiaca_fetal: values.frecuencia_cardiaca_fetal,
        presentacion_fetal: values.presentacion_fetal || null,
        movimientos_fetales: values.movimientos_fetales || 'presentes',
        edema: values.edema || 'no',
        proteinuria: values.proteinuria || 'negativa',
        observaciones: values.observaciones || ''
      };

      // ✅ SOLO AGREGAR embarazo_id Y paciente SI ES CREACIÓN
      if (!modoEdicion) {
        const embarazoSeleccionado = embarazos.find(e => e.id === values.embarazo_id);
        payload.embarazo_id = values.embarazo_id;
        payload.paciente = embarazoSeleccionado?.paciente;
      }

      if (modoEdicion && controlId) {
        // ✅ ACTUALIZAR - NO ENVIAR embarazo_id ni paciente
        const response = await axios.put(`http://127.0.0.1:8000/api/controles/${controlId}/`, payload, {
          headers: { Authorization: `Bearer ${token}` }
        });
        
        // Mostrar alertas si las hay
        if (response.data.alertas && response.data.alertas.length > 0) {
          const alertasCriticas = response.data.alertas.filter((a: any) => a.tipo === 'critico');
          if (alertasCriticas.length > 0) {
            message.warning({
              content: `Control actualizado con ${alertasCriticas.length} alerta(s) crítica(s)`,
              duration: 5
            });
          }
        }
        
        message.success('Control actualizado exitosamente');
      } else {
        // CREAR
        const response = await axios.post('http://127.0.0.1:8000/api/controles/', payload, {
          headers: { Authorization: `Bearer ${token}` }
        });
        
        // Mostrar alertas si las hay
        if (response.data.alertas && response.data.alertas.length > 0) {
          const alertasCriticas = response.data.alertas.filter((a: any) => a.tipo === 'critico');
          if (alertasCriticas.length > 0) {
            message.warning({
              content: `Control registrado con ${alertasCriticas.length} alerta(s) crítica(s)`,
              duration: 5
            });
          }
        }
        
        message.success('Control prenatal registrado exitosamente');
      }
      
      form.resetFields();
      setImcCalculado('');
      setPamCalculada('');
      setGananciaCalculada('');
      setAlertasPreliminares([]);
      onSuccess();
    } catch (error: any) {
      console.error('Error al guardar control:', error.response?.data);
      
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
        message.error(`Error al ${modoEdicion ? 'actualizar' : 'registrar'} control`);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card title={modoEdicion ? "Editar Control Prenatal" : "Nuevo Control Prenatal"}>
      {alertasPreliminares.length > 0 && (
        <Alert
          message="Alertas Preliminares"
          description={
            <ul style={{ marginBottom: 0, paddingLeft: 20 }}>
              {alertasPreliminares.map((alerta, index) => (
                <li key={index}>{alerta}</li>
              ))}
            </ul>
          }
          type="warning"
          showIcon
          icon={<WarningOutlined />}
          style={{ marginBottom: 16 }}
        />
      )}

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
        onValuesChange={recalcularTodo}
      >
        <Divider orientation="left">📋 Datos del Control</Divider>
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              name="embarazo_id"
              label="Embarazo"
              rules={[{ required: true, message: 'Seleccione un embarazo' }]}
            >
              <Select
                placeholder="Seleccionar embarazo activo"
                showSearch
                optionFilterProp="children"
                onChange={calcularSemanasGestacion}
                disabled={modoEdicion}
                filterOption={(input, option: any) =>
                  option.children.toLowerCase().includes(input.toLowerCase())
                }
              >
                {embarazos.map(e => (
                  <Select.Option key={e.id} value={e.id}>
                    {e.paciente_nombre || `Embarazo #${e.id} - Paciente #${e.paciente}`} (Gesta {e.numero_gesta})
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

        <Divider orientation="left">🤰 Edad Gestacional</Divider>
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
                placeholder="0-6"
              />
            </Form.Item>
          </Col>
        </Row>

        <Divider orientation="left">⚖️ Mediciones Antropométricas</Divider>
        <Row gutter={16}>
          <Col span={8}>
            <Form.Item
              name="peso_actual"
              label="Peso Actual (kg)"
              rules={[{ required: true, message: 'Obligatorio' }]}
            >
              <InputNumber 
                style={{ width: '100%' }} 
                min={30} 
                max={200} 
                step={0.1}
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
              rules={[{ required: true, message: 'Obligatorio' }]}
            >
              <InputNumber 
                style={{ width: '100%' }} 
                min={130} 
                max={200}
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

        <Divider orientation="left">💓 Signos Vitales Maternos</Divider>
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

        <Divider orientation="left">👶 Mediciones Obstétricas</Divider>
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
                min={90} 
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
                <Select.Option value="oblicua">Oblicua</Select.Option>
              </Select>
            </Form.Item>
          </Col>
        </Row>

        <Divider orientation="left">🩺 Evaluación Clínica</Divider>
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
                <Select.Option value="aumentados">Aumentados</Select.Option>
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
                <Select.Option value="generalizado">Generalizado</Select.Option>
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
                <Select.Option value="positiva_4">++++</Select.Option>
              </Select>
            </Form.Item>
          </Col>
        </Row>

        <Divider orientation="left">📝 Observaciones</Divider>
        <Row gutter={16}>
          <Col span={24}>
            <Form.Item
              name="observaciones"
              label="Observaciones / Hallazgos"
            >
              <Input.TextArea 
                rows={4} 
                placeholder="Observaciones del control prenatal, hallazgos relevantes, indicaciones..."
                maxLength={1000}
                showCount
              />
            </Form.Item>
          </Col>
        </Row>

        <Form.Item>
          <Button 
            type="primary" 
            htmlType="submit" 
            loading={loading} 
            icon={<SaveOutlined />}
            size="large"
          >
            {modoEdicion ? 'Actualizar Control' : 'Guardar Control'}
          </Button>
          <Button 
            style={{ marginLeft: 8 }} 
            onClick={onCancel} 
            icon={<CloseOutlined />}
            size="large"
          >
            Cancelar
          </Button>
        </Form.Item>
      </Form>
    </Card>
  );
};

export default FormularioControl;