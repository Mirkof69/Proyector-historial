import React from 'react';
import { Button, Space, Tag, Tooltip, Badge, Typography } from 'antd';
import {
  EyeOutlined, EditOutlined, DeleteOutlined, CalendarOutlined, UserOutlined, RobotOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { Ecografia } from '../../services/ecografiasService';

const { Text } = Typography;

interface BuildColumnsArgs {
  handleVerVistaRapida: (ecografia: Ecografia) => void;
  handleEditar: (id: number) => void;
  handleEliminar: (ecografia: any) => void;
  canChange: (perm: string) => boolean;
  canDelete: (perm: string) => boolean;
}

export const buildColumnsEcografias = ({ handleVerVistaRapida, handleEditar, handleEliminar, canChange, canDelete }: BuildColumnsArgs) => [
  {
    title: 'Paciente',
    key: 'paciente',
    width: 200,
    render: (_: any, record: Ecografia) => (
      <Space direction="vertical" size={0}>
        <Space>
          <UserOutlined style={{ color: '#1890ff' }} />
          <span style={{ fontWeight: 500 }}>{record.paciente_nombre || 'No especificado'}</span>
        </Space>
      </Space>
    ),
  },
  {
    title: 'Fecha',
    dataIndex: 'fecha_ecografia',
    key: 'fecha_ecografia',
    width: 120,
    sorter: (a: Ecografia, b: Ecografia) =>
      dayjs(a.fecha_ecografia).unix() - dayjs(b.fecha_ecografia).unix(),
    render: (fecha: string) => (
      <Space>
        <CalendarOutlined />
        {dayjs(fecha).format('DD/MM/YYYY')}
      </Space>
    ),
  },
  {
    title: 'Tipo',
    dataIndex: 'tipo_ecografia',
    key: 'tipo_ecografia',
    width: 150,
    render: (tipo: string) => {
      const colores: Record<string, string> = {
        primer_trimestre: 'cyan',
        segundo_trimestre: 'blue',
        tercer_trimestre: 'purple',
        morfologica: 'green',
        doppler: 'orange',
        genetica: 'gold',
        '4d': 'magenta',
      };
      return <Tag color={colores[tipo] || 'default'}>{tipo?.replace('_', ' ').toUpperCase()}</Tag>;
    },
  },
  {
    title: 'Edad Gestacional',
    key: 'edad_gestacional',
    width: 130,
    render: (_: any, record: Ecografia) => (
      <Text>
        {record.edad_gestacional_texto ||
          `${record.edad_gestacional_semanas || 0}+${record.edad_gestacional_dias || 0}`}
      </Text>
    ),
  },
  {
    title: 'Diagnóstico',
    dataIndex: 'diagnostico',
    key: 'diagnostico',
    ellipsis: true,
    render: (text: string) => (
      <Tooltip title={text}>
        <Text ellipsis>{text || '-'}</Text>
      </Tooltip>
    ),
  },
  {
    title: 'Estado',
    key: 'estado',
    width: 100,
    render: (_: any, record: Ecografia) => {
      // Determinar si hay alertas basado en FCF y vitalidad
      const tieneAlertas = !record.vitalidad_fetal ||
        (record.frecuencia_cardiaca_fetal && (record.frecuencia_cardiaca_fetal < 110 || record.frecuencia_cardiaca_fetal > 160));

      if (tieneAlertas) {
        return <Badge status="error" text="Con alertas" />;
      }
      return <Badge status="success" text="Normal" />;
    },
  },
  {
    title: 'IA',
    key: 'tiene_analisis_ia',
    width: 60,
    align: 'center' as const,
    render: (_: any, record: Ecografia) => {
      if ((record as any).tiene_analisis_ia) {
        return (
          <Tooltip title="Tiene análisis IA">
            <RobotOutlined style={{ color: '#722ed1', fontSize: 18 }} />
          </Tooltip>
        );
      }
      return null;
    },
  },
  {
    title: 'Acciones',
    key: 'acciones',
    fixed: 'right' as const,
    width: 150,
    render: (_: any, record: Ecografia) => (
      <Space size="small">
        <Tooltip title="Ver detalle">
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => handleVerVistaRapida(record)}
          />
        </Tooltip>
        {canChange('ecografia') && (
          <Tooltip title="Editar">
            <Button
              type="link"
              icon={<EditOutlined />}
              onClick={() => handleEditar(record.id!)}
            />
          </Tooltip>
        )}
        {canDelete('ecografia') && (
          <Tooltip title="Eliminar">
            <Button
              type="link"
              danger
              icon={<DeleteOutlined />}
              onClick={() => handleEliminar(record)}
            />
          </Tooltip>
        )}
      </Space>
    ),
  },
];
