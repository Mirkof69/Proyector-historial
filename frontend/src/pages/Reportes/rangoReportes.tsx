import React, { createContext, useContext, useMemo, useState } from 'react';
import { DatePicker, Segmented, Space } from 'antd';
import dayjs, { Dayjs } from 'dayjs';

/**
 * Rango de fechas común a todo el centro de reportes. Antes cada pestaña
 * filtraba a su manera (o no filtraba): al cambiar de pestaña se perdía el
 * período elegido. Las pestañas que dependen de fechas lo leen con
 * `useRangoReportes()`; fuera del centro devuelve null y cada pantalla usa
 * su propio filtro.
 */
export type Preset = 'hoy' | 'semana' | 'mes' | 'anio' | 'personalizado';

export interface RangoReportes {
  preset: Preset;
  desde: Dayjs;
  hasta: Dayjs;
  /** Para la API: { desde: 'AAAA-MM-DD', hasta: 'AAAA-MM-DD' } */
  params: { desde: string; hasta: string };
}

export const rangoDePreset = (preset: Exclude<Preset, 'personalizado'>, hoy: Dayjs = dayjs()): [Dayjs, Dayjs] => {
  const fin = hoy.endOf('day');
  switch (preset) {
    case 'hoy': return [hoy.startOf('day'), fin];
    case 'semana': return [hoy.subtract(6, 'day').startOf('day'), fin];
    case 'mes': return [hoy.startOf('month'), fin];
    default: return [hoy.startOf('year'), fin];
  }
};

interface Valor { rango: RangoReportes; elegir: (preset: Preset, personalizado?: [Dayjs, Dayjs]) => void }

const Contexto = createContext<Valor | null>(null);

export const ProveedorRangoReportes: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [estado, setEstado] = useState<{ preset: Preset; desde: Dayjs; hasta: Dayjs }>(() => {
    const [desde, hasta] = rangoDePreset('mes');
    return { preset: 'mes', desde, hasta };
  });
  const valor = useMemo<Valor>(() => ({
    rango: { ...estado, params: { desde: estado.desde.format('YYYY-MM-DD'), hasta: estado.hasta.format('YYYY-MM-DD') } },
    elegir: (preset, personalizado) => {
      if (preset === 'personalizado') {
        if (personalizado) setEstado({ preset, desde: personalizado[0].startOf('day'), hasta: personalizado[1].endOf('day') });
        else setEstado((e) => ({ ...e, preset }));
        return;
      }
      const [desde, hasta] = rangoDePreset(preset);
      setEstado({ preset, desde, hasta });
    },
  }), [estado]);
  return <Contexto.Provider value={valor}>{children}</Contexto.Provider>;
};

export const useRangoReportes = (): RangoReportes | null => useContext(Contexto)?.rango ?? null;

export const FiltroFechasReportes: React.FC = () => {
  const ctx = useContext(Contexto);
  if (!ctx) return null;
  const { rango, elegir } = ctx;
  return (
    <Space wrap>
      <Segmented
        value={rango.preset}
        onChange={(v) => elegir(v as Preset)}
        options={[
          { value: 'hoy', label: 'Hoy' }, { value: 'semana', label: '7 días' }, { value: 'mes', label: 'Este mes' },
          { value: 'anio', label: 'Este año' }, { value: 'personalizado', label: 'Rango' },
        ]}
      />
      <DatePicker.RangePicker
        value={[rango.desde, rango.hasta]}
        format={{ format: 'DD/MM/YYYY', type: 'mask' }}
        allowClear={false}
        disabledDate={(d) => d.isAfter(dayjs(), 'day')}
        onChange={(v) => { if (v?.[0] && v[1]) elegir('personalizado', [v[0], v[1]]); }}
        aria-label="Período del reporte"
      />
    </Space>
  );
};
