import dayjs from 'dayjs';

// ── Helpers puros (nivel de módulo: identidad estable) ───────────────────────
export const calcularEdadGestacional = (fumStr: string, fechaEcoStr: string) => {
  try {
    const fum = dayjs(fumStr);
    const fechaEco = dayjs(fechaEcoStr);

    if (!fum.isValid() || !fechaEco.isValid()) return { semanas: 0, dias: 0 };

    const diasTotales = fechaEco.diff(fum, 'days');
    if (diasTotales < 0) return { semanas: 0, dias: 0 };

    const semanas = Math.floor(diasTotales / 7);
    const dias = diasTotales % 7;
    return { semanas, dias };
  } catch (error) {
    return { semanas: 0, dias: 0 };
  }
};

export const getBase64 = (file: File): Promise<string> =>
  new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => resolve(reader.result as string);
    reader.onerror = (error) => reject(error);
  });
