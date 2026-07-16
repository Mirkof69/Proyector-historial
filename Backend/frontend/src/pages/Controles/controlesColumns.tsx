import React from 'react';
import { Button, Space, Tag, Typography, Tooltip, Badge } from 'antd';
import {
  EditOutlined, DeleteOutlined, SearchOutlined, WarningOutlined,
  EyeOutlined, CheckCircleOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { ControlPrenatal } from '../../services/controlesService';

const { Text } = Typography;

export interface ControlesColumnsDeps {
  getIdClinicoPaciente: (control: ControlPrenatal) => string;
  getNombrePaciente: (control: ControlPrenatal) => string;
  getEdadGestacional: (control: ControlPrenatal) => string;
  getPresionArterial: (control: ControlPrenatal) => string;
  calcularIMC: (peso: number | null | undefined, talla: number | null | undefined) => number | null;
  clasificarIMC: (imc: number | null) => { texto: string; color: string };
  detectarAlertas: (values: any) => string[];
  calcularEdadGestacional: (fum: string) => { semanas: number; dias: number };
  handleQuickView: (control: ControlPrenatal) => void;
  handleViewDetails: (control: ControlPrenatal) => void;
  handleEdit: (control: ControlPrenatal) => void;
  handleDelete: (control: any) => void;
  canChange: (perm: string) => boolean;
  canDelete: (perm: string) => boolean;
}

export const buildControlesColumns = (deps: ControlesColumnsDeps) => {
  const {
    getIdClinicoPaciente, getNombrePaciente, getEdadGestacional, getPresionArterial,
    calcularIMC, clasificarIMC, detectarAlertas, calcularEdadGestacional,
    handleQuickView, handleViewDetails, handleEdit, handleDelete, canChange, canDelete,
  } = deps;

  return [
    {
      title: 'ID Clínico',
      key: 'id_clinico',
      width: 120,
      render: (_: any, record: ControlPrenatal) => (
        <Tag color="blue">{getIdClinicoPaciente(record)}</Tag>
      ),
    },
    {
      title: 'Paciente',
      key: 'paciente',
      render: (_: any, record: ControlPrenatal) => (
        <Text strong>{getNombrePaciente(record)}</Text>
      ),
    },
    {
      title: 'Fecha',
      dataIndex: 'fecha_control',
      key: 'fecha_control',
      width: 120,
      render: (date: string) => dayjs(date).format('DD/MM/YYYY'),
      sorter: (a: ControlPrenatal, b: ControlPrenatal) =>
        dayjs(a.fecha_control).unix() - dayjs(b.fecha_control).unix(),
    },
    {
      title: 'EG',
      key: 'edad_gestacional',
      width: 100,
      render: (_: any, record: ControlPrenatal) => (
        <Tag color="cyan">{getEdadGestacional(record)}</Tag>
      ),
    },
    {
      title: 'N°',
      dataIndex: 'numero_control',
      key: 'numero_control',
      width: 60,
      align: 'center' as const,
    },
    {
      title: 'PA (mmHg)',
      key: 'presion_arterial',
      width: 100,
      render: (_: any, record: ControlPrenatal) => {
        const pa = getPresionArterial(record);
        const isHigh =
          (record.presion_arterial_sistolica || 0) >= 140 ||
          (record.presion_arterial_diastolica || 0) >= 90;
        return <Text type={isHigh ? 'danger' : undefined}>{pa}</Text>;
      },
    },
    {
      title: 'AU (cm)',
      dataIndex: 'altura_uterina',
      key: 'altura_uterina',
      width: 90,
      align: 'center' as const,
      render: (val: number) => val || '-',
    },
    {
      title: 'Peso (kg)',
      dataIndex: 'peso_actual',
      key: 'peso_actual',
      width: 90,
    },
    {
      title: 'IMC',
      key: 'imc',
      width: 120,
      render: (_: any, record: ControlPrenatal) => {
        const imc = calcularIMC(record.peso_actual, record.talla);
        if (!imc) return <Text type="secondary">-</Text>;
        const clasificacion = clasificarIMC(imc);
        return (
          <Space direction="vertical" size={0} style={{ width: '100%' }}>
            <Text strong style={{ fontSize: 14 }}>{imc.toFixed(1)}</Text>
            <Tag color={clasificacion.color} style={{ fontSize: '12px', margin: 0, padding: '0 4px' }}>
              {clasificacion.texto}
            </Tag>
          </Space>
        );
      },
    },
    {
      title: 'FCF (lpm)',
      dataIndex: 'frecuencia_cardiaca_fetal',
      key: 'frecuencia_cardiaca_fetal',
      width: 90,
      render: (val: number) => {
        if (!val) return '-';
        const isBad = val < 110 || val > 160;
        return <Text type={isBad ? 'danger' : undefined}>{val}</Text>;
      },
    },
    {
      title: 'Alertas',
      key: 'alertas',
      width: 100,
      align: 'center' as const,
      render: (_: any, record: ControlPrenatal) => {
        const alertas = detectarAlertas(record);
        return record.tiene_alertas ? (
          <Tooltip title={`${alertas.length} alertas detectadas`}>
            <Badge count={alertas.length} offset={[0, 0]}>
              <WarningOutlined style={{ color: 'red', fontSize: 18 }} />
            </Badge>
          </Tooltip>
        ) : (
          <Tooltip title="Sin alertas">
            <Badge count={0} showZero color="green">
              <CheckCircleOutlined style={{ color: 'green', fontSize: 18 }} />
            </Badge>
          </Tooltip>
        );
      },
    },
    {
      title: 'Acciones',
      key: 'acciones',
      width: 200,
      align: 'center' as const,
      render: (_: any, record: ControlPrenatal) => {
        const eg = calcularEdadGestacional(record.fecha_control);
        return (
          <Space>
            <Tooltip title={`Vista rápida (EG: ${eg.semanas}+${eg.dias})`}>
              <Button
                icon={<SearchOutlined />}
                size="small"
                onClick={() => handleQuickView(record)}
              />
            </Tooltip>
            <Tooltip title="Ver detalles completos">
              <Button
                icon={<EyeOutlined />}
                size="small"
                onClick={() => handleViewDetails(record)}
              />
            </Tooltip>
            {canChange('control') && (
              <Tooltip title="Editar control">
                <Button
                  type="primary"
                  icon={<EditOutlined />}
                  size="small"
                  onClick={() => handleEdit(record)}
                />
              </Tooltip>
            )}
            {canDelete('control') && (
              <Tooltip title="Eliminar control">
                <Button
                  danger
                  icon={<DeleteOutlined />}
                  size="small"
                  onClick={() => handleDelete(record)}
                />
              </Tooltip>
            )}
          </Space>
        );
      },
    },
  ];
};
