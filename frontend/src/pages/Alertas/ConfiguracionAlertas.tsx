import React, { useState, useEffect, useCallback } from 'react';
import { Card, Form, Switch, Button, InputNumber, Typography, message, Spin, Divider } from 'antd';
import { SaveOutlined } from '@ant-design/icons';
import './AlertasMedicas.css';
import api from '../../services/api';

const { Title, Text } = Typography;

const ConfiguracionAlertas: React.FC = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  const cargarConfig = useCallback(async () => {
    setLoading(true);
    try {
      const response = await api.get('/reportes/configuracion/alertas/');
      form.setFieldsValue(response.data);
    } catch {
      // Si no hay config, usar valores por defecto
    } finally {
      setLoading(false);
    }
  }, [form]);

  useEffect(() => {
    cargarConfig();
  }, [cargarConfig]);

  const handleSave = async (values: any) => {
    setSaving(true);
    try {
      await api.post('/reportes/configuracion/alertas/', values);
      message.success('Configuración guardada correctamente');
    } catch {
      message.error('Error al guardar la configuración');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="alertas-page page-container">
    <header className="alertas-page__cabecera">
      <div>
        <Title level={2}>Configuración de Alertas</Title>
        <Text type="secondary">Qué valores disparan una alerta y por qué medio se avisa.</Text>
      </div>
      <Button type="primary" icon={<SaveOutlined />} loading={saving} onClick={() => form.submit()}>Guardar</Button>
    </header>
    <Card>
      <Spin spinning={loading}>
        <Form form={form} layout="vertical" onFinish={handleSave} className="alertas-page__formulario">
          <Title level={5}>Alertas de Signos Vitales</Title>
          <Form.Item name="alertar_presion_alta" label="Alertar sobre presión arterial alta" valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item name="limite_presion_sistolica" label="Límite superior presión sistólica (mmHg)">
            <InputNumber min={100} max={250} className="alertas-page__control" placeholder="140" />
          </Form.Item>
          <Form.Item name="alertar_glucosa_alta" label="Alertar sobre glucosa elevada" valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item name="limite_glucosa_ayunas" label="Límite glucosa en ayunas (mg/dL)">
            <InputNumber min={70} max={300} className="alertas-page__control" placeholder="105" />
          </Form.Item>

          <Divider />
          <Title level={5}>Alertas de Laboratorio</Title>
          <Form.Item name="alertar_resultados_criticos" label="Alertar sobre resultados críticos" valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item name="alertar_resultados_anormales" label="Alertar sobre resultados anormales" valuePropName="checked">
            <Switch />
          </Form.Item>

          <Divider />
          <Title level={5}>Notificaciones</Title>
          <Form.Item name="notificar_por_email" label="Enviar notificaciones por email" valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item name="notificar_por_sistema" label="Mostrar notificaciones en el sistema" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Form>
      </Spin>
    </Card>
    </div>
  );
};

export default ConfiguracionAlertas;
