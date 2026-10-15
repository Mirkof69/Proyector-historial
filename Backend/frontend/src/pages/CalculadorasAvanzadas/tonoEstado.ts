/**
 * Convierte un color de estado (variable CSS del contrato) en el estado de
 * `Tag`/`Alert` de Ant Design, que toma sus colores de los tokens del tema.
 * Un `Tag` con un color libre pinta texto blanco sobre ese color, ilegible en
 * el tema oscuro, donde los semánticos son claros.
 */
export const tagEstado = (color: string): 'success' | 'warning' | 'error' | 'processing' | 'default' => {
  if (color.includes('peligro')) return 'error';
  if (color.includes('aviso')) return 'warning';
  if (color.includes('exito')) return 'success';
  if (color.includes('info')) return 'processing';
  return 'default';
};
