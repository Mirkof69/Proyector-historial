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
}

// ── Tipos del Microservicio IA (EfficientNet-B4 FastAPI) ──────────────────────

export interface Pathology {
  name: string;
  probability: number;
  icd10?: string;
  description?: string;
}

export interface BiometryResult {
  BPD_mm?: number;
  HC_mm?: number;
  AC_mm?: number;
  FL_mm?: number;
  peso_estimado_g?: number;
}

export interface ShapRiskScores {
  riesgo_preeclampsia: number;
  riesgo_parto_prematuro: number;
  riesgo_rciu: number;
  riesgo_placenta_previa: number;
  riesgo_global: number;
  [key: string]: number;
}

export interface PathologyDetection {
  pathologies: Pathology[];
  normal_probability: number;
  threshold_used: number;
  total_pathologies_detected: number;
}

export interface BiometryAssessment {
  measurements: BiometryResult;
  percentiles?: Record<string, number>;
  alerts?: string[];
}

export interface AnalisisCNNCompleto {
  model_version: string;
  inference_time_ms: number;
  score_global: number;
  gradcam_base64?: string;
  shap_risk_scores?: ShapRiskScores;
  pathology_detection: PathologyDetection;
  biometry: BiometryAssessment;
  image_quality?: Record<string, any>;
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
    file: File,
    ecografiaId?: string,
  ): Promise<{ status: string; ai_analysis: AnalisisCNNCompleto; message: string }> => {
    const formData = new FormData();
    formData.append('file', file);
    if (ecografiaId) {
      formData.append('ecografia_id', ecografiaId);
    }
    const response = await api.post('/ecografias/analyze-with-ai/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 30000, // 30s — la inferencia CNN puede tomar hasta 3s + red
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

  // Consulta IA (NLP) - Mantener compatibilidad con módulo original
  consultarIA: async (payload: any) => {
    // Si envían string, convertir a objeto para mantener compatibilidad antigua
    const body = typeof payload === 'string' ? { consulta: payload } : payload;

    const response = await api.post('/ia/consultas/consultar/', body);
    return response.data;
  },
};


