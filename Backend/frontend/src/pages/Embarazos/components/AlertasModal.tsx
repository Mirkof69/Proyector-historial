import React from 'react';
import { Modal, Space, Tabs, List, Button, Alert, Form, Switch, Checkbox, Table, Tag, Typography } from 'antd';
import { BellOutlined, WarningOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { EmbarazoExtendido } from '../embarazosReducer';

const { Text } = Typography;

interface AlertasModalProps {
  visible: boolean;
  onClose: () => void;
  embarazos: EmbarazoExtendido[];
}

const AlertasModal: React.FC<AlertasModalProps> = ({ visible, onClose, embarazos }) => (
  <Modal
    title={<Space><BellOutlined /> Sistema de Alertas Inteligentes</Space>}
    open={visible}
    onCancel={onClose}
    width={900}
    footer={null}
  >
    <Tabs
      items={[
        {
          key: '1',
          label: 'Alertas Activas',
          children: (
            <List
              itemLayout="horizontal"
                dataSource={
                  embarazos.reduce((acc, e) => {
                    if (e.estado === 'activo' && (e.edad_gestacional_semanas_num || 0) >= 37) {
                      acc.push({
                        id: e.id,
                        tipo: 'TÉRMINO',
                        mensaje: `${e.paciente_nombre} - ${e.edad_gestacional_semanas_num} semanas. Próximo a término.`,
                        prioridad: 'media',
                        fecha: dayjs().format('DD/MM/YYYY')
                      });
                    }
                    return acc;
                  }, [] as any[])
                }
              renderItem={(item: any) => (
                <List.Item
                  actions={[
                    <Button key="ver-detalle" size="small" type="link">Ver Detalle</Button>,
                    <Button key="descartar" size="small" type="link" danger>Descartar</Button>
                  ]}
                >
                  <List.Item.Meta
                    avatar={<WarningOutlined style={{ fontSize: 24, color: '#faad14' }} />}
                    title={<Text strong>[{item.tipo}] {item.mensaje}</Text>}
                    description={`Fecha: ${item.fecha} • Prioridad: ${item.prioridad.toUpperCase()}`}
                  />
                </List.Item>
              )}
            />
          ),
        },
        {
          key: '2',
          label: 'Recordatorios Programados',
          children: (
            <>
              <Alert
                message="Configuración de Notificaciones"
                description="El sistema enviará recordatorios automáticos para citas programadas 24h antes vía SMS/Email."
                type="info"
                showIcon
                style={{ marginBottom: 16 }}
              />
              <Form layout="vertical">
                <Form.Item label="Activar Recordatorios">
                  <Switch defaultChecked /> Notificaciones Push
                </Form.Item>
                <Form.Item label="Canales de Notificación">
                  <Checkbox.Group defaultValue={['sms', 'email']}>
                    <Space direction="vertical">
                      <Checkbox value="sms">SMS (Mensajería)</Checkbox>
                      <Checkbox value="email">Correo Electrónico</Checkbox>
                      <Checkbox value="whatsapp">WhatsApp (Próximamente)</Checkbox>
                    </Space>
                  </Checkbox.Group>
                </Form.Item>
                <Button type="primary">Guardar Configuración</Button>
              </Form>
            </>
          ),
        },
        {
          key: '3',
          label: 'Historial de Notificaciones',
          children: (
            <Table
              size="small"
              columns={[
                { title: 'Fecha', dataIndex: 'fecha', key: 'fecha' },
                { title: 'Paciente', dataIndex: 'paciente', key: 'paciente' },
                { title: 'Tipo', dataIndex: 'tipo', key: 'tipo' },
                {
                  title: 'Estado',
                  dataIndex: 'estado',
                  key: 'estado',
                  render: (estado: string) => (
                    <Tag color={estado === 'enviado' ? 'green' : 'orange'}>
                      {estado}
                    </Tag>
                  )
                }
              ]}
              dataSource={[
                { key: '1', fecha: dayjs().format('DD/MM/YYYY'), paciente: 'María González', tipo: 'Recordatorio Cita', estado: 'enviado' },
                { key: '2', fecha: dayjs().subtract(1, 'day').format('DD/MM/YYYY'), paciente: 'Ana Torres', tipo: 'Alerta Laboratorio', estado: 'enviado' }
              ]}
              pagination={{ pageSize: 5 }}
            />
          ),
        },
      ]}
    />
  </Modal>
);

export default AlertasModal;
