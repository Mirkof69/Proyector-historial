import React, { useState, useEffect, useCallback } from 'react';
import { Card, Table, Button, Space, Tag, Switch, Popconfirm, Empty, Alert, Typography } from 'antd';
import { useAntdApp } from '../../hooks/useMessage';
import { PlusOutlined, EyeOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import cargosService, { Cargo } from '../../services/cargosService';
import { configuracionDeRol } from '../../config/roles';
import RolesDelSistema from './RolesDelSistema';
import { mensajeDeError } from '../../services/partoDetalleService';

import './Roles.css';

const { Text, Title } = Typography;

/**
 * Cargos del hospital. Antes esta pantalla editaba «permisos» que ningún código
 * leía; ahora cada cargo se aplica en el menú y en la API.
 */
const Roles: React.FC = () => {
  const navigate = useNavigate();
  const { message } = useAntdApp();
  const [cargos, setCargos] = useState<Cargo[]>([]);
  const [loading, setLoading] = useState(false);

  const cargar = useCallback(async () => {
    setLoading(true);
    try {
      setCargos(await cargosService.listar());
    } catch (error) {
      message.error(mensajeDeError(error, 'No se pudieron cargar los cargos'));
    } finally {
      setLoading(false);
    }
  }, [message]);

  useEffect(() => {
    cargar();
  }, [cargar]);

  const eliminar = async (cargo: Cargo) => {
    try {
      await cargosService.eliminar(cargo.id);
      message.success(`Cargo «${cargo.nombre}» eliminado`);
      cargar();
    } catch (error) {
      message.error(mensajeDeError(error, 'No se pudo eliminar el cargo'));
    }
  };

  const cambiarActivo = async (cargo: Cargo, activo: boolean) => {
    try {
      await cargosService.actualizar(cargo.id, { activo });
      setCargos(prev => prev.map(c => (c.id === cargo.id ? { ...c, activo } : c)));
      message.success(`Cargo «${cargo.nombre}» ${activo ? 'activado' : 'desactivado'}`);
    } catch (error) {
      message.error(mensajeDeError(error, 'No se pudo cambiar el estado del cargo'));
    }
  };

  const columns = [
    {
      title: 'Cargo',
      dataIndex: 'nombre',
      key: 'nombre',
      render: (nombre: string, cargo: Cargo) => (
        <Space direction="vertical" size={0}>
          <Text strong>{nombre}</Text>
          {cargo.descripcion && <Text type="secondary">{cargo.descripcion}</Text>}
        </Space>
      ),
    },
    {
      title: 'Rol en que se basa',
      dataIndex: 'rol_base',
      key: 'rol_base',
      render: (rol: string) => {
        const config = configuracionDeRol(rol);
        return <Tag icon={config.icono}>{config.nombre}</Tag>;
      },
    },
    {
      title: 'Módulos',
      dataIndex: 'nombres_modulos',
      key: 'modulos',
      render: (nombres: string[]) => (
        <Space wrap size={[4, 4]}>
          {nombres.slice(0, 4).map(n => <Tag key={n}>{n}</Tag>)}
          {nombres.length > 4 && <Tag>+{nombres.length - 4} más</Tag>}
        </Space>
      ),
    },
    { title: 'Usuarios', dataIndex: 'usuarios_count', key: 'usuarios', width: 100 },
    {
      title: 'Activo',
      dataIndex: 'activo',
      key: 'activo',
      width: 90,
      render: (activo: boolean, cargo: Cargo) => (
        <Switch checked={activo} aria-label={`Activar o desactivar ${cargo.nombre}`}
          onChange={(checked) => cambiarActivo(cargo, checked)} />
      ),
    },
    {
      title: 'Acciones',
      key: 'acciones',
      width: 130,
      render: (_: unknown, cargo: Cargo) => (
        <Space>
          <Button size="small" icon={<EyeOutlined />} aria-label={`Ver ${cargo.nombre}`}
            onClick={() => navigate(`/dashboard/roles/${cargo.id}`)} />
          <Button size="small" icon={<EditOutlined />} aria-label={`Editar ${cargo.nombre}`}
            onClick={() => navigate(`/dashboard/roles/${cargo.id}/editar`)} />
          <Popconfirm
            title={`¿Eliminar el cargo «${cargo.nombre}»?`}
            description={cargo.usuarios_count > 0
              ? `Lo tienen ${cargo.usuarios_count} usuario(s): no se podrá borrar. Desactívelo en su lugar.`
              : 'Esta acción no se puede deshacer.'}
            okText="Sí, eliminar"
            cancelText="Cancelar"
            onConfirm={() => eliminar(cargo)}
          >
            <Button size="small" danger icon={<DeleteOutlined />} aria-label={`Eliminar ${cargo.nombre}`} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div className="roles-page page-container">
      <header className="roles-page__cabecera">
        <div>
          <Title level={2}>Cargos y permisos</Title>
          <Text type="secondary">Qué módulos usa cada funcionario, sobre el rol del sistema en que se basa.</Text>
        </div>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate('/dashboard/roles/nuevo')}>
          Nuevo cargo
        </Button>
      </header>
      <RolesDelSistema />
      <Alert
        type="info"
        showIcon
        message="Para otros funcionarios del hospital (obstetriz, nutricionista, trabajo social…)"
        description="Cada cargo se basa en un rol del sistema y elige qué módulos de ese rol usa. Puede quitar módulos, nunca agregar: lo que el sistema deja hacer sigue siendo lo del rol base."
      />
      <Card title="Cargos del hospital">
        <Table
          columns={columns}
          dataSource={cargos}
          loading={loading}
          rowKey="id"
          pagination={false}
          scroll={{ x: 900 }}
          locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="Todavía no hay cargos. Los usuarios usan su rol completo." /> }}
        />
      </Card>
    </div>
  );
};

export default Roles;
