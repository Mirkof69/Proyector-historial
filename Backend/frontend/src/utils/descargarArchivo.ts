/**
 * Descarga un archivo binario servido por la API (PDF/Excel) con la sesión
 * de cookies actual, y lo entrega al navegador como descarga con nombre.
 */
import api from '../services/api';

export const descargarArchivo = async (url: string, nombreArchivo: string): Promise<void> => {
  const response = await api.get(url, { responseType: 'blob' });
  const blob = new Blob([response.data]);
  const enlace = document.createElement('a');
  enlace.href = URL.createObjectURL(blob);
  enlace.download = nombreArchivo;
  document.body.appendChild(enlace);
  enlace.click();
  enlace.remove();
  URL.revokeObjectURL(enlace.href);
};
