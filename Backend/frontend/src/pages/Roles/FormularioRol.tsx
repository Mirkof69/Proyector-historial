import React, { useState, useEffect, useMemo } from 'react';
import { Card, Form, Input, Button, Switch, Select, Space, Spin, Checkbox, Alert, Typography } from 'antd';
import { SaveOutlined, CloseOutlined } from '@ant-design/icons';
import { useParams, useNavigate } from 'react-router-dom';
import { useAntdApp } from '../../hooks/useMessage';
import cargosService, { CargoEntrada, ModuloElegible, ModulosPorRol, RolBase } from '../../services/cargosService';
import { mensajeDeError } from '../../services/partoDetalleService';
import './Roles.css';

const { TextArea } = Input;

const { Text, Title } = Typography;

interface SelectorModulosProps {
  modulos: ModuloElegible[];
  value?: string[];
  onChange?: (valor: string[]) => void;
}

/** Casillas de módulos, controladas por el Form.Item; los obligatorios quedan fijos. */
const SelectorModulos: React.FC<SelectorModulosProps> = ({ modulos, value = [], onChange }) => (
  <div role="group" aria-label="Módulos que usa" className="roles-page__modulos">
    {modulos.map(m => (
      <Checkbox
        key={m.modulo}
        checked={m.obligatorio || value.includes(m.modulo)}
        disabled={m.obligatorio}
        onChange={(e) => onChange?.(e.target.checked
          ? [...value, m.modulo]
          : value.filter(v => v !== m.modulo))}
      >
        {m.nombre}
        {m.obligatorio && <Text type="secondary"> (siempre)</Text>}
        {!m.acciones.includes('add') && <Text type="secondary"> · solo ver</Text>}
      </Checkbox>
    ))}
  </div>
);

/** Formulario de un cargo: rol base y los módulos de ese rol que usa. */
const FormularioRol: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { message } = useAntdApp();
  const [form] = Form.useForm<CargoEntrada>();
  const [catalogo, setCatalogo] = useState<ModulosPorRol[]>([]);
  const [inicial, setInicial] = useState<Partial<CargoEntrada> | null>(null);
  const [saving, setSaving] = useState(false);
  const isEditing = !!id;
  const rolBase = Form.useWatch('rol_base', form) as RolBase | undefined;

  useEffect(() => {
    let vigente = true;
    (async () => {
      try {
        const [modulos, cargo] = await Promise.all([
          cargosService.modulos(),
          id ? cargosService.obtener(Number(id)) : Promise.resolve(null),
        ]);
        if (!vigente) return;
        setCatalogo(modulos);
        // El formulario se muestra recién con los datos: antes se podía
        // escribir en él mientras cargaba y lo cargado lo pisaba.
        setInicial(cargo ?? { activo: true, modulos: [] });
      } catch (error) {
        if (vigente) message.error(mensajeDeError(error, 'No se pudo cargar el cargo'));
      }
    })();
    return () => { vigente = false; };
  }, [id, message]);

  const modulosDelRol = useMemo(
    () => catalogo.find(r => r.rol === rolBase)?.modulos ?? [],
    [catalogo, rolBase],
  );

  // Al cambiar el rol base, se marcan todos sus módulos: el administrador quita
  // los que el cargo no usa (lo más común es quitar uno o dos).
  const cambiarRol = (rol: RolBase) => {
    const modulos = catalogo.find(r => r.rol === rol)?.modulos ?? [];
    form.setFieldsValue({ modulos: modulos.map(m => m.modulo) });
  };

  const guardar = async (values: CargoEntrada) => {
    setSaving(true);
    try {
      const datos = { ...values, descripcion: values.descripcion ?? '' };
      if (isEditing) await cargosService.actualizar(Number(id), datos);
      else await cargosService.crear(datos);
      message.success(isEditing ? 'Cargo actualizado' : 'Cargo creado');
      navigate('/dashboard/roles');
    } catch (error) {
      message.error(mensajeDeError(error, 'No se pudo guardar el cargo'));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="roles-page page-container">
      <header className="roles-page__cabecera">
        <div>
          <Title level={2}>{isEditing ? 'Editar cargo' : 'Nuevo cargo'}</Title>
          <Text type="secondary">Elija el rol en que se basa y desmarque los módulos que este cargo no usa.</Text>
        </div>
        <Button icon={<CloseOutlined />} onClick={() => navigate('/dashboard/roles')}>Cancelar</Button>
      </header>
      <Card>
        {!inicial ? <div className="roles-page__cargando"><Spin /></div> : (
          <Form form={form} layout="vertical" onFinish={guardar} initialValues={inicial} className="roles-page__formulario">
            <Form.Item name="nombre" label="Nombre del cargo" rules={[{ required: true, whitespace: true, message: 'Escriba el nombre del cargo' }]}>
              <Input placeholder="Ej.: Obstetriz, Nutricionista, Trabajo social" maxLength={80} />
            </Form.Item>
            <Form.Item name="descripcion" label="Descripción">
              <TextArea rows={2} placeholder="Qué hace este funcionario (opcional)" />
            </Form.Item>
            <Form.Item
              name="rol_base"
              label="Rol en que se basa"
              extra="Decide lo que el sistema le deja hacer en cada módulo (ver, registrar, editar)."
              rules={[{ required: true, message: 'Elija el rol en que se basa el cargo' }]}
            >
              <Select
                placeholder="Elija un rol"
                onChange={cambiarRol}
                options={catalogo.map(r => ({ value: r.rol, label: r.nombre }))}
              />
            </Form.Item>
            {/* Siempre registrado (oculto sin rol): si se monta recién al elegir
                el rol, los módulos que marca `cambiarRol` se perdían al guardar. */}
            <Form.Item name="modulos" label="Módulos que usa" hidden={!rolBase}>
                <SelectorModulos modulos={modulosDelRol} />
            </Form.Item>
            <Alert
              type="info"
              showIcon
              className="roles-page__aviso"
              message="Un cargo solo puede quitar módulos a su rol, nunca agregar. Lo que no marque desaparece del menú y la API lo rechaza."
            />
            <Form.Item name="activo" label="Activo" valuePropName="checked" extra="Un cargo inactivo no se puede asignar a usuarios nuevos; quien ya lo tiene lo conserva.">
              <Switch />
            </Form.Item>
            <Form.Item>
              <Space>
                <Button type="primary" htmlType="submit" icon={<SaveOutlined />} loading={saving}>Guardar</Button>
                <Button onClick={() => navigate('/dashboard/roles')}>Cancelar</Button>
              </Space>
            </Form.Item>
          </Form>
        )}
      </Card>
    </div>
  );
};

export default FormularioRol;
