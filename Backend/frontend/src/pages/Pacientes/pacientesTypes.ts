export interface Paciente {
    id: number;
    id_clinico: string;
    nombre: string;
    apellido_paterno: string;
    apellido_materno?: string;
    nombre_completo?: string; // Campo calculado en frontend o backend
    fecha_nacimiento: string; // ISO string YYYY-MM-DD
    edad?: number;
    genero: 'femenino' | 'masculino' | 'otro';
    ci: string;
    telefono?: string;
    email?: string;
    direccion?: string;
    ciudad?: string;
    pais?: string;
    estado_civil?: string; // Nuevo campo extendido
    ocupacion?: string; // Nuevo campo extendido
    grupo_sanguineo?: string; // Nuevo campo extendido
    tipo_sangre?: string; // Campo de tipo de sangre desde backend
    peso_kg?: number;
    altura_cm?: number;
    imc?: number;
    factor_rh?: string;
    numero_seguro_social?: string;
    estado_paciente?: string;
    fecha_baja?: string;
    observaciones?: string;
    activo: boolean;
    embarazos_activos?: boolean;
    fecha_registro?: string;
    foto_perfil?: string; // URL simulada
    _uniqueRowKey?: string; // ✅ Para evitar warnings de keys duplicadas
}

// Filtros avanzados
export interface AdvancedFilters {
    genero?: string;
    edadMin?: number;
    edadMax?: number;
    ciudad?: string;
    estado?: string; // 'activo' | 'inactivo'
    tieneEmbarazo?: boolean;
}

// Estadísticas
export interface PacienteStats {
    total: number;
    activos: number;
    nuevosMes: number;
    embarazadas: number;
    promedioEdad: number;
}

/**
 * `GET /pacientes/resumen/`: cifras calculadas en el servidor sobre TODAS las
 * pacientes que cumplen los filtros (antes, en el navegador sobre lo descargado).
 */
export interface ResumenPacientes {
    total: number;
    activos: number;
    nuevos_mes: number;
    embarazadas: number;
    promedio_edad: number;
    rangos_edad: Record<'<15' | '15-19' | '20-24' | '25-29' | '30-34' | '35-39' | '>=40', number>;
    anosas_gestando: number;
    /** 12 valores: registros de enero a diciembre del año en curso. */
    registros_por_mes: number[];
    por_ciudad: { ciudad: string; total: number }[];
}

export const RESUMEN_PACIENTES_VACIO: ResumenPacientes = {
    total: 0,
    activos: 0,
    nuevos_mes: 0,
    embarazadas: 0,
    promedio_edad: 0,
    rangos_edad: { '<15': 0, '15-19': 0, '20-24': 0, '25-29': 0, '30-34': 0, '35-39': 0, '>=40': 0 },
    anosas_gestando: 0,
    registros_por_mes: Array(12).fill(0),
    por_ciudad: [],
};

export const getEstadoCivilConGenero = (estadoCivil: string | undefined, genero: string | undefined): string => {
  if (!estadoCivil) return 'N/A';
  const esFemenino = genero === 'femenino';
  switch (estadoCivil) {
    case 'soltero': return esFemenino ? 'Soltera' : 'Soltero';
    case 'casado': return esFemenino ? 'Casada' : 'Casado';
    case 'divorciado': return esFemenino ? 'Divorciada' : 'Divorciado';
    case 'viudo': return esFemenino ? 'Viuda' : 'Viudo';
    case 'union_libre': return 'Unión Libre';
    default: return estadoCivil;
  }
};
