import React from 'react';
import { Button, Space, Tag, Typography, Tooltip, Badge, Progress, Avatar, Dropdown } from 'antd';
import {
  EditOutlined, DeleteOutlined, EyeOutlined, UserOutlined, MedicineBoxOutlined,
  HistoryOutlined, ArrowRightOutlined, StopOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import {
  EmbarazoExtendido, EmbarazosAction, RISK_COLORS, RISK_LABELS, STATUS_COLORS, STATUS_LABELS,
} from './embarazosReducer';

const { Text } = Typography;

const userOutlinedIcon3 = <UserOutlined />;
const medicineBoxOutlinedIcon6 = <MedicineBoxOutlined />;
const eyeOutlinedIcon4 = <EyeOutlined />;
const historyIcon3 = <HistoryOutlined />;
const arrowRightOutlinedIcon = <ArrowRightOutlined />;

export interface EmbarazosColumnsDeps {
  navigate: (path: string) => void;
  canChange: (perm: string) => boolean;
  canDelete: (perm: string) => boolean;
  dispatch: React.Dispatch<EmbarazosAction>;
  handleVerHistorial: (embarazo: EmbarazoExtendido) => void;
  handleOpenEdit: (record: EmbarazoExtendido) => void;
  handleFinalizarEmbarazo: (embarazo: EmbarazoExtendido) => void;
  handleDelete: (id: number) => void;
}

export const buildEmbarazosColumns = (deps: EmbarazosColumnsDeps) => {
  const {
    navigate, canChange, canDelete, dispatch, handleVerHistorial,
    handleOpenEdit, handleFinalizarEmbarazo, handleDelete,
  } = deps;

  return [
    {
      title: 'Paciente',
      key: 'paciente',
      width: 220,
      render: (_: any, r: EmbarazoExtendido) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <Avatar style={{ backgroundColor: '#f56a00' }} icon={userOutlinedIcon3} size="small">
            {r.paciente_nombre?.charAt(0)}
          </Avatar>
          <div>
            <Text strong style={{ display: 'block', lineHeight: 1.2 }}>{r.paciente_nombre || `Paciente #${r.paciente}`}</Text>
            <Text type="secondary" style={{ fontSize: 12 }}>Gesta: {r.numero_gesta}</Text>
          </div>
        </div>
      )
    },
    {
      title: 'Calendario Obstétrico',
      // Ordena el SERVIDOR por FPP (`?ordering=fecha_probable_parto`).
      dataIndex: 'fecha_probable_parto',
      key: 'fecha_probable_parto',
      sorter: true,
      width: 200,
      render: (_: any, r: EmbarazoExtendido) => (
        <div style={{ fontSize: 12 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: '#666' }}>FUM:</span>
            <Text strong>{dayjs(r.fecha_ultima_menstruacion).format('DD/MM/YY')}</Text>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: '#666' }}>FPP:</span>
            <Text type={r.fecha_probable_parto ? 'success' : 'secondary'}>
              {r.fecha_probable_parto ? dayjs(r.fecha_probable_parto).format('DD/MM/YY') : '?'}
            </Text>
          </div>
        </div>
      )
    },
    {
      title: 'Edad Gestacional (Progreso)',
      key: 'progreso',
      width: 220,
      render: (_: any, r: EmbarazoExtendido) => {
        const semanas = r.edad_gestacional_semanas_num || 0;
        const dias = r.edad_gestacional_dias_num || 0;
        const percent = Math.min((semanas / 40) * 100, 100);

        let progressColor = '#1890ff';
        if (semanas >= 37) progressColor = '#52c41a'; // A término
        else if (semanas >= 41) progressColor = '#faad14'; // Post-término

        return (
          <Tooltip title={`Trimestre ${r.trimestre_actual} • ${semanas} semanas`}>
            <div style={{ width: '100%' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 2 }}>
                <Text strong>{semanas}s + {dias}d</Text>
                <Text type="secondary">40s</Text>
              </div>
              <Progress
                percent={percent}
                showInfo={false}
                strokeColor={progressColor}
                size="small"
                trailColor="#f0f0f0"
              />
            </div>
          </Tooltip>
        );
      }
    },
    {
      title: 'Riesgo',
      dataIndex: 'riesgo_embarazo',
      width: 130,
      align: 'center' as 'center',
      render: (riesgo: string) => (
        <Tag
          color={(RISK_COLORS as any)[riesgo] || 'default'}
          style={{ width: '100%', textAlign: 'center', fontWeight: 600 }}
        >
          {(RISK_LABELS as any)[riesgo] || riesgo?.toUpperCase()}
        </Tag>
      )
    },
    {
      title: 'Estado',
      dataIndex: 'estado',
      width: 120,
      align: 'center' as 'center',
      render: (estado: string) => {
        const label = (STATUS_LABELS as any)[estado] || estado?.toUpperCase();
        const status = (STATUS_COLORS as any)[estado] || 'default';
        return <Badge status={status as any} text={label} />;
      }
    },
    {
      title: 'Acciones',
      key: 'actions',
      fixed: 'right' as const,
      width: 220,
      render: (_: any, r: EmbarazoExtendido) => (
        <Space size={4}>
          <Button
            type="primary"
            ghost
            shape="circle"
            icon={medicineBoxOutlinedIcon6}
            aria-label={`Ver controles e historia de ${r.paciente_nombre || 'la paciente'}`}
            title="Ver controles e historia"
            onClick={() => navigate(`/dashboard/pacientes/${r.paciente}/historia`)}
          />
          <Button
            shape="circle"
            icon={eyeOutlinedIcon4}
            aria-label="Detalle rápido del embarazo"
            title="Detalle rápido"
            onClick={() => { dispatch({ type: 'SET_SELECTED_EMBARAZO', payload: r }); dispatch({ type: 'SET_DRAWER_VISIBLE', payload: true }); }}
          />
          <Button
            shape="circle"
            icon={historyIcon3}
            aria-label="Historial completo del embarazo"
            title="Historial completo"
            onClick={() => handleVerHistorial(r)}
          />
          <Dropdown
            menu={{
              items: [
                // Editar - solo si tiene permiso
                ...(canChange('embarazo') ? [{
                  key: 'edit',
                  label: 'Editar',
                  icon: <EditOutlined />,
                  onClick: () => handleOpenEdit(r)
                }] : []),
                ...(canChange('embarazo') ? [{
                  key: 'finalizar',
                  label: 'Finalizar Embarazo',
                  icon: <StopOutlined />,
                  onClick: () => handleFinalizarEmbarazo(r),
                  disabled: r.estado !== 'activo'
                }] : []),
                // Separador solo si puede eliminar
                ...(canDelete('embarazo') ? [{
                  type: 'divider' as const
                }] : []),
                // Eliminar: `handleDelete` ya pide confirmación. Antes aquí se
                // abría OTRA confirmación antes (doble diálogo) que además
                // anunciaba borrar controles y partos, cuando el backend
                // rechaza borrar un embarazo que los tenga.
                ...(canDelete('embarazo') ? [{
                  key: 'delete',
                  label: 'Eliminar',
                  icon: <DeleteOutlined />,
                  danger: true,
                  onClick: () => handleDelete(r.id!)
                }] : [])
              ]
            }}
          >
            <Button icon={arrowRightOutlinedIcon} aria-label="Más acciones del embarazo" title="Más acciones" />
          </Dropdown>
        </Space>
      )
    }
  ];
};
