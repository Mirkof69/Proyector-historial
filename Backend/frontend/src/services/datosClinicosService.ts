/**
 * =============================================================================
 * SERVICIO DE DATOS CLÍNICOS CONSOLIDADOS
 * =============================================================================
 * Servicio centralizado para obtener TODOS los datos clínicos de un paciente
 * desde TODAS las fuentes disponibles:
 * - Triaje
 * - Notas de Evolución
 * - Controles Prenatales
 * - Embarazos
 * - Partos
 * - Pacientes
 * - Antecedentes
 * - Vacunas
 *
 * Prioriza siempre los datos MÁS RECIENTES independientemente de la fuente
 * =============================================================================
 */

import { triajeService } from './triajeService';
import { notasEvolucionService } from './notasEvolucionService';
import { pacientesService } from './pacientesService';
import { embarazosService } from './embarazosService';
import { logger } from '../utils/logger';

// =====================================================================================
// INTERFACES
// =====================================================================================

interface SignosVitalesConsolidados {
  // Signos vitales
  presion_sistolica?: number;
  presion_diastolica?: number;
  temperatura?: number;
  frecuencia_cardiaca?: number;
  frecuencia_respiratoria?: number;
  saturacion_oxigeno?: number;
  dolor_escala?: number;

  // Antropometría
  peso_kg?: number;
  talla_cm?: number;
  imc?: number;
  perimetro_abdominal_cm?: number;

  // Datos obstétricos
  altura_uterina?: number;
  frecuencia_cardiaca_fetal?: number;
  edad_gestacional_semanas?: number;
  edad_gestacional_dias?: number;

  // Metadata
  fuente?: string; // De dónde viene el dato más reciente
  fecha_dato?: string; // Fecha del dato más reciente
}

interface AntecedentesConsolidados {
  // Alergias y condiciones
  alergias?: string;
  enfermedades_cronicas?: string;

  // Antecedentes personales
  enfermedades_previas?: string;
  medicamentos_actuales?: string;
  cirugias_previas?: string;
  hospitalizaciones_previas?: string;

  // Antecedentes obstétricos
  gestas?: number;
  partos?: number;
  cesareas?: number;
  abortos?: number;
  hijos_vivos?: number;

  // Antecedentes familiares
  enfermedades_familiares?: string;
}

interface EmbarazoActual {
  embarazo?: any;
  ultimoControl?: any;
  datosObstetricos?: {
    edad_gestacional_semanas?: number;
    edad_gestacional_dias?: number;
    altura_uterina?: number;
    frecuencia_cardiaca_fetal?: number;
    peso_actual?: number;
    presion_arterial?: string;
  };
}

interface DatosClinicosCompletos {
  signosVitales: SignosVitalesConsolidados;
  antecedentes: AntecedentesConsolidados;
  embarazoActual: EmbarazoActual | null;
  alertas: string[];
  fuentes: string[]; // Lista de fuentes desde donde se obtuvieron datos
}

// =====================================================================================
// SERVICIO PRINCIPAL
// =====================================================================================

