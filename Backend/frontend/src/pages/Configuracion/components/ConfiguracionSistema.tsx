import React from 'react';
import { Card, Form, Input, Button, Switch, Divider, Row, Col, Typography, Select, List, Popconfirm } from 'antd';
import { useAntdApp } from '../../../hooks/useMessage';
import { MailOutlined, SaveOutlined, DatabaseOutlined, SafetyCertificateOutlined, DeleteOutlined } from '@ant-design/icons';

const { Title, Paragraph, Text } = Typography;
const { TextArea } = Input;
const { Option } = Select;

interface Backup {
  id: string;
  fecha: string;
  size: string;
}

interface ConfiguracionSistemaProps {
  formSmtp: any;
  diasRetencion: number;
  setDiasRetencion: (value: number) => void;
  notasAdmin: string;
  setNotasAdmin: (value: string) => void;
  backups: Backup[];
  onCreateBackup: () => void;
  onDescargarBackup: (filename: string) => void;
  onEliminarBackup: (filename: string) => void;
}

const SAVE_ICON = <SaveOutlined />;
const DATABASE_ICON = <DatabaseOutlined />;
const DELETE_ICON = <DeleteOutlined />;

const ConfiguracionSistema: React.FC<ConfiguracionSistemaProps> = ({
  formSmtp,
  diasRetencion,
  setDiasRetencion,
  notasAdmin,
  setNotasAdmin,
  backups,
  onCreateBackup,
  onDescargarBackup,
  onEliminarBackup
}) => {
  const { message } = useAntdApp();

  return (
    <Row gutter={24}>
      <Col xs={24} md={12}>
        <Card title="Mantenimiento y Seguridad" className="shadow-sm" style={{ height: '100%' }}>
          <Form form={formSmtp} layout="vertical" onFinish={() => { message.success('Config SMTP guardada'); }}>
            <Form.Item name="modo_mantenimiento" label="Modo Mantenimiento" valuePropName="checked">
              <Switch checkedChildren="ACTIVADO" unCheckedChildren="DESACTIVADO" />
            </Form.Item>
            <Paragraph type="secondary" style={{ fontSize: 12 }}>
              Si se activa, solo los administradores podrán iniciar sesión. Útil para actualizaciones.
            </Paragraph>
            <Divider />
            <Title level={5}><MailOutlined /> Configuración de Correo (SMTP)</Title>
            <Row gutter={12}>
              <Col span={16}><Form.Item name="smtp_host" label="Servidor SMTP"><Input /></Form.Item></Col>
              <Col span={8}><Form.Item name="smtp_port" label="Puerto"><Input /></Form.Item></Col>
            </Row>
            <Form.Item name="smtp_user" label="Usuario SMTP"><Input /></Form.Item>

            <Divider />
            <Title level={5}><DatabaseOutlined /> Retención de Logs</Title>
            <Form.Item label="Días de Retención">
              <Select value={diasRetencion} onChange={setDiasRetencion} style={{ width: '100%' }}>
                <Option value={7}>7 días</Option>
                <Option value={15}>15 días</Option>
                <Option value={30}>30 días (recomendado)</Option>
                <Option value={60}>60 días</Option>
                <Option value={90}>90 días</Option>
              </Select>
            </Form.Item>

            <Divider />
            <Title level={5}>Notas del Administrador</Title>
            <TextArea
              rows={3}
              placeholder="Agregue notas sobre cambios de configuración, mantenimientos programados, etc."
              value={notasAdmin}
              onChange={(e) => setNotasAdmin(e.target.value)}
            />

            <Divider />
            <Button htmlType="submit" icon={SAVE_ICON}>Guardar Técnica</Button>
          </Form>
        </Card>
      </Col>

      <Col xs={24} md={12}>
        <Card
          title="Copias de Seguridad (Backups)"
          className="shadow-sm"
          extra={<Button type="primary" size="small" icon={DATABASE_ICON} onClick={onCreateBackup}>Crear Backup</Button>}
          style={{ height: '100%' }}
        >
          <List
            size="small"
            dataSource={backups}
            renderItem={item => (
              <List.Item actions={[
                <Button key="descargar" type="link" size="small" onClick={() => onDescargarBackup(item.id)}>Descargar</Button>,
                <Popconfirm key="eliminar"
                  title="¿Eliminar este backup?"
                  description="Esta acción no se puede deshacer. ¿Está seguro?"
                  okText="Sí, eliminar"
                  cancelText="Cancelar"
                  onConfirm={() => onEliminarBackup(item.id)}
                >
                  <Button type="text" danger size="small" icon={DELETE_ICON} />
                </Popconfirm>
              ]}>
                <List.Item.Meta
                  avatar={<SafetyCertificateOutlined style={{ color: '#52c41a', fontSize: 20 }} />}
                  title={item.id}
                  description={`${item.fecha} • Tamaño: ${item.size}`}
                />
              </List.Item>
            )}
          />
          {backups.length === 0 && <div style={{ padding: 20, textAlign: 'center' }}>No hay backups recientes</div>}
        </Card>
      </Col>
    </Row>
  );
};

export default ConfiguracionSistema;
