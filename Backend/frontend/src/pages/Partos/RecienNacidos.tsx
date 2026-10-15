import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Alert, Card, Table, Tag } from 'antd';
import { SmileOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { partosService } from '../../services/partosService';
import './Partos.css';

/**
 * Recién nacidos de un parto (ruta partos/:id/recien-nacido).
 *
 * Antes esta pantalla mostraba dos bebés inventados (mockData) como si fueran
 * del parto, porque la API /partos/recien-nacidos/ estaba tapada por el router.
 * Ahora lee los registros reales del parto.
 */

type RecienNacidoFila = Awaited<ReturnType<typeof partosService.obtenerRecienNacidos>>[number];

const colorApgar = (v: number) => (v >= 7 ? 'success' : v >= 4 ? 'warning' : 'error');

const RecienNacidos: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [filas, setFilas] = useState<RecienNacidoFila[]>([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let vigente = true;
    const partoId = Number(id);
    if (!partoId) {
      setError('El enlace no indica a qué parto pertenecen los recién nacidos.');
      setCargando(false);
      return undefined;
    }
    partosService.obtenerRecienNacidos(partoId)
      .then((datos) => { if (vigente) setFilas(datos); })
      .catch(() => { if (vigente) setError('No se pudieron cargar los recién nacidos de este parto.'); })
      .finally(() => { if (vigente) setCargando(false); });
    return () => { vigente = false; };
  }, [id]);

  const columns = [
    { title: 'N.º', dataIndex: 'numero_gemelo', key: 'numero', width: 60 },
    {
      title: 'Sexo', dataIndex: 'sexo', key: 'sexo',
      render: (s: string) => <Tag>
        {s === 'masculino' ? 'Masculino' : s === 'femenino' ? 'Femenino' : 'Indeterminado'}</Tag>,
    },
    { title: 'Peso (g)', dataIndex: 'peso_nacimiento', key: 'peso', render: (v: number) => (v ? <Tag color={v < 2500 ? 'warning' : v > 4000 ? 'error' : 'success'}>{v} g</Tag> : '—') },
    { title: 'Talla (cm)', dataIndex: 'talla_nacimiento', key: 'talla', render: (v: number) => (v ? `${v} cm` : '—') },
    { title: "Apgar 1'", dataIndex: 'apgar_1_minuto', key: 'apgar1', render: (v: number) => (v != null ? <Tag color={colorApgar(v)}>{v}</Tag> : '—') },
    { title: "Apgar 5'", dataIndex: 'apgar_5_minutos', key: 'apgar5', render: (v: number) => (v != null ? <Tag color={colorApgar(v)}>{v}</Tag> : '—') },
    { title: 'Estado', dataIndex: 'estado_nacimiento', key: 'estado' },
    { title: 'Fecha de nacimiento', dataIndex: 'fecha_nacimiento', key: 'fecha', render: (f: string) => (f ? dayjs(f).format('DD/MM/YYYY HH:mm') : '—') },
  ];

  return (
    <Card title={<span><SmileOutlined className="partos-icono-titulo" />Recién nacidos del parto</span>}>
      {error && <Alert type="error" showIcon message={error} className="partos-separado" />}
      <Table
        columns={columns}
        dataSource={filas}
        rowKey={(r) => String(r.id ?? r.numero_gemelo)}
        loading={cargando}
        pagination={false}
        bordered
        locale={{ emptyText: 'Este parto no tiene recién nacidos registrados.' }}
      />
    </Card>
  );
};

export default RecienNacidos;
