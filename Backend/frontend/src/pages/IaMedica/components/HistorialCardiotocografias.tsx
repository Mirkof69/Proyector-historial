import React, { useEffect, useState } from 'react';
import { Button, Card, Descriptions, Empty, Input, Modal, Progress, Select, Space, Table, Tag, Typography, theme } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { EyeOutlined, SearchOutlined } from '@ant-design/icons';
import { useListadoServidor } from '../../../hooks/useListadoServidor';
import '../IaMedica.css';

const { Title, Text } = Typography;

export interface RegistroCTG {
  id: number;
  paciente: number;
  paciente_nombre: string;
  semana_gestacional: number | null;
  valores_etiquetados: { clave: string; etiqueta: string; unidad: string; valor: number }[];
  clase: 'normal' | 'sospechosa' | 'patologica';
  clase_nombre: string;
  probabilidades: Record<string, number>;
  advertencias: string[];
  modelo_version: string;
  realizado_por_nombre: string | null;
  fecha: string;
}

export const COLOR_CLASE_CTG: Record<string, string> = { normal: 'success', sospechosa: 'warning', patologica: 'error' };
export const NOMBRE_CLASE_CTG: Record<string, string> = { normal: 'Normal', sospechosa: 'Sospechosa', patologica: 'Patológica' };
const OPCIONES_CLASE = Object.entries(NOMBRE_CLASE_CTG).map(([value, label]) => ({ value, label }));
const fechaHora = (iso: string) => new Date(iso).toLocaleString('es-BO', { dateStyle: 'short', timeStyle: 'short' });

interface Props {
  /** Solo las cardiotocografías de esta paciente (ficha). */
  pacienteId?: number;
  /** Al cambiar, vuelve a pedir la lista: se acaba de guardar una. */
  claveRecarga?: number;
}

/**
 * Cardiotocografías clasificadas y guardadas: de quién son, qué salió y con qué
 * valores. Pagina y busca en el servidor, como el historial de ecografías.
 */
const HistorialCardiotocografias: React.FC<Props> = ({ pacienteId, claveRecarga }) => {
  const { token } = theme.useToken();
  const colorBarra: Record<string, string> = {
    normal: token.colorSuccess, sospechosa: token.colorWarning, patologica: token.colorError,
  };
  const [busqueda, setBusqueda] = useState('');
  const [filtroClase, setFiltroClase] = useState<string>();
  const [abierto, setAbierto] = useState<RegistroCTG | null>(null);

  const listado = useListadoServidor<RegistroCTG>('/ia/cardiotocografias/', {
    busqueda,
    tamanoInicial: 10,
    filtros: { paciente_id: pacienteId, clase: filtroClase },
  });

  useEffect(() => {
    if (claveRecarga) listado.recargar();
    // eslint-disable-next-line react-doctor/exhaustive-deps
  }, [claveRecarga]);

  const columnas: ColumnsType<RegistroCTG> = [
    ...(pacienteId ? [] : [{
      title: 'Paciente', key: 'paciente', dataIndex: 'paciente_nombre',
      render: (nombre: string) => <Text strong>{nombre}</Text>,
    }]),
    { title: 'Semana', key: 'semana', width: 80, align: 'center', render: (_, r) => r.semana_gestacional ?? '—' },
    {
      title: 'Resultado', key: 'clase', width: 130,
      render: (_, r) => <Tag color={COLOR_CLASE_CTG[r.clase]}>{r.clase_nombre}</Tag>,
    },
    {
      title: 'Probabilidad', key: 'probabilidad', width: 110, align: 'right',
      render: (_, r) => `${((r.probabilidades[r.clase] ?? 0) * 100).toFixed(1)} %`,
    },
    { title: 'Clasificó', key: 'realizado_por', render: (_, r) => r.realizado_por_nombre ?? '—' },
    { title: 'Fecha', key: 'fecha', width: 140, render: (_, r) => fechaHora(r.fecha) },
    {
      title: 'Acciones', key: 'acciones', width: 130,
      render: (_, r) => (
        <Button size="small" type="primary" icon={<EyeOutlined />} onClick={() => setAbierto(r)}>Ver registro</Button>
      ),
    },
  ];

  return (
    <Card>
      <div className="ia-historial-barra">
        <Title level={4} className="ia-sin-margen">Cardiotocografías guardadas</Title>
        <Space wrap>
          {!pacienteId && (
            <Input allowClear prefix={<SearchOutlined />} className="ia-historial-buscar"
              aria-label="Buscar cardiotocografías por nombre o CI" placeholder="Buscar paciente por nombre o CI"
              value={busqueda} onChange={(e) => setBusqueda(e.target.value)} />
          )}
          <Select allowClear className="ia-historial-filtro" aria-label="Filtrar por clasificación" placeholder="Todas las clasificaciones"
            value={filtroClase} onChange={setFiltroClase} options={OPCIONES_CLASE} />
        </Space>
      </div>
      <Table
        rowKey="id"
        columns={columnas}
        dataSource={listado.datos}
        loading={listado.cargando}
        pagination={listado.paginacion}
        onChange={listado.onChange}
        scroll={{ x: 760 }}
        locale={{ emptyText: <Empty description={listado.error ?? 'No hay cardiotocografías guardadas'} /> }}
      />
      <Modal
        open={!!abierto}
        title={abierto ? `Cardiotocografía de ${abierto.paciente_nombre}` : ''}
        onCancel={() => setAbierto(null)}
        footer={<Button onClick={() => setAbierto(null)}>Cerrar</Button>}
        width={720}
      >
        {abierto && (
          <Space direction="vertical" size="middle" style={{ width: '100%' }}>
            <Space wrap>
              <Tag color={COLOR_CLASE_CTG[abierto.clase]} className="ia-ctg-clase">{abierto.clase_nombre}</Tag>
              <Text type="secondary">
                {fechaHora(abierto.fecha)}
                {abierto.semana_gestacional ? ` · semana ${abierto.semana_gestacional}` : ''}
                {abierto.realizado_por_nombre ? ` · ${abierto.realizado_por_nombre}` : ''}
                {abierto.modelo_version ? ` · modelo v${abierto.modelo_version}` : ''}
              </Text>
            </Space>
            {Object.entries(abierto.probabilidades).map(([clase, p]) => (
              <div key={clase}>
                <Text>{NOMBRE_CLASE_CTG[clase] ?? clase}</Text>
                <Progress percent={Math.round(p * 1000) / 10} strokeColor={colorBarra[clase]} />
              </div>
            ))}
            {abierto.advertencias.map((a) => <Text key={a} type="secondary">{a}</Text>)}
            {/* Con todos los tamaños de pantalla: si falta uno, antd usa 3 columnas y los números se parten. */}
            <Descriptions column={{ xs: 1, sm: 1, md: 2, lg: 2, xl: 2, xxl: 2 }} size="small" bordered title="Valores del registro"
              labelStyle={{ width: '34%' }} contentStyle={{ whiteSpace: 'nowrap' }}>
              {abierto.valores_etiquetados.map((v) => (
                <Descriptions.Item key={v.clave} label={`${v.etiqueta}${v.unidad ? ` (${v.unidad})` : ''}`}>
                  {v.valor}
                </Descriptions.Item>
              ))}
            </Descriptions>
          </Space>
        )}
      </Modal>
    </Card>
  );
};

export default HistorialCardiotocografias;
