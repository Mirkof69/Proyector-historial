import React, { useEffect, useState } from 'react';
import { Button, Card, Empty, Input, Popconfirm, Select, Space, Table, Tag, Tooltip, Typography } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import {
  DeleteOutlined, ExperimentOutlined, EyeOutlined, FileImageOutlined, LinkOutlined, NodeIndexOutlined, SearchOutlined,
} from '@ant-design/icons';
import { useAntdApp } from '../../../hooks/useMessage';
import { useListadoServidor } from '../../../hooks/useListadoServidor';
import {
  iaMedicaService, ImagenEcografica, InformeRedesMedidas, ReporteNarrativoIA,
} from '../../../services/iaMedicaService';
import { renderResultBadge } from '../iaMedicaHelpers';
import InformeAnalisisModal, { urlMedia } from './InformeAnalisisModal';
import ModalVincular from './ModalVincular';
import '../IaMedica.css';

const { Title, Text } = Typography;

const OPCIONES_RESULTADO = [
  { value: 'normal', label: 'Normal' },
  { value: 'requiere_revision', label: 'Requiere revisión' },
  { value: 'anomalia_leve', label: 'Anomalía leve' },
  { value: 'anomalia_moderada', label: 'Anomalía moderada' },
  { value: 'anomalia_grave', label: 'Anomalía grave' },
  { value: 'sin_analizar', label: 'Sin analizar' },
];

/** Imagen de la fila; si el archivo falta o no carga, lo dice en vez de un icono roto. */
const Miniatura: React.FC<{ url?: string | null }> = ({ url }) => {
  const [rota, setRota] = useState(false);
  if (!url || rota) {
    return <span className="ia-miniatura ia-miniatura--vacia"><FileImageOutlined aria-label="Imagen no disponible" /></span>;
  }
  return <img className="ia-miniatura" loading="lazy" src={urlMedia(url)} alt="Ecografía" onError={() => setRota(true)} />;
};

interface Props {
  /** Solo los análisis de esta paciente (ficha e historia clínica). */
  pacienteId?: number;
  /** Al cambiar, vuelve a pedir la lista: se acaba de guardar un análisis. */
  claveRecarga?: number;
  /** Se analizó o se eliminó algo: las cifras de la pantalla cambiaron. */
  onCambio?: () => void;
}

/**
 * Todos los análisis de IA guardados: de quién son, qué resultó y su informe
 * completo. Pagina y busca en el servidor (hay miles); antes la galería mostraba
 * las primeras 200 imágenes, sin filtro por paciente ni por resultado.
 */
