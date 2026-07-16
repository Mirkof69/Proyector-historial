import React from 'react';
import { Form, Divider, Checkbox } from 'antd';

const SeccionConsentimientoPaciente: React.FC = () => (
  <>
    <Divider orientation="left">Consentimiento de Tratamiento de Datos</Divider>
    <Form.Item
      name="consentimiento_datos_aceptado"
      valuePropName="checked"
      rules={[
        {
          validator: (_, value) =>
            value
              ? Promise.resolve()
              : Promise.reject(new Error('Se requiere el consentimiento del paciente para registrar sus datos (Ley 164)')),
        },
      ]}
    >
      <Checkbox>
        El paciente (o su representante) ha sido informado y otorga su consentimiento
        expreso para la recolección y tratamiento de sus datos personales con fines
        de atención médica, conforme a la Ley 164 de Bolivia.
      </Checkbox>
    </Form.Item>
  </>
);

export default SeccionConsentimientoPaciente;
