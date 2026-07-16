import React, { useState } from 'react';
import { Row, Col, Card, Typography, Form, Input, Select, Button } from 'antd';
import { useAntdApp } from '../../../hooks/useMessage';
import { PhoneOutlined, MailOutlined, CheckCircleOutlined, SendOutlined } from '@ant-design/icons';
import { soporteService } from '../../../services/soporteService';

const { Title, Paragraph, Text } = Typography;
const { TextArea } = Input;

interface AyudaSoporteTecnicoProps {
  form: any;
}

const AyudaSoporteTecnico: React.FC<AyudaSoporteTecnicoProps> = ({ form }) => {
  const { message } = useAntdApp();
  const [sendingTicket, setSendingTicket] = useState(false);

  const onFinishTicket = async (values: any) => {
    setSendingTicket(true);
    try {
      await soporteService.crearTicket({
        asunto: values.asunto,
        modulo: values.modulo,
        prioridad: values.prioridad,
        descripcion: values.descripcion,
      });
      message.success({
        content: '¡Ticket enviado con éxito! Un técnico lo contactará pronto.',
        icon: <CheckCircleOutlined style={{ color: '#52c41a' }} />,
        duration: 5,
      });
      form.resetFields();
    } catch (error) {
      message.error('Error al enviar el ticket de soporte. Intente nuevamente.');
    } finally {
      setSendingTicket(false);
    }
  };

  return (
    <Row gutter={48} style={{ padding: 20 }}>
      <Col xs={24} md={12}>
        <Title level={3}>¿Necesitas ayuda especializada?</Title>
        <Paragraph>
          Si encontraste un error en el sistema o necesitas asistencia urgente,
          por favor completa el formulario. El equipo de TI responderá en menos de 24 horas.
        </Paragraph>

        <div style={{ marginTop: 40 }}>
          <div style={{ display: 'flex', marginBottom: 24 }}>
            <PhoneOutlined style={{ fontSize: 24, color: '#1890ff', marginRight: 16 }} />
            <div>
              <Text strong>Línea Directa TI</Text>
              <br />
              <Text type="secondary">+591 2 222-3333 (Int. 105)</Text>
            </div>
          </div>
          <div style={{ display: 'flex' }}>
            <MailOutlined style={{ fontSize: 24, color: '#1890ff', marginRight: 16 }} />
            <div>
              <Text strong>Correo Electrónico</Text>
              <br />
              <Text type="secondary">soporte@fetalmedical.com</Text>
            </div>
          </div>
        </div>
      </Col>

      <Col xs={24} md={12}>
        <Card title="Crear Ticket de Soporte" bordered className="shadow-sm">
          <Form form={form} layout="vertical" onFinish={onFinishTicket}>
            <Form.Item name="asunto" label="Asunto" rules={[{ required: true, message: 'Por favor ingrese un asunto' }]}>
              <Input placeholder="Ej: Error al guardar ecografía" />
            </Form.Item>

            <Form.Item name="modulo" label="Módulo Afectado" rules={[{ required: true, message: 'Seleccione un módulo' }]}>
              <Select placeholder="Seleccione...">
                <Select.Option value="login">Acceso / Login</Select.Option>
                <Select.Option value="pacientes">Pacientes</Select.Option>
                <Select.Option value="controles">Controles Prenatales</Select.Option>
                <Select.Option value="reportes">Reportes</Select.Option>
                <Select.Option value="otro">Otro</Select.Option>
              </Select>
            </Form.Item>

            <Form.Item name="prioridad" label="Prioridad" initialValue="media">
              <Select>
                <Select.Option value="baja">Baja (Consulta)</Select.Option>
                <Select.Option value="media">Media (Funcionalidad parcial)</Select.Option>
                <Select.Option value="alta">Alta (Sistema detenido)</Select.Option>
              </Select>
            </Form.Item>

            <Form.Item name="descripcion" label="Descripción Detallada" rules={[{ required: true, message: 'Describa el problema' }]}>
              <TextArea rows={4} placeholder="Describa qué estaba haciendo cuando ocurrió el error..." />
            </Form.Item>

            <Form.Item>
              <Button type="primary" htmlType="submit" icon={<SendOutlined />} loading={sendingTicket} block size="large">
                Enviar Solicitud
              </Button>
            </Form.Item>
          </Form>
        </Card>
      </Col>
    </Row>
  );
};

export default AyudaSoporteTecnico;
