/**
 * =============================================================================
 * UTILIDAD: Exportación a Excel
 * =============================================================================
 * Funciones para exportar datos a archivos Excel (.xlsx)
 * =============================================================================
 */

import * as XLSX from 'xlsx';
import dayjs from 'dayjs';

interface ExcelExportOptions {
  filename?: string;
  sheetName?: string;
  title?: string;
}

/**
 * Exporta datos a Excel
 * @param data Array de objetos con los datos a exportar
 * @param columns Objeto que mapea las claves a los encabezados de columna
 * @param options Opciones adicionales para la exportación
 */
export const exportarExcel = (
  data: any[],
  columns: Record<string, string>,
  options: ExcelExportOptions = {}
) => {
  try {
    const {
      filename = `export_${dayjs().format('YYYYMMDD_HHmmss')}.xlsx`,
      sheetName = 'Datos',
      title
    } = options;

    // Transformar datos usando las columnas especificadas
    const dataTransformada = data.map(row => {
      const nuevaFila: any = {};
      Object.keys(columns).forEach(key => {
        const valor = obtenerValorAnidado(row, key);
        nuevaFila[columns[key]] = formatearValor(valor);
      });
      return nuevaFila;
    });

    // Si hay título, agregarlo como primera fila
    let wsData: any[] = dataTransformada;
    if (title) {
      // Agregar fila de título
      const tituloRow: any = {};
      Object.values(columns).forEach((col, idx) => {
        tituloRow[col] = idx === 0 ? title : '';
      });
      wsData = [tituloRow, {}, ...dataTransformada];
    }

    // Crear libro y hoja
    const ws = XLSX.utils.json_to_sheet(wsData, { skipHeader: title ? true : false });
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, sheetName);

    // Aplicar estilos (ancho de columnas)
    const wscols = Object.values(columns).map(col => ({
      wch: Math.max(col.length + 5, 15)
    }));
    ws['!cols'] = wscols;

    // Descargar archivo
    XLSX.writeFile(wb, filename);
  } catch (error) {
    console.error('Error exportando a Excel:', error);
    throw error;
  }
};

/**
 * Obtiene valor de propiedad anidada usando notación de punto
 * Ejemplo: 'paciente_info.nombre' => row.paciente_info.nombre
 */
export const obtenerValorAnidado = (obj: any, path: string): any => {
  const keys = path.split('.');
  let valor = obj;

  for (const key of keys) {
    if (valor === null || valor === undefined) {
      return '';
    }
    valor = valor[key];
  }

  return valor;
};

/**
 * Formatea valores para Excel
 */
export const formatearValor = (valor: any): any => {
  if (valor === null || valor === undefined) {
    return '';
  }

  // Fechas
  if (dayjs(valor).isValid() && typeof valor === 'string' && valor.match(/^\d{4}-\d{2}-\d{2}/)) {
    return dayjs(valor).format('DD/MM/YYYY');
  }

  // Booleanos
  if (typeof valor === 'boolean') {
    return valor ? 'Sí' : 'No';
  }

  // Objetos y arrays (convertir a JSON string)
  if (typeof valor === 'object') {
    return JSON.stringify(valor);
  }

  return valor;
};

/**
 * Exporta múltiples hojas a un solo archivo Excel
 */
const exportarExcelMultipleHojas = (
  hojas: Array<{
    nombre: string;
    datos: any[];
    columnas: Record<string, string>;
  }>,
  filename: string = `export_${dayjs().format('YYYYMMDD_HHmmss')}.xlsx`
) => {
  try {
    const wb = XLSX.utils.book_new();

    hojas.forEach(({ nombre, datos, columnas }) => {
      const dataTransformada = datos.map(row => {
        const nuevaFila: any = {};
        Object.keys(columnas).forEach(key => {
          const valor = obtenerValorAnidado(row, key);
          nuevaFila[columnas[key]] = formatearValor(valor);
        });
        return nuevaFila;
      });

      const ws = XLSX.utils.json_to_sheet(dataTransformada);

      // Aplicar estilos (ancho de columnas)
      const wscols = Object.values(columnas).map(col => ({
        wch: Math.max(col.length + 5, 15)
      }));
      ws['!cols'] = wscols;

      XLSX.utils.book_append_sheet(wb, ws, nombre);
    });

    XLSX.writeFile(wb, filename);
  } catch (error) {
    console.error('Error exportando a Excel (múltiples hojas):', error);
    throw error;
  }
};

const excelExportService = {
  exportarExcel,
  exportarExcelMultipleHojas
};

export default excelExportService;
