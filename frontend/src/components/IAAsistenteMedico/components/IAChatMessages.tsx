import React from 'react';
import { Space, Tag, List, Typography, Spin } from 'antd';
import { RobotOutlined, UserOutlined, BugOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { Mensaje } from '../iaAsistenteUtils';

const { Text, Paragraph } = Typography;

interface IAChatMessagesProps {
  mensajes: Mensaje[];
  cargando: boolean;
  messagesEndRef: React.RefObject<HTMLDivElement>;
}

const NOMBRE_TEMA: Record<string, string> = {
  preeclampsia: 'Preeclampsia', rciu: 'RCIU', diabetes: 'Diabetes gestacional', laboratorio: 'Laboratorio',
  edad_gestacional: 'Edad gestacional', emergencia: 'Emergencia', general: 'General',
};

const IAChatMessages: React.FC<IAChatMessagesProps> = ({ mensajes, cargando, messagesEndRef }) => (
  <div className="chat-messages-container" aria-live="polite">
    <List
      dataSource={mensajes}
      renderItem={(mensaje) => (
        <div className={`mensaje-fila ${mensaje.tipo}`}>
          <div className={`mensaje-bubble ${mensaje.tipo}`}>
            <Space direction="vertical" size={4} className="mensaje-cuerpo">
              <Space wrap>
                {mensaje.tipo === 'ia' ? (
                  <RobotOutlined className="mensaje-icono" />
                ) : mensaje.tipo === 'sistema' ? (
                  <BugOutlined className="mensaje-icono alarma" />
                ) : (
                  <UserOutlined />
                )}
                <Text strong className="mensaje-sender">
                  {mensaje.tipo === 'ia' ? 'Asistente' : mensaje.tipo === 'sistema' ? 'Sistema' : 'Usted'}
                </Text>
                {mensaje.fuente === 'base_conocimiento' && (
                  <Tag>Base de conocimiento{mensaje.tema ? ` · ${NOMBRE_TEMA[mensaje.tema] ?? mensaje.tema}` : ''}</Tag>
                )}
                {mensaje.fuente === 'sin_conexion' && <Tag color="warning">Sin conexión</Tag>}
              </Space>
              <Paragraph className="mensaje-text">
                {mensaje.contenido}
              </Paragraph>
              <Text type="secondary" className="mensaje-time">
                {dayjs(mensaje.timestamp).format('HH:mm')}
              </Text>
            </Space>
          </div>
        </div>
      )}
    />
    {cargando && (
      <div className="mensaje-cargando">
        <Space>
          <Spin />
          <Text type="secondary">Buscando en la base de conocimiento…</Text>
        </Space>
      </div>
    )}
    <div ref={messagesEndRef} />
  </div>
);

export default IAChatMessages;
