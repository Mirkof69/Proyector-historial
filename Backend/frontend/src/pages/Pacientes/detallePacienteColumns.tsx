import React from 'react';
import { Tag } from 'antd';
import dayjs from 'dayjs';

export const columnsEmbarazos = [
  {
    title: 'Gesta',
    dataIndex: 'numero_gesta',
    key: 'numero_gesta',
  },
  {
    title: 'FUM',
    dataIndex: 'fecha_ultima_menstruacion',
    key: 'fecha_ultima_menstruacion',
    render: (text: string) => text ? dayjs(text).format('DD/MM/YYYY') : '-',
  },
  {
    title: 'FPP',
    dataIndex: 'fecha_probable_parto',
    key: 'fecha_probable_parto',
    render: (text: string) => text ? dayjs(text).format('DD/MM/YYYY') : '-',
  },
  {
    title: 'Estado',
    dataIndex: 'estado',
    key: 'estado',
    render: (estado: string) => {
      let color = 'default';
      if (estado === 'activo') color = 'green';
      if (estado === 'finalizado') color = 'blue';
      return <Tag color={color}>{estado?.toUpperCase()}</Tag>;
    },
  },
  {
    title: 'Riesgo',
    dataIndex: 'riesgo_embarazo',
    key: 'riesgo_embarazo',
    render: (riesgo: string) => {
      let color = 'default';
      if (riesgo === 'alto') color = 'red';
      if (riesgo === 'medio') color = 'orange';
      if (riesgo === 'bajo') color = 'green';
      return <Tag color={color}>{riesgo ? riesgo.toUpperCase() : 'NO DEFINIDO'}</Tag>;
    },
  },
];

export const columnsTriajes = [
  {
    title: 'Fecha',
    dataIndex: 'fecha_hora',
    key: 'fecha',
    render: (text: string, record: any) => dayjs(text || record.fecha_registro).format('DD/MM/YYYY HH:mm'),
  },
  {
    title: 'Prioridad',
    dataIndex: 'prioridad',
    key: 'prioridad',
    render: (p: string) => {
      const colors: any = { urgente: 'red', alto: 'orange', normal: 'blue', bajo: 'green' };
      return <Tag color={colors[p] || 'default'}>{p?.toUpperCase()}</Tag>;
    },
  },
  {
    title: 'PA',
    render: (_: any, record: any) => `${record.presion_sistolica || '-'}/${record.presion_diastolica || '-'}`,
  },
  {
    title: 'FC',
    dataIndex: 'frecuencia_cardiaca',
    render: (fc: number) => `${fc} bpm`,
  },
  {
    title: 'Temp',
    dataIndex: 'temperatura',
    render: (t: number) => `${t}°C`,
  },
  {
    title: 'Estado',
    dataIndex: 'estado',
    render: (e: string) => <Tag color={e === 'completado' ? 'green' : 'orange'}>{e}</Tag>,
  },
];

export const columnsNotas = [
  {
    title: 'Fecha',
    dataIndex: 'fecha_consulta',
    render: (f: string) => dayjs(f).format('DD/MM/YYYY'),
  },
  {
    title: 'Tipo',
    dataIndex: 'tipo_consulta',
    render: (tipo: string) => {
      const labels: any = {
        control_prenatal: 'Control',
        urgencia: 'Urgencia',
        seguimiento: 'Seguimiento',
      };
      return <Tag>{labels[tipo] || tipo}</Tag>;
    },
  },
  {
    title: 'Motivo',
    dataIndex: 'motivo_consulta',
    render: (m: string) => m?.substring(0, 50) + '...',
  },
  {
    title: 'Médico',
    dataIndex: 'medico_nombre',
  },
];

export const columnsVacunas = [
  {
    title: 'Fecha',
    dataIndex: 'fecha_aplicacion',
    render: (f: string) => dayjs(f).format('DD/MM/YYYY'),
  },
  {
    title: 'Vacuna',
    dataIndex: 'tipo_vacuna_nombre',
    render: (_: any, record: any) => record.tipo_vacuna_nombre || record.tipo_vacuna_info?.nombre || '-',
  },
  {
    title: 'Dosis',
    dataIndex: 'numero_dosis',
    render: (n: number) => <Tag color="blue">{n}</Tag>,
  },
  {
    title: 'Lote',
    dataIndex: 'lote',
  },
  {
    title: 'Próxima Dosis',
    dataIndex: 'proxima_dosis_fecha',
    render: (f: string) => f ? dayjs(f).format('DD/MM/YYYY') : <Tag color="green">Completo</Tag>,
  },
];
