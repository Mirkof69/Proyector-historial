import React from 'react';
import { Col, Divider, Typography, List } from 'antd';
import { InfoCircleOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { DicomMetadata } from '../visorDicomReducer';

const { Title, Text, Paragraph } = Typography;

interface VisorMetadataPanelProps {
  metadata: DicomMetadata;
  ecografia: any;
}

const VisorMetadataPanel: React.FC<VisorMetadataPanelProps> = ({ metadata, ecografia }) => (
  <Col className="visor-metadatos">
    <Title level={5}>
      <InfoCircleOutlined /> Metadata DICOM
    </Title>
    <Divider className="visor-separador" />
    <List
      size="small"
      dataSource={[
        { label: 'Paciente', value: metadata.patientName },
        { label: 'ID Paciente', value: metadata.patientID },
        { label: 'Fecha Estudio', value: dayjs(metadata.studyDate).format('DD/MM/YYYY') },
        { label: 'Modalidad', value: metadata.modality },
        { label: 'Descripción', value: metadata.studyDescription },
        { label: 'Serie', value: metadata.seriesDescription },
        { label: 'Institución', value: metadata.institutionName },
        { label: 'Filas', value: metadata.rows },
        { label: 'Columnas', value: metadata.columns },
        { label: 'Fabricante', value: metadata.manufacturer },
        { label: 'Modelo', value: metadata.model },
      ]}
      renderItem={item => (
        <List.Item className="visor-metadatos__fila">
          <Text className="u-c-texto-3 u-t-xs">{item.label}:</Text>
          <Text strong className="u-t-xs u-ml-2">
            {item.value}
          </Text>
        </List.Item>
      )}
    />

    <Divider className="visor-separador" />

    <Title level={5}>
      Observaciones
    </Title>
    <Paragraph className="u-t-xs u-c-texto-2">
      {ecografia.observaciones || 'Sin observaciones'}
    </Paragraph>

    {ecografia.diagnostico && (
      <>
        <Title level={5}>
          Diagnóstico
        </Title>
        <Paragraph className="u-t-xs u-c-texto-2">
          {ecografia.diagnostico}
        </Paragraph>
      </>
    )}
  </Col>
);

export default VisorMetadataPanel;
