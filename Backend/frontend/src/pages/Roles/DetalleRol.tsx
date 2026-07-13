import React, { useState, useEffect, useCallback } from 'react';
import { Card, Descriptions, Tag, Button, Space, Spin, Alert, Typography, Switch } from 'antd';
import { ArrowLeftOutlined, EditOutlined, SafetyOutlined } from '@ant-design/icons';
import { useParams, useNavigate } from 'react-router-dom';
import rolesService, { Rol } from '../../services/rolesService';

const { Text } = Typography;

const DetalleRol: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [rol, setRol] = useState<Rol | null>(null);
  const [loading, setLoading] = useState(true);

  const cargarRol = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    try {
      const data = await rolesService.obtener(Number(id));
      setRol(data);
    } catch {
      setRol(null);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    cargarRol();
  }, [cargarRol]);

  if (loading) return <div style={{ textAlign: 'center', padding: 100 }}><Spin size="large" /></div>;
  if (!rol) return <Card><Alert message="Rol no encontrado" type="error" showIcon /></Card>;

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/dashboard/roles')}>Volver</Button>
        <Button type="primary" icon={<EditOutlined />} onClick={() => navigate(`/dashboard/roles/${id}/editar`)}>Editar</Button>
      </Space>
      <Card title={<span><SafetyOutlined style={{ marginRight: 8 }} />Detalle del Rol: {rol.nombre}</span>}>
        <Descriptions column={{ xs: 1, sm: 2 }} bordered>
          <Descriptions.Item label="ID">#{rol.id}</Descriptions.Item>
          <Descriptions.Item label="Nombre"><Text strong>{rol.nombre}</Text></Descriptions.Item>
          <Descriptions.Item label="Descripción">{rol.descripcion || 'Sin descripción'}</Descriptions.Item>
          <Descriptions.Item label="Activo"><Switch checked={rol.activo} disabled /></Descriptions.Item>
          <Descriptions.Item label="Permisos" span={2}>
            <Space wrap>
              {rol.permisos?.map((p: string) => (
                <Tag key={p} color="blue">{p}</Tag>
              ))}
              {(!rol.permisos || rol.permisos.length === 0) && <Text type="secondary">Sin permisos asignados</Text>}
            </Space>
          </Descriptions.Item>
        </Descriptions>
      </Card>
    </div>
  );
};

export default DetalleRol;
