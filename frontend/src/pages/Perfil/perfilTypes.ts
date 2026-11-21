export interface Usuario {
  id: number;
  username?: string;
  nombre: string;
  apellido_paterno: string;
  apellido_materno?: string;
  email: string;
  telefono?: string;
  rol: 'medico' | 'enfermero' | 'enfermera' | 'administrador' | 'paciente' | 'recepcion' | 'laboratorista';
  especialidad?: string;
  activo?: boolean;
  foto_url?: string | null;
  last_login?: string | null;
  fecha_creacion?: string;
}
