import React from 'react';
import { Drawer, Space, Button, Descriptions, Divider, Card, Tag } from 'antd';
import {
  CalendarOutlined,
  EyeOutlined,
  EditOutlined,
  UserOutlined,
  MedicineBoxOutlined,
  SearchOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import dayjs from 'dayjs';
import { Cita, EstadoCita } from '../../../services/citasService';

interface CitasDrawerProps {
  visible: boolean;
  cita: Cita | null;
  canChange: boolean;
  onClose: () => void;
  getEstadoTag: (estado: EstadoCita) => React.ReactNode;
}

const CitasDrawer: React.FC<CitasDrawerProps> = ({
  visible,
  cita,
  canChange,
  onClose,
  getEstadoTag,
}) => {
  const navigate = useNavigate();

  const handleVerCompleto = () => {
    if (cita) {
      onClose();
      navigate(`/dashboard/citas/${cita.id}`);
    }
  };

  const handleEditar = () => {
    if (cita) {
      onClose();
      navigate(`/dashboard/citas/${cita.id}/editar`);
    }
  };

  return (
    <Drawer
      title={
        <Space>
          <CalendarOutlined />
          Vista Rápida de Cita
          {cita && getEstadoTag(cita.estado)}
        </Space>
      }
      placement="right"
      width={600}
      onClose={onClose}
      open={visible}
      extra={
        <Space>
          <Button icon={<EyeOutlined />} onClick={handleVerCompleto}>
            Ver Página Completa
          </Button>
          {canChange && (
            <Button type="primary" icon={<EditOutlined />} onClick={handleEditar}>
              Editar Completo
            </Button>
          )}
        </Space>
      }
    >
      {cita && (
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <Descriptions title="Información de la Cita" bordered column={1} size="small">
            <Descriptions.Item label="Paciente">
              <strong>{cita.paciente_info?.nombre_completo || 'No especificado'}</strong>
            </Descriptions.Item>
            <Descriptions.Item label="Fecha y Hora">
              {dayjs(cita.fecha_cita).format('DD/MM/YYYY - HH:mm')}
            </Descriptions.Item>
            <Descriptions.Item label="Tipo de Cita">
              <Tag color="blue">{cita.tipo_cita}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="Estado">
              {getEstadoTag(cita.estado)}
            </Descriptions.Item>
            <Descriptions.Item label="Médico">
              {cita.medico_info?.nombre || 'No asignado'}
            </Descriptions.Item>
            <Descriptions.Item label="Motivo">
              {cita.motivo || 'No especificado'}
            </Descriptions.Item>
            {cita.observaciones && (
              <Descriptions.Item label="Observaciones">
                {cita.observaciones}
              </Descriptions.Item>
            )}
          </Descriptions>

          <Divider orientation="left">🔗 Acceso Rápido a Módulos</Divider>
          <Card size="small">
            <Space direction="vertical" style={{ width: '100%' }} size="small">
              <Button
                type="link"
                icon={<UserOutlined />}
                block
                style={{ textAlign: 'left' }}
                onClick={() => {
                  onClose();
                  navigate(`/dashboard/pacientes?id=${cita.paciente}`);
                }}
              >
                Ver Paciente: {cita.paciente_info?.nombre_completo || 'No especificado'}
              </Button>
              <Button
                type="link"
                icon={<MedicineBoxOutlined />}
                block
                style={{ textAlign: 'left' }}
                onClick={() => {
                  onClose();
                  navigate(`/dashboard/embarazos?paciente=${cita.paciente}`);
                }}
              >
                Ver Embarazos del Paciente
              </Button>
              <Button
                type="link"
                icon={<MedicineBoxOutlined />}
                block
                style={{ textAlign: 'left' }}
                onClick={() => {
                  onClose();
                  navigate(`/dashboard/controles?paciente=${cita.paciente}`);
                }}
              >
                Ver Controles Prenatales
              </Button>
              <Button
                type="link"
                icon={<SearchOutlined />}
                block
                style={{ textAlign: 'left' }}
                onClick={() => {
                  onClose();
                  navigate(`/dashboard/ecografias?paciente=${cita.paciente}`);
                }}
              >
                Ver Ecografías
              </Button>
              <Button
                type="link"
                icon={<ExclamationCircleOutlined />}
                block
                style={{ textAlign: 'left' }}
                onClick={() => {
                  onClose();
                  navigate(`/dashboard/laboratorio?paciente=${cita.paciente}`);
                }}
              >
                Ver Exámenes de Laboratorio
              </Button>
              <Button
                type="link"
                icon={<CalendarOutlined />}
                block
                style={{ textAlign: 'left' }}
                onClick={() => {
                  onClose();
                  navigate(`/dashboard/partos?paciente=${cita.paciente}`);
                }}
              >
                Ver Información de Parto
              </Button>
              <Divider style={{ margin: '8px 0' }} />
              <Button
                type="primary"
                icon={<UserOutlined />}
                block
                onClick={() => {
                  onClose();
                  navigate(`/dashboard/pacientes/${cita.paciente}/historia`);
                }}
              >
                Ver Historia Clínica Completa
              </Button>
            </Space>
          </Card>
        </Space>
      )}
    </Drawer>
  );
};

export default CitasDrawer;
