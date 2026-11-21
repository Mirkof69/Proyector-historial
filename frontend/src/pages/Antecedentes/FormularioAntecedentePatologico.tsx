import React, { useEffect, useState } from 'react';
import { App, Card, Form, Input, Button, Select, Switch, Typography, Space, Spin } from 'antd';
import { SaveOutlined, CloseOutlined } from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import { antecedentesService, AntecedentePatologico } from '../../services/antecedentesService';
import { PacienteSelect } from '../../components/clinico/SelectoresClinicos';

const { Title } = Typography;
const { Option } = Select;
const { TextArea } = Input;

const LISTA = '/dashboard/antecedentes/patologicos';

// Antes la pantalla ofrecía «Paciente 1 / Paciente 2» fijos y «Guardar» solo
// escribía en la consola: ningún antecedente patológico se guardaba.
const FormularioAntecedentePatologico: React.FC = () => {
  const [form] = Form.useForm();
  const { message } = App.useApp();
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [cargando, setCargando] = useState(false);
  const [guardando, setGuardando] = useState(false);

  useEffect(() => {
    if (!id) return;
    setCargando(true);
    antecedentesService.getPatologicoById(Number(id))
      .then((a) => form.setFieldsValue(a))
      .catch(() => message.error('No se pudo cargar el antecedente'))
      .finally(() => setCargando(false));
  }, [id, form, message]);

  const guardar = async (valores: Partial<AntecedentePatologico>) => {
    setGuardando(true);
    try {
      if (id) {
        await antecedentesService.updatePatologico(Number(id), valores);
        message.success('Antecedente actualizado');
      } else {
        await antecedentesService.createPatologico(valores);
        message.success('Antecedente registrado');
      }
      navigate(LISTA);
    } catch {
      // El detalle del rechazo lo muestra el interceptor de la API.
    } finally {
      setGuardando(false);
    }
  };

  return (
    <Card title={<span className="antecedentes-titulo">{id ? 'Editar' : 'Nuevo'} antecedente patológico</span>}>
      <Spin spinning={cargando}>
        <Form form={form} layout="vertical" onFinish={guardar} className="antecedentes-formulario"
          initialValues={{ tipo: 'personal' }}>
          <Title level={5}>Información General</Title>
          <Form.Item name="paciente" label="Paciente" rules={[{ required: true, message: 'Seleccione la paciente' }]}>
            <PacienteSelect placeholder="Buscar paciente por nombre o CI" disabled={!!id} />
          </Form.Item>
          <Form.Item name="tipo" label="Tipo" rules={[{ required: true }]}>
            <Select placeholder="Seleccione tipo">
              <Option value="personal">Personales</Option>
              <Option value="heredofamiliar">Heredofamiliares</Option>
            </Select>
          </Form.Item>

          <Title level={5}>Alergias</Title>
          <Form.Item name="tiene_alergias" label="Tiene Alergias" valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item name="alergias_medicamentos" label="Alergias a Medicamentos">
            <Input placeholder="Ej: Penicilina, sulfa" />
          </Form.Item>
          <Form.Item name="alergias_alimentos" label="Alergias a Alimentos">
            <Input placeholder="Ej: Mariscos, maní" />
          </Form.Item>

          <Title level={5}>Enfermedades Crónicas</Title>
          <Form.Item name="diabetes" label="Diabetes" valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item name="hipertension" label="Hipertensión" valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item name="asma" label="Asma" valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item name="cardiopatias" label="Cardiopatías" valuePropName="checked">
            <Switch />
          </Form.Item>

          <Title level={5}>Antecedentes Obstétricos Específicos</Title>
          <Form.Item name="preeclampsia_previa" label="Preeclampsia Previa" valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item name="diabetes_gestacional_previa" label="Diabetes Gestacional Previa" valuePropName="checked">
            <Switch />
          </Form.Item>

          <Form.Item name="otras_enfermedades" label="Otras Enfermedades">
            <TextArea rows={3} placeholder="Describa otras enfermedades o condiciones relevantes" />
          </Form.Item>
          {/* El campo del modelo se llama `cirugiasanteriores` (sin guion bajo). */}
          <Form.Item name="cirugiasanteriores" label="Cirugías Anteriores">
            <TextArea rows={3} placeholder="Describa cirugías previas" />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" icon={<SaveOutlined />} loading={guardando}>Guardar</Button>
              <Button icon={<CloseOutlined />} onClick={() => navigate(LISTA)}>Cancelar</Button>
            </Space>
          </Form.Item>
        </Form>
      </Spin>
    </Card>
  );
};

export default FormularioAntecedentePatologico;
