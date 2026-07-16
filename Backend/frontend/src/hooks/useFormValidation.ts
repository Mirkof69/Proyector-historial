/**
 * Hook de Validaciones de Formularios
 * Validaciones del lado del cliente antes de enviar al backend
 *
 * Las funciones de validación son puras (no dependen de estado/props/hooks),
 * por lo que viven a nivel de módulo: así mantienen una identidad estable entre
 * renders. Los hooks quedan como wrappers finos que preservan la API existente
 * (`const { validateEmbarazo } = useEmbarazoValidation()`).
 */

// ── Validación de embarazo ───────────────────────────────────────────────────
const validateEmbarazo = (values: any) => {
  const errors: any = {};

  // ✅ 1. FUM no puede estar en el futuro
  if (values.fecha_ultima_menstruacion) {
    const fum = new Date(values.fecha_ultima_menstruacion);
    const hoy = new Date();
    hoy.setHours(0, 0, 0, 0);

    if (fum > hoy) {
      errors.fecha_ultima_menstruacion = 'La FUM no puede estar en el futuro';
    }

    // ✅ 2. FUM no puede ser mayor a 1 año atrás
    const haceUnAnio = new Date();
    haceUnAnio.setFullYear(haceUnAnio.getFullYear() - 1);

    if (fum < haceUnAnio) {
      errors.fecha_ultima_menstruacion = 'La FUM no puede ser mayor a 1 año atrás';
    }
  }

  // ✅ 3. Número de partos no puede ser mayor que gestas
  if (values.numero_para !== undefined && values.numero_gesta !== undefined) {
    if (values.numero_para > values.numero_gesta) {
      errors.numero_para = 'Los partos no pueden superar las gestas';
    }
  }

  // ✅ 4. Validar fórmula obstétrica: G >= P + Abortos + 1 (embarazo actual)
  if (
    values.numero_gesta !== undefined &&
    values.numero_para !== undefined &&
    values.numero_abortos !== undefined
  ) {
    const totalEsperado = values.numero_para + values.numero_abortos + 1;
    if (values.numero_gesta < totalEsperado - 1) {
      errors.numero_gesta = `Las gestas deben ser al menos ${totalEsperado - 1} (Partos: ${values.numero_para} + Abortos: ${values.numero_abortos})`;
    }
  }

  // ✅ 5. Peso pregestacional razonable
  if (values.peso_pregestacional !== undefined && values.peso_pregestacional !== null) {
    if (values.peso_pregestacional < 30) {
      errors.peso_pregestacional = 'El peso parece muy bajo (mínimo 30 kg)';
    }
    if (values.peso_pregestacional > 200) {
      errors.peso_pregestacional = 'El peso parece muy alto (máximo 200 kg)';
    }
  }

  // ✅ 6. Talla materna razonable
  if (values.talla_materna !== undefined && values.talla_materna !== null) {
    if (values.talla_materna < 100) {
      errors.talla_materna = 'La talla parece muy baja (mínimo 100 cm)';
    }
    if (values.talla_materna > 230) {
      errors.talla_materna = 'La talla parece muy alta (máximo 230 cm)';
    }
  }

  // ✅ 7. Número de cesáreas no puede ser mayor que partos
  if (values.numero_cesareas !== undefined && values.numero_para !== undefined) {
    if (values.numero_cesareas > values.numero_para) {
      errors.numero_cesareas = 'Las cesáreas no pueden superar los partos';
    }
  }

  return errors;
};

export const useEmbarazoValidation = () => {
  return { validateEmbarazo };
};

