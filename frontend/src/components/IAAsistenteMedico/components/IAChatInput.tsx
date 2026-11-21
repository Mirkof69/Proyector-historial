import React from 'react';
import { Input, Button, Space } from 'antd';
import { SendOutlined } from '@ant-design/icons';

const { TextArea } = Input;

interface IAChatInputProps {
  inputTexto: string;
  setInputTexto: (value: string) => void;
  enviarMensaje: () => void;
  cargando: boolean;
}

const IAChatInput: React.FC<IAChatInputProps> = ({ inputTexto, setInputTexto, enviarMensaje, cargando }) => (
  <Space.Compact className="ia-asistente-entrada">
    <TextArea
      value={inputTexto}
      onChange={(e) => setInputTexto(e.target.value)}
      placeholder="Escriba su consulta (p. ej.: ¿cómo detectar preeclampsia?)"
      aria-label="Consulta al asistente"
      autoSize={{ minRows: 1, maxRows: 3 }}
      onPressEnter={(e) => {
        if (!e.shiftKey) {
          e.preventDefault();
          enviarMensaje();
        }
      }}
    />
    <Button
      type="primary"
      icon={<SendOutlined />}
      onClick={() => enviarMensaje()}
      loading={cargando}
    >
      Enviar
    </Button>
  </Space.Compact>
);

export default IAChatInput;
