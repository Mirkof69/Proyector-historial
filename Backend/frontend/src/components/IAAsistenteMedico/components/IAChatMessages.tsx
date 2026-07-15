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

const IAChatMessages: React.FC<IAChatMessagesProps> = ({ mensajes, cargando, messagesEndRef }) => (
  <div
    className="chat-messages-container"
  >
    <List
      dataSource={mensajes}
      renderItem={(mensaje) => (
        <div
          style={{
            display: 'flex',
            justifyContent: mensaje.tipo === 'usuario' ? 'flex-end' : 'flex-start',
            marginBottom: 12
          }}
        >
          <div className={`mensaje-bubble ${mensaje.tipo}`}>
            <Space direction="vertical" size={4} style={{ width: '100%' }}>
              <Space>
                {mensaje.tipo === 'ia' ? (
                  <RobotOutlined style={{ color: '#722ed1' }} />
                ) : mensaje.tipo === 'sistema' ? (
                  <BugOutlined style={{ color: '#ff4d4f' }} />
                ) : (
                  <UserOutlined />
                )}
                <Text strong className="mensaje-sender">
                  {mensaje.tipo === 'ia' ? 'IA Médica' : mensaje.tipo === 'sistema' ? 'Sistema' : 'Tú'}
                </Text>
                {mensaje.confianza && (
                  <Tag color="green" style={{ fontSize: '12px' }}>
                    {mensaje.confianza}% confianza
                  </Tag>
                )}
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
      <div style={{ textAlign: 'center', padding: 16 }}>
        <Space>
          <Spin />
          <Text type="secondary">IA analizando…</Text>
        </Space>
      </div>
    )}
    <div ref={messagesEndRef} />
  </div>
);

export default IAChatMessages;
