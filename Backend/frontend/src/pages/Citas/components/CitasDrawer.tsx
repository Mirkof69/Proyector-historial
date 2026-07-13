import React, { useCallback } from 'react';
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

interface QuickLink {
  icon: React.ReactNode;
  label: string;
  path: (pacienteId: number) => string;
  primary?: boolean;
}

const QUICK_LINKS: QuickLink[] = [
  {
    icon: <UserOutlined />,
    label: 'Ver Paciente: {nombre}',
    path: (id) => `/dashboard/pacientes?id=${id}`,
  },
  {
    icon: <MedicineBoxOutlined />,
    label: 'Ver Embarazos del Paciente',
    path: (id) => `/dashboard/embarazos?paciente=${id}`,
  },
  {
    icon: <MedicineBoxOutlined />,
    label: 'Ver Controles Prenatales',
    path: (id) => `/dashboard/controles?paciente=${id}`,
  },
  {
    icon: <SearchOutlined />,
    label: 'Ver Ecografías',
    path: (id) => `/dashboard/ecografias?paciente=${id}`,
  },
  {
    icon: <ExclamationCircleOutlined />,
    label: 'Ver Exámenes de Laboratorio',
    path: (id) => `/dashboard/laboratorio?paciente=${id}`,
  },
  {
    icon: <CalendarOutlined />,
    label: 'Ver Información de Parto',
    path: (id) => `/dashboard/partos?paciente=${id}`,
  },
  {
    icon: <UserOutlined />,
    label: 'Ver Historia Clínica Completa',
    path: (id) => `/dashboard/pacientes/${id}/historia`,
    primary: true,
  },
];

const CitasDrawer: React.FC<CitasDrawerProps> = React.memo(({
  visible,
  cita,
  canChange,
  onClose,
  getEstadoTag,
}) => {
  const navigate = useNavigate();

  const handleVerCompleto = useCallback(() => {
    if (cita) {
      onClose();
      navigate(`/dashboard/citas/${cita.id}`);
    }
  }, [cita, onClose, navigate]);

  const handleEditar = useCallback(() => {
    if (cita) {
      onClose();
      navigate(`/dashboard/citas/${cita.id}/editar`);
    }
  }, [cita, onClose, navigate]);

  const handleNavigate = useCallback((path: string) => {
    onClose();
    navigate(path);
  }, [onClose, navigate]);

  if (!cita) return null;

  return (
    <Drawer
      title={
        <Space>
          <CalendarOutlined />
          Vista Rápida de Cita
          {getEstadoTag(cita.estado)}
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

        <Divider orientation="left">Acceso Rápido a Módulos</Divider>
        <Card size="small">
          <Space direction="vertical" style={{ width: '100%' }} size="small">
            {QUICK_LINKS.map((link) => {
              const label = link.label.replace('{nombre}', cita.paciente_info?.nombre_completo || '');
              const isLastPrimary = link.primary;
              return (
                <Button
                  key={link.label}
                  type={isLastPrimary ? 'primary' : 'link'}
                  icon={link.icon}
                  block
                  style={isLastPrimary ? undefined : { textAlign: 'left' }}
                  onClick={() => handleNavigate(link.path(cita.paciente))}
                >
                  {label}
                </Button>
              );
            })}
          </Space>
        </Card>
      </Space>
    </Drawer>
  );
});

export default CitasDrawer;
