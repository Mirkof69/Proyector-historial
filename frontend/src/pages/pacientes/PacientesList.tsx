// Componente de Lista de Pacientes con Tabla
import React, { useEffect, useState } from 'react';
import { Table, Button, Space, Input, message, Tag, Popconfirm } from 'antd';
import { EditOutlined, DeleteOutlined, EyeOutlined, PlusOutlined, SearchOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { PacientesService } from '../../services/api';
import { Paciente } from '../../types';

const PacientesList: React.FC = () => {
  const [pacientes, setPacientes] = useState<Paciente[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchText, setSearchText] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    fetchPacientes();
  }, []);

  const fetchPacientes = async () => {
    setLoading(true);
    try {
      const response = await PacientesService.getAll();
      setPacientes(response.data.results || response.data);
    } catch (error) {
      message.error('Error al cargar pacientes');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await PacientesService.delete(id);
      message.success('Paciente desactivado exitosamente');
      fetchPacientes();
    } catch (error) {
      message.error('Error al desactivar paciente');
    }
  };

  const columns = [
    {
      title: 'ID Clínico',
      dataIndex: 'id_clinico',
      key: 'id_clinico',
    },
    {
      title: 'Nombre Completo',
      dataIndex: 'nombre_completo',
      key: 'nombre_completo',
    },
    {
      title: 'CI',
      dataIndex: 'cedula_identidad',
      key: 'cedula_identidad',
    },
    {
      title: 'Edad',
      dataIndex: 'edad',
      key: 'edad',
      render: (edad: number) => `${edad} años`,
    },
    {
      title: 'Género',
      dataIndex: 'genero',
      key: 'genero',
      render: (genero: string) => (
        <Tag color={genero === 'femenino' ? 'pink' : 'blue'}>
          {genero.toUpperCase()}
        </Tag>
      ),
    },
    {
      title: 'Estado',
      dataIndex: 'activo',
      key: 'activo',
      render: (activo: boolean) => (
        <Tag color={activo ? 'green' : 'red'}>
          {activo ? 'ACTIVO' : 'INACTIVO'}
        </Tag>
      ),
    },
    {
      title: 'Acciones',
      key: 'acciones',
      render: (_: any, record: Paciente) => (
        <Space>
          <Button 
            icon={<EyeOutlined />} 
            onClick={() => navigate(`/pacientes/${record.id}`)}
          />
          <Button 
            icon={<EditOutlined />} 
            onClick={() => navigate(`/pacientes/${record.id}/edit`)}
          />
          <Popconfirm
            title="¿Está seguro de desactivar este paciente?"
            onConfirm={() => handleDelete(record.id)}
            okText="Sí"
            cancelText="No"
          >
            <Button icon={<DeleteOutlined />} danger />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const filteredPacientes = pacientes.filter((p) =>
    p.nombre_completo.toLowerCase().includes(searchText.toLowerCase()) ||
    p.id_clinico.toLowerCase().includes(searchText.toLowerCase()) ||
    (p.cedula_identidad && p.cedula_identidad.includes(searchText))
  );

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <Input
          placeholder="Buscar paciente..."
          prefix={<SearchOutlined />}
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          style={{ width: 300 }}
        />
        <Button 
          type="primary" 
          icon={<PlusOutlined />}
          onClick={() => navigate('/pacientes/new')}
        >
          Nuevo Paciente
        </Button>
      </div>
      <Table
        columns={columns}
        dataSource={filteredPacientes}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 10 }}
      />
    </div>
  );
};

export default PacientesList;
