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
  <Modal rootClassName="capa-clinica"
    title={<><DownloadOutlined /> Exportar Imagen</>}
    open={exportModalVisible}
    onCancel={() => dispatch({ type: 'SET_EXPORT_MODAL_VISIBLE', payload: false })}

    onOk={() => {
      handleExportImage();
      dispatch({ type: 'SET_EXPORT_MODAL_VISIBLE', payload: false });
    }}
    width={500}
  >
    <Space direction="vertical" size="large" className="u-ancho">
      <div>
        <Text strong>Formato de Exportación:</Text>
        <Radio.Group defaultValue="png" className="u-mt-2 u-ancho">
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
          className="u-ancho u-mt-2"
          options={[
            { value: 'low', label: 'Baja (compresión alta)' },
            { value: 'medium', label: 'Media (balanceada)' },
            { value: 'high', label: 'Alta (sin compresión)' }
          ]}
        />
      </div>

      <div>
        <Text strong>Incluir en la exportación:</Text>
        <div className="u-mt-2">
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
