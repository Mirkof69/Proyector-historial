/**
 * Tipos del detalle de reporte. Deben coincidir con los Serializers de Django.
 */
export interface UsuarioResumen {
  id: number;
  username: string;
  nombre_completo: string;
  rol: string;
}

export interface ReporteMetadata {
  total_registros: number;
  tiempo_procesamiento_seg?: number;
  fuente_datos: string;
}

export interface Reporte {
  id: number;
  uuid?: string;
  titulo: string;
  tipo_reporte: 'PACIENTES' | 'EMBARAZOS' | 'CONTROLES' | 'ESTADISTICAS' | 'CLINICO';
  formato: 'PDF' | 'EXCEL' | 'CSV';
  fecha_creacion: string;
  fecha_actualizacion: string;
  creado_por: UsuarioResumen;
  estado: 'PENDIENTE' | 'PROCESANDO' | 'TERMINADO' | 'FALLIDO';
  archivo_url: string | null;
  parametros_busqueda: Record<string, any>;
  resumen_data?: ReporteMetadata;
  mensaje_error?: string;
}
