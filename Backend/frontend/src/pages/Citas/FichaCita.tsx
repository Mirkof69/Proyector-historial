/**
 * =============================================================================
 * FICHA DE CITA MÉDICA
 * =============================================================================
 * Componente para mostrar la ficha/resumen de una cita médica
 * =============================================================================
 */

import React from 'react';
import { Card, Descriptions, Tag, Space, Typography, Divider } from 'antd';
import {
  CalendarOutlined,
  ClockCircleOutlined,
  UserOutlined,
  MedicineBoxOutlined,
  FileTextOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { Cita } from '../../services/citasService';

import './Citas.css';

const { Title, Text } = Typography;

interface FichaCitaProps {
  cita: Cita;
}

const getEstadoColor = (estado: string): string => {
  const colors: Record<string, string> = {
    agendada: 'default',
    confirmada: 'processing',
    en_espera: 'warning',
    en_consulta: 'processing',
    completada: 'success',
    cancelada: 'error',
    no_asistio: 'default',
  };
  return colors[estado] || 'default';
};

const getTipoCitaLabel = (tipo: string): string => {
  const labels: Record<string, string> = {
    primera_vez: 'Primera Vez',
    control: 'Control',
    urgencia: 'Urgencia',
    seguimiento: 'Seguimiento',
  };
  return labels[tipo] || tipo;
};

export const FichaCita: React.FC<FichaCitaProps> = ({ cita }) => {
  return (
    <div className="citas-ficha">
      <div className="citas-ficha__cabecera">
        <Title level={4}>
          Ficha de Cita Médica
        </Title>
        <Text type="secondary">Comprobante de programación</Text>
      </div>

      <Card>
        <Descriptions column={1} bordered size="small">
          <Descriptions.Item label="Estado">
            <Tag color={getEstadoColor(cita.estado)}>
              {cita.estado_display || cita.estado.toUpperCase()}
            </Tag>
          </Descriptions.Item>

          <Descriptions.Item label="Tipo de Cita">
            <Tag>{getTipoCitaLabel(cita.tipo_cita)}</Tag>
          </Descriptions.Item>

          <Descriptions.Item label={<Space><UserOutlined /> Paciente</Space>}>
            {cita.paciente_info?.nombre_completo || `Paciente #${cita.paciente}`}
          </Descriptions.Item>

          <Descriptions.Item label={<Space><MedicineBoxOutlined /> Médico</Space>}>
            {cita.medico_info
              ? `Dr(a). ${cita.medico_info.nombre}${cita.medico_info.especialidad ? ` - ${cita.medico_info.especialidad}` : ''}`
              : `Médico #${cita.medico}`}
          </Descriptions.Item>

          <Descriptions.Item label={<Space><CalendarOutlined /> Fecha</Space>}>
            {dayjs(cita.fecha_cita).format('DD/MM/YYYY')}
          </Descriptions.Item>

          <Descriptions.Item label={<Space><ClockCircleOutlined /> Hora</Space>}>
            {dayjs(cita.hora_cita, 'HH:mm:ss').format('HH:mm')}
          </Descriptions.Item>

          {cita.duracion && (
            <Descriptions.Item label="Duración">
              {cita.duracion} minutos
            </Descriptions.Item>
          )}

          {cita.consultorio_info && (
            <Descriptions.Item label="Consultorio">
              {cita.consultorio_info.nombre} - {cita.consultorio_info.ubicacion}
            </Descriptions.Item>
          )}

          <Descriptions.Item label={<Space><FileTextOutlined /> Motivo</Space>} span={1}>
            {cita.motivo}
          </Descriptions.Item>

          {cita.observaciones && (
            <Descriptions.Item label="Observaciones" span={1}>
              {cita.observaciones}
            </Descriptions.Item>
          )}
        </Descriptions>

        <Divider />

        <div className="citas-ficha__pie">
          <Text type="secondary">
            Fecha de registro: {cita.fecha_creacion ? dayjs(cita.fecha_creacion).format('DD/MM/YYYY HH:mm') : '-'}
          </Text>
        </div>
      </Card>
    </div>
  );
};
