import React from 'react';
import { Card, Descriptions, Divider, Alert } from 'antd';
import { IdcardOutlined, MailOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { Usuario } from './perfilTypes';

const PerfilResumenAcceso: React.FC<{ user: Usuario }> = ({ user }) => (
  <Card
    title="Información de Acceso"
    variant="borderless"
    className="shadow-sm"
    style={{ marginBottom: 24 }}
  >
    <Descriptions column={1} size="small" bordered>
      <Descriptions.Item label={<><IdcardOutlined /> ID Usuario</>}>
        {user.id}
      </Descriptions.Item>
      <Descriptions.Item label={<><MailOutlined /> Email</>}>
        {user.email}
      </Descriptions.Item>
      <Descriptions.Item label="Teléfono">
        {user.telefono || 'No registrado'}
      </Descriptions.Item>
      <Descriptions.Item label="Último Acceso">
        {user.last_login ? dayjs(user.last_login).format('DD/MM/YYYY HH:mm') : 'Nunca'}
      </Descriptions.Item>
      <Descriptions.Item label="Fecha Registro">
        {user.fecha_creacion ? dayjs(user.fecha_creacion).format('DD/MM/YYYY') : 'N/A'}
      </Descriptions.Item>
    </Descriptions>

    <Divider />
    <Alert
      message="Seguridad"
      description="Recuerde cambiar su contraseña cada 3 meses para mantener su cuenta segura."
      type="info"
      showIcon
    />
  </Card>
);

export default PerfilResumenAcceso;
