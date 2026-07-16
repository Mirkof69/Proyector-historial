import React, { useState } from 'react';
import { Card, Form, Alert, Tag } from 'antd';
import { HeartOutlined } from '@ant-design/icons';
import './SufrimientoFetal.css';
import { FormularioBienestarFetal } from './components/FormularioBienestarFetal';
import { ResultadosBienestarFetal } from './components/ResultadosBienestarFetal';

// ============================================
// INTERFACES Y TIPOS
// ============================================

interface DatosSufrimiento {
  // CTG (Cardiotocografía)
  fcf_basal: number;
  variabilidad_fcf: number;
  aceleraciones_20min: number;
  desaceleraciones_tipo: 'ninguna' | 'tempranas' | 'variables' | 'tardias';
  contracciones_10min: number;

  // Perfil Biofísico (Manning)
  nst_reactivo: boolean;
  movimientos_respiratorios: boolean;
  movimientos_corporales: boolean;
  tono_fetal: boolean;
  volumen_liquido: number; // AFI en cm

  // Doppler
  arteria_umbilical_pi: number;
  arteria_umbilical_ri: number;
  arteria_cerebral_media_pi: number;
  ductus_venoso_normal: boolean;

  // Complementarios
  edad_gestacional: number;
  oligohidramnios: boolean;
  peso_estimado_percentil: number;
}

interface ResultadoSufrimiento {
  // CTG
  ctg_categoria: string;
  ctg_interpretacion: string;
  ctg_color: string;

  // BPP
  bpp_score: number;
  bpp_interpretacion: string;
  bpp_color: string;
  bpp_componentes: {
    nst: number;
    respiracion: number;
    movimientos: number;
    tono: number;
    liquido: number;
  };

  // Doppler
  relacion_cp: number; // Cerebro-Placentaria
  doppler_interpretacion: string;
  doppler_anormal: boolean;

  // Clasificación general
  nivel_riesgo: string;
  color_riesgo: string;
  recomendaciones: string[];
  accion_inmediata: string;

  interpretacion: string;
}

interface RegistroSufrimiento {
  fecha: string;
  bpp_score: number;
  ctg_categoria: string;
  nivel_riesgo: string;
}

// ============================================
// FUNCIONES DE CÁLCULO
// ============================================

const evaluarCTG = (datos: DatosSufrimiento): { categoria: string; interpretacion: string; color: string } => {
  // ACOG Classification (2008)

  // Criterios para Categoría I (Normal - Reassuring)
  const criterios_cat1 =
    datos.fcf_basal >= 110 && datos.fcf_basal <= 160 &&
    datos.variabilidad_fcf >= 6 && datos.variabilidad_fcf <= 25 &&
    datos.desaceleraciones_tipo === 'ninguna' &&
    (datos.aceleraciones_20min >= 2 || datos.edad_gestacional < 32);

  if (criterios_cat1) {
    return {
      categoria: 'Categoría I - Normal',
      interpretacion: 'CTG normal. Predice fuertemente ausencia de acidemia fetal. Continuar vigilancia rutinaria.',
      color: '#52c41a'
    };
  }

  // Criterios para Categoría III (Anormal - Abnormal)
  const bradicardia_persistente = datos.fcf_basal < 110;
  const variabilidad_ausente = datos.variabilidad_fcf < 5;
  const desaceleraciones_tardias_recurrentes = datos.desaceleraciones_tipo === 'tardias';
  const desaceleraciones_variables_severas = datos.desaceleraciones_tipo === 'variables' && datos.variabilidad_fcf < 5;

  const criterios_cat3 =
    variabilidad_ausente && (bradicardia_persistente || desaceleraciones_tardias_recurrentes || desaceleraciones_variables_severas);

  if (criterios_cat3) {
    return {
      categoria: 'Categoría III - Anormal',
      interpretacion: '🚨 CTG ANORMAL. Alta probabilidad de acidemia fetal. Requiere ACCIÓN INMEDIATA: reanimación intrauterina, preparación para parto urgente.',
      color: '#ff4d4f'
    };
  }

  // Todo lo demás es Categoría II (Indeterminado - Indeterminate)
  let interpretacion_cat2 = 'CTG indeterminado. No cumple criterios Categoría I ni III. ';

  if (datos.fcf_basal < 110 || datos.fcf_basal > 160) {
    interpretacion_cat2 += 'Taquicardia/Bradicardia presente. ';
  }
  if (datos.variabilidad_fcf < 6) {
    interpretacion_cat2 += 'Variabilidad mínima/ausente. ';
  }
  if (datos.variabilidad_fcf > 25) {
    interpretacion_cat2 += 'Variabilidad marcada. ';
  }
  if (datos.desaceleraciones_tipo === 'variables') {
    interpretacion_cat2 += 'Desaceleraciones variables presentes. ';
  }

  interpretacion_cat2 += 'Requiere vigilancia estrecha, evaluar contexto clínico, considerar medidas de reanimación y reevaluación en 30-60 min.';

  return {
    categoria: 'Categoría II - Indeterminado',
    interpretacion: interpretacion_cat2,
    color: '#faad14'
  };
};

