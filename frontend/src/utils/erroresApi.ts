/**
 * Errores de validación de DRF en texto legible, también los anidados: el
 * recién nacido de un parto llega como `{recien_nacidos: [{peso_nacimiento: [...]}]}`
 * y se mostraba «recien_nacidos: [object Object]» (BUG-010).
 */
export const aplanarErrores = (valor: unknown, ruta: string[] = []): string[] => {
  if (valor == null) return [];
  if (Array.isArray(valor)) {
    const varios = valor.filter((v) => v && typeof v === 'object').length > 1;
    return valor.flatMap((v, i) => aplanarErrores(v, varios ? [...ruta, `n.º ${i + 1}`] : ruta));
  }
  if (typeof valor === 'object') {
    return Object.entries(valor as Record<string, unknown>).flatMap(([campo, v]) =>
      aplanarErrores(v, campo === 'non_field_errors' ? ruta : [...ruta, campo.replace(/_/g, ' ')]));
  }
  return [ruta.length ? `${ruta.join(' › ')}: ${String(valor)}` : String(valor)];
};

/**
 * Motivo que dio el servidor, para mostrarlo tras «No se pudo …»: las acciones
 * responden `{error}` y los formularios `{campo: [mensaje]}`. Sin esto la
 * pantalla decía solo «Error al confirmar la cita» y nadie sabía por qué.
 */
export const motivoDelError = (error: unknown): string => {
  const datos = (error as { response?: { data?: unknown } })?.response?.data;
  if (!datos || typeof datos !== 'object') return '';
  const { error: texto, detail, mensaje } = datos as Record<string, unknown>;
  const directo = [texto, detail, mensaje].find((v) => typeof v === 'string');
  return (directo as string | undefined) ?? aplanarErrores(datos).join(' · ');
};

/** «No se pudo X: motivo» o solo «No se pudo X» si el servidor no dijo nada. */
export const conMotivo = (texto: string, error: unknown): string => {
  const motivo = motivoDelError(error);
  return motivo ? `${texto}: ${motivo}` : texto;
};
