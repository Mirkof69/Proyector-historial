export interface RegistroPacienteCompleto {
  // Datos demográficos
  id_clinico: string;
  nombre: string;
  apellido_paterno: string;
  apellido_materno: string;
  cedula_identidad: string;
  fecha_nacimiento: string;
  edad: number;
  sexo: 'F' | 'M';

  // Contacto
  telefono: string;
  celular?: string;
  email?: string;
  direccion: string;
  ciudad: string;
  provincia: string;
  codigo_postal?: string;

  // Datos obstétricos
  grupo_sanguineo?: string;
  factor_rh?: string;
  gestas_previas?: number;
  partos_previos?: number;
  cesareas_previas?: number;
  abortos_previos?: number;
  hijos_vivos?: number;

  // Antecedentes médicos
  antecedentes_personales: string[];
  antecedentes_familiares: string[];
  alergias: string[];
  medicamentos_actuales: string[];
  cirugias_previas: string[];

  // Datos sociales
  estado_civil?: string;
  ocupacion?: string;
  nivel_educativo?: string;
  seguro_medico?: string;
  numero_seguro?: string;

  // Contacto de emergencia
  emergencia_nombre?: string;
  emergencia_telefono?: string;
  emergencia_relacion?: string;

  // Auditoría
  fecha_registro: string;
  activo: boolean;
}