const calcularBPP = (datos: DatosSufrimiento) => {
  // Perfil Biofísico de Manning (0-10 puntos)
  // Cada componente: 2 puntos si normal, 0 si anormal

  const nst = datos.nst_reactivo ? 2 : 0;
  const respiracion = datos.movimientos_respiratorios ? 2 : 0;
  const movimientos = datos.movimientos_corporales ? 2 : 0;
  const tono = datos.tono_fetal ? 2 : 0;
  const liquido = datos.volumen_liquido >= 5 ? 2 : 0; // AFI ≥5 cm

  const score = nst + respiracion + movimientos + tono + liquido;

  let interpretacion = '';
  let color = '';

  if (score >= 8) {
    interpretacion = 'Normal. Riesgo bajo de asfixia perinatal. Continuar vigilancia según protocolo.';
    color = '#52c41a';
  } else if (score === 6) {
    interpretacion = 'Equívoco/Sospechoso. Riesgo moderado. Repetir en 24 horas, considerar maduración pulmonar si <34 semanas.';
    color = '#faad14';
  } else if (score === 4) {
    interpretacion = 'Anormal. Alto riesgo de asfixia. Considerar finalización del embarazo si ≥36 semanas. Maduración + vigilancia estrecha si <36 semanas.';
    color = '#ff7875';
  } else {
    interpretacion = '🚨 Anormal Severo. Muy alto riesgo de asfixia perinatal. Considerar FINALIZACIÓN INMEDIATA independiente de edad gestacional.';
    color = '#ff4d4f';
  }

  return {
    score,
    interpretacion,
    color,
    componentes: {
      nst,
      respiracion,
      movimientos,
      tono,
      liquido
    }
  };
};

