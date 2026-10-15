import React, { useState } from 'react';
import { Alert, Button, Modal, Result, Space, Statistic, Steps, Table, Tag, Typography, Upload, theme } from 'antd';
import { DownloadOutlined, InboxOutlined } from '@ant-design/icons';
import api from '../../../services/api';
import { descargarArchivo } from '../../../utils/descargarArchivo';

const { Text, Paragraph } = Typography;

type EstadoFila = 'valida' | 'creada' | 'error' | 'duplicada';

interface FilaImportacion {
  fila: number;
  ci: string;
  nombre: string;
  estado: EstadoFila;
  errores: string[];
  id_clinico?: string;
}

interface ResultadoImportacion {
  resumen: { total: number; valida: number; creada: number; error: number; duplicada: number; confirmado: boolean };
  filas: FilaImportacion[];
}

const ETIQUETA: Record<EstadoFila, { color: string; texto: string }> = {
  valida: { color: 'success', texto: 'Lista para importar' },
  creada: { color: 'success', texto: 'Registrada' },
  error: { color: 'error', texto: 'Con errores' },
  duplicada: { color: 'warning', texto: 'Ya registrada' },
};

interface Props {
  open: boolean;
  onClose: () => void;
  /** Se llama tras importar para recargar el listado. */
  onImportado: () => void;
}

/**
 * Importar pacientes desde Excel en tres pasos: subir la plantilla llena,
 * revisar la vista previa fila por fila y confirmar. Nada se guarda hasta
 * confirmar, y solo se guardan las filas sin errores.
 */
const ImportarPacientesModal: React.FC<Props> = ({ open, onClose, onImportado }) => {
  const { token } = theme.useToken();
  const [archivo, setArchivo] = useState<File | null>(null);
  const [previa, setPrevia] = useState<ResultadoImportacion | null>(null);
  const [final, setFinal] = useState<ResultadoImportacion | null>(null);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const paso = final ? 2 : previa ? 1 : 0;

  const reiniciar = () => {
    setArchivo(null); setPrevia(null); setFinal(null); setError(null);
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
      const r = await api.post<ResultadoImportacion>('/pacientes/importar-excel/', datos, {
        headers: { 'Content-Type': 'multipart/form-data' }, timeout: 120000,
      });
      if (confirmar) setFinal(r.data); else setPrevia(r.data);
    } catch (e: any) {
      setError(e?.response?.data?.error || 'No se pudo leer el archivo.');
    } finally {
      setCargando(false);
    }
  };

  const columnas = [
    { title: 'Fila', dataIndex: 'fila', key: 'fila', width: 70 },
    { title: 'CI', dataIndex: 'ci', key: 'ci', width: 110 },
    { title: 'Nombre', dataIndex: 'nombre', key: 'nombre' },
    {
      title: 'Estado', dataIndex: 'estado', key: 'estado', width: 170,
      render: (e: EstadoFila, f: FilaImportacion) => (
        <Space direction="vertical" size={0}>
          <Tag color={ETIQUETA[e].color}>{ETIQUETA[e].texto}</Tag>
          {f.id_clinico && <Text type="secondary" className="texto-mono">{f.id_clinico}</Text>}
        </Space>
      ),
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
      title="Importar pacientes desde Excel"
      width={920}
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
            {listas ? `Importar ${listas} paciente${listas === 1 ? '' : 's'}` : 'Nada que importar'}
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
            Descargue la plantilla, llénela (una paciente por fila) y súbala. Antes de guardar
            verá qué filas están listas y qué hay que corregir en las demás.
          </Paragraph>
          <Button icon={<DownloadOutlined />}
            onClick={() => descargarArchivo('/pacientes/plantilla-excel/', 'plantilla_pacientes.xlsx')}>
            Descargar plantilla
          </Button>
          <Upload.Dragger
            accept=".xlsx"
            maxCount={1}
            beforeUpload={(f) => { setArchivo(f); setError(null); return false; }}
            onRemove={() => setArchivo(null)}
            fileList={archivo ? [{ uid: '1', name: archivo.name, status: 'done' }] : []}
          >
            <p className="ant-upload-drag-icon"><InboxOutlined /></p>
            <p className="ant-upload-text">Arrastre el Excel aquí o haga clic para elegirlo</p>
            <p className="ant-upload-hint">Solo .xlsx · hasta 2.000 filas · 5 MB</p>
          </Upload.Dragger>
          <Alert type="info" showIcon message="La columna «Consentimiento firmado» es obligatoria"
            description="Solo se registran las pacientes que firmaron el consentimiento de tratamiento de datos (Ley 164)." />
        </Space>
      )}

      {paso >= 1 && resumen && (
        <>
          {paso === 2 && (
            <Result
              status={resumen.creada ? 'success' : 'warning'}
              title={resumen.creada ? `Se registraron ${resumen.creada} pacientes` : 'No se registró ninguna paciente'}
              subTitle="Las filas con errores o ya registradas no se guardaron. Puede corregirlas y volver a importarlas."
              style={{ padding: '8px 0 16px' }}
            />
          )}
          <Space size="large" style={{ marginBottom: 16 }} wrap>
            <Statistic title="Filas leídas" value={resumen.total} />
            <Statistic title={paso === 2 ? 'Registradas' : 'Listas'} value={paso === 2 ? resumen.creada : resumen.valida}
              valueStyle={{ color: token.colorSuccess }} />
            <Statistic title="Con errores" value={resumen.error} valueStyle={{ color: resumen.error ? token.colorError : undefined }} />
            <Statistic title="Ya registradas" value={resumen.duplicada} />
          </Space>
          <Table
            rowKey="fila"
            size="small"
            columns={columnas}
            dataSource={(final ?? previa)?.filas}
            pagination={{ pageSize: 8, showSizeChanger: false }}
            scroll={{ x: 760 }}
          />
        </>
      )}
    </Modal>
  );
};

export default ImportarPacientesModal;
