import api from './api';

export interface Rol {
  id: number;
  nombre: string;
  descripcion?: string;
  permisos: string[];
  activo: boolean;
  fecha_creacion?: string;
}

const BASE_URL = '/roles/roles/';

export const rolesService = {
  async listar(): Promise<Rol[]> {
    const response = await api.get<Rol[] | { results: Rol[] }>(BASE_URL);
    const data = response.data;
    if (Array.isArray(data)) return data;
    if (data && Array.isArray((data as { results: Rol[] }).results)) {
      return (data as { results: Rol[] }).results;
    }
    return [];
  },

  async obtener(id: number): Promise<Rol> {
    const response = await api.get<Rol>(`${BASE_URL}${id}/`);
    return response.data;
  },

  async crear(data: Partial<Rol>): Promise<Rol> {
    const response = await api.post<Rol>(BASE_URL, data);
    return response.data;
  },

  async actualizar(id: number, data: Partial<Rol>): Promise<Rol> {
    const response = await api.put<Rol>(`${BASE_URL}${id}/`, data);
    return response.data;
  },

  async eliminar(id: number): Promise<void> {
    await api.delete(`${BASE_URL}${id}/`);
  },
};

export default rolesService;