class DatosClinicosService {
  /**
   * Obtiene TODOS los datos clínicos de un paciente desde TODAS las fuentes
   */
  async obtenerDatosCompletos(pacienteId: number): Promise<DatosClinicosCompletos> {
    const alertas: string[] = [];
    const fuentesSet = new Set<string>();


    try {
      // ========================================================================
      // CARGA PARALELA DE TODAS LAS FUENTES
      // ========================================================================
      const [
        pacienteData,
        ultimoTriaje,
        ultimaNota,
        embarazos,
        antecedentesPersonales,
        antecedentesObstetricos,
        antecedentesFamiliares,
      ] = await Promise.all([
        pacientesService.getById(pacienteId).catch(() => null),
        triajeService.getUltimoTriajePaciente(pacienteId).catch(() => null),
        notasEvolucionService.getNotasPorPaciente(pacienteId, { page_size: 1 })
          .then(res => (res.results && res.results.length > 0 ? res.results[0] : null))
          .catch(() => null),
        embarazosService.obtenerPorPaciente(pacienteId).catch(() => []),
        pacientesService.obtenerAntecedentesPersonales(pacienteId).catch(() => null),
        pacientesService.obtenerAntecedentesObstetricos(pacienteId).catch(() => null),
        pacientesService.obtenerAntecedentesFamiliares(pacienteId).catch(() => null),
      ]);

      // ========================================================================
      // CONSOLIDAR SIGNOS VITALES DE TODAS LAS FUENTES
      // ========================================================================
      const signosVitales = await this.consolidarSignosVitales(
        pacienteData,
        ultimoTriaje,
        ultimaNota,
        embarazos,
        fuentesSet
      );


      // ========================================================================
      // CONSOLIDAR ANTECEDENTES
      // ========================================================================
      const antecedentes = this.consolidarAntecedentes(
        pacienteData,
        antecedentesPersonales,
        antecedentesObstetricos,
        antecedentesFamiliares,
        fuentesSet
      );


      // ========================================================================
      // DATOS DE EMBARAZO ACTUAL
      // ========================================================================
      const embarazoActual = await this.obtenerEmbarazoActual(embarazos, fuentesSet);


      // ========================================================================
      // GENERAR ALERTAS
      // ========================================================================
      this.generarAlertas(signosVitales, antecedentes, embarazoActual, alertas);

      return {
        signosVitales,
        antecedentes,
        embarazoActual,
        alertas,
        fuentes: Array.from(fuentesSet),
      };

    } catch (error) {
      console.error('Error obteniendo datos clínicos completos:', error);
      throw error;
    }
  }

