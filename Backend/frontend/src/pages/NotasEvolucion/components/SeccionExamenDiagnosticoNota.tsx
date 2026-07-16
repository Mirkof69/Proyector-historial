import React from 'react';
import { Form, Input, Row, Col, Divider } from 'antd';

const { TextArea } = Input;

const SeccionExamenDiagnosticoNota: React.FC = () => (
  <>
    {/* EXAMEN FÍSICO */}
    <Divider orientation="left">Examen Físico</Divider>

    <Row gutter={16}>
      <Col xs={24}>
        <Form.Item
          label="Examen Físico General"
          name="examen_fisico"
          rules={[{ required: true, message: 'Ingrese los hallazgos del examen físico' }]}
        >
          <TextArea
            rows={4}
            placeholder="Describa los hallazgos del examen físico general (estado general, piel, cabeza, cuello, tórax, abdomen, extremidades...)"
            maxLength={2000}
            showCount
          />
        </Form.Item>
      </Col>
    </Row>

    <Row gutter={16}>
      <Col xs={24}>
        <Form.Item
          label="Examen Obstétrico (si aplica)"
          name="examen_obstetrico"
        >
          <TextArea
            rows={4}
            placeholder="Describa los hallazgos del examen obstétrico (maniobras de Leopold, altura uterina, FCF, actividad uterina, estado de membranas, dilatación...)"
            maxLength={2000}
            showCount
          />
        </Form.Item>
      </Col>
    </Row>

    {/* DIAGNÓSTICOS Y PLAN */}
    <Divider orientation="left">Impresión Diagnóstica y Plan</Divider>

    <Row gutter={16}>
      <Col xs={24}>
        <Form.Item
          label="Diagnósticos / Impresión Diagnóstica"
          name="diagnosticos"
          rules={[{ required: true, message: 'Ingrese los diagnósticos' }]}
        >
          <TextArea
            rows={4}
            placeholder="Liste los diagnósticos en orden de importancia (ej: 1. Embarazo de 28 semanas, 2. Diabetes gestacional controlada...)"
            maxLength={1000}
            showCount
          />
        </Form.Item>
      </Col>
    </Row>

    <Row gutter={16}>
      <Col xs={24}>
        <Form.Item
          label="Plan de Tratamiento"
          name="plan_tratamiento"
          rules={[{ required: true, message: 'Ingrese el plan de tratamiento' }]}
        >
          <TextArea
            rows={4}
            placeholder="Describa el plan de tratamiento (medicamentos, procedimientos, controles, interconsultas...)"
            maxLength={1000}
            showCount
          />
        </Form.Item>
      </Col>
    </Row>

    <Row gutter={16}>
      <Col xs={24}>
        <Form.Item
          label="Indicaciones al Paciente"
          name="indicaciones"
        >
          <TextArea
            rows={3}
            placeholder="Indicaciones específicas para la paciente (dieta, reposo, signos de alarma, próxima cita...)"
            maxLength={1000}
            showCount
          />
        </Form.Item>
      </Col>
    </Row>

    <Row gutter={16}>
      <Col xs={24}>
        <Form.Item label="Observaciones Adicionales" name="observaciones">
          <TextArea
            rows={3}
            placeholder="Observaciones adicionales o notas relevantes (opcional)"
            maxLength={500}
            showCount
          />
        </Form.Item>
      </Col>
    </Row>
  </>
);

export default SeccionExamenDiagnosticoNota;
