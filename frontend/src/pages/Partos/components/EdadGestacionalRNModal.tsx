import React, { useEffect, useMemo, useState } from 'react';
import { Alert, Form, InputNumber, Modal, Radio, Select, Spin, Typography } from 'antd';
import { partoDetalleService, TablasEdadGestacional, mensajeDeError } from '../../../services/partoDetalleService';
import { useAntdApp } from '../../../hooks/useMessage';

const { Text } = Typography;

interface Props {
  rn: any;
  abierto: boolean;
  onCerrar: () => void;
  onGuardado: (rn: any) => void;
}

/** Semanas como las calcula el backend (partos/edad_gestacional_rn.py), para mostrarlas antes de guardar. */
export const semanasCapurro = (items: Record<string, number | undefined>, constante = 204): number | null => {
  const valores = Object.values(items);
  if (valores.length !== 5 || valores.some((v) => v === undefined || v === null)) return null;
  return Math.round(((constante + valores.reduce((a, b) => a + (b as number), 0)) / 7) * 10) / 10;
};
export const semanasBallard = (puntaje?: number | null): number | null =>
  (puntaje === undefined || puntaje === null ? null : Math.round(((2 * puntaje + 120) / 5) * 10) / 10);

const clasificar = (s: number) => (s < 37 ? 'pretérmino' : s < 42 ? 'a término' : 'postérmino');

const EdadGestacionalRNModal: React.FC<Props> = ({ rn, abierto, onCerrar, onGuardado }) => {
  const { message } = useAntdApp();
  const [tablas, setTablas] = useState<TablasEdadGestacional | null>(null);
  const [metodo, setMetodo] = useState<'capurro' | 'ballard'>(rn?.metodo_edad_gestacional === 'ballard' ? 'ballard' : 'capurro');
  const [items, setItems] = useState<Record<string, number | undefined>>(rn?.capurro_items ?? {});
  const [ballard, setBallard] = useState<number | null>(rn?.ballard_puntaje ?? null);
  const [guardando, setGuardando] = useState(false);

  useEffect(() => {
    if (abierto && !tablas) {
      partoDetalleService.tablasEdadGestacional().then(setTablas).catch(() => message.error('No se pudieron cargar las escalas'));
    }
  }, [abierto, tablas, message]);

  const semanas = useMemo(() => {
    if (metodo === 'ballard') return semanasBallard(ballard);
    if (!tablas) return null;
    const completos = Object.fromEntries(Object.keys(tablas.capurro).map((k) => [k, items[k]]));
    return semanasCapurro(completos, tablas.capurro_constante_dias);
  }, [metodo, ballard, items, tablas]);

  const guardar = async () => {
    if (semanas === null) {
      message.warning(metodo === 'capurro' ? 'Complete los cinco signos de Capurro' : 'Indique el puntaje de Ballard');
      return;
    }
    setGuardando(true);
    try {
      const datos = metodo === 'capurro'
        ? { metodo_edad_gestacional: 'capurro', capurro_items: items }
        : { metodo_edad_gestacional: 'ballard', ballard_puntaje: ballard };
      onGuardado(await partoDetalleService.actualizarRecienNacido(rn.id, datos));
      message.success('Edad gestacional registrada');
      onCerrar();
    } catch (e) {
      message.error(mensajeDeError(e, 'No se pudo guardar la edad gestacional'));
    } finally {
      setGuardando(false);
    }
  };

  return (
    <Modal title="Edad gestacional por examen físico" open={abierto} onCancel={onCerrar} onOk={guardar}
      okText="Guardar" confirmLoading={guardando} width={640} destroyOnClose>
      {!tablas ? <Spin /> : (
        <Form layout="vertical">
          <Form.Item label="Método">
            <Radio.Group value={metodo} onChange={(e) => setMetodo(e.target.value)}
              options={[{ value: 'capurro', label: 'Capurro somático' }, { value: 'ballard', label: 'Nuevo Ballard' }]}
              optionType="button" />
          </Form.Item>
          {metodo === 'capurro' ? Object.entries(tablas.capurro).map(([clave, signo]) => (
            <Form.Item key={clave} label={signo.etiqueta} required>
              <Select value={items[clave]} placeholder="Elija el hallazgo"
                onChange={(v) => setItems((prev) => ({ ...prev, [clave]: v }))}
                options={signo.opciones.map((o) => ({ value: o.puntos, label: `${o.descripcion} (${o.puntos})` }))} />
            </Form.Item>
          )) : (
            <Form.Item label={`Puntaje total (${tablas.ballard.minimo} a ${tablas.ballard.maximo})`} required
              extra="Suma de los seis signos neuromusculares y los seis físicos.">
              <InputNumber value={ballard ?? undefined} min={tablas.ballard.minimo} max={tablas.ballard.maximo}
                onChange={(v) => setBallard(v ?? null)} className="partos-ballard" />
            </Form.Item>
          )}
          {semanas !== null ? (
            <Alert type={semanas < 37 || semanas >= 42 ? 'warning' : 'success'} showIcon
              message={<Text strong>{semanas} semanas · {clasificar(semanas)}</Text>}
              description={metodo === 'capurro'
                ? `(${tablas.capurro_constante_dias} + puntos) / 7`
                : tablas.ballard.formula} />
          ) : <Text type="secondary">Complete los datos para ver la edad gestacional.</Text>}
        </Form>
      )}
    </Modal>
  );
};

export default EdadGestacionalRNModal;
