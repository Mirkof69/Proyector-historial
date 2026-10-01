import React, { useState } from 'react';
import { Alert, Button, Collapse, Col, Modal, Result, Row, Select, Space, Statistic, Steps, Table, Tag, Typography, Upload } from 'antd';
import { DownloadOutlined, InboxOutlined } from '@ant-design/icons';
import api from '../../../services/api';
import { descargarArchivo } from '../../../utils/descargarArchivo';
import HistorialImportaciones from './HistorialImportaciones';

const { Text, Paragraph } = Typography;

type EstadoFila = 'valida' | 'creada' | 'error' | 'duplicada';

interface FilaImportacion {
  fila: number;
  ci: string;
  examen: string;
  parametro: string;
  valor: string;
  estado: EstadoFila;
  errores: string[];
}

interface ResultadoImportacion {
  resumen: {
    total: number; valida: number; creada: number; error: number; duplicada: number;
    examenes: number; confirmado: boolean;
  };
  filas: FilaImportacion[];
  importacion_id?: number;
}

interface PedidoMapeo {
  encabezados: string[];
  sugerido: Record<string, string>;
  campos: { campo: string; etiqueta: string; obligatorio: boolean }[];
}

const ETIQUETA: Record<EstadoFila, { color: string; texto: string }> = {
  valida: { color: 'green', texto: 'Lista para importar' },
  creada: { color: 'green', texto: 'Guardada' },
  error: { color: 'red', texto: 'Con errores' },
  duplicada: { color: 'orange', texto: 'Ya cargada' },
};

interface Props {
  open: boolean;
  onClose: () => void;
  /** Se llama tras importar para recargar el listado. */
  onImportado: () => void;
}

/**
 * Importar RESULTADOS de laboratorio desde Excel: una fila por parámetro.
 * Las filas de la misma paciente, examen y fecha forman un examen completado.
 * Nada se guarda hasta confirmar, y solo las filas sin errores.
 */
