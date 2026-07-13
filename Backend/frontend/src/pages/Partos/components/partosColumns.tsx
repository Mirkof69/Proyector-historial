import React from 'react';
import { Tag, Space, Typography, Tooltip, Button } from 'antd';
import { CalendarOutlined, EyeOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { Parto } from '../../../services/partosService';

const { Text } = Typography;

// ── Helpers puros de clasificación (identidad estable) ───────────────────────
const getViaPartoColor = (via: string) => {
  const colores: Record<string, string> = {
    vaginal_espontaneo: 'green',
    vaginal_instrumentado: 'blue',
    cesarea_electiva: 'orange',
    cesarea_urgencia: 'red',
    cesarea_emergencia: 'volcano',
  };
  return colores[via] || 'default';
};

const getViaPartoLabel = (via: string) => {
  return via?.replace(/_/g, ' ').toUpperCase() || 'NO ESPECIFICADO';
};

const esAborto = (edadGestacional: string | undefined) => {
  if (!edadGestacional) return false;
  try {
    const semanas = parseInt(edadGestacional.split('+')[0]);
    return semanas < 20;
  } catch {
    return false;
  }
};

const getTipoAbortoLabel = (tipoAborto: string) => {
  const etiquetas: Record<string, string> = {
    espontaneo: 'Aborto Espontáneo',
    inducido: 'Aborto Inducido',
    incompleto: 'Aborto Incompleto',
    completo: 'Aborto Completo',
    diferido: 'Aborto Diferido/Retenido',
    inevitable: 'Aborto Inevitable',
  };
  return etiquetas[tipoAborto] || tipoAborto.toUpperCase();
};

export const buildPartosColumns = (
  canChange: (perm: string) => boolean,
  canDelete: (perm: string) => boolean,
  onView: (id: number) => void,
  onEdit: (id: number) => void,
  onDelete: (parto: any) => void,
) => [
  {
    title: 'ID Parto',
    dataIndex: 'id',
    key: 'id',
    width: 100,
    render: (id: number) => <Tag color="blue">#{id}</Tag>,
  },
  {
    title: 'CI Paciente',
    key: 'ci_paciente',
    width: 120,
    render: (_: any, record: Parto) => (
      record.paciente_info?.cedula_identidad ? (
        <Tag color="geekblue">{record.paciente_info.cedula_identidad}</Tag>
      ) : <Text type="secondary">-</Text>
    ),
  },
  {
    title: 'Nombre Paciente',
    key: 'nombre_paciente',
    width: 200,
    render: (_: any, record: Parto) => (
      <Text strong>
        {record.paciente_info
          ? `${record.paciente_info.nombre} ${record.paciente_info.apellido_paterno}`
          : 'Paciente Desconocido'}
      </Text>
    ),
  },
  {
    title: 'Fecha de Parto',
    dataIndex: 'fecha_parto',
    key: 'fecha_parto',
    width: 160,
    render: (text: string) => (
      <Space>
        <CalendarOutlined style={{ color: '#1890ff' }} />
        {dayjs(text).format('DD/MM/YYYY HH:mm')}
      </Space>
    ),
    sorter: (a: Parto, b: Parto) => dayjs(a.fecha_parto).unix() - dayjs(b.fecha_parto).unix(),
    defaultSortOrder: 'descend' as const,
  },
  {
    title: 'Tipo de Parto',
    key: 'tipo_parto',
    width: 130,
    render: (_: any, record: Parto) => {
      const tipoAborto = (record as any).tipo_aborto;
      const tipoParto = record.tipo_parto;

      if (tipoAborto) {
        return <Tag color="orange">{getTipoAbortoLabel(tipoAborto)}</Tag>;
      } else if (tipoParto) {
        return <Tag color={getViaPartoColor(tipoParto)}>{getViaPartoLabel(tipoParto)}</Tag>;
      } else {
        const isAborto = esAborto(record.edad_gestacional_parto);
        return (
          <Tag color={isAborto ? "orange" : "default"}>
            {isAborto ? 'ABORTO' : 'Sin clasificar'}
          </Tag>
        );
      }
    },
  },
  {
    title: 'Resultado',
    key: 'resultado',
    width: 120,
    render: (_: any, record: Parto) => {
      const rn = record.recien_nacidos && record.recien_nacidos.length > 0 ? record.recien_nacidos[0] : null;
      const apgar5 = rn?.apgar_5_minutos || record.apgar_5min;

      if (!apgar5 && !rn) return <Tag color="default">Sin datos</Tag>;
      if (typeof apgar5 === 'number') {
        if (apgar5 >= 7) return <Tag color="success">Normal</Tag>;
        if (apgar5 >= 4) return <Tag color="warning">Moderado</Tag>;
        return <Tag color="error">Crítico</Tag>;
      }
      return <Tag color="processing">Evaluando</Tag>;
    },
  },
  {
    title: 'Sexo RN',
    key: 'sexo_rn',
    width: 110,
    render: (_: any, record: Parto) => {
      const rn = record.recien_nacidos && record.recien_nacidos.length > 0 ? record.recien_nacidos[0] : null;
      if (!rn || !rn.sexo) return <Text type="secondary">-</Text>;
      return (
        <Tag color={rn.sexo === 'masculino' ? 'blue' : 'magenta'}>
          {rn.sexo === 'masculino' ? 'Masculino' : 'Femenino'}
        </Tag>
      );
    },
  },
  {
    title: 'Peso RN (g)',
    key: 'peso_rn',
    width: 110,
    render: (_: any, record: Parto) => {
      const rn = record.recien_nacidos && record.recien_nacidos.length > 0 ? record.recien_nacidos[0] : null;
      if (!rn || !rn.peso_nacimiento) return <Text type="secondary">-</Text>;

      const peso = rn.peso_nacimiento;
      let color = 'default';
      if (peso < 2500) color = 'orange';
      else if (peso >= 2500 && peso <= 4000) color = 'green';
      else color = 'red';

      return <Tag color={color}>{peso}g</Tag>;
    },
  },
  {
    title: 'Acciones',
    key: 'acciones',
    render: (_: any, record: Parto) => (
      <Space>
        <Tooltip title="Ver detalles">
          <Button icon={<EyeOutlined />} onClick={() => onView(record.id!)} size="small" />
        </Tooltip>
        {canChange('parto') && (
          <Tooltip title="Editar">
            <Button type="primary" icon={<EditOutlined />} onClick={() => onEdit(record.id!)} size="small" ghost />
          </Tooltip>
        )}
        {canDelete('parto') && (
          <Tooltip title="Eliminar">
            <Button danger icon={<DeleteOutlined />} onClick={() => onDelete(record)} size="small" />
          </Tooltip>
        )}
      </Space>
    ),
  },
];