  /**
   * Consolida signos vitales priorizando los más recientes
   */
  private async consolidarSignosVitales(
    pacienteData: any,
    ultimoTriaje: any,
    ultimaNota: any,
    embarazos: any[],
    fuentes: Set<string>
  ): Promise<SignosVitalesConsolidados> {

    const signos: SignosVitalesConsolidados = {};

    logger.log('🔍 CONSOLIDANDO SIGNOS VITALES:');
    logger.log('   - ultimoTriaje:', ultimoTriaje);
    logger.log('   - ultimaNota:', ultimaNota);
    logger.log('   - embarazos:', embarazos);

    // Determinar qué fuente tiene los datos más recientes
    const fechas: Array<{ fecha: Date | null; fuente: string; datos: any }> = [];

    if (ultimoTriaje?.fecha_registro) {
      logger.log('✅ Triaje tiene fecha_registro:', ultimoTriaje.fecha_registro);
      fechas.push({
        fecha: new Date(ultimoTriaje.fecha_registro),
        fuente: 'triaje',
        datos: ultimoTriaje,
      });
    } else {
      logger.log('❌ Triaje NO tiene fecha_registro o es null/undefined');
    }

    if (ultimaNota?.fecha_consulta) {
      fechas.push({
        fecha: new Date(ultimaNota.fecha_consulta),
        fuente: 'nota_evolucion',
        datos: ultimaNota,
      });
    }

    // Obtener controles prenatales si hay embarazo activo
    const embarazoActivo = embarazos.find((e: any) => e.estado === 'activo' || e.activo === true);
    if (embarazoActivo?.id) {
      try {
        const controles = await embarazosService.obtenerControles(embarazoActivo.id);
        if (controles && controles.length > 0) {
          const ultimoControl = controles[controles.length - 1];
          if (ultimoControl.fecha_control) {
            fechas.push({
              fecha: new Date(ultimoControl.fecha_control),
              fuente: 'control_prenatal',
              datos: ultimoControl,
            });
          }
        }
      } catch (error) {
        console.error('Error obteniendo controles prenatales:', error);
      }
    }

    // Ordenar por fecha más reciente primero
    logger.log('📅 Fechas ANTES de ordenar:', fechas);
    fechas.sort((a, b) => {
      if (!a.fecha) return 1;
      if (!b.fecha) return -1;
      return b.fecha.getTime() - a.fecha.getTime();
    });
    logger.log('📅 Fechas DESPUÉS de ordenar (más reciente primero):', fechas);

    // ========================================================================
    // CONSOLIDAR DATOS PRIORIZANDO LOS MÁS RECIENTES
    // ========================================================================

    // Inicializar con datos del paciente (más antiguos, menor prioridad)
    if (pacienteData) {
      if (pacienteData.peso_kg) signos.peso_kg = pacienteData.peso_kg;
      if (pacienteData.altura_cm) signos.talla_cm = pacienteData.altura_cm;
      fuentes.add('perfil_paciente');
    }


    // Aplicar datos de cada fuente en orden de fecha (más reciente sobrescribe)
    for (const item of fechas.reverse()) {
      const { fuente, datos } = item;

      if (fuente === 'triaje') {
        // Datos de triaje
        logger.log('📊 Datos de triaje recibidos:', datos);
        if (datos.peso_kg) signos.peso_kg = datos.peso_kg;
        if (datos.talla_cm) signos.talla_cm = datos.talla_cm;
        if (datos.imc) signos.imc = datos.imc;
        if (datos.perimetro_abdominal_cm) signos.perimetro_abdominal_cm = datos.perimetro_abdominal_cm;
        if (datos.presion_sistolica) signos.presion_sistolica = datos.presion_sistolica;
        if (datos.presion_diastolica) signos.presion_diastolica = datos.presion_diastolica;
        if (datos.temperatura) signos.temperatura = datos.temperatura;
        if (datos.frecuencia_cardiaca) signos.frecuencia_cardiaca = datos.frecuencia_cardiaca;
        if (datos.frecuencia_respiratoria) signos.frecuencia_respiratoria = datos.frecuencia_respiratoria;
        if (datos.saturacion_oxigeno) signos.saturacion_oxigeno = datos.saturacion_oxigeno;
        logger.log('📊 Signos vitales consolidados después de triaje:', signos);
        if (datos.dolor_escala) signos.dolor_escala = datos.dolor_escala;

        fuentes.add('triaje');
      } else if (fuente === 'nota_evolucion') {

        // Datos de nota de evolución
        if (datos.presion_arterial_sistolica) signos.presion_sistolica = datos.presion_arterial_sistolica;
        if (datos.presion_arterial_diastolica) signos.presion_diastolica = datos.presion_arterial_diastolica;
        if (datos.temperatura) signos.temperatura = datos.temperatura;
        if (datos.frecuencia_cardiaca) signos.frecuencia_cardiaca = datos.frecuencia_cardiaca;
        if (datos.frecuencia_respiratoria) signos.frecuencia_respiratoria = datos.frecuencia_respiratoria;
        if (datos.saturacion_oxigeno) signos.saturacion_oxigeno = datos.saturacion_oxigeno;

        fuentes.add('nota_evolucion');
      } else if (fuente === 'control_prenatal') {

        // Datos de control prenatal
        if (datos.peso_actual) signos.peso_kg = datos.peso_actual;
        if (datos.altura_uterina) signos.altura_uterina = datos.altura_uterina;
        if (datos.frecuencia_cardiaca_fetal) signos.frecuencia_cardiaca_fetal = datos.frecuencia_cardiaca_fetal;
        if (datos.edad_gestacional_semanas) signos.edad_gestacional_semanas = datos.edad_gestacional_semanas;
        if (datos.edad_gestacional_dias) signos.edad_gestacional_dias = datos.edad_gestacional_dias;

        // Parsear presión arterial si está en formato "120/80"
        if (datos.presion_arterial && typeof datos.presion_arterial === 'string') {
          const partes = datos.presion_arterial.split('/');
          if (partes.length === 2) {
            signos.presion_sistolica = parseInt(partes[0]);
            signos.presion_diastolica = parseInt(partes[1]);
          }
        }

        fuentes.add('control_prenatal');
      }
    }


    // Guardar metadata
    if (fechas.length > 0 && fechas[fechas.length - 1]) {
      signos.fuente = fechas[fechas.length - 1].fuente;
      signos.fecha_dato = fechas[fechas.length - 1].fecha?.toISOString();
    }

    logger.log('🎯 SIGNOS VITALES FINALES CONSOLIDADOS:', signos);
    return signos;
  }

