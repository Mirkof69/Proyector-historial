import React from 'react';
import { Button, Form } from 'antd';

interface BotonSiguienteProps {
  /** Campos del paso que deben estar completos antes de avanzar. */
  campos: string[];
  alAvanzar: () => void;
}

/**
 * «Siguiente» que valida el paso actual. Antes avanzaba sin paciente ni médico
 * y el error recién aparecía al guardar, en otro paso.
 */
const BotonSiguiente: React.FC<BotonSiguienteProps> = ({ campos, alAvanzar }) => {
  const form = Form.useFormInstance();
  const avanzar = async () => {
    try {
      await form.validateFields(campos);
      alAvanzar();
    } catch {
      // Los mensajes quedan debajo de cada campo.
    }
  };
  return <Button type="primary" onClick={avanzar}>Siguiente</Button>;
};

export default BotonSiguiente;
