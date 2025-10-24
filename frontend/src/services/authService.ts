import axios from 'axios';

const API_URL = 'http://127.0.0.1:8000/api';

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface LoginResponse {
  access: string;
  refresh: string;
  user: {
    id: number;
    email: string;
    nombre: string;
    rol: string;
  };
}

export const authService = {
  async login(credentials: LoginCredentials): Promise<LoginResponse> {
    const response = await axios.post(`${API_URL}/usuarios/login/`, credentials);
    if (response.data.access) {
      localStorage.setItem('token', response.data.access);
      localStorage.setItem('user', JSON.stringify(response.data.user));
    }
    return response.data;
  },

  logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  },

  getToken(): string | null {
    return localStorage.getItem('token');
  },

  getCurrentUser() {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
  },

  isAuthenticated(): boolean {
    return !!this.getToken();
  },

  // PACIENTES - CRUD
  updatePaciente: async (id: number, data: any) => {
    const token = localStorage.getItem('token');
    const response = await axios.put(
      `${API_URL}/pacientes/${id}/`,
      data,
      { headers: { Authorization: `Bearer ${token}` } }
    );
    return response.data;
  },

  deletePaciente: async (id: number) => {
    const token = localStorage.getItem('token');
    const response = await axios.delete(
      `${API_URL}/pacientes/${id}/`,
      { headers: { Authorization: `Bearer ${token}` } }
    );
    return response.data;
  },

  // EMBARAZOS - CRUD
  updateEmbarazo: async (id: number, data: any) => {
    const token = localStorage.getItem('token');
    const response = await axios.put(
      `${API_URL}/embarazos/${id}/`,
      data,
      { headers: { Authorization: `Bearer ${token}` } }
    );
    return response.data;
  },

  deleteEmbarazo: async (id: number) => {
    const token = localStorage.getItem('token');
    const response = await axios.delete(
      `${API_URL}/embarazos/${id}/`,
      { headers: { Authorization: `Bearer ${token}` } }
    );
    return response.data;
  },

  // CONTROLES - CRUD
  updateControl: async (id: number, data: any) => {
    const token = localStorage.getItem('token');
    const response = await axios.put(
      `${API_URL}/controles/${id}/`,
      data,
      { headers: { Authorization: `Bearer ${token}` } }
    );
    return response.data;
  },

  deleteControl: async (id: number) => {
    const token = localStorage.getItem('token');
    const response = await axios.delete(
      `${API_URL}/controles/${id}/`,
      { headers: { Authorization: `Bearer ${token}` } }
    );
    return response.data;
  }
};