const ImportarLaboratorioModal: React.FC<Props> = ({ open, onClose, onImportado }) => {
  const [archivo, setArchivo] = useState<File | null>(null);
  const [previa, setPrevia] = useState<ResultadoImportacion | null>(null);
  const [final, setFinal] = useState<ResultadoImportacion | null>(null);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pedidoMapeo, setPedidoMapeo] = useState<PedidoMapeo | null>(null);
  const [mapeo, setMapeo] = useState<Record<string, string>>({});

  const paso = final ? 2 : previa ? 1 : 0;

  const reiniciar = () => {
    setArchivo(null); setPrevia(null); setFinal(null); setError(null); setPedidoMapeo(null); setMapeo({});
  };

  const cerrar = () => {
    if (final?.resumen.creada) onImportado();
    reiniciar();
    onClose();
  };

  const enviar = async (confirmar: boolean) => {
    if (!archivo) return;
    setCargando(true);
    setError(null);
    try {
      const datos = new FormData();
      datos.append('archivo', archivo);
      if (confirmar) datos.append('confirmar', '1');
      if (Object.keys(mapeo).length) datos.append('mapeo', JSON.stringify(mapeo));
      const r = await api.post<ResultadoImportacion & Partial<PedidoMapeo> & { requiere_mapeo?: boolean; error?: string }>(
        '/laboratorios/examenes/importar-excel/', datos, {
          headers: { 'Content-Type': 'multipart/form-data' }, timeout: 120000,
        });
      if (r.data.requiere_mapeo) {
        // El archivo no usa la plantilla: el usuario dice qué columna es cada dato.
        setPedidoMapeo({ encabezados: r.data.encabezados ?? [], sugerido: r.data.sugerido ?? {}, campos: r.data.campos ?? [] });
        setMapeo(r.data.sugerido ?? {});
        setError('No se reconocieron todas las columnas: indique cuál es cada dato y vuelva a revisar.');
        return;
      }
      if (confirmar) setFinal(r.data); else setPrevia(r.data);
    } catch (e: any) {
      setError(e?.response?.data?.error || 'No se pudo leer el archivo.');
    } finally {
      setCargando(false);
    }
  };

  const columnas = [
    { title: 'Fila', dataIndex: 'fila', key: 'fila', width: 64 },
    { title: 'CI', dataIndex: 'ci', key: 'ci', width: 100 },
    { title: 'Examen', dataIndex: 'examen', key: 'examen', width: 90 },
    { title: 'Parámetro', dataIndex: 'parametro', key: 'parametro' },
    { title: 'Valor', dataIndex: 'valor', key: 'valor', width: 90 },
    {
      title: 'Estado', dataIndex: 'estado', key: 'estado', width: 150,
      render: (e: EstadoFila) => <Tag color={ETIQUETA[e].color}>{ETIQUETA[e].texto}</Tag>,
    },
    {
      title: 'Qué corregir', dataIndex: 'errores', key: 'errores',
      render: (errores: string[]) => (errores.length
        ? <ul style={{ margin: 0, paddingLeft: 18 }}>{errores.map((x) => <li key={x}>{x}</li>)}</ul>
        : <Text type="secondary">—</Text>),
    },
  ];

  const resumen = (final ?? previa)?.resumen;
  const listas = previa?.resumen.valida ?? 0;

  return (
    <Modal
      open={open}
      onCancel={cerrar}
      title="Importar resultados de laboratorio (Excel o CSV)"
      width={980}
      destroyOnClose
      footer={
        paso === 0 ? [
          <Button key="cancelar" onClick={cerrar}>Cancelar</Button>,
          <Button key="revisar" type="primary" disabled={!archivo} loading={cargando} onClick={() => enviar(false)}>
            Revisar archivo
          </Button>,
        ] : paso === 1 ? [
          <Button key="otro" onClick={reiniciar}>Elegir otro archivo</Button>,
          <Button key="importar" type="primary" disabled={!listas} loading={cargando} onClick={() => enviar(true)}>
            {listas ? `Guardar ${listas} resultado${listas === 1 ? '' : 's'}` : 'Nada que importar'}
          </Button>,
        ] : [
          <Button key="cerrar" type="primary" onClick={cerrar}>Terminar</Button>,
        ]
      }
    >
      <Steps
        current={paso}
        size="small"
        style={{ marginBottom: 24 }}
        items={[{ title: 'Subir archivo' }, { title: 'Revisar' }, { title: 'Resultado' }]}
      />
      {error && <Alert type="error" showIcon message={error} style={{ marginBottom: 16 }} />}

      {paso === 0 && (
        <Space direction="vertical" style={{ width: '100%' }} size="middle">
          <Paragraph style={{ margin: 0 }}>
            Descargue la plantilla: trae la hoja «Catálogo» con los códigos de examen, los
            parámetros y sus rangos. Ponga una fila por parámetro; las filas de la misma
            paciente, examen y fecha se guardan como un solo examen completado.
          </Paragraph>
          <Button icon={<DownloadOutlined />}
            onClick={() => descargarArchivo('/laboratorios/examenes/plantilla-excel/', 'plantilla_resultados_laboratorio.xlsx')}>
            Descargar plantilla
          </Button>
          <Upload.Dragger
            accept=".xlsx,.csv,.txt"
            maxCount={1}
            beforeUpload={(f) => { setArchivo(f); setError(null); setPedidoMapeo(null); setMapeo({}); return false; }}
            onRemove={() => { setArchivo(null); setPedidoMapeo(null); setMapeo({}); }}
            fileList={archivo ? [{ uid: '1', name: archivo.name, status: 'done' }] : []}
          >
            <p className="ant-upload-drag-icon"><InboxOutlined /></p>
            <p className="ant-upload-text">Arrastre el archivo aquí o haga clic para elegirlo</p>
            <p className="ant-upload-hint">Excel (.xlsx) o CSV (coma, punto y coma o tabulador) · hasta 5.000 filas · 5 MB.
              Si no usa la plantilla, se le pedirá qué columna es cada dato.</p>
          </Upload.Dragger>
          {pedidoMapeo && (
            <Row gutter={[12, 8]}>
              {pedidoMapeo.campos.map((c) => (
                <Col xs={24} sm={12} key={c.campo}>
                  <Text strong>{c.etiqueta}{c.obligatorio ? ' *' : ''}</Text>
                  <Select
                    style={{ width: '100%' }}
                    allowClear={!c.obligatorio}
                    placeholder="Columna del archivo"
                    value={mapeo[c.campo]}
                    onChange={(v) => setMapeo((m) => ({ ...m, [c.campo]: v }))}
                    options={pedidoMapeo.encabezados.map((e) => ({ value: e, label: e }))}
                  />
                </Col>
              ))}
            </Row>
          )}
          <Alert type="info" showIcon message="Cada valor se evalúa contra su rango de referencia"
            description="Los resultados fuera de rango quedan marcados como anormales o críticos, igual que al cargarlos a mano." />
          <Collapse items={[{ key: 'historial', label: 'Importaciones anteriores (deshacer un lote)',
            children: <HistorialImportaciones onCambio={onImportado} /> }]} />
        </Space>
      )}

      {paso >= 1 && resumen && (
        <>
          {paso === 2 && (
            <Result
              status={resumen.creada ? 'success' : 'warning'}
              title={resumen.creada
                ? `Se guardaron ${resumen.creada} resultados en ${resumen.examenes} exámenes`
                : 'No se guardó ningún resultado'}
              subTitle="Las filas con errores o ya cargadas no se guardaron. Puede corregirlas y volver a importarlas. Si subió el archivo equivocado, deshágalo desde «Importaciones anteriores»."
              style={{ padding: '8px 0 16px' }}
            />
          )}
          <Space size="large" style={{ marginBottom: 16 }} wrap>
            <Statistic title="Filas leídas" value={resumen.total} />
            <Statistic title={paso === 2 ? 'Guardadas' : 'Listas'} value={paso === 2 ? resumen.creada : resumen.valida}
              valueStyle={{ color: 'var(--color-success, #16a34a)' }} />
            <Statistic title="Exámenes" value={resumen.examenes} />
            <Statistic title="Con errores" value={resumen.error}
              valueStyle={{ color: resumen.error ? 'var(--color-error, #dc2626)' : undefined }} />
            <Statistic title="Ya cargadas" value={resumen.duplicada} />
          </Space>
          <Table
            rowKey="fila"
            size="small"
            columns={columnas}
            dataSource={(final ?? previa)?.filas}
            pagination={{ pageSize: 8, showSizeChanger: false }}
            scroll={{ x: 820 }}
          />
        </>
      )}
    </Modal>
  );
};

export default ImportarLaboratorioModal;
