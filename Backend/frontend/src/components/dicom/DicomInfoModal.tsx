import React from 'react';
import { Modal, Space, Alert, Card, Button } from 'antd';

interface DicomInfoModalProps {
  open: boolean;
  onClose: () => void;
  patientName: string;
  studyDate: string;
  modality: string;
  stableSeriesId: string;
  stableStudyId: string;
}

const DicomInfoModal: React.FC<DicomInfoModalProps> = ({
  open, onClose, patientName, studyDate, modality, stableSeriesId, stableStudyId,
}) => (
  <Modal
    title="Información del Estudio DICOM"
    open={open}
    onCancel={onClose}
    footer={[
      <Button key="close" type="primary" onClick={onClose}>
        Cerrar
      </Button>
    ]}
    width={600}
  >
    <Space direction="vertical" style={{ width: '100%' }}>
      <Alert
        message="Datos del Estudio"
        description="Información extraída del archivo DICOM"
        type="info"
        showIcon
      />

      <Card size="small">
        <p><strong>Nombre del Paciente:</strong> {patientName}</p>
        <p><strong>Fecha del Estudio:</strong> <span suppressHydrationWarning>{new Date(studyDate).toISOString().slice(0, 16).replace('T', ' ')}</span></p>
        <p><strong>Modalidad:</strong> {modality} (Ultrasonido)</p>
        <p><strong>Institución:</strong> Hospital Materno Infantil</p>
        <p><strong>Médico Tratante:</strong> Dr. [A asignar]</p>
        <p><strong>Número de Serie:</strong> {stableSeriesId}</p>
        <p><strong>ID del Estudio:</strong> {stableStudyId}</p>
      </Card>

      <Alert
        message="⚠️ Nota Importante"
        description="Este visor es para fines de visualización y anotación. Para diagnóstico oficial, consulte con un radiólogo certificado."
        type="warning"
        showIcon
      />
    </Space>
  </Modal>
);

export default DicomInfoModal;
