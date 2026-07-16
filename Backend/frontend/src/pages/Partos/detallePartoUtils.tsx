import React from 'react';
import { CheckCircleOutlined, ExclamationCircleOutlined, WarningOutlined } from '@ant-design/icons';

// ── Helpers puros (nivel de módulo: identidad estable entre renders) ─────────
export const handleImprimir = () => {
  window.print();
};

export const getViaPartoColor = (via: string) => {
  const colores: Record<string, string> = {
    vaginal_espontaneo: 'green',
    vaginal_instrumentado: 'blue',
    cesarea_electiva: 'orange',
    cesarea_urgencia: 'red',
    cesarea_emergencia: 'volcano',
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
    return { text: 'Bajo peso', color: 'orange' };
  } else if (peso >= 2500 && peso <= 4000) {
    return { text: 'Peso adecuado', color: 'green' };
  } else {
    return { text: 'Macrosomía', color: 'red' };
  }
};