// ── Validación de control prenatal ───────────────────────────────────────────
const validateControl = (values: any) => {
  const errors: any = {};

  // ✅ 1. Presión arterial en rangos
  if (values.presion_arterial_sistolica !== undefined) {
    if (values.presion_arterial_sistolica < 70 || values.presion_arterial_sistolica > 200) {
      errors.presion_arterial_sistolica = 'Presión sistólica fuera de rango (70-200 mmHg)';
    }
  }

  if (values.presion_arterial_diastolica !== undefined) {
    if (values.presion_arterial_diastolica < 40 || values.presion_arterial_diastolica > 120) {
      errors.presion_arterial_diastolica = 'Presión diastólica fuera de rango (40-120 mmHg)';
    }
  }

  // ✅ 2. La sistólica debe ser mayor que la diastólica
  if (
    values.presion_arterial_sistolica !== undefined &&
    values.presion_arterial_diastolica !== undefined
  ) {
    if (values.presion_arterial_sistolica <= values.presion_arterial_diastolica) {
      errors.presion_arterial_sistolica = 'La sistólica debe ser mayor que la diastólica';
    }
  }

  // ✅ 3. FCF en rango (110-160 lpm)
  if (values.frecuencia_cardiaca_fetal !== undefined && values.frecuencia_cardiaca_fetal !== null) {
    if (values.frecuencia_cardiaca_fetal < 110 || values.frecuencia_cardiaca_fetal > 160) {
      errors.frecuencia_cardiaca_fetal = 'FCF fuera de rango normal (110-160 lpm)';
    }
  }

  // ✅ 4. Edad gestacional válida (0-42 semanas)
  if (values.edad_gestacional_semanas !== undefined) {
    if (values.edad_gestacional_semanas < 0 || values.edad_gestacional_semanas > 42) {
      errors.edad_gestacional_semanas = 'Edad gestacional fuera de rango (0-42 semanas)';
    }
  }

  if (values.edad_gestacional_dias !== undefined) {
    if (values.edad_gestacional_dias < 0 || values.edad_gestacional_dias > 6) {
      errors.edad_gestacional_dias = 'Días deben estar entre 0 y 6';
    }
  }

  // ✅ 5. Temperatura en rango (35-42°C)
  if (values.temperatura !== undefined && values.temperatura !== null) {
    if (values.temperatura < 35 || values.temperatura > 42) {
      errors.temperatura = 'Temperatura fuera de rango (35-42°C)';
    }
  }

  // ✅ 6. Frecuencia cardíaca materna (40-200 lpm)
  if (values.frecuencia_cardiaca !== undefined && values.frecuencia_cardiaca !== null) {
    if (values.frecuencia_cardiaca < 40 || values.frecuencia_cardiaca > 200) {
      errors.frecuencia_cardiaca = 'Frecuencia cardíaca fuera de rango (40-200 lpm)';
    }
  }

  // ✅ 7. Saturación de oxígeno (70-100%)
  if (values.saturacion_oxigeno !== undefined && values.saturacion_oxigeno !== null) {
    if (values.saturacion_oxigeno < 70 || values.saturacion_oxigeno > 100) {
      errors.saturacion_oxigeno = 'Saturación fuera de rango (70-100%)';
    }
  }

  // ✅ 8. Peso actual razonable
  if (values.peso_actual !== undefined && values.peso_actual !== null) {
    if (values.peso_actual < 30 || values.peso_actual > 200) {
      errors.peso_actual = 'Peso fuera de rango (30-200 kg)';
    }
  }

  // ✅ 9. Altura uterina razonable (debe aproximarse a semanas de gestación ±2cm)
  if (
    values.altura_uterina !== undefined &&
    values.altura_uterina !== null &&
    values.edad_gestacional_semanas !== undefined
  ) {
    const diferencia = Math.abs(values.altura_uterina - values.edad_gestacional_semanas);
    if (diferencia > 4) {
      errors.altura_uterina = `Altura uterina muy diferente a edad gestacional (diferencia: ${diferencia}cm)`;
    }
  }

  return errors;
};

const useControlValidation = () => {
  return { validateControl };
};

