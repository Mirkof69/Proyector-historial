/**
 * Selectores de paciente y de embarazo que buscan en el servidor.
 *
 * Antes cada formulario cargaba `getAll()`, que solo trae la primera página
 * (200 registros): con 5.000 pacientes, las antiguas no se podían elegir. Y
 * el valor que llegaba por la URL (?paciente=, ?embarazo=) se ignoraba.
 * Estos selectores buscan por nombre o CI mientras se escribe y, si reciben
 * un id que no está en la lista, lo piden al servidor para mostrar su nombre.
 * Funcionan dentro de un Form.Item (value/onChange).
 */
import React, { useEffect, useRef, useState } from 'react';
import { Select, Spin, Tag } from 'antd';
import dayjs from 'dayjs';
import api from '../../services/api';

interface PacienteOpcion {
  id: number;
  nombre_completo?: string;
  nombre?: string;
  apellido_paterno?: string;
  apellido_materno?: string;
  ci?: string;
  id_clinico?: string;
}

export interface EmbarazoOpcion {
  id: number;
  paciente: number | { id: number };
  paciente_nombre?: string;
  numero_gesta?: number;
  numero_para?: number;
  fecha_ultima_menstruacion?: string;
  estado?: string;
  [clave: string]: unknown;
}

const lista = <T,>(data: unknown): T[] =>
  (Array.isArray(data) ? data : ((data as { results?: T[] })?.results ?? [])) as T[];

const nombrePaciente = (p: PacienteOpcion) =>
  p.nombre_completo || [p.nombre, p.apellido_paterno, p.apellido_materno].filter(Boolean).join(' ');

/** Espera `ms` sin cambios antes de llamar (evita una petición por tecla). */
const useConRetardo = (fn: (texto: string) => void, ms = 300) => {
  const temporizador = useRef<ReturnType<typeof setTimeout>>();
  useEffect(() => () => clearTimeout(temporizador.current), []);
  return (texto: string) => {
    clearTimeout(temporizador.current);
    temporizador.current = setTimeout(() => fn(texto), ms);
  };
};

interface PacienteSelectProps {
  value?: number;
  onChange?: (id: number | undefined, paciente?: PacienteOpcion) => void;
  soloMujeres?: boolean;
  disabled?: boolean;
  placeholder?: string;
}

export const PacienteSelect: React.FC<PacienteSelectProps> = ({
  value, onChange, soloMujeres = true, disabled, placeholder = 'Escriba nombre o CI de la paciente',
}) => {
  const [opciones, setOpciones] = useState<PacienteOpcion[]>([]);
  const [cargando, setCargando] = useState(false);

  const buscar = async (texto: string) => {
    setCargando(true);
    try {
      const r = await api.get('/pacientes/', {
        params: { search: texto || undefined, page_size: 20, ...(soloMujeres ? { genero: 'femenino' } : {}) },
      });
      setOpciones(lista<PacienteOpcion>(r.data));
    } catch {
      setOpciones([]);
    } finally {
      setCargando(false);
    }
  };
  const buscarConRetardo = useConRetardo(buscar);

  // Primera carga y valor que llega de fuera (URL o edición) sin estar en la lista
  useEffect(() => { buscar(''); }, []); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (!value || opciones.some((o) => o.id === value)) return;
    api.get(`/pacientes/${value}/`)
      .then((r) => setOpciones((prev) => [r.data, ...prev.filter((o) => o.id !== value)]))
      .catch(() => undefined);
  }, [value]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <Select
      showSearch
      allowClear
      value={value}
      disabled={disabled}
      placeholder={placeholder}
      filterOption={false}
      onSearch={buscarConRetardo}
      notFoundContent={cargando ? <Spin size="small" /> : 'Sin resultados'}
      onChange={(id?: number) => onChange?.(id, opciones.find((o) => o.id === id))}
      options={opciones.map((p) => ({
        value: p.id,
        label: `${nombrePaciente(p)}${p.ci ? ` · CI ${p.ci}` : ''}${p.id_clinico ? ` · ${p.id_clinico}` : ''}`,
      }))}
      aria-label="Paciente"
      style={{ width: '100%' }}
    />
  );
};

interface EmbarazoSelectProps {
  value?: number;
  onChange?: (id: number | undefined, embarazo?: EmbarazoOpcion) => void;
  /** Se llama cuando un valor que llegó de fuera (URL, edición) termina de cargarse. */
  onCargado?: (embarazo: EmbarazoOpcion) => void;
  /** Limita a los embarazos de una paciente. */
  pacienteId?: number;
  soloActivos?: boolean;
  disabled?: boolean;
  placeholder?: string;
}

const etiquetaEmbarazo = (e: EmbarazoOpcion) => (
  <span>
    <Tag color="blue">G{e.numero_gesta ?? '?'}</Tag>
    {e.paciente_nombre ?? `Embarazo ${e.id}`}
    {e.fecha_ultima_menstruacion ? ` · FUM ${dayjs(e.fecha_ultima_menstruacion).format('DD/MM/YYYY')}` : ''}
    {e.estado && e.estado !== 'activo' ? ` · ${e.estado}` : ''}
  </span>
);

export const EmbarazoSelect: React.FC<EmbarazoSelectProps> = ({
  value, onChange, onCargado, pacienteId, soloActivos = true, disabled,
  placeholder = 'Escriba el nombre o CI de la paciente',
}) => {
  const [opciones, setOpciones] = useState<EmbarazoOpcion[]>([]);
  const [cargando, setCargando] = useState(false);

  const buscar = async (texto: string) => {
    setCargando(true);
    try {
      const r = await api.get('/embarazos/', {
        params: {
          search: texto || undefined, page_size: 20, paciente: pacienteId,
          ...(soloActivos ? { estado: 'activo' } : {}),
        },
      });
      setOpciones(lista<EmbarazoOpcion>(r.data));
    } catch {
      setOpciones([]);
    } finally {
      setCargando(false);
    }
  };
  const buscarConRetardo = useConRetardo(buscar);

  useEffect(() => { buscar(''); }, [pacienteId]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (!value || opciones.some((o) => o.id === value)) return;
    api.get(`/embarazos/${value}/`).then((r) => {
      setOpciones((prev) => [r.data, ...prev.filter((o) => o.id !== value)]);
      onCargado?.(r.data);
    }).catch(() => undefined);
  }, [value]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <Select
      showSearch
      allowClear
      value={value}
      disabled={disabled}
      placeholder={placeholder}
      filterOption={false}
      onSearch={buscarConRetardo}
      notFoundContent={cargando ? <Spin size="small" /> : 'Sin embarazos activos'}
      onChange={(id?: number) => onChange?.(id, opciones.find((o) => o.id === id))}
      options={opciones.map((e) => ({ value: e.id, label: etiquetaEmbarazo(e) }))}
      aria-label="Embarazo"
      size="large"
      style={{ width: '100%' }}
    />
  );
};

/** Lee ?paciente= y ?embarazo= de la URL (enteros positivos o undefined). */
export const leerContextoClinico = (busqueda: URLSearchParams) => {
  const num = (clave: string) => {
    const v = Number(busqueda.get(clave));
    return Number.isInteger(v) && v > 0 ? v : undefined;
  };
  return { pacienteId: num('paciente'), embarazoId: num('embarazo') };
};
