import api from './api';

export interface ImagenEcografica {
  id: number;
  paciente: number;
  paciente_nombre: string;
  url_imagen: string;
  nombre_original: string;
  tipo_imagen: string;
  estado: 'pendiente' | 'procesando' | 'analizada' | 'error';
  semana_gestacional?: number;
  fecha_captura?: string;
  fecha_subida: string;
  tamanio_mb: number;
  resolucion_ancho: number;
  resolucion_alto: number;
  es_principal: boolean;
  descripcion?: string;
  tiene_analisis: boolean;
  analisis_resultado?: {
    resultado: string;
    confianza: number;
  };
}

export interface SugerenciaDiagnostica {
  patologia: string;
  confianza: number;
  descripcion: string;
  icd10: string;
  recomendacion: string;
}

export interface AnalisisCNN {
  id: number;
  modelo_usado: string;
  resultado: string;
  confianza: number;
  confianza_porcentaje: number;
  score_general: number;
  predicciones: any[];
  clases_detectadas: string[];
  bounding_boxes?: any[];
  estructuras_detectadas: Record<string, any>;
  medidas_estimadas?: Record<string, any>;
  anomalias_detectadas: any[];
  alertas: any[];
  recomendaciones: string[];
  fecha_analisis: string;
  es_normal: boolean;
  requiere_atencion: boolean;
  sugerencia_diagnostica_data?: SugerenciaDiagnostica;
  mapa_calor?: string;
  patologias?: string[];
  shap_valores?: Record<string, number>;
  tiempo_inferencia_ms?: number;
  nivel_riesgo?: string;
}

// ── Tipos del Microservicio IA (EfficientNet-B4 FastAPI) ──────────────────────

export interface Pathology {
  pathology: string;
  confidence: number;
  icd10?: string;
  description?: string;
  severity?: string;
  requires_specialist?: boolean;
  recommendation?: string;
  ultrasound_type?: string;
  gestational_weeks?: string;
  ultrasound_markers?: string;
}

export interface BiometryResult {
  BPD_mm?: number;
  HC_mm?: number;
  AC_mm?: number;
  FL_mm?: number;
  peso_estimado_g?: number;
}

export interface ShapRiskScores {
  riesgo_preeclampsia?: number;
  riesgo_parto_prematuro?: number;
  riesgo_hemorragia?: number;
  riesgo_diabetes_gestacional?: number;
  riesgo_mortalidad_perinatal?: number;
  riesgo_global?: number;
  [key: string]: number | undefined;
}

export interface PathologyDetection {
  pathologies: Pathology[];
  total_detected: number;
  requires_specialist?: boolean;
  all_probabilities?: Record<string, number>;
  mensaje?: string;
}

// La API devuelve la biometría en formato plano: { BPD_mm, HC_mm, ..., disponible, motivo? }
export interface BiometryAssessment extends BiometryResult {
  disponible: boolean;
  metodo?: string;
  motivo?: string;
  alerts?: string[];
}

export interface ReporteNarrativoIA {
  clasificacion_clinica: string;
  tipo_embarazo: string;
  edad_gestacional: string;
  trimestre: string;
  tipo_imagen: string;
  biometria: {
    LCC_CRL: string | null;
    DBP: string | null;
    CC: string | null;
    CA: string | null;
    LF: string | null;
    TN: string | null;
    LA: string;
    placenta: string;
    FCF: string | null;
    peso_estimado: string | null;
  };
  patologias_detectadas: string[];
  clasificacion_riesgo: string;
  tipo_seguimiento: string;
  descripcion_ecografia: string;
  hallazgos: string[];
  signos_normales: string[];
  signos_alarma: string[];
  hallazgos_visuales_complementarios: string[];
  recomendaciones: string[];
  diagnostico_presuntivo: string;
  pronostico: string;
  nota_tecnica: string;
  _error_llm?: string;
}

export interface UltrasoundValidation {
  es_ecografia_obstetrica_valida: boolean;
  tipo_ecografia?: string;
  calidad_suficiente?: boolean;
  sharpness?: number;
  contrast?: number;
  motivo?: string;
  motivo_calidad?: string;
  motivo_validez?: string;
  mensaje?: string;
  saturacion_media?: number;
}

export interface ClinicalRecommendations {
  urgencia: string;
  especialista_requerido: string;
  tiempo_recomendado: string;
  estudios_adicionales: string[];
}

export interface AnalisisCNNCompleto {
  status: string;
  fuente: string;
  modelo_version: string;
  score_global: number;
  gradcam_base64?: string;
  shap_risk_scores?: ShapRiskScores;
  ultrasound_validation?: UltrasoundValidation;
  pregnancy_assessment?: Record<string, any>;
  pathology_detection: PathologyDetection;
  biometry: BiometryAssessment;
  liquido_amniotico?: Record<string, any>;
  placenta?: Record<string, any>;
  clinical_recommendations?: ClinicalRecommendations;
  riesgo_preeclampsia?: number;
  riesgo_parto_prematuro?: number;
  filename?: string;
  ecografia_id?: string;
}

