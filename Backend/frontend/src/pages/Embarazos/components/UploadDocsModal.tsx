import React from 'react';
import { Modal, Space, Button, Alert, Spin, Upload, Divider, List } from 'antd';
import {
  CloudUploadOutlined, CloudDownloadOutlined, InboxOutlined,
  UploadOutlined, DownloadOutlined, FileTextOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { EmbarazoExtendido, EmbarazosAction } from '../embarazosReducer';

const cloudDownloadOutlinedIcon3 = <CloudDownloadOutlined />;
const inboxIcon2 = <InboxOutlined />;
const downloadIcon3 = <DownloadOutlined />;

interface UploadDocsModalProps {
  visible: boolean;
  onClose: () => void;
  selectedEmbarazo: EmbarazoExtendido | null;
  uploadingFiles: boolean;
  fileList: any[];
  dispatch: React.Dispatch<EmbarazosAction>;
  handleUploadDocuments: (options: any) => void;
  message: { info: (m: string) => void };
}

const UploadDocsModal: React.FC<UploadDocsModalProps> = ({
  visible, onClose, selectedEmbarazo, uploadingFiles, fileList, dispatch,
  handleUploadDocuments, message,
}) => (
  <Modal
    title={
      <Space>
        <CloudUploadOutlined />
        <span>Subir Documentos del Embarazo</span>
      </Space>
    }
    open={visible}
    onCancel={onClose}
    width={700}
    footer={[
      <Button key="close" onClick={onClose}>
        Cerrar
      </Button>,
      <Button
        key="download"
        icon={cloudDownloadOutlinedIcon3}
        onClick={() => message.info('Descargando documentos...')}
      >
        Descargar Todos
      </Button>
    ]}
  >
    {selectedEmbarazo && (
      <div>
        <Alert
          message="Gestión de Documentos Clínicos"
          description={`Suba ecografías, análisis de laboratorio y otros documentos relacionados con el embarazo de ${selectedEmbarazo?.paciente_nombre}`}
          type="info"
          showIcon
          icon={inboxIcon2}
          style={{ marginBottom: 16 }}
        />

        <Spin spinning={uploadingFiles} tip="Subiendo archivos…">
          <Upload.Dragger
            name="file"
            multiple
            customRequest={handleUploadDocuments}
            fileList={fileList}
            onChange={({ fileList: newFileList }) => dispatch({ type: 'SET_FILE_LIST', payload: newFileList })}
            disabled={uploadingFiles}
          >
            <p className="ant-upload-drag-icon">
              <InboxOutlined style={{ fontSize: 48, color: '#1890ff' }} />
            </p>
            <p className="ant-upload-text">
              <UploadOutlined /> Haga clic o arrastre archivos aquí
            </p>
            <p className="ant-upload-hint">
              Formatos soportados: PDF, JPG, PNG, DICOM (ecografías)
            </p>
          </Upload.Dragger>
        </Spin>

        <Divider>Documentos Existentes</Divider>

        <List
          size="small"
          dataSource={[
            { id: 1, nombre: 'Ecografía 12 semanas.pdf', fecha: dayjs().subtract(2, 'weeks').format('DD/MM/YYYY'), tipo: 'Ecografía' },
            { id: 2, nombre: 'Análisis Hemograma.pdf', fecha: dayjs().subtract(1, 'week').format('DD/MM/YYYY'), tipo: 'Laboratorio' }
          ]}
          renderItem={(item) => (
            <List.Item
              actions={[
                <Button key="descargar" size="small" type="link" icon={downloadIcon3}>Descargar</Button>,
                <Button key="eliminar" size="small" type="link" danger>Eliminar</Button>
              ]}
            >
              <List.Item.Meta
                avatar={<FileTextOutlined style={{ fontSize: 24, color: '#1890ff' }} />}
                title={item.nombre}
                description={`${item.tipo} • ${item.fecha}`}
              />
            </List.Item>
          )}
        />
      </div>
    )}
  </Modal>
);

export default UploadDocsModal;