  /**
   * Consolida antecedentes de todas las fuentes
   */
  private consolidarAntecedentes(
    pacienteData: any,
    antecedentesPersonales: any,
    antecedentesObstetricos: any,
    antecedentesFamiliares: any,
    fuentes: Set<string>
  ): AntecedentesConsolidados {

    const antecedentes: AntecedentesConsolidados = {};

    // Datos del paciente
    if (pacienteData) {
      if (pacienteData.alergias) antecedentes.alergias = pacienteData.alergias;
      if (pacienteData.enfermedades_cronicas) antecedentes.enfermedades_cronicas = pacienteData.enfermedades_cronicas;
    }

    // Antecedentes personales
    if (antecedentesPersonales) {
      if (antecedentesPersonales.enfermedades_previas) {
        antecedentes.enfermedades_previas = antecedentesPersonales.enfermedades_previas;
      }
      if (antecedentesPersonales.medicamentos_actuales) {
        antecedentes.medicamentos_actuales = antecedentesPersonales.medicamentos_actuales;
      }
      if (antecedentesPersonales.cirugias_previas) {
        antecedentes.cirugias_previas = antecedentesPersonales.cirugias_previas;
      }
      if (antecedentesPersonales.hospitalizaciones_previas) {
        antecedentes.hospitalizaciones_previas = antecedentesPersonales.hospitalizaciones_previas;
      }
      fuentes.add('antecedentes_personales');
    }


    // Antecedentes obstétricos
    if (antecedentesObstetricos) {
      if (antecedentesObstetricos.gestas !== undefined) antecedentes.gestas = antecedentesObstetricos.gestas;
      if (antecedentesObstetricos.partos !== undefined) antecedentes.partos = antecedentesObstetricos.partos;
      if (antecedentesObstetricos.cesareas !== undefined) antecedentes.cesareas = antecedentesObstetricos.cesareas;
      if (antecedentesObstetricos.abortos !== undefined) antecedentes.abortos = antecedentesObstetricos.abortos;
      if (antecedentesObstetricos.hijos_vivos !== undefined) {
        antecedentes.hijos_vivos = antecedentesObstetricos.hijos_vivos;
      }
      fuentes.add('antecedentes_obstetricos');
    }


    // Antecedentes familiares
    if (antecedentesFamiliares) {
      if (antecedentesFamiliares.enfermedades_familiares) {
        antecedentes.enfermedades_familiares = antecedentesFamiliares.enfermedades_familiares;
      }
      fuentes.add('antecedentes_familiares');
    }


    return antecedentes;
  }

  /**
   * Obtiene datos del embarazo actual si existe
   */
  private async obtenerEmbarazoActual(
    embarazos: any[],
    fuentes: Set<string>
  ): Promise<EmbarazoActual | null> {

    const embarazoActivo = embarazos.find((e: any) => e.estado === 'activo' || e.activo === true);

    if (!embarazoActivo) {
      return null;
    }

    fuentes.add('embarazo');


    try {
      if (!embarazoActivo.id) {
        return { embarazo: embarazoActivo, ultimoControl: null, datosObstetricos: {} };
      }

      const controles = await embarazosService.obtenerControles(embarazoActivo.id);

      if (controles && controles.length > 0) {
        const ultimoControl: any = controles[controles.length - 1];

        const datosObstetricos: any = {};

        if (ultimoControl.edad_gestacional_semanas) {
          datosObstetricos.edad_gestacional_semanas = ultimoControl.edad_gestacional_semanas;
        }
        if (ultimoControl.edad_gestacional_dias) {
          datosObstetricos.edad_gestacional_dias = ultimoControl.edad_gestacional_dias;
        }
        if (ultimoControl.altura_uterina) {
          datosObstetricos.altura_uterina = ultimoControl.altura_uterina;
        }
        if (ultimoControl.frecuencia_cardiaca_fetal) {
          datosObstetricos.frecuencia_cardiaca_fetal = ultimoControl.frecuencia_cardiaca_fetal;
        }
        if (ultimoControl.peso_actual) {
          datosObstetricos.peso_actual = ultimoControl.peso_actual;
        }
        if (ultimoControl.presion_arterial) {
          datosObstetricos.presion_arterial = ultimoControl.presion_arterial;
        }

        fuentes.add('controles_prenatales');

        return {

          embarazo: embarazoActivo,
          ultimoControl,
          datosObstetricos,
        };
      }

      return { embarazo: embarazoActivo, ultimoControl: null, datosObstetricos: {} };
    } catch (error) {
      console.error('Error obteniendo controles del embarazo:', error);
      return { embarazo: embarazoActivo, ultimoControl: null, datosObstetricos: {} };
    }
  }

