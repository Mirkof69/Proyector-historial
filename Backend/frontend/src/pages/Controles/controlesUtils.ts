import dayjs from 'dayjs';

// ========== DETECCIÓN DE ALERTAS MÉDICAS ==========
export const detectarAlertas = (values: any): string[] => {
  const alertasDetectadas: string[] = [];

  // ALERTA: Hipertensión arterial (≥140/90)
  if (values.presion_arterial_sistolica && values.presion_arterial_diastolica) {
    if (values.presion_arterial_sistolica >= 140 || values.presion_arterial_diastolica >= 90) {
      alertasDetectadas.push('🔴 HIPERTENSIÓN ARTERIAL - Riesgo de preeclampsia');
    } else if (
      values.presion_arterial_sistolica >= 120 ||
      values.presion_arterial_diastolica >= 80
    ) {
      alertasDetectadas.push('⚠️ PREHIPERTENSIÓN - Monitoreo estrecho requerido');
    } else if (
      values.presion_arterial_sistolica < 90 ||
      values.presion_arterial_diastolica < 60
    ) {
      alertasDetectadas.push('⚠️ HIPOTENSIÓN ARTERIAL - Evaluar hidratación');
    }
  }

  // ALERTA: Frecuencia cardíaca fetal anormal (<110 o >160)
  if (values.frecuencia_cardiaca_fetal) {
    if (values.frecuencia_cardiaca_fetal < 110) {
      alertasDetectadas.push('🚨 BRADICARDIA FETAL (<110 lpm) - URGENTE: NST inmediato');
    } else if (values.frecuencia_cardiaca_fetal > 160) {
      alertasDetectadas.push('🔴 TAQUICARDIA FETAL (>160 lpm) - Evaluar bienestar fetal');
    } else if (
      values.frecuencia_cardiaca_fetal < 120 ||
      values.frecuencia_cardiaca_fetal > 150
    ) {
      alertasDetectadas.push('⚠️ FCF en límite de normalidad - Monitoreo continuo');
    }
  }

  // ALERTA: Edema severo/generalizado
  if (values.edema === 'severo' || values.edema === 'generalizado') {
    alertasDetectadas.push('⚠️ EDEMA SEVERO/GENERALIZADO - Evaluar preeclampsia');
  }

  // ALERTA: Proteinuria positiva
  if (values.proteinuria && !['negativa', 'trazas'].includes(values.proteinuria)) {
    const nivelProteinuria = values.proteinuria.includes('4')
      ? 'CRÍTICA (++++)'
      : values.proteinuria.includes('3')
        ? 'SEVERA (+++)'
        : values.proteinuria.includes('2')
          ? 'MODERADA (++)'
          : 'LEVE (+)';
    alertasDetectadas.push(
      `⚠️ PROTEINURIA ${nivelProteinuria} - Descartar preeclampsia/síndrome nefrítico`
    );
  }

  // ALERTA: Movimientos fetales ausentes o disminuidos
  if (values.movimientos_fetales === 'ausentes') {
    alertasDetectadas.push('🚨 MOVIMIENTOS FETALES AUSENTES - EMERGENCIA: Evaluación inmediata');
  } else if (values.movimientos_fetales === 'disminuidos') {
    alertasDetectadas.push('⚠️ MOVIMIENTOS FETALES DISMINUIDOS - NST en 24 horas');
  }

  // ALERTA: Temperatura elevada (≥38°C)
  if (values.temperatura && values.temperatura >= 38) {
    alertasDetectadas.push(
      '⚠️ FIEBRE MATERNA (≥38°C) - Descartar infección. Hemograma y hemocultivo'
    );
  } else if (values.temperatura && values.temperatura >= 37.5) {
    alertasDetectadas.push('⚠️ FEBRÍCULA (≥37.5°C) - Monitoreo de temperatura cada 4 horas');
  }

  // ALERTA: Frecuencia cardíaca materna anormal
  if (values.frecuencia_cardiaca) {
    if (values.frecuencia_cardiaca > 100) {
      alertasDetectadas.push('⚠️ TAQUICARDIA MATERNA (>100 lpm) - Evaluar causas');
    } else if (values.frecuencia_cardiaca < 60) {
      alertasDetectadas.push('⚠️ BRADICARDIA MATERNA (<60 lpm) - Evaluar medicación');
    }
  }

  // ALERTA: Ganancia de peso excesiva
  if (values.peso_actual && values.peso_pregestacional) {
    const ganancia = values.peso_actual - values.peso_pregestacional;
    const semanas = values.edad_gestacional_semanas || 0;
    if (semanas > 12) {
      const gananciaEsperadaMax = semanas < 28 ? 0.5 * (semanas - 12) : 18;
      if (ganancia > gananciaEsperadaMax) {
        alertasDetectadas.push('⚠️ GANANCIA DE PESO EXCESIVA - Evaluar dieta y retención');
      }
    }
  }

  // ALERTA: Altura uterina discordante
  if (values.altura_uterina && values.edad_gestacional_semanas && values.edad_gestacional_semanas >= 20) {
    const esperada = values.edad_gestacional_semanas;
    const diferencia = Math.abs(values.altura_uterina - esperada);
    if (diferencia > 3) {
      if (values.altura_uterina < esperada - 3) {
        alertasDetectadas.push('⚠️ ALTURA UTERINA BAJA - Descartar RCIU o oligohidramnios');
      } else {
        alertasDetectadas.push(
          '⚠️ ALTURA UTERINA ELEVADA - Descartar macrosomía o polihidramnios'
        );
      }
    }
  }

  // ✅ FIX: Ya NO llama a setAlertasPreview aquí (evita loop infinito)
  // setAlertasPreview se llama solo en event handlers (handleQuickView)
  return alertasDetectadas;
};

// ========== CALCULAR EDAD GESTACIONAL DESDE FUM ==========
export const calcularEdadGestacional = (fum: string) => {
  const hoy = dayjs();
  const fechaFum = dayjs(fum);
  const diasDiferencia = hoy.diff(fechaFum, 'day');
  const semanas = Math.floor(diasDiferencia / 7);
  const dias = diasDiferencia % 7;
  return { semanas, dias };
};

// ========== CÁLCULO DE IMC MATERNO ==========
export const calcularIMC = (peso: number | null | undefined, talla: number | null | undefined): number | null => {
  if (!peso || !talla) return null;
  const tallaMts = talla / 100;
  return peso / (tallaMts * tallaMts);
};

// ========== CLASIFICACIÓN DE IMC ==========
export const clasificarIMC = (imc: number | null): { texto: string; color: string } => {
  if (!imc) return { texto: '-', color: 'default' };
  if (imc < 18.5) return { texto: 'Bajo peso', color: 'warning' };
  if (imc < 25) return { texto: 'Normal', color: 'success' };
  if (imc < 30) return { texto: 'Sobrepeso', color: 'warning' };
  return { texto: 'Obesidad', color: 'error' };
};
