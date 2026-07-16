import React from 'react';
import { Space, Typography, Alert, Radio, Select, Modal } from 'antd';
import { DownloadOutlined } from '@ant-design/icons';
import { ViewerAction } from '../visorDicomReducer';

const { Text } = Typography;

interface VisorExportModalProps {
  exportModalVisible: boolean;
  zoom: number;
  rotation: number;
  dispatch: React.Dispatch<ViewerAction>;
  handleExportImage: () => void;
}

const VisorExportModal: React.FC<VisorExportModalProps> = ({
  exportModalVisible, zoom, rotation, dispatch, handleExportImage,
}) => (
  <Modal
    title={<><DownloadOutlined /> Exportar Imagen</>}
    open={exportModalVisible}
    onCancel={() => dispatch({ type: 'SET_EXPORT_MODAL_VISIBLE', payload: false })}

    onOk={() => {
      handleExportImage();
      dispatch({ type: 'SET_EXPORT_MODAL_VISIBLE', payload: false });
    }}
    width={500}
  >
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <div>
        <Text strong>Formato de Exportación:</Text>
        <Radio.Group defaultValue="png" style={{ marginTop: 8, width: '100%' }}>
          <Radio.Button value="png">PNG</Radio.Button>
          <Radio.Button value="jpeg">JPEG</Radio.Button>
          <Radio.Button value="dicom">DICOM</Radio.Button>
          <Radio.Button value="pdf">PDF</Radio.Button>
        </Radio.Group>
      </div>

      <div>
        <Text strong>Calidad:</Text>
        <Select
          defaultValue="high"
          style={{ width: '100%', marginTop: 8 }}
          options={[
            { value: 'low', label: 'Baja (compresión alta)' },
            { value: 'medium', label: 'Media (balanceada)' },
            { value: 'high', label: 'Alta (sin compresión)' }
          ]}
        />
      </div>

      <div>
        <Text strong>Incluir en la exportación:</Text>
        <div style={{ marginTop: 8 }}>
          <Space direction="vertical">
            <Radio checked>Imagen actual</Radio>
            <Radio>Incluir mediciones</Radio>
            <Radio>Incluir anotaciones</Radio>
            <Radio>Incluir metadata DICOM</Radio>
          </Space>
        </div>
      </div>

      <Alert
        message="Información"
        description={`La imagen se exportará con las configuraciones actuales de zoom (${zoom}%), rotación (${rotation}°) y ajustes de ventana/nivel.`}
        type="info"
        showIcon
      />
    </Space>
  </Modal>
);

export default VisorExportModal;
