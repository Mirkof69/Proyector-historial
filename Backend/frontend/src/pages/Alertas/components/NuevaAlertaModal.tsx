import React from 'react';
import { Input, Select, Modal, Form } from 'antd';
import type { FormInstance } from 'antd';
import { AlertasState } from '../alertasMedicasUtils';

interface NuevaAlertaModalProps {
  modalNuevaAlerta: boolean;
  setState: React.Dispatch<React.SetStateAction<AlertasState>>;
  form: FormInstance;
  handleCrearAlerta: (values: any) => void;
}

const NuevaAlertaModal: React.FC<NuevaAlertaModalProps> = ({
  modalNuevaAlerta, setState, form, handleCrearAlerta,
}) => (
  <Modal
    title="Crear Nueva Alerta Médica"
    open={modalNuevaAlerta}
    onCancel={() => {
      setState(prev => ({ ...prev, modalNuevaAlerta: false }));
      form.resetFields();
    }}
    onOk={() => {
      form.validateFields().then(handleCrearAlerta);
    }}
    width={600}
  >
    <Form form={form} layout="vertical">
      <Form.Item name="titulo" label="Título" rules={[{ required: true }]}>
        <Input placeholder="Ej: Presión arterial alta" />
      </Form.Item>
      <Form.Item name="paciente_id" label="ID Paciente">
        <Input type="number" placeholder="ID numérico (opcional)" />
      </Form.Item>
      <Form.Item name="tipo" label="Tipo de Alerta" rules={[{ required: true }]}>
        <Select>
          <Select.Option value="valor_critico">Valor crítico detectado</Select.Option>
          <Select.Option value="seguimiento_vencido">Seguimiento vencido</Select.Option>
          <Select.Option value="medicamento_contraindicado">Medicamento contraindicado</Select.Option>
          <Select.Option value="riesgo_alto">Riesgo alto detectado</Select.Option>
          <Select.Option value="resultado_anormal">Resultado anormal</Select.Option>
          <Select.Option value="cita_perdida">Cita perdida</Select.Option>
          <Select.Option value="protocolo_incumplido">Protocolo no seguido</Select.Option>
          <Select.Option value="auditoria">Requiere auditoría</Select.Option>
        </Select>
      </Form.Item>
      <Form.Item name="prioridad" label="Prioridad" rules={[{ required: true }]}>
        <Select>
          <Select.Option value="baja">Baja</Select.Option>
          <Select.Option value="media">Media</Select.Option>
          <Select.Option value="alta">Alta</Select.Option>
          <Select.Option value="critica">Crítica</Select.Option>
          <Select.Option value="emergencia">Emergencia</Select.Option>
        </Select>
      </Form.Item>
      <Form.Item name="descripcion" label="Descripción" rules={[{ required: true }]}>
        <Input.TextArea rows={3} placeholder="Descripción detallada de la alerta" />
      </Form.Item>
      <Form.Item name="accion_recomendada" label="Acción Recomendada" rules={[{ required: true }]}>
        <Input.TextArea rows={2} placeholder="Qué debe hacer el equipo médico" />
      </Form.Item>
      <Form.Item name="modulo_origen" label="Módulo Origen" rules={[{ required: true }]}>
        <Select>
          <Select.Option value="pacientes">Módulo de Pacientes</Select.Option>
          <Select.Option value="embarazos">Módulo de Embarazos</Select.Option>
          <Select.Option value="controles">Controles Prenatales</Select.Option>
          <Select.Option value="ecografias">Ecografías</Select.Option>
          <Select.Option value="laboratorio">Laboratorio</Select.Option>
          <Select.Option value="calculadoras">Calculadoras Médicas</Select.Option>
          <Select.Option value="partos">Partos</Select.Option>
          <Select.Option value="sistema">Sistema</Select.Option>
        </Select>
      </Form.Item>
      <Form.Item name="valor_actual" label="Valor Actual">
        <Input placeholder="Ej: 150/95 mmHg" />
      </Form.Item>
      <Form.Item name="valor_umbral" label="Valor Umbral">
        <Input placeholder="Ej: Normal: <140/90 mmHg" />
      </Form.Item>
    </Form>
  </Modal>
);

export default NuevaAlertaModal;
