import React from 'react';
import { CheckCircleOutlined, ExclamationCircleOutlined, WarningOutlined } from '@ant-design/icons';

// ── Helpers puros (nivel de módulo: identidad estable entre renders) ─────────
export const handleImprimir = () => {
  window.print();
};

export const getViaPartoColor = (via: string) => {
  const colores: Record<string, string> = {
    // Solo la urgencia es un estado; la vía en sí va en neutro.
    cesarea_urgencia: 'warning',
    cesarea_emergencia: 'error',
  };
  return colores[via] || 'default';
};

export const getApgarInterpretacion = (apgar: number) => {
  if (apgar >= 7) {
    return { text: 'Normal', color: 'success', icon: <CheckCircleOutlined /> };
  } else if (apgar >= 4) {
    return { text: 'Depresión moderada', color: 'warning', icon: <ExclamationCircleOutlined /> };
  } else {
    return { text: 'Depresión severa', color: 'error', icon: <WarningOutlined /> };
  }
};

export const getClasificacionPeso = (peso: number) => {
  if (peso < 2500) {
    return { text: 'Bajo peso', color: 'warning' };
  } else if (peso >= 2500 && peso <= 4000) {
    return { text: 'Peso adecuado', color: 'success' };
  } else {
    return { text: 'Macrosomía', color: 'error' };
  }
};