  /**
   * Genera alertas basadas en los datos consolidados
   */
  private generarAlertas(
    signosVitales: SignosVitalesConsolidados,
    antecedentes: AntecedentesConsolidados,
    embarazoActual: EmbarazoActual | null,
    alertas: string[]
  ): void {
    // Alertas de alergias
    if (antecedentes.alergias) {
      alertas.push(`⚠️ ALERGIAS: ${antecedentes.alergias}`);
    }

    // Alertas de enfermedades crónicas
    if (antecedentes.enfermedades_cronicas) {
      alertas.push(`⚠️ Enfermedades crónicas: ${antecedentes.enfermedades_cronicas}`);
    }

    // Alertas de medicamentos
    if (antecedentes.medicamentos_actuales) {
      alertas.push(`💊 Medicamentos actuales: ${antecedentes.medicamentos_actuales}`);
    }

    // Alertas de embarazo
    if (embarazoActual?.embarazo) {
      alertas.push(`🤰 Embarazo activo detectado`);
    }

    // Alertas de signos vitales anormales
    if (signosVitales.presion_sistolica && signosVitales.presion_diastolica) {
      if (signosVitales.presion_sistolica >= 140 || signosVitales.presion_diastolica >= 90) {
        alertas.push(`⚠️ Presión arterial elevada: ${signosVitales.presion_sistolica}/${signosVitales.presion_diastolica}`);
      }
      if (signosVitales.presion_sistolica < 90 || signosVitales.presion_diastolica < 60) {
        alertas.push(`⚠️ Presión arterial baja: ${signosVitales.presion_sistolica}/${signosVitales.presion_diastolica}`);
      }
    }

    if (signosVitales.temperatura) {
      if (signosVitales.temperatura >= 38) {
        alertas.push(`🌡️ Fiebre: ${signosVitales.temperatura}°C`);
      }
      if (signosVitales.temperatura < 36) {
        alertas.push(`🌡️ Hipotermia: ${signosVitales.temperatura}°C`);
      }
    }

    if (signosVitales.frecuencia_cardiaca) {
      if (signosVitales.frecuencia_cardiaca > 100) {
        alertas.push(`❤️ Taquicardia: ${signosVitales.frecuencia_cardiaca} lpm`);
      }
      if (signosVitales.frecuencia_cardiaca < 60) {
        alertas.push(`❤️ Bradicardia: ${signosVitales.frecuencia_cardiaca} lpm`);
      }
    }

    if (signosVitales.saturacion_oxigeno && signosVitales.saturacion_oxigeno < 95) {
      alertas.push(`🫁 Saturación baja: ${signosVitales.saturacion_oxigeno}%`);
    }

    // Alertas de antecedentes obstétricos
    if (antecedentes.gestas !== undefined) {
      const formula = `G${antecedentes.gestas || 0}P${antecedentes.partos || 0}C${antecedentes.cesareas || 0}A${antecedentes.abortos || 0}`;
      alertas.push(`📋 Antecedentes obstétricos: ${formula}`);
    }
  }
}

// Exportar instancia única del servicio
export const datosClinicosService = new DatosClinicosService();

