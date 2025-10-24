import React, { useState, useEffect } from 'react';
import { Card, Descriptions, Button, Spin, message, Tag } from 'antd';
import { ArrowLeftOutlined, EditOutlined } from '@ant-design/icons';
import axios from 'axios';
import { authService } from '../services/authService';
import dayjs from 'dayjs';

interface DetallePacienteProps {
  pacienteId: number;
  onBack: () => void;
  onEdit: (id: number) => void;
}

interface Paciente {
  id: number;
  id_clinico: string;
  nombre: string;
  apellido_paterno: string;
  apellido_materno: string;
  fecha_nacimiento: string;
  genero: string;
  telefono_principal: string;
  email: string;
  cedula_identidad: string;
  direccion: string;
  activo: boolean;
  fecha_registro: string;
}

const DetallePaciente: React.FC<DetallePacienteProps> = ({ pacienteId, onBack, onEdit }) => {
  const [paciente, setPaciente] = useState<Paciente | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPaciente();
  }, [pacienteId]);

  const fetchPaciente = async () => {
    setLoading(true);
    try {
      const token = authService.getToken();
      const response = await axios.get(`http://127.0.0.1:8000/api/pacientes/${pacienteId}/`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setPaciente(response.data);
    } catch (error) {
      message.error('Error al cargar datos del paciente');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const calcularEdad = (fechaNacimiento: string) => {
    const hoy = dayjs();
    const nacimiento = dayjs(fechaNacimiento);
    return hoy.diff(nacimiento, 'year');
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!paciente) {
    return (
      <div style={{ padding: 24 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={onBack} style={{ marginBottom: 16 }}>
          Volver a la lista
        </Button>
        <Card>
          <p>Paciente no encontrado</p>
        </Card>
      </div>
    );
  }

  return (
    <div style={{ padding: 24 }}>
      <Button icon={<ArrowLeftOutlined />} onClick={onBack} style={{ marginBottom: 16 }}>
        Volver a la lista
      </Button>

      <Card
        title={`Detalle del Paciente - ${paciente.id_clinico}`}
        extra={
          <Button 
            type="primary" 
            icon={<EditOutlined />} 
            onClick={() => onEdit(paciente.id)}
          >
            Editar
          </Button>
        }
      >
        <Descriptions bordered column={2}>
          <Descriptions.Item label="ID Clínico">{paciente.id_clinico}</Descriptions.Item>
          <Descriptions.Item label="Estado">
            <Tag color={paciente.activo ? 'green' : 'red'}>
              {paciente.activo ? 'Activo' : 'Inactivo'}
            </Tag>
          </Descriptions.Item>

          <Descriptions.Item label="Nombre Completo" span={2}>
            {`${paciente.nombre} ${paciente.apellido_paterno} ${paciente.apellido_materno || ''}`}
          </Descriptions.Item>

          <Descriptions.Item label="Fecha de Nacimiento">
            {dayjs(paciente.fecha_nacimiento).format('DD/MM/YYYY')}
          </Descriptions.Item>
          <Descriptions.Item label="Edad">
            {calcularEdad(paciente.fecha_nacimiento)} años
          </Descriptions.Item>

          <Descriptions.Item label="Género">
            {paciente.genero.charAt(0).toUpperCase() + paciente.genero.slice(1)}
          </Descriptions.Item>
          <Descriptions.Item label="Teléfono">
            {paciente.telefono_principal || 'No registrado'}
          </Descriptions.Item>

          <Descriptions.Item label="Email" span={2}>
            {paciente.email || 'No registrado'}
          </Descriptions.Item>

          <Descriptions.Item label="Cédula de Identidad">
            {paciente.cedula_identidad || 'No registrado'}
          </Descriptions.Item>
          <Descriptions.Item label="Dirección">
            {paciente.direccion || 'No registrado'}
          </Descriptions.Item>

          <Descriptions.Item label="Fecha de Registro" span={2}>
            {dayjs(paciente.fecha_registro).format('DD/MM/YYYY HH:mm')}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <Card title="Historial de Embarazos" style={{ marginTop: 16 }}>
        <p>No hay embarazos registrados</p>
      </Card>

      <Card title="Controles Prenatales" style={{ marginTop: 16 }}>
        <p>No hay controles registrados</p>
      </Card>
    </div>
  );
};

export default DetallePaciente;