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
