import React from 'react';
import { Drawer, Space, Descriptions, Divider, Card, Button, Tag } from 'antd';
import { CalendarOutlined, EyeOutlined, EditOutlined, UserOutlined, MedicineBoxOutlined, SearchOutlined, ExclamationCircleOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';

interface Cita {
  id?: number;
  paciente?: number;
  paciente_info?: { nombre_completo?: string };
  fecha_cita: string;
  hora_cita: string;
  tipo_cita: string;
  estado: string;
  medico_info?: { nombre?: string };
  motivo?: string;
  observaciones?: string;
}

interface EstadoTagProps {
  estado: string;
}

const EstadoTag: React.FC<EstadoTagProps> = ({ estado }) => {
  const colors: Record<string, string> = {
    agendada: 'blue', confirmada: 'processing', en_espera: 'warning',
    en_consulta: 'purple', completada: 'success', cancelada: 'error', no_asistio: 'default',
  };
  return <Tag color={colors[estado] || 'default'}>{estado}</Tag>;
};

interface VistaRapidaDrawerProps {
  visible: boolean;
  cita: Cita | null;
  onClose: () => void;
  onVerCompleto: (id: number) => void;
  onEditar: (id: number) => void;
  onNavigate: (path: string) => void;
  canChange: boolean;
}

const VistaRapidaDrawer: React.FC<VistaRapidaDrawerProps> = ({
  visible, cita, onClose, onVerCompleto, onEditar, onNavigate, canChange,
}) => (
  <Drawer
    title={<Space><CalendarOutlined />Vista Rápida de Cita{cita && <EstadoTag estado={cita.estado} />}</Space>}
    placement="right" width={600} onClose={onClose} open={visible}
    extra={
      <Space>
        <Button icon={<EyeOutlined />} onClick={() => { if (cita) { onClose(); onVerCompleto(cita.id!); } }}>Ver Página Completa</Button>
        {canChange && <Button type="primary" icon={<EditOutlined />} onClick={() => { if (cita) { onClose(); onEditar(cita.id!); } }}>Editar Completo</Button>}
      </Space>
    }
  >
    {cita && (
      <Space direction="vertical" style={{ width: '100%' }} size="large">
        <Descriptions title="Información de la Cita" bordered column={1} size="small">
          <Descriptions.Item label="Paciente"><strong>{cita.paciente_info?.nombre_completo || 'No especificado'}</strong></Descriptions.Item>
          <Descriptions.Item label="Fecha y Hora">{dayjs(cita.fecha_cita).format('DD/MM/YYYY - HH:mm')}</Descriptions.Item>
          <Descriptions.Item label="Tipo de Cita"><Tag color="blue">{cita.tipo_cita}</Tag></Descriptions.Item>
          <Descriptions.Item label="Estado"><EstadoTag estado={cita.estado} /></Descriptions.Item>
          <Descriptions.Item label="Médico">{cita.medico_info?.nombre || 'No asignado'}</Descriptions.Item>
          <Descriptions.Item label="Motivo">{cita.motivo || 'No especificado'}</Descriptions.Item>
          {cita.observaciones && <Descriptions.Item label="Observaciones">{cita.observaciones}</Descriptions.Item>}
        </Descriptions>
        <Divider orientation="left">🔗 Acceso Rápido a Módulos</Divider>
        <Card size="small">
          <Space direction="vertical" style={{ width: '100%' }} size="small">
            <Button type="link" icon={<UserOutlined />} block style={{ textAlign: 'left' }} onClick={() => { onClose(); onNavigate(`/dashboard/pacientes?id=${cita.paciente}`); }}>Ver Paciente: {cita.paciente_info?.nombre_completo || 'No especificado'}</Button>
            <Button type="link" icon={<MedicineBoxOutlined />} block style={{ textAlign: 'left' }} onClick={() => { onClose(); onNavigate(`/dashboard/embarazos?paciente=${cita.paciente}`); }}>Ver Embarazos del Paciente</Button>
            <Button type="link" icon={<MedicineBoxOutlined />} block style={{ textAlign: 'left' }} onClick={() => { onClose(); onNavigate(`/dashboard/controles?paciente=${cita.paciente}`); }}>Ver Controles Prenatales</Button>
            <Button type="link" icon={<SearchOutlined />} block style={{ textAlign: 'left' }} onClick={() => { onClose(); onNavigate(`/dashboard/ecografias?paciente=${cita.paciente}`); }}>Ver Ecografías</Button>
            <Button type="link" icon={<ExclamationCircleOutlined />} block style={{ textAlign: 'left' }} onClick={() => { onClose(); onNavigate(`/dashboard/laboratorio?paciente=${cita.paciente}`); }}>Ver Exámenes de Laboratorio</Button>
            <Button type="link" icon={<CalendarOutlined />} block style={{ textAlign: 'left' }} onClick={() => { onClose(); onNavigate(`/dashboard/partos?paciente=${cita.paciente}`); }}>Ver Información de Parto</Button>
            <Divider style={{ margin: '8px 0' }} />
            <Button type="primary" icon={<UserOutlined />} block onClick={() => { onClose(); onNavigate(`/dashboard/pacientes/${cita.paciente}/historia`); }}>Ver Historia Clínica Completa</Button>
          </Space>
        </Card>
      </Space>
    )}
  </Drawer>
);

export default VistaRapidaDrawer;
