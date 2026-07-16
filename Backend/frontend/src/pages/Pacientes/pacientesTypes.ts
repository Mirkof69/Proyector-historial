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