export interface EstadisticasIA {
  total_imagenes: number;
  total_analisis: number;
  analisis_normales: number;
  analisis_anomalias: number;
  confianza_promedio: number;
  por_tipo_imagen: Record<string, number>;
  por_estado: Record<string, number>;
  por_resultado_cnn: Record<string, number>;
  modelos_disponibles: any[];
}

export const iaMedicaService = {
  // Obtener lista paginada de imágenes
  getImagenes: async (params?: { paciente_id?: number; tipo_imagen?: string; estado?: string }) => {
    const response = await api.get('/ia/imagenes/', { params });
    return response.data;
  },

  // Obtener detalle de imagen con su análisis
  getImagenDetalle: async (id: number) => {
    const response = await api.get(`/ia/imagenes/${id}/`);
    return response.data;
  },

  // Subir nueva imagen ecográfica
  uploadImagen: async (data: FormData) => {
    const response = await api.post('/ia/imagenes/', data, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Eliminar imagen
  deleteImagen: async (id: number) => {
    const response = await api.delete(`/ia/imagenes/${id}/`);
    return response.data;
  },

  // Ejecutar análisis CNN
  analizarImagen: async (id: number, modelo: string = 'resnet50') => {
    const response = await api.post(`/ia/imagenes/${id}/analizar/`, { modelo });
    return response.data;
  },

  // Obtener solo el resultado del análisis
  getResultadoAnalisis: async (id: number) => {
    const response = await api.get(`/ia/imagenes/${id}/resultado/`);
    return response.data;
  },

  // Reporte narrativo de IA local (LLM con visión, Ollama) — grounded en el
  // resultado real del CNN, requiere que la imagen ya tenga analisis_cnn.
  generarReporteNarrativo: async (id: number): Promise<ReporteNarrativoIA> => {
    const response = await api.post(`/ia/imagenes/${id}/reporte-narrativo/`);
    return response.data;
  },

  // Obtener estadísticas globales
  getEstadisticas: async () => {
    const response = await api.get('/ia/imagenes/estadisticas/');
    return response.data;
  },

  // Obtener modelos configurados
  getModelos: async () => {
    const response = await api.get('/ia/imagenes/modelos/');
    return response.data;
  },

  // Análisis completo EfficientNet-B4 con Grad-CAM + SHAP (microservicio FastAPI)
  analyzeWithAI: async (
    file?: File,
    ecografiaId?: string,
  ): Promise<{ status: string; ai_analysis: AnalisisCNNCompleto; message: string }> => {
    const formData = new FormData();
    if (file) {
      formData.append('file', file);
    }
    if (ecografiaId) {
      formData.append('ecografia_id', ecografiaId);
    }
    const response = await api.post('/ecografias/analyze-with-ai/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 30000,
    });
    return response.data;
  },

  // Exportar dataset
  exportarDataset: async () => {
    const response = await api.get('/ia/imagenes/exportar/', {
      responseType: 'blob',
    });
    
    // Trigger file download
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `dataset_cnn_${new Date().toISOString().split('T')[0]}.json`);
    document.body.appendChild(link);
    link.click();
    link.parentNode?.removeChild(link);
    
    return true;
  },

  // Subir imagen y disparar análisis CNN inmediatamente
  subirYAnalizarImagen: async (
    imagenFile: File,
    pacienteId: number,
    opciones?: { semanaGestacional?: number; tipoImagen?: string; modelo?: string }
  ) => {
    const formData = new FormData();
    formData.append('imagen', imagenFile);
    formData.append('paciente', String(pacienteId));
    if (opciones?.semanaGestacional)
      formData.append('semana_gestacional', String(opciones.semanaGestacional));
    if (opciones?.tipoImagen)
      formData.append('tipo_imagen', opciones.tipoImagen);

    // Subir imagen
    const uploadRes = await api.post('/ia/imagenes/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    const imagenId: number = uploadRes.data.id;

    // Disparar análisis CNN en la imagen recién subida
    const modelo = opciones?.modelo ?? 'efficientnet';
    const analisisRes = await api.post(
      `/ia/imagenes/${imagenId}/analizar/`,
      { modelo }
    );

    return { imagen: uploadRes.data, analisis: analisisRes.data };
  },

  // Vincular imagen IA a una Ecografía del módulo ecografias
  vincularAEcografia: async (imagenIaId: number, pacienteId: number) => {
    const response = await api.post('/ecografias/crear-desde-ia/', {
      imagen_ia_id: imagenIaId,
      paciente_id: pacienteId,
    });
    return response.data;
  },

  // Consulta IA (NLP) - Mantener compatibilidad con módulo original
  consultarIA: async (payload: any) => {
    // Si envían string, convertir a objeto para mantener compatibilidad antigua
    const body = typeof payload === 'string' ? { consulta: payload } : payload;

    const response = await api.post('/ia/consultas/consultar/', body);
    return response.data;
  },
};


