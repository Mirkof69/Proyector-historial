import React, { useEffect, useState } from 'react';
import { Card, Table, Tag, Space, Typography } from 'antd';
import cargosService, { ModulosPorRol } from '../../services/cargosService';
import { configuracionDeRol } from '../../config/roles';

const { Text } = Typography;

const ACCION: Record<string, string> = { view: 'ver', add: 'crear', change: 'editar', delete: 'borrar' };

interface FilaRol {
  rol: string;
  nombre: string;
  modulos: ModulosPorRol['modulos'] | null;
}

/** El administrador no está en la tabla de permisos: tiene todo. */
const ADMINISTRADOR: FilaRol = { rol: 'administrador', nombre: 'Administrador', modulos: null };

/**
 * Los cinco roles con lo que cada uno puede hacer, leído de la misma tabla que
 * aplica la API (usuarios/permisos_por_rol.py). Antes la pantalla solo listaba
 * los cargos creados a mano y los permisos de cada rol no se veían en ningún lado.
 */
const RolesDelSistema: React.FC = () => {
  const [roles, setRoles] = useState<FilaRol[]>([]);
  const [cargando, setCargando] = useState(true);

  useEffect(() => {
    let vigente = true;
    cargosService.modulos()
      .then((lista) => { if (vigente) setRoles([ADMINISTRADOR, ...lista]); })
      .catch(() => { if (vigente) setRoles([ADMINISTRADOR]); })
      .finally(() => { if (vigente) setCargando(false); });
    return () => { vigente = false; };
  }, []);

  const columnas = [
    {
      title: 'Rol', dataIndex: 'rol', key: 'rol', width: 170,
      render: (rol: string) => {
        const config = configuracionDeRol(rol);
        return <Tag icon={config.icono}>{config.nombre}</Tag>;
      },
    },
    {
      title: 'Permisos', dataIndex: 'modulos', key: 'modulos',
      render: (modulos: FilaRol['modulos']) => (modulos === null
        ? <Text>Todo el sistema: usuarios, roles, configuración, auditoría, respaldos y todos los módulos clínicos.</Text>
        : (
          <Space wrap size={[4, 4]}>
            {modulos.map((m) => (
              <Tag key={m.modulo}>
                {m.nombre}: {m.acciones.map((a) => ACCION[a] ?? a).join(', ')}
              </Tag>
            ))}
          </Space>
        )),
    },
  ];

  return (
    <Card title="Roles del sistema y sus permisos">
      <Table
        columns={columnas}
        dataSource={roles}
        loading={cargando}
        rowKey="rol"
        pagination={false}
        scroll={{ x: 700 }}
      />
    </Card>
  );
};

export default RolesDelSistema;
