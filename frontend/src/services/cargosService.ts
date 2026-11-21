import api from './api';

/**
 * Cargos del hospital (obstetriz, nutricionista…). Cada uno se apoya en un rol
 * del sistema y elige qué módulos de ese rol usa: solo puede quitar, nunca
 * agregar. La API aplica la misma regla (`backend/roles/acceso.py`).
 */
export type RolBase = 'medico' | 'enfermera' | 'laboratorista' | 'recepcion';

export interface Cargo {
  id: number;
  nombre: string;
  descripcion: string;
  rol_base: RolBase;
  rol_base_display: string;
  modulos: string[];
  nombres_modulos: string[];
  activo: boolean;
  usuarios_count: number;
}

export type CargoEntrada = Pick<Cargo, 'nombre' | 'descripcion' | 'rol_base' | 'modulos' | 'activo'>;

export interface ModuloElegible {
  modulo: string;
  nombre: string;
  obligatorio: boolean;
  acciones: string[];
}

export interface ModulosPorRol {
  rol: RolBase;
  nombre: string;
  modulos: ModuloElegible[];
}

const BASE = '/roles/cargos/';

export const cargosService = {
  async listar(): Promise<Cargo[]> {
    const { data } = await api.get<Cargo[] | { results: Cargo[] }>(BASE);
    return Array.isArray(data) ? data : data.results;
  },
  async obtener(id: number): Promise<Cargo> {
    return (await api.get<Cargo>(`${BASE}${id}/`)).data;
  },
  async crear(datos: CargoEntrada): Promise<Cargo> {
    return (await api.post<Cargo>(BASE, datos)).data;
  },
  async actualizar(id: number, datos: Partial<CargoEntrada>): Promise<Cargo> {
    return (await api.patch<Cargo>(`${BASE}${id}/`, datos)).data;
  },
  async eliminar(id: number): Promise<void> {
    await api.delete(`${BASE}${id}/`);
  },
  async modulos(): Promise<ModulosPorRol[]> {
    return (await api.get<ModulosPorRol[]>(`${BASE}modulos/`)).data;
  },
};

export default cargosService;
