import React, { useState, useEffect } from 'react';
import { Card, Descriptions, Tag, Button, Space, Spin, Alert, Typography } from 'antd';
import { ArrowLeftOutlined, EditOutlined, SafetyOutlined } from '@ant-design/icons';
import { useParams, useNavigate } from 'react-router-dom';
import cargosService, { Cargo } from '../../services/cargosService';
import { configuracionDeRol } from '../../config/roles';

const { Text } = Typography;

const DetalleRol: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [cargo, setCargo] = useState<Cargo | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let vigente = true;
    cargosService.obtener(Number(id))
      .then((datos) => { if (vigente) setCargo(datos); })
      .catch(() => { if (vigente) setCargo(null); })
      .finally(() => { if (vigente) setLoading(false); });
    return () => { vigente = false; };
  }, [id]);

  if (loading) return <div style={{ textAlign: 'center', padding: 100 }}><Spin size="large" /></div>;
  if (!cargo) return <Card><Alert message="Cargo no encontrado" type="error" showIcon /></Card>;

  const rol = configuracionDeRol(cargo.rol_base);
  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/dashboard/roles')}>Volver</Button>
        <Button type="primary" icon={<EditOutlined />} onClick={() => navigate(`/dashboard/roles/${id}/editar`)}>Editar</Button>
      </Space>
      <Card title={<span><SafetyOutlined style={{ marginRight: 8 }} />{cargo.nombre}</span>}>
        <Descriptions column={{ xs: 1, sm: 2 }} bordered>
          <Descriptions.Item label="Rol en que se basa"><Tag color={rol.color} icon={rol.icono}>{rol.nombre}</Tag></Descriptions.Item>
          <Descriptions.Item label="Estado">{cargo.activo ? <Tag color="green">Activo</Tag> : <Tag>Inactivo</Tag>}</Descriptions.Item>
          <Descriptions.Item label="Usuarios con este cargo">{cargo.usuarios_count}</Descriptions.Item>
          <Descriptions.Item label="Descripción">{cargo.descripcion || <Text type="secondary">Sin descripción</Text>}</Descriptions.Item>
          <Descriptions.Item label="Módulos que usa" span={2}>
            <Space wrap>{cargo.nombres_modulos.map(n => <Tag key={n} color="blue">{n}</Tag>)}</Space>
          </Descriptions.Item>
        </Descriptions>
      </Card>
    </div>
  );
};

export default DetalleRol;
