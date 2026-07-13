import React, { useState, useEffect, useCallback } from 'react';
import { Card, Form, Input, Button, Switch, Select, Typography, Space, message, Spin } from 'antd';
import { SaveOutlined, CloseOutlined, SafetyOutlined } from '@ant-design/icons';
import { useParams, useNavigate } from 'react-router-dom';
import rolesService from '../../services/rolesService';

const { Title } = Typography;
const { Option } = Select;
const { TextArea } = Input;

const permisosDisponibles = [
  'ver_pacientes', 'crear_pacientes', 'editar_pacientes', 'eliminar_pacientes',
  'ver_embarazos', 'crear_embarazos', 'editar_embarazos', 'eliminar_embarazos',
  'ver_partos', 'crear_partos', 'editar_partos', 'eliminar_partos',
  'ver_laboratorio', 'crear_laboratorio', 'editar_laboratorio', 'eliminar_laboratorio',
  'ver_alertas', 'crear_alertas', 'resolver_alertas',
  'ver_reportes', 'generar_reportes', 'exportar_reportes',
  'gestionar_usuarios', 'gestionar_roles', 'ver_auditoria',
];

const FormularioRol: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const isEditing = !!id;

  const cargarRol = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    try {
      const data = await rolesService.obtener(Number(id));
      form.setFieldsValue(data);
    } catch {
      message.error('Error al cargar el rol');
    } finally {
      setLoading(false);
    }
  }, [id, form]);

  useEffect(() => {
    if (isEditing) cargarRol();
  }, [cargarRol, isEditing]);

  const handleFinish = async (values: any) => {
    setLoading(true);
    try {
      if (isEditing) {
        await rolesService.actualizar(Number(id), values);
        message.success('Rol actualizado correctamente');
      } else {
        await rolesService.crear(values);
        message.success('Rol creado correctamente');
      }
      navigate('/dashboard/roles');
    } catch {
      message.error('Error al guardar el rol');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <Button icon={<CloseOutlined />} onClick={() => navigate('/dashboard/roles')} style={{ marginBottom: 16 }}>Cancelar</Button>
      <Card title={<span><SafetyOutlined style={{ marginRight: 8 }} />{isEditing ? 'Editar' : 'Nuevo'} Rol</span>}>
        <Spin spinning={loading}>
          <Form form={form} layout="vertical" onFinish={handleFinish} style={{ maxWidth: 600 }}>
            <Form.Item name="nombre" label="Nombre del Rol" rules={[{ required: true, message: 'Ingrese el nombre del rol' }]}>
              <Input placeholder="Ej: Médico, Enfermero, Administrador" />
            </Form.Item>
            <Form.Item name="descripcion" label="Descripción">
              <TextArea rows={3} placeholder="Descripción del rol y sus responsabilidades" />
            </Form.Item>
            <Form.Item name="activo" label="Activo" valuePropName="checked">
              <Switch defaultChecked />
            </Form.Item>
            <Form.Item name="permisos" label="Permisos" rules={[{ required: true, message: 'Seleccione al menos un permiso' }]}>
              <Select mode="multiple" placeholder="Seleccione los permisos">
                {permisosDisponibles.map(p => (
                  <Option key={p} value={p}>{p.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</Option>
                ))}
              </Select>
            </Form.Item>
            <Form.Item>
              <Space>
                <Button type="primary" htmlType="submit" icon={<SaveOutlined />} loading={loading}>Guardar</Button>
                <Button onClick={() => navigate('/dashboard/roles')}>Cancelar</Button>
              </Space>
            </Form.Item>
          </Form>
        </Spin>
      </Card>
    </div>
  );
};

export default FormularioRol;
