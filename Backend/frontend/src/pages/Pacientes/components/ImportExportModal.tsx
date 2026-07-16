import React from 'react';
import {
  Modal, Tabs, Card, Alert, Upload, Divider, Space, Button, Form, Radio, Checkbox,
  Row, Col, Descriptions, Tag,
} from 'antd';
import {
  UploadOutlined, DownloadOutlined, SyncOutlined, InboxOutlined,
  FileExcelOutlined, FileTextOutlined, FilePdfOutlined, ApiOutlined,
  ExportOutlined, CloudUploadOutlined, CloudDownloadOutlined, DatabaseOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';

const DOWNLOAD_ICON_5 = <DownloadOutlined />;
const FILE_TEXT_ICON_6 = <FileTextOutlined />;
const EXPORT_ICON_3 = <ExportOutlined />;
const CLOUD_UPLOAD_ICON = <CloudUploadOutlined />;
const CLOUD_DOWNLOAD_ICON = <CloudDownloadOutlined />;
const DATABASE_ICON_2 = <DatabaseOutlined />;

interface ImportExportModalProps {
  visible: boolean;
  onClose: () => void;
  token: any;
}

const ImportExportModal: React.FC<ImportExportModalProps> = ({ visible, onClose, token }) => (
  <Modal
    title="Importación/Exportación Masiva de Pacientes"
    open={visible}
    onCancel={onClose}
    width={800}
    footer={null}
  >
    <Tabs
      items={[
        {
          key: '1',
          label: <span><UploadOutlined /> Importar Datos</span>,
          children: (
            <Card>
              <Alert
                message="Carga Masiva desde Excel/CSV"
                description="Importe hasta 1000 registros simultáneamente. Formato requerido: Excel (.xlsx) o CSV (UTF-8)"
                type="info"
                showIcon
                style={{ marginBottom: 16 }}
              />
              <Upload.Dragger
                name="file"
                multiple={false}
                accept=".xlsx,.xls,.csv"
                beforeUpload={() => false}
              >
                <p className="ant-upload-drag-icon">
                  <InboxOutlined style={{ fontSize: 48, color: token.colorPrimary }} />
                </p>
                <p className="ant-upload-text">Click o arrastre el archivo aquí</p>
                <p className="ant-upload-hint">
                  Soporta archivos Excel (.xlsx) o CSV. Máximo 5MB.
                </p>
              </Upload.Dragger>
              <Divider />
              <Space>
                <Button icon={DOWNLOAD_ICON_5} type="link">
                  Descargar Plantilla Excel
                </Button>
                <Button icon={FILE_TEXT_ICON_6} type="link">
                  Ver Guía de Importación
                </Button>
              </Space>
            </Card>
          ),
        },
        {
          key: '2',
          label: <span><DownloadOutlined /> Exportar Datos</span>,
          children: (
            <Card>
              <Form layout="vertical">
                <Form.Item label="Formato de Exportación">
                  <Radio.Group defaultValue="excel">
                    <Radio.Button value="excel">
                      <FileExcelOutlined /> Excel (.xlsx)
                    </Radio.Button>
                    <Radio.Button value="csv">
                      <FileTextOutlined /> CSV
                    </Radio.Button>
                    <Radio.Button value="pdf">
                      <FilePdfOutlined /> PDF
                    </Radio.Button>
                    <Radio.Button value="json">
                      <ApiOutlined /> JSON
                    </Radio.Button>
                  </Radio.Group>
                </Form.Item>

                <Form.Item label="Filtros de Exportación">
                  <Checkbox.Group>
                    <Row>
                      <Col span={12}><Checkbox value="activos">Solo Activos</Checkbox></Col>
                      <Col span={12}><Checkbox value="embarazadas">Solo Embarazadas</Checkbox></Col>
                      <Col span={12}><Checkbox value="nuevos">Nuevos Este Mes</Checkbox></Col>
                      <Col span={12}><Checkbox value="todos">Todos los Registros</Checkbox></Col>
                    </Row>
                  </Checkbox.Group>
                </Form.Item>

                <Form.Item label="Campos a Incluir">
                  <Checkbox.Group defaultValue={['basicos', 'contacto']}>
                    <Space direction="vertical">
                      <Checkbox value="basicos">Datos Básicos (Nombre, CI, Edad)</Checkbox>
                      <Checkbox value="contacto">Información de Contacto</Checkbox>
                      <Checkbox value="medicos">Datos Médicos (Grupo Sanguíneo, etc.)</Checkbox>
                      <Checkbox value="obstetricos">Historial Obstétrico</Checkbox>
                      <Checkbox value="observaciones">Observaciones y Notas</Checkbox>
                    </Space>
                  </Checkbox.Group>
                </Form.Item>

                <Divider />

                <Button type="primary" icon={EXPORT_ICON_3} block size="large">
                  Generar y Descargar Reporte
                </Button>
              </Form>
            </Card>
          ),
        },
        {
          key: '3',
          label: <span><SyncOutlined /> Sincronización</span>,
          children: (
            <Card title="Sincronización con Sistemas Externos">
              <Alert
                message="Integración con SNIS-VE (Sistema Nacional)"
                description="Exporte datos al formato SNIS para reportes epidemiológicos mensuales"
                type="success"
                showIcon
                style={{ marginBottom: 16 }}
              />

              <Space direction="vertical" style={{ width: '100%' }} size="middle">
                <Button icon={CLOUD_UPLOAD_ICON} block>
                  Exportar a SNIS-VE (Formulario 301)
                </Button>
                <Button icon={CLOUD_DOWNLOAD_ICON} block>
                  Importar desde Sistema Anterior
                </Button>
                <Button icon={DATABASE_ICON_2} block>
                  Backup Completo de Base de Datos
                </Button>
              </Space>

              <Divider />

              <Descriptions title="Última Sincronización" column={1} size="small" bordered>
                <Descriptions.Item label="Fecha">{dayjs().subtract(2, 'day').format('DD/MM/YYYY HH:mm')}</Descriptions.Item>
                <Descriptions.Item label="Registros Enviados">245 pacientes</Descriptions.Item>
                <Descriptions.Item label="Estado"><Tag color="green">EXITOSO</Tag></Descriptions.Item>
              </Descriptions>
            </Card>
          ),
        },
      ]}
    />
  </Modal>
);

export default ImportExportModal;
