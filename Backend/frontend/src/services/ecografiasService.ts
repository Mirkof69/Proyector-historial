/**
 * =============================================================================
 * SERVICIO DE ECOGRAFÍAS
 * =============================================================================
 * ✅ COMPLETO: Interfaces para los 4 modelos del backend
 * - Ecografia (principal)
 * - BiometriaFetal
 * - AnatomiaFetal
 * - AnexosFetales
 * - ImagenEcografia
 * =============================================================================
 */

import api from './api';
import { postFormData } from './api';

// ═══════════════════════════════════════════════════════════════════════════
// INTERFACES
// ═══════════════════════════════════════════════════════════════════════════

interface BiometriaFetal {
  id?: number;
  ecografia_id?: number;
  diametro_biparietal?: number; // DBP en mm
  circunferencia_cefalica?: number; // CC en mm
  circunferencia_abdominal?: number; // CA en mm
  longitud_femur?: number; // LF en mm
  peso_fetal_estimado?: number; // gramos
  percentil_peso?: number;
  percentil_dbp?: number;
  percentil_cc?: number;
  percentil_ca?: number;
  percentil_lf?: number;
  longitud_cefalocaudal?: number; // LCC en mm (primer trimestre)
  translucencia_nucal?: number; // mm
  hueso_nasal_presente?: boolean;
  evaluacion_crecimiento?: string; // Evaluación del crecimiento fetal
  observaciones?: string;
}

interface AnatomiaFetal {
  id?: number;
  ecografia_id?: number;
  sistema_nervioso_central?: 'normal' | 'anormal' | 'no_evaluado';
  snc_detalles?: string;
  cara?: 'normal' | 'anormal' | 'no_evaluado';
  cara_detalles?: string;
  torax?: 'normal' | 'anormal' | 'no_evaluado';
  torax_detalles?: string;
  corazon?: 'normal' | 'anormal' | 'no_evaluado';
  corazon_normal?: boolean; // Alias para compatibilidad
  corazon_detalles?: string;
  abdomen?: 'normal' | 'anormal' | 'no_evaluado';
  abdomen_detalles?: string;
  tracto_urinario?: 'normal' | 'anormal' | 'no_evaluado';
  tracto_urinario_detalles?: string;
  columna_vertebral?: 'normal' | 'anormal' | 'no_evaluado';
  columna_normal?: boolean; // Alias para compatibilidad
  columna_detalles?: string;
  extremidades?: 'normal' | 'anormal' | 'no_evaluado';
  extremidades_superiores_normales?: boolean;
  extremidades_inferiores_normales?: boolean;
  extremidades_detalles?: string;
  genitales?: 'masculino' | 'femenino' | 'indeterminado';
  sexo_fetal?: string; // Alias para compatibilidad
  craneo_normal?: boolean; // Alias para compatibilidad
  cerebro_normal?: boolean; // Alias para compatibilidad
  evaluacion_anatomica?: string; // Evaluación general de la anatomía
  observaciones?: string;
}

interface AnexosFetales {
  id?: number;
  ecografia_id?: number;
  placenta_localizacion?: 'anterior' | 'posterior' | 'lateral' | 'previa' | 'fundica';
  placenta_grado?: '0' | 'I' | 'II' | 'III';
  placenta_espesor?: number; // mm
  placenta_observaciones?: string;
  cordon_umbilical_vasos?: number; // 2 o 3 vasos
  numero_vasos_cordon?: number; // Alias para compatibilidad
  cordon_umbilical_insercion?: 'central' | 'marginal' | 'velamentosa';
  cordon_umbilical_circular?: boolean;
  cordon_umbilical_vueltas?: number;
  cordon_observaciones?: string;
  evaluacion_cordon?: string; // Evaluación general del cordón
  liquido_amniotico?: 'normal' | 'oligohidramnios' | 'polihidramnios';
  indice_liquido_amniotico?: number; // ILA en cm
  bolsillo_mayor?: number; // cm
  cervix_longitud?: number; // mm
  cervix_dilatacion?: boolean;
  cervix_observaciones?: string;
}

interface ImagenEcografia {
  id?: number;
  ecografia_id?: number;
  imagen: File | string; // File para upload, string (URL) para display
  url_imagen?: string; // URL de la imagen (alias para compatibilidad)
  tipo_imagen?: 'dicom' | 'jpg' | 'png';
  descripcion?: string;
  titulo?: string; // Título o nombre de la imagen
  orden?: number;
}

export interface Ecografia {
  id?: number;
  embarazo: number;
  paciente: number;
  paciente_nombre?: string;
  medico?: number | null;
  medico_nombre?: string;
  fecha_ecografia: string;
  tipo_ecografia: 'primer_trimestre' | 'segundo_trimestre' | 'tercer_trimestre' | 'doppler' | '4d' | 'genetica' | 'morfologica';
  indicacion?: 'control_rutina' | 'sospecha_malformacion' | 'control_crecimiento' | 'evaluacion_bienestar' | 'sangrado' | 'screening_genetico' | 'evaluacion_cervical' | 'doppler_materno' | 'doppler_fetal' | 'otro';
  edad_gestacional_semanas: number;
  edad_gestacional_dias?: number;
  edad_gestacional_texto?: string; // Representación textual como "20 semanas 3 días"
  numero_fetos?: number;
  vitalidad_fetal?: boolean;
  frecuencia_cardiaca_fetal?: number | null;
  indice_liquido_amniotico?: number | null;
  bolsillo_maximo?: number | null;
  localizacion_placenta?: string;
  grado_madurez_placenta?: number | null;
  calidad_estudio?: 'excelente' | 'buena' | 'regular' | 'limitada';
  limitaciones_tecnicas?: string;
  observaciones?: string;
  hallazgos_anormales?: string;
  conclusion?: string;
  diagnostico?: string;
  requiere_seguimiento?: boolean;
  estado_liquido_amniotico?: 'normal' | 'disminuido' | 'aumentado';
  tiene_alertas?: boolean;
  alertas?: any[];
  fecha_creacion?: string;
  fecha_registro?: string; // Fecha de registro del estudio
  fecha_actualizacion?: string;
  fecha_modificacion?: string; // Alias para fecha_actualizacion

