import { useCallback, useEffect, useRef, useState } from 'react';
import type { TablePaginationConfig } from 'antd';
import type { SorterResult } from 'antd/es/table/interface';
import api from '../services/api';

/**
 * Listado paginado EN EL SERVIDOR.
 *
 * Antes, cada pantalla descargaba todas las páginas en bucle (17 peticiones
 * para 3.200 pacientes; Embarazos bajaba además todos los pacientes) y
 * filtraba en el navegador. Otras pedían `page_size=1000`, pero el servidor
 * corta en 200 y se quedaban con los primeros 200 sin avisar.
 *
 * Aquí se pide solo la página visible; búsqueda (`?search=`, que entiende los
 * nombres cifrados), filtros y orden los resuelve el backend.
 */

export type ValorFiltro = string | number | boolean | null | undefined;
export type Filtros = Record<string, ValorFiltro>;

interface Opciones {
  filtros?: Filtros;
  busqueda?: string;
  tamanoInicial?: number;
  /** Campo de orden del backend, p. ej. `-fecha_parto`. */
  ordenInicial?: string;
  /** Espera antes de buscar mientras se escribe. */
  esperaBusquedaMs?: number;
}

export const OPCIONES_TAMANO = ['10', '20', '50', '100'];

/** Quita vacíos: un filtro sin valor no se envía. */
export const limpiarFiltros = (filtros: Filtros): Record<string, string | number | boolean> =>
  Object.fromEntries(
    Object.entries(filtros).filter(([, v]) => v !== undefined && v !== null && v !== ''),
  ) as Record<string, string | number | boolean>;

/** `{field: 'fecha', order: 'descend'}` → `-fecha`. */
export const ordenDesdeSorter = (sorter: SorterResult<unknown> | SorterResult<unknown>[]): string | undefined => {
  const s = Array.isArray(sorter) ? sorter[0] : sorter;
  if (!s?.order || !s.field) return undefined;
  const campo = Array.isArray(s.field) ? s.field.join('__') : String(s.field);
  return s.order === 'descend' ? `-${campo}` : campo;
};

export function useListadoServidor<T>(url: string, opciones: Opciones = {}) {
  const { filtros = {}, busqueda = '', tamanoInicial = 20, ordenInicial, esperaBusquedaMs = 350 } = opciones;
  const [datos, setDatos] = useState<T[]>([]);
  const [total, setTotal] = useState(0);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pagina, setPagina] = useState(1);
  const [tamano, setTamano] = useState(tamanoInicial);
  const [orden, setOrden] = useState<string | undefined>(ordenInicial);
  const [busquedaEfectiva, setBusquedaEfectiva] = useState(busqueda);
  // Solo vale la respuesta de la última petición: si el usuario escribe
  // rápido, una respuesta vieja no debe pisar a la nueva.
  const ultimaPeticion = useRef(0);

  useEffect(() => {
    const t = setTimeout(() => setBusquedaEfectiva(busqueda.trim()), esperaBusquedaMs);
    return () => clearTimeout(t);
  }, [busqueda, esperaBusquedaMs]);

  const claveFiltros = JSON.stringify(limpiarFiltros(filtros));
  // Cambiar filtros o búsqueda vuelve a la primera página.
  useEffect(() => { setPagina(1); }, [claveFiltros, busquedaEfectiva]);

  const parametros = useCallback(() => ({
    ...JSON.parse(claveFiltros),
    ...(busquedaEfectiva ? { search: busquedaEfectiva } : {}),
    ...(orden ? { ordering: orden } : {}),
  }), [claveFiltros, busquedaEfectiva, orden]);

  const cargar = useCallback(async () => {
    const id = ++ultimaPeticion.current;
    setCargando(true);
    setError(null);
    try {
      const respuesta = await api.get(url, { params: { ...parametros(), page: pagina, page_size: tamano } });
      if (id !== ultimaPeticion.current) return;
      const cuerpo = respuesta.data;
      const lista: T[] = Array.isArray(cuerpo) ? cuerpo : cuerpo?.results ?? [];
      setDatos(lista);
      setTotal(Array.isArray(cuerpo) ? lista.length : cuerpo?.count ?? lista.length);
    } catch (e: any) {
      if (id !== ultimaPeticion.current) return;
      setDatos([]);
      setTotal(0);
      setError(e?.response?.data?.detail || e?.response?.data?.error || 'No se pudo cargar el listado.');
    } finally {
      if (id === ultimaPeticion.current) setCargando(false);
    }
  }, [url, parametros, pagina, tamano]);

  useEffect(() => { cargar(); }, [cargar]);

  const paginacion: TablePaginationConfig = {
    current: pagina,
    pageSize: tamano,
    total,
    showSizeChanger: true,
    pageSizeOptions: OPCIONES_TAMANO,
    showTotal: (t) => `${t.toLocaleString('es-BO')} registros`,
  };

  const onChange = (p: TablePaginationConfig, _f: unknown, sorter: SorterResult<T> | SorterResult<T>[]) => {
    if (p.pageSize && p.pageSize !== tamano) {
      setTamano(p.pageSize);
      setPagina(1);
    } else if (p.current) {
      setPagina(p.current);
    }
    setOrden(ordenDesdeSorter(sorter as SorterResult<unknown>) ?? ordenInicial);
  };

  return { datos, total, cargando, error, paginacion, onChange, recargar: cargar, parametros };
}

/** Cuántos registros cumplen unos filtros (una petición de 1 fila). */
export const contarEnServidor = async (url: string, filtros: Filtros = {}): Promise<number> => {
  const respuesta = await api.get(url, { params: { ...limpiarFiltros(filtros), page_size: 1 } });
  return respuesta.data?.count ?? 0;
};

/** `?a=1&b=2` para llamadas que reciben la URL ya armada (p. ej. descargarArchivo). */
export const aQuery = (params: Record<string, string | number | boolean>): string => {
  const q = new URLSearchParams(Object.entries(params).map(([k, v]) => [k, String(v)])).toString();
  return q ? `?${q}` : '';
};