const HistorialAnalisisIA: React.FC<Props> = ({ pacienteId, claveRecarga, onCambio }) => {
  const { message } = useAntdApp();
  const [busqueda, setBusqueda] = useState('');
  const [filtroResultado, setFiltroResultado] = useState<string>();
  const [analizandoId, setAnalizandoId] = useState<number | null>(null);
  const [abriendoId, setAbriendoId] = useState<number | null>(null);
  const [abierto, setAbierto] = useState<{ informe: InformeRedesMedidas; imagen: ImagenEcografica } | null>(null);
  const [narrativa, setNarrativa] = useState<ReporteNarrativoIA | null>(null);
  const [generandoNarrativa, setGenerandoNarrativa] = useState(false);
  const [aVincular, setAVincular] = useState<ImagenEcografica | null>(null);
  const [vinculando, setVinculando] = useState(false);
  const [vinculadas, setVinculadas] = useState<Record<number, number>>({});

  const sinAnalizar = filtroResultado === 'sin_analizar';
  const listado = useListadoServidor<ImagenEcografica>('/ia/imagenes/', {
    busqueda,
    tamanoInicial: 10,
    filtros: {
      paciente_id: pacienteId,
      resultado: sinAnalizar ? undefined : filtroResultado,
      estado: sinAnalizar ? 'pendiente' : undefined,
    },
  });

  useEffect(() => {
    if (claveRecarga) listado.recargar();
    // eslint-disable-next-line react-doctor/exhaustive-deps
  }, [claveRecarga]);

  const mostrar = (informe: InformeRedesMedidas, imagen: ImagenEcografica) => {
    setNarrativa(null);
    setAbierto({ informe, imagen });
  };

  const verInforme = async (img: ImagenEcografica) => {
    setAbriendoId(img.id);
    try {
      mostrar(await iaMedicaService.getInforme(img.id), img);
    } catch (error: any) {
      message.error(error?.response?.data?.error || 'No se pudo abrir el análisis');
    } finally {
      setAbriendoId(null);
    }
  };

  const analizar = async (img: ImagenEcografica) => {
    setAnalizandoId(img.id);
    try {
      const r = await iaMedicaService.analyzeWithAI(undefined, String(img.id));
      // Recién guardado se relee: trae además de quién es y quién lo pidió.
      mostrar(r.guardado ? await iaMedicaService.getInforme(img.id) : r.ai_analysis, img);
      message.success('Análisis completado');
      listado.recargar();
      onCambio?.();
    } catch (error: any) {
      message.error(error?.response?.data?.error || `No se pudo analizar la imagen: ${error?.message || 'error desconocido'}`);
    } finally {
      setAnalizandoId(null);
    }
  };

  const eliminar = async (id: number) => {
    try {
      await iaMedicaService.deleteImagen(id);
      message.success('Imagen eliminada');
      listado.recargar();
      onCambio?.();
    } catch {
      message.error('Error al eliminar imagen');
    }
  };

  const vincular = async () => {
    if (!aVincular) return;
    setVinculando(true);
    try {
      const r = await iaMedicaService.vincularAEcografia(aVincular.id, aVincular.paciente);
      if (r.ecografia_id) {
        setVinculadas((prev) => ({ ...prev, [aVincular.id]: r.ecografia_id }));
        message.success(`Ecografía #${r.ecografia_id} creada con análisis IA`);
      } else {
        message.success('Vinculado correctamente');
      }
      setAVincular(null);
    } catch (error: any) {
      message.error(`Error al vincular: ${error?.response?.data?.error || error.message}`);
    } finally {
      setVinculando(false);
    }
  };

  // Reporte narrativo de IA local (LLM con visión, Ollama): siempre sobre el
  // resultado real de las redes que ya se muestra.
  const redactar = async () => {
    if (!abierto) return;
    setGenerandoNarrativa(true);
    try {
      const reporte = await iaMedicaService.generarReporteNarrativo(abierto.imagen.id);
      setNarrativa(reporte);
      if (reporte._error_llm) message.warning(`El reporte narrativo se generó parcialmente: ${reporte._error_llm}`);
      else message.success('Reporte narrativo generado');
    } catch (error: any) {
      message.error(`Error generando el reporte narrativo: ${error?.message || 'Error desconocido'}`);
    } finally {
      setGenerandoNarrativa(false);
    }
  };

  const columnas: ColumnsType<ImagenEcografica> = [
    { title: 'Imagen', key: 'imagen', width: 96, render: (_, img) => <Miniatura url={img.url_imagen} /> },
    ...(pacienteId ? [] : [{
      title: 'Paciente', key: 'paciente', dataIndex: 'paciente_nombre',
      render: (nombre: string) => <Text strong>{nombre}</Text>,
    }]),
    {
      title: 'Semana', key: 'semana', width: 80, align: 'center',
      render: (_, img) => img.semana_gestacional ?? '—',
    },
    {
      title: 'Plano o análisis', key: 'plano',
      render: (_, img) => img.analisis_resultado?.plano ?? '—',
    },
    {
      title: 'Resultado', key: 'resultado', width: 170,
      render: (_, img) => (img.tiene_analisis && img.analisis_resultado
        ? renderResultBadge(img.analisis_resultado.resultado)
        : <Tag color="processing">Sin analizar</Tag>),
    },
    {
      title: 'Confianza', key: 'confianza', width: 100, align: 'right',
      render: (_, img) => (img.analisis_resultado ? `${img.analisis_resultado.confianza} %` : '—'),
    },
    {
      title: 'Fecha', key: 'fecha', width: 110,
      render: (_, img) => new Date(img.analisis_resultado?.fecha ?? img.fecha_subida).toLocaleDateString('es-BO'),
    },
    {
      title: 'Acciones', key: 'acciones', width: 210,
      render: (_, img) => (
        <Space size={4} wrap>
          {img.tiene_analisis ? (
            <Button size="small" type="primary" icon={<EyeOutlined />} loading={abriendoId === img.id} onClick={() => verInforme(img)}>
              Ver análisis
            </Button>
          ) : (
            <Button size="small" type="primary" icon={<ExperimentOutlined />} loading={analizandoId === img.id} onClick={() => analizar(img)}>
              Analizar con IA
            </Button>
          )}
          {img.tiene_analisis && (
            <Tooltip title="Volver a analizar">
              <Button size="small" aria-label="Volver a analizar" icon={<ExperimentOutlined />} loading={analizandoId === img.id} onClick={() => analizar(img)} />
            </Tooltip>
          )}
          {vinculadas[img.id] ? (
            <Tooltip title={`Ver Ecografía #${vinculadas[img.id]}`}>
              <Button size="small" aria-label={`Ver Ecografía ${vinculadas[img.id]}`} icon={<NodeIndexOutlined />}
                onClick={() => window.open(`/dashboard/ecografias/${vinculadas[img.id]}`, '_blank')} />
            </Tooltip>
          ) : (
            <Tooltip title="Vincular a una ecografía de la paciente">
              <Button size="small" aria-label="Vincular a Ecografía" icon={<LinkOutlined />} onClick={() => setAVincular(img)} />
            </Tooltip>
          )}
          <Popconfirm title="¿Eliminar esta imagen y su análisis?" okText="Eliminar" cancelText="Cancelar" okButtonProps={{ danger: true }}
            onConfirm={() => eliminar(img.id)}>
            <Button size="small" danger aria-label="Eliminar" icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <Card>
      <div className="ia-historial-barra">
        <Title level={4} className="ia-sin-margen">Historial de análisis</Title>
        <Space wrap>
          {!pacienteId && (
            <Input allowClear prefix={<SearchOutlined />} className="ia-historial-buscar"
              aria-label="Buscar paciente por nombre o CI" placeholder="Buscar paciente por nombre o CI"
              value={busqueda} onChange={(e) => setBusqueda(e.target.value)} />
          )}
          <Select allowClear className="ia-historial-filtro" aria-label="Filtrar por resultado" placeholder="Todos los resultados"
            value={filtroResultado} onChange={setFiltroResultado} options={OPCIONES_RESULTADO} />
        </Space>
      </div>
      <Table
        rowKey="id"
        columns={columnas}
        dataSource={listado.datos}
        loading={listado.cargando}
        pagination={listado.paginacion}
        onChange={listado.onChange}
        scroll={{ x: 900 }}
        locale={{ emptyText: <Empty description={listado.error ?? 'No hay análisis con estos filtros'} /> }}
      />
      <InformeAnalisisModal
        abierto={!!abierto}
        informe={abierto?.informe ?? null}
        imagenUrl={urlMedia(abierto?.informe.imagen_url ?? abierto?.imagen.url_imagen)}
        reporteNarrativo={narrativa}
        generandoNarrativa={generandoNarrativa}
        onGenerarNarrativa={redactar}
        onCerrar={() => setAbierto(null)}
      />
      <ModalVincular
        vincularModalVisible={!!aVincular}
        imagenAVincular={aVincular}
        vinculando={vinculando}
        onCancel={() => setAVincular(null)}
        onOk={vincular}
      />
    </Card>
  );
};

export default HistorialAnalisisIA;