const evaluarDoppler = (datos: DatosSufrimiento) => {
  // Arteria Umbilical (AU): PI normal <1.4 a término, RI normal <0.7
  // Arteria Cerebral Media (ACM): PI normal >1.0
  // Relación Cerebro-Placentaria (CPR): ACM PI / AU PI, normal >1.0

  const au_pi_anormal = datos.arteria_umbilical_pi > 1.4;
  const au_ri_anormal = datos.arteria_umbilical_ri > 0.7;
  const acm_pi_bajo = datos.arteria_cerebral_media_pi < 1.0; // Centralización
  const dv_anormal = !datos.ductus_venoso_normal;

  const relacion_cp = datos.arteria_cerebral_media_pi / datos.arteria_umbilical_pi;
  const relacion_cp_anormal = relacion_cp < 1.0;

  const doppler_anormal = au_pi_anormal || au_ri_anormal || acm_pi_bajo || relacion_cp_anormal || dv_anormal;

  let interpretacion = '';

  if (!doppler_anormal) {
    interpretacion = '✅ Doppler normal. Perfusión placentaria adecuada. No signos de centralización hemodinámica fetal.';
  } else {
    interpretacion = '⚠️ Doppler anormal detectado: ';
    const hallazgos: string[] = [];

    if (au_pi_anormal || au_ri_anormal) {
      hallazgos.push('Aumento de resistencia en arteria umbilical (insuficiencia placentaria)');
    }
    if (acm_pi_bajo) {
      hallazgos.push('Vasodilatación cerebral (centralización - signo de hipoxemia fetal)');
    }
    if (relacion_cp_anormal) {
      hallazgos.push(`Relación cerebro-placentaria anormal (${relacion_cp.toFixed(2)} <1.0) - Redistribución hemodinámica`);
    }
    if (dv_anormal) {
      hallazgos.push('Ductus venoso anormal (signo tardío de compromiso grave)');
    }

    interpretacion += hallazgos.join('; ') + '. Requiere vigilancia estrecha y considerar finalización según edad gestacional.';
  }

  return {
    relacion_cp,
    interpretacion,
    doppler_anormal
  };
};