  // Trazabilidad
  created_by?: number | null;
  updated_by?: number | null;
  created_by_nombre?: string | null;
  updated_by_nombre?: string | null;

  // Relaciones con otros modelos
  biometria?: BiometriaFetal;
  anatomia?: AnatomiaFetal;
  anexos?: AnexosFetales;
  imagenes?: ImagenEcografia[];

  // Optimización para React Table
  _uniqueRowKey?: string;
}

// ═══════════════════════════════════════════════════════════════════════════
// SERVICIO
// ═══════════════════════════════════════════════════════════════════════════

export const ecografiasService = {
  /** Lista ecografías de un embarazo */
  getByEmbarazo: async (embarazoId: number) => {
    const response = await api.get('/ecografias/', { params: { embarazo_id: embarazoId } });
    return response.data;
  },

  getById: async (id: number) => {
    const response = await api.get(`/ecografias/${id}/`);
    return response.data;
  },

  /** Crea ecografía completa con biometría, anatomía, anexos e imágenes */
  create: async (data: Partial<Ecografia>) => {
    // Si hay imágenes, usar FormData
    if (data.imagenes && data.imagenes.length > 0) {
      const formData = new FormData();

      // Agregar campos principales
      Object.keys(data).forEach(key => {
        const value = (data as any)[key];
        if (key !== 'imagenes' && key !== 'biometria' && key !== 'anatomia' && key !== 'anexos' && value !== undefined && value !== null) {
          formData.append(key, typeof value === 'object' ? JSON.stringify(value) : value);
        }
      });

      // Agregar datos anidados como JSON
      if (data.biometria) {
        formData.append('biometria', JSON.stringify(data.biometria));
      }
      if (data.anatomia) {
        formData.append('anatomia', JSON.stringify(data.anatomia));
      }
      if (data.anexos) {
        formData.append('anexos', JSON.stringify(data.anexos));
      }

      // Agregar imágenes
      data.imagenes.forEach((img, index) => {
        if (img.imagen instanceof File) {
          formData.append(`imagenes[${index}]`, img.imagen);
          if (img.descripcion) {
            formData.append(`imagenes_descripcion[${index}]`, img.descripcion);
          }
        }
      });

      return await postFormData('/ecografias/', formData);
    } else {
      // Sin imágenes, usar JSON normal
      return await api.post('/ecografias/', data);
    }
  },

  /** Actualizar ecografía */
  update: async (id: number, data: Partial<Ecografia>) => {
    const response = await api.put(`/ecografias/${id}/`, data);
    return response.data;
  },

  delete: async (id: number) => {
    await api.delete(`/ecografias/${id}/`);
  },

  /** Agregar imagen a ecografía existente */
  addImagen: async (ecografiaId: number, imagen: ImagenEcografia) => {
    const formData = new FormData();
    if (imagen.imagen instanceof File) {
      formData.append('imagen', imagen.imagen);
    }
    if (imagen.descripcion) {
      formData.append('descripcion', imagen.descripcion);
    }
    if (imagen.tipo_imagen) {
      formData.append('tipo_imagen', imagen.tipo_imagen);
    }
    if (imagen.titulo) {
      formData.append('titulo', imagen.titulo);
    }
    // Endpoint correcto: subir_imagen (no imagenes que es solo GET)
    return await postFormData(`/ecografias/${ecografiaId}/subir_imagen/`, formData);
  },

  /** Eliminar imagen — imagen_id va en el body, no en la URL */
  deleteImagen: async (ecografiaId: number, imagenId: number) => {
    return await api.delete(`/ecografias/${ecografiaId}/eliminar_imagen/`, {
      data: { imagen_id: imagenId },
    });
  },

  // ── Aliases en español para compatibilidad con componentes existentes ──────

  listar: async () => {
    const response = await api.get('/ecografias/');
    return response.data;
  },

  obtener: async (id: number) => {
    const response = await api.get(`/ecografias/${id}/`);
    return response.data;
  },

  obtenerPorEmbarazo: async (embarazo_id: number) => {
    const response = await api.get(`/ecografias/?embarazo_id=${embarazo_id}`);
    return response.data;
  },

  obtenerPorPaciente: async (paciente_id: number) => {
    const response = await api.get(`/ecografias/?paciente_id=${paciente_id}`);
    return response.data;
  },

  obtenerMediciones: async (ecografia_id: number) => {
    const response = await api.get(`/ecografias/${ecografia_id}/mediciones/`);
    return response.data;
  },

  evaluarICC: async (diametro_ac: number, diametro_cerebelo: number) => {
    const response = await api.post('/ecografias/evaluar_icc/', {
      diametro_ac,
      diametro_cerebelo
    });
    return response.data;
  },

  evaluarCapurro: async (peso: number, talla: number, pliegue: number, areola: number, textura: number) => {
    const response = await api.post('/ecografias/evaluar_capurro/', {
      peso,
      talla,
      pliegue,
      areola,
      textura
    });
    return response.data;
  },
};