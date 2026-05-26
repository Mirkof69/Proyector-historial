import React from 'react';
import { Descriptions, Space, Tag, Divider } from 'antd';
import {
  CalendarOutlined,
  UserOutlined,
  MedicineBoxOutlined,
  ClockCircleOutlined,
  HomeOutlined,
  FileTextOutlined,
  PhoneOutlined,
  MailOutlined,
  IdcardOutlined,
  BellOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { Cita } from '../../../services/citasService';

interface DetalleCitaInfoProps {
  cita: Cita;
  esHoy: boolean;
  esAtrasada: boolean;
}

const DetalleCitaInfo: React.FC<DetalleCitaInfoProps> = ({ cita, esHoy, esAtrasada }) => (
  <>
    <Descriptions title="Información General" bordered column={{ xs: 1, sm: 2 }}>
      <Descriptions.Item label="Tipo de Cita">
        <Tag color="blue">{cita.tipo_cita}</Tag>
      </Descriptions.Item>
      <Descriptions.Item label="Duración">
        {cita.duracion} minutos
      </Descriptions.Item>
      <Descriptions.Item label="Fecha" span={2}>
        <Space>
          <CalendarOutlined />
          <strong>{dayjs(cita.fecha_cita).format('DD/MM/YYYY')}</strong>
          {esHoy && <Tag color="blue">HOY</Tag>}
          {esAtrasada && <Tag color="red">ATRASADA</Tag>}
        </Space>
      </Descriptions.Item>
      <Descriptions.Item label="Hora Programada" span={2}>
        <Space>
          <ClockCircleOutlined />
          <strong>{cita.hora_cita.substring(0, 5)}</strong>
        </Space>
      </Descriptions.Item>
    </Descriptions>

    <Divider />

    <Descriptions title="Información del Paciente" bordered column={{ xs: 1, sm: 2 }}>
      <Descriptions.Item label="Nombre Completo" span={2}>
        <Space>
          <UserOutlined />
          <strong>{cita.paciente_info?.nombre_completo || 'No especificado'}</strong>
        </Space>
      </Descriptions.Item>
      {cita.paciente_info?.id_clinico && (
        <Descriptions.Item label="ID Clínico">
          <Space>
            <IdcardOutlined />
            {cita.paciente_info.id_clinico}
          </Space>
        </Descriptions.Item>
      )}
      {cita.paciente_info?.edad !== undefined && (
        <Descriptions.Item label="Edad">
          {cita.paciente_info.edad} años
        </Descriptions.Item>
      )}
      {cita.paciente_info?.telefono && (
        <Descriptions.Item label="Teléfono">
          <Space>
            <PhoneOutlined />
            <a href={`tel:${cita.paciente_info.telefono}`}>
              {cita.paciente_info.telefono}
            </a>
          </Space>
        </Descriptions.Item>
      )}
      {cita.paciente_info?.email && (
        <Descriptions.Item label="Email">
          <Space>
            <MailOutlined />
            <a href={`mailto:${cita.paciente_info.email}`}>
              {cita.paciente_info.email}
            </a>
          </Space>
        </Descriptions.Item>
      )}
    </Descriptions>

    <Divider />

    <Descriptions title="Información del Médico" bordered column={{ xs: 1, sm: 2 }}>
      <Descriptions.Item label="Médico" span={2}>
        <Space>
          <MedicineBoxOutlined />
          {cita.medico_info?.nombre || 'No asignado'}
        </Space>
      </Descriptions.Item>
      {cita.medico_info?.especialidad && (
        <Descriptions.Item label="Especialidad" span={2}>
          {cita.medico_info.especialidad}
        </Descriptions.Item>
      )}
      {cita.medico_info?.email && (
        <Descriptions.Item label="Email" span={2}>
          <Space>
            <MailOutlined />
            <a href={`mailto:${cita.medico_info.email}`}>
              {cita.medico_info.email}
            </a>
          </Space>
        </Descriptions.Item>
      )}
    </Descriptions>

    <Divider />

    <Descriptions title="Detalles de la Cita" bordered column={1}>
      <Descriptions.Item label="Motivo">
        <Space direction="vertical" style={{ width: '100%' }}>
          <FileTextOutlined />
          {cita.motivo || '-'}
        </Space>
      </Descriptions.Item>
      {cita.observaciones && (
        <Descriptions.Item label="Observaciones">
          {cita.observaciones}
        </Descriptions.Item>
      )}
      {cita.consultorio && (
        <Descriptions.Item label="Consultorio">
          <Space>
            <HomeOutlined />
            Consultorio asignado
          </Space>
        </Descriptions.Item>
      )}
    </Descriptions>

    <Divider />

    <Descriptions title="Información de Registro" bordered column={{ xs: 1, sm: 2 }}>
      <Descriptions.Item label="Creada por">
        {cita.creado_por_nombre || 'Sistema'}
      </Descriptions.Item>
      <Descriptions.Item label="Fecha de Creación">
        {cita.fecha_creacion ? dayjs(cita.fecha_creacion).format('DD/MM/YYYY HH:mm') : '-'}
      </Descriptions.Item>
      {cita.confirmada_por_nombre && (
        <>
          <Descriptions.Item label="Confirmada por">
            {cita.confirmada_por_nombre}
          </Descriptions.Item>
          <Descriptions.Item label="Fecha de Confirmación">
            {cita.fecha_confirmacion ? dayjs(cita.fecha_confirmacion).format('DD/MM/YYYY HH:mm') : '-'}
          </Descriptions.Item>
        </>
      )}
      {cita.recordatorio_enviado && (
        <Descriptions.Item label="Recordatorio" span={2}>
          <Space>
            <BellOutlined />
            Enviado el {cita.fecha_recordatorio ? dayjs(cita.fecha_recordatorio).format('DD/MM/YYYY HH:mm') : '-'}
          </Space>
        </Descriptions.Item>
      )}
    </Descriptions>
  </>
);

export default DetalleCitaInfo;