const calcularSufrimiento = (datos: DatosSufrimiento): ResultadoSufrimiento => {
  // Evaluar CTG
  const ctg = evaluarCTG(datos);

  // Calcular BPP
  const bpp = calcularBPP(datos);

  // Evaluar Doppler
  const doppler = evaluarDoppler(datos);

  // Determinar nivel de riesgo global
  let nivel_riesgo = 'Bajo';
  let color_riesgo = '#52c41a';
  let accion_inmediata = '';

  // Clasificación por riesgo
  if (ctg.categoria.includes('III') || bpp.score <= 2 || (doppler.doppler_anormal && !datos.ductus_venoso_normal)) {
    nivel_riesgo = 'MUY ALTO - CRÍTICO';
    color_riesgo = '#ff4d4f';
    accion_inmediata = '🚨 ACCIÓN INMEDIATA REQUERIDA';
  } else if (ctg.categoria.includes('II') || bpp.score <= 4 || doppler.doppler_anormal) {
    nivel_riesgo = 'ALTO';
    color_riesgo = '#ff7875';
    accion_inmediata = 'Vigilancia estrecha y preparación para intervención';
  } else if (bpp.score === 6) {
    nivel_riesgo = 'MODERADO';
    color_riesgo = '#faad14';
    accion_inmediata = 'Repetir evaluación en 24 horas';
  } else {
    nivel_riesgo = 'Bajo';
    color_riesgo = '#52c41a';
    accion_inmediata = 'Continuar vigilancia rutinaria';
  }

  // Generar recomendaciones
  const recomendaciones: string[] = [];

  // Recomendaciones según CTG
  if (ctg.categoria.includes('III')) {
    recomendaciones.push('🚨 CTG Cat III: Reanimación intrauterina (O₂ materno, decúbito lateral, suspender oxitocina)');
    recomendaciones.push('🚨 Preparar para PARTO URGENTE (cesárea de emergencia vs parto vaginal operatorio)');
    recomendaciones.push('🚨 Notificar a Pediatría/Neonatología - Preparar reanimación neonatal');
  } else if (ctg.categoria.includes('II')) {
    recomendaciones.push('⚠️ CTG Cat II: Medidas de reanimación intrauterina');
    recomendaciones.push('⚠️ Cambio de posición materna, hidratación IV, amnioinfusión si variables recurrentes');
    recomendaciones.push('⚠️ Reevaluar en 30-60 min, considerar muestra de sangre fetal si disponible');
  } else {
    recomendaciones.push('✅ CTG Cat I: Continuar monitorización según protocolo institucional');
  }

  // Recomendaciones según BPP
  if (bpp.score <= 2) {
    recomendaciones.push('🚨 BPP ≤2: Finalizar embarazo INMEDIATAMENTE independiente de EG');
  } else if (bpp.score === 4) {
    if (datos.edad_gestacional >= 36) {
      recomendaciones.push('⚠️ BPP 4 + ≥36 sem: Considerar finalización del embarazo');
    } else {
      recomendaciones.push('⚠️ BPP 4 + <36 sem: Maduración pulmonar + vigilancia estrecha cada 12-24h');
    }
  } else if (bpp.score === 6) {
    recomendaciones.push('⚠️ BPP 6: Repetir en 24 horas, considerar maduración si <34 semanas');
  } else {
    recomendaciones.push('✅ BPP ≥8: Repetir semanalmente (o más frecuente si factores de riesgo)');
  }

  // Recomendaciones según Doppler
  if (!datos.ductus_venoso_normal) {
    recomendaciones.push('🚨 Ductus Venoso anormal: Signo de acidemia inminente - Considerar finalización urgente');
  } else if (doppler.relacion_cp < 1.0) {
    recomendaciones.push('⚠️ Centralización fetal: Aumentar frecuencia de vigilancia a 2-3x/semana');
    if (datos.edad_gestacional >= 37) {
      recomendaciones.push('⚠️ Centralización a término: Considerar finalización electiva');
    }
  } else if (datos.arteria_umbilical_pi > 1.4) {
    recomendaciones.push('⚠️ Resistencia placentaria aumentada: Vigilancia Doppler 2x/semana');
  }

  // Recomendaciones según oligohidramnios
  if (datos.oligohidramnios || datos.volumen_liquido < 5) {
    recomendaciones.push('⚠️ Oligohidramnios: Descartar ruptura de membranas, considerar amnioinfusión terapéutica');
    if (datos.edad_gestacional >= 37) {
      recomendaciones.push('⚠️ Oligohidramnios a término: Considerar inducción del trabajo de parto');
    }
  }

  // Recomendaciones según RCIU
  if (datos.peso_estimado_percentil < 10) {
    recomendaciones.push('⚠️ Peso <p10 (RCIU sospechado): Vigilancia intensificada, evaluación de bienestar fetal 2-3x/semana');
  }

  // Consideraciones por edad gestacional
  if (datos.edad_gestacional < 24) {
    recomendaciones.push('📅 <24 semanas: Valoración individualizada según viabilidad y deseos parentales');
  } else if (datos.edad_gestacional < 34) {
    if (nivel_riesgo === 'MUY ALTO - CRÍTICO') {
      recomendaciones.push('📅 <34 sem: Maduración pulmonar + preparar finalización, sopesar riesgos prematuridad vs hipoxia');
    }
  } else if (datos.edad_gestacional >= 37) {
    if (nivel_riesgo === 'ALTO' || nivel_riesgo === 'MUY ALTO - CRÍTICO') {
      recomendaciones.push('📅 ≥37 semanas + Alto riesgo: Bajo umbral para finalización del embarazo');
    }
  }

  // Interpretación global
  let interpretacion = `Evaluación de bienestar fetal a las ${datos.edad_gestacional} semanas:\n\n`;
  interpretacion += `CTG: ${ctg.categoria}. ${ctg.interpretacion}\n\n`;
  interpretacion += `Perfil Biofísico: ${bpp.score}/10 puntos. ${bpp.interpretacion}\n\n`;
  interpretacion += `Doppler: ${doppler.interpretacion}\n\n`;
  interpretacion += `NIVEL DE RIESGO GLOBAL: ${nivel_riesgo}.\n\n`;
  interpretacion += `ACCIÓN RECOMENDADA: ${accion_inmediata}.`;

  return {
    ctg_categoria: ctg.categoria,
    ctg_interpretacion: ctg.interpretacion,
    ctg_color: ctg.color,
    bpp_score: bpp.score,
    bpp_interpretacion: bpp.interpretacion,
    bpp_color: bpp.color,
    bpp_componentes: bpp.componentes,
    relacion_cp: doppler.relacion_cp,
    doppler_interpretacion: doppler.interpretacion,
    doppler_anormal: doppler.doppler_anormal,
    nivel_riesgo,
    color_riesgo,
    recomendaciones,
    accion_inmediata,
    interpretacion
  };
};

