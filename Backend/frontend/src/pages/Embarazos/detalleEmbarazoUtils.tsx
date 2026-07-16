import React from 'react';
import {
  SoundOutlined, ExperimentOutlined, WarningOutlined,
  CheckCircleOutlined, InfoCircleOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';

export const tabEcografias = <span><SoundOutlined /> Ecografías</span>;
export const tabLaboratorio = <span><ExperimentOutlined /> Laboratorio</span>;

// ── Cálculos obstétricos y config (puros, nivel de módulo) ───────────────────
export const calcularSemanasGestacion = (fum: string) => {
  const hoy = dayjs();
  const fechaFum = dayjs(fum);
  const diasDiferencia = hoy.diff(fechaFum, 'day');
  const semanas = Math.floor(diasDiferencia / 7);
  const dias = diasDiferencia % 7;
  return { semanas, dias, texto: `${semanas} semanas + ${dias} días` };
};

export const calcularDiasRestantes = (fpp: string) => {
  const hoy = dayjs();
  const fechaFpp = dayjs(fpp);
  const diasRestantes = fechaFpp.diff(hoy, 'day');
  return diasRestantes > 0 ? diasRestantes : 0;
};

export const calcularProgreso = (fum: string) => {
  const hoy = dayjs();
  const fechaFum = dayjs(fum);
  const diasTranscurridos = hoy.diff(fechaFum, 'day');
  const progreso = Math.min((diasTranscurridos / 280) * 100, 100);
  return Math.round(progreso);
};

export const getTrimestre = (semanas: number) => {
  if (semanas < 13) return { numero: 1, texto: 'Primer Trimestre', color: 'cyan' };
  if (semanas < 28) return { numero: 2, texto: 'Segundo Trimestre', color: 'blue' };
  return { numero: 3, texto: 'Tercer Trimestre', color: 'purple' };
};

export const calcularIMCClasificacion = (imc: number) => {
  if (imc < 18.5) return { texto: 'Bajo peso', color: 'orange' };
  if (imc < 25) return { texto: 'Normal', color: 'green' };
  if (imc < 30) return { texto: 'Sobrepeso', color: 'orange' };
  return { texto: 'Obesidad', color: 'red' };
};

export const getEstadoConfig = (estado: string) => {
  const configs = {
    activo: { color: 'success', icon: <CheckCircleOutlined />, texto: 'ACTIVO' },
    finalizado: { color: 'default', icon: <InfoCircleOutlined />, texto: 'FINALIZADO' },
    perdida: { color: 'error', icon: <WarningOutlined />, texto: 'PÉRDIDA' },
  };
  return configs[estado as keyof typeof configs] || configs.activo;
};

export const getRiesgoConfig = (riesgo: string) => {
  const configs = {
    bajo: { color: 'success', texto: 'BAJO RIESGO' },
    medio: { color: 'warning', texto: 'RIESGO MEDIO' },
    alto: { color: 'error', texto: 'ALTO RIESGO' },
  };
  return configs[riesgo as keyof typeof configs] || configs.bajo;
};
