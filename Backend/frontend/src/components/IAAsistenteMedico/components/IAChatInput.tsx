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
  <Space.Compact style={{ width: '100%' }}>
    <TextArea
      value={inputTexto}
      onChange={(e) => setInputTexto(e.target.value)}
      placeholder="Pregunta al Asistente IA... (ej: ¿Cómo detectar preeclampsia?)"
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
      onClick={enviarMensaje}
      loading={cargando}
    >
      Enviar
    </Button>
  </Space.Compact>
);

export default IAChatInput;
