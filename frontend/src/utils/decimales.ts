/**
 * La API devuelve los DecimalField como texto («20.0»): DRF lo hace así para no
 * perder precisión. Cargado tal cual en un formulario, la regla
 * `{ type: 'number' }` lo rechaza («Rango válido: 10-50 cm») y no deja guardar
 * la edición aunque el valor sea correcto. Antes de `setFieldsValue`, los
 * campos decimales pasan a número; vacío queda vacío.
 */
export const decimalesANumero = <T extends Record<string, any>>(datos: T, campos: string[]): T => {
  const copia: Record<string, any> = { ...datos };
  for (const campo of campos) {
    const valor = copia[campo];
    if (typeof valor === 'string') {
      const numero = valor.trim() === '' ? NaN : Number(valor);
      copia[campo] = Number.isFinite(numero) ? numero : undefined;
    }
  }
  return copia as T;
};
