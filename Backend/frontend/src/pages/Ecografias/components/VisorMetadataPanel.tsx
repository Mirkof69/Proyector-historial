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
  <Col
    style={{
      width: 300,
      background: '#141414',
      borderLeft: '1px solid #434343',
      padding: 16,
      overflowY: 'auto'
    }}
  >
    <Title level={5} style={{ color: '#fff' }}>
      <InfoCircleOutlined /> Metadata DICOM
    </Title>
    <Divider style={{ background: '#434343' }} />
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
        <List.Item style={{ padding: '8px 0', borderBottom: '1px solid #434343' }}>
          <Text style={{ color: '#999', fontSize: 12 }}>{item.label}:</Text>
          <Text strong style={{ color: '#fff', fontSize: 12, marginLeft: 8 }}>
            {item.value}
          </Text>
        </List.Item>
      )}
    />

    <Divider style={{ background: '#434343' }} />

    <Title level={5} style={{ color: '#fff' }}>
      Observaciones
    </Title>
    <Paragraph style={{ color: '#ccc', fontSize: 12 }}>
      {ecografia.observaciones || 'Sin observaciones'}
    </Paragraph>

    {ecografia.diagnostico && (
      <>
        <Title level={5} style={{ color: '#fff' }}>
          Diagnóstico
        </Title>
        <Paragraph style={{ color: '#ccc', fontSize: 12 }}>
          {ecografia.diagnostico}
        </Paragraph>
      </>
    )}
  </Col>
);

export default VisorMetadataPanel;