// ============================================
// COMPONENTE PRINCIPAL
// ============================================

const SufrimientoFetal: React.FC = () => {
  const [form] = Form.useForm();
  const [resultado, setResultado] = useState<ResultadoSufrimiento | null>(null);
  const [historial, setHistorial] = useState<RegistroSufrimiento[]>([]);
  const [loading, setLoading] = useState(false);

  const onFinish = (valores: any) => {
    setLoading(true);

    const datos: DatosSufrimiento = {
      fcf_basal: valores.fcf_basal,
      variabilidad_fcf: valores.variabilidad_fcf,
      aceleraciones_20min: valores.aceleraciones_20min,
      desaceleraciones_tipo: valores.desaceleraciones_tipo,
      contracciones_10min: valores.contracciones_10min,
      nst_reactivo: valores.nst_reactivo ?? false,
      movimientos_respiratorios: valores.movimientos_respiratorios ?? false,
      movimientos_corporales: valores.movimientos_corporales ?? false,
      tono_fetal: valores.tono_fetal ?? false,
      volumen_liquido: valores.volumen_liquido,
      arteria_umbilical_pi: valores.arteria_umbilical_pi,
      arteria_umbilical_ri: valores.arteria_umbilical_ri,
      arteria_cerebral_media_pi: valores.arteria_cerebral_media_pi,
      ductus_venoso_normal: valores.ductus_venoso_normal ?? true,
      edad_gestacional: valores.edad_gestacional,
      oligohidramnios: valores.oligohidramnios ?? false,
      peso_estimado_percentil: valores.peso_estimado_percentil
    };

    const res = calcularSufrimiento(datos);
    setResultado(res);

    // Agregar al historial
    const nuevoRegistro: RegistroSufrimiento = {
      fecha: new Date().toLocaleString('es-ES'),
      bpp_score: res.bpp_score,
      ctg_categoria: res.ctg_categoria,
      nivel_riesgo: res.nivel_riesgo
    };
    setHistorial(prev => [nuevoRegistro, ...prev]);

    setLoading(false);
  };

  return (
    <div className="sufrimiento-fetal-page">
      <Card
        title={
          <>
            <HeartOutlined style={{ marginRight: 8, color: '#eb2f96' }} />
            Evaluación Integral de Bienestar Fetal
          </>
        }
      >
        <Alert
          message="CTG + Perfil Biofísico Manning + Doppler Fetal"
          description="Evaluación completa según ACOG para CTG (Categorías I/II/III), Perfil Biofísico de Manning (0-10 puntos), y estudios Doppler (AU, ACM, DV, CPR) para determinar el nivel de riesgo fetal y la necesidad de intervención."
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />

        <Form form={form} layout="vertical" onFinish={onFinish} initialValues={{
          fcf_basal: 140, variabilidad_fcf: 12, aceleraciones_20min: 3, desaceleraciones_tipo: 'ninguna',
          contracciones_10min: 3, nst_reactivo: true, movimientos_respiratorios: true, movimientos_corporales: true,
          tono_fetal: true, volumen_liquido: 12, arteria_umbilical_pi: 1.0, arteria_umbilical_ri: 0.6,
          arteria_cerebral_media_pi: 1.8, ductus_venoso_normal: true, edad_gestacional: 38,
          oligohidramnios: false, peso_estimado_percentil: 50
        }}>
          <FormularioBienestarFetal loading={loading} />
        </Form>
      </Card>

      {resultado && <ResultadosBienestarFetal resultado={resultado} historial={historial} form={form} />}
    </div>
  );
};

export default SufrimientoFetal;