// ── Validación de parto ──────────────────────────────────────────────────────
const validateParto = (values: any) => {
  const errors: any = {};

  // ✅ 1. APGAR entre 0-10
  if (values.apgar_1min !== undefined && values.apgar_1min !== null) {
    if (values.apgar_1min < 0 || values.apgar_1min > 10) {
      errors.apgar_1min = 'APGAR al minuto debe estar entre 0 y 10';
    }
  }

  if (values.apgar_5min !== undefined && values.apgar_5min !== null) {
    if (values.apgar_5min < 0 || values.apgar_5min > 10) {
      errors.apgar_5min = 'APGAR a los 5 minutos debe estar entre 0 y 10';
    }
  }

  // ✅ 2. Pérdida sanguínea razonable (0-2000ml normal, >2000 hemorragia)
  if (values.perdida_sanguinea_estimada !== undefined && values.perdida_sanguinea_estimada !== null) {
    if (values.perdida_sanguinea_estimada < 0) {
      errors.perdida_sanguinea_estimada = 'La pérdida sanguínea no puede ser negativa';
    }
    if (values.perdida_sanguinea_estimada > 5000) {
      errors.perdida_sanguinea_estimada = 'Pérdida sanguínea muy alta (verificar valor)';
    }
    if (values.perdida_sanguinea_estimada > 2000) {
      // Advertencia, no error
      console.warn('Pérdida sanguínea >2000ml - Posible hemorragia postparto');
    }
  }

  // ✅ 3. Peso del recién nacido razonable (500g-6000g)
  if (values.peso_recien_nacido !== undefined && values.peso_recien_nacido !== null) {
    if (values.peso_recien_nacido < 500) {
      errors.peso_recien_nacido = 'Peso muy bajo (mínimo 500g)';
    }
    if (values.peso_recien_nacido > 6000) {
      errors.peso_recien_nacido = 'Peso muy alto (máximo 6000g)';
    }
  }

  // ✅ 4. Talla del recién nacido razonable (30-60cm)
  if (values.talla_recien_nacido !== undefined && values.talla_recien_nacido !== null) {
    if (values.talla_recien_nacido < 30 || values.talla_recien_nacido > 60) {
      errors.talla_recien_nacido = 'Talla fuera de rango (30-60 cm)';
    }
  }

  // ✅ 5. Perímetro cefálico razonable (25-40cm)
  if (values.perimetro_cefalico !== undefined && values.perimetro_cefalico !== null) {
    if (values.perimetro_cefalico < 25 || values.perimetro_cefalico > 40) {
      errors.perimetro_cefalico = 'Perímetro cefálico fuera de rango (25-40 cm)';
    }
  }

  // ✅ 6. Duración de trabajo de parto razonable (0-48 horas)
  if (values.duracion_trabajo_parto !== undefined && values.duracion_trabajo_parto !== null) {
    if (values.duracion_trabajo_parto < 0) {
      errors.duracion_trabajo_parto = 'La duración no puede ser negativa';
    }
    if (values.duracion_trabajo_parto > 48) {
      errors.duracion_trabajo_parto = 'Duración muy prolongada (verificar valor)';
    }
  }

  // ✅ 7. Edad gestacional válida
  if (values.edad_gestacional !== undefined && values.edad_gestacional !== null) {
    const match = String(values.edad_gestacional).match(/^(\d+)\+?(\d?)$/);
    if (!match) {
      errors.edad_gestacional = 'Formato inválido (usar: 39 o 39+2)';
    } else {
      const semanas = parseInt(match[1]);
      const dias = match[2] ? parseInt(match[2]) : 0;

      if (semanas < 20 || semanas > 45) {
        errors.edad_gestacional = 'Semanas fuera de rango (20-45)';
      }
      if (dias > 6) {
        errors.edad_gestacional = 'Días deben estar entre 0 y 6';
      }
    }
  }

  // ✅ 8. Fecha de parto no en el futuro
  if (values.fecha_parto) {
    const fechaParto = new Date(values.fecha_parto);
    const hoy = new Date();
    hoy.setHours(23, 59, 59, 999);

    if (fechaParto > hoy) {
      errors.fecha_parto = 'La fecha de parto no puede estar en el futuro';
    }
  }

  return errors;
};

const usePartoValidation = () => {
  return { validateParto };
};

// ── Validaciones generales reutilizables ─────────────────────────────────────
const validateEmail = (email: string): boolean => {
  const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return regex.test(email);
};

const validatePhone = (phone: string): boolean => {
  const regex = /^[+]?[\d\s()-]{7,}$/;
  return regex.test(phone);
};

const validateCI = (ci: string): boolean => {
  // Validación básica de CI boliviano
  const regex = /^[\d]{5,10}[\s]?[A-Z]{2,3}$/;
  return regex.test(ci);
};

const validateDate = (date: string): boolean => {
  const parsedDate = new Date(date);
  return parsedDate instanceof Date && !isNaN(parsedDate.getTime());
};

const validateDateNotFuture = (date: string): boolean => {
  const parsedDate = new Date(date);
  const today = new Date();
  today.setHours(23, 59, 59, 999);
  return parsedDate <= today;
};

const validateDateNotPast = (date: string, yearsAgo: number = 1): boolean => {
  const parsedDate = new Date(date);
  const limitDate = new Date();
  limitDate.setFullYear(limitDate.getFullYear() - yearsAgo);
  return parsedDate >= limitDate;
};

const useGeneralValidation = () => {
  return {
    validateEmail,
    validatePhone,
    validateCI,
    validateDate,
    validateDateNotFuture,
    validateDateNotPast,
  };
};

// Se re-exportan para que sigan disponibles aunque hoy solo se use el hook de
// embarazo; evita que queden como declaraciones muertas.
export { useControlValidation, usePartoValidation, useGeneralValidation };
