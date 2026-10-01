import React, { useCallback, useEffect, useState } from 'react';
import { Button, Input, Modal, Table, Tag, Typography } from 'antd';
import { RollbackOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import api from '../../../services/api';
import { useAntdApp } from '../../../hooks/useMessage';

const { Text } = Typography;

interface Importacion {
  id: number;
  nombre_archivo: string;
  fecha: string;
  usuario_nombre: string | null;
  resultados: number;
  anulada: boolean;
  motivo_anulacion: string;
  anulada_por_nombre: string | null;
  fecha_anulacion: string | null;
}

/**
 * Importaciones de resultados ya confirmadas, con «Deshacer»: si se subió el
 * archivo equivocado se retira el lote entero (sus resultados y los exámenes
 * que creó), con motivo y auditoría.
 */
const HistorialImportaciones: React.FC<{ onCambio?: () => void }> = ({ onCambio }) => {
  const { message } = useAntdApp();
  const [datos, setDatos] = useState<Importacion[]>([]);
  const [cargando, setCargando] = useState(false);
  const [anulando, setAnulando] = useState<Importacion | null>(null);
  const [motivo, setMotivo] = useState('');
  const [enviando, setEnviando] = useState(false);

  const cargar = useCallback(async () => {
    setCargando(true);
    try {
      const r = await api.get('/laboratorios/importaciones/', { params: { page_size: 10 } });
      setDatos(Array.isArray(r.data) ? r.data : r.data?.results ?? []);
    } catch {
      setDatos([]);
    } finally {
      setCargando(false);
    }
  }, []);

  useEffect(() => { cargar(); }, [cargar]);

  const deshacer = async () => {
    if (!anulando) return;
    setEnviando(true);
    try {
      const r = await api.post(`/laboratorios/importaciones/${anulando.id}/deshacer/`, { motivo });
      message.success(`Importación anulada: ${r.data.resultados_borrados} resultados retirados`);
      setAnulando(null);
      setMotivo('');
      cargar();
      onCambio?.();
    } catch (e: any) {
      message.error(e?.response?.data?.motivo || e?.response?.data?.error || 'No se pudo anular la importación');
    } finally {
      setEnviando(false);
    }
  };

  return (
    <>
      <Table
        rowKey="id"
        size="small"
        loading={cargando}
        dataSource={datos}
        pagination={false}
        locale={{ emptyText: 'Todavía no hay importaciones' }}
        scroll={{ x: 640 }}
        columns={[
          { title: 'Fecha', dataIndex: 'fecha', width: 130, render: (f: string) => dayjs(f).format('DD/MM/YYYY HH:mm') },
          { title: 'Archivo', dataIndex: 'nombre_archivo', ellipsis: true },
          { title: 'Resultados', dataIndex: 'resultados', width: 100 },
          { title: 'Por', dataIndex: 'usuario_nombre', width: 150, ellipsis: true },
          {
            title: '', key: 'accion', width: 150,
            render: (_: unknown, i: Importacion) => (i.anulada
              ? <Tag title={`${i.motivo_anulacion} — ${i.anulada_por_nombre ?? ''}`}>Anulada</Tag>
              : <Button size="small" danger icon={<RollbackOutlined />} onClick={() => setAnulando(i)}>Deshacer</Button>),
          },
        ]}
      />
      <Modal
        open={!!anulando}
        title="Deshacer la importación"
        okText="Deshacer"
        okButtonProps={{ danger: true, disabled: motivo.trim().length < 10 }}
        confirmLoading={enviando}
        onOk={deshacer}
        onCancel={() => { setAnulando(null); setMotivo(''); }}
      >
        <Text>Se borrarán los {anulando?.resultados} resultados de «{anulando?.nombre_archivo}» y los exámenes que
          quedaron vacíos. Queda registrado quién lo hizo y por qué.</Text>
        <Input.TextArea style={{ marginTop: 12 }} rows={3} value={motivo} onChange={(e) => setMotivo(e.target.value)}
          placeholder="Motivo (por ejemplo: archivo de otro día)" maxLength={500} />
      </Modal>
    </>
  );
};

export default HistorialImportaciones;
