import React from 'react';
import { Card, Row, Col, Button, Space, Alert, List, Badge, Statistic, Empty, Tabs } from 'antd';
import { LineChartOutlined, EditOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { DicomMetadata } from '../visorDicomReducer';
import { tabResumen } from '../visorDicomTabs';

interface VisorMedicionesCardProps {
  measurements: any[];
  annotations: any[];
  tabMedicionesLabel: React.ReactNode;
  tabAnotacionesLabel: React.ReactNode;
  metadata: DicomMetadata;
  deleteMeasurement: (id: number) => void;
  deleteAnnotation: (id: number) => void;
}

const VisorMedicionesCard: React.FC<VisorMedicionesCardProps> = ({
  measurements, annotations, tabMedicionesLabel, tabAnotacionesLabel,
  metadata, deleteMeasurement, deleteAnnotation,
}) => (
  <Card
    title={
      <Space>
        <LineChartOutlined />
        <span>Mediciones y Anotaciones</span>
        <Badge count={measurements.length + annotations.length} showZero />
      </Space>
    }
    style={{ marginTop: 16 }}
  >
    <Tabs defaultActiveKey="measurements" type="card" items={[
      {
        key: "measurements",
        label: tabMedicionesLabel,
        children: measurements.length === 0 ? (
          <Empty description="No hay mediciones. Haz click en la imagen con la herramienta de medición activa para agregar." />
        ) : (
          <List
            dataSource={measurements}
            renderItem={measurement => (
              <List.Item
                key={measurement.id}
                actions={[
                  <Button
                    key="delete"
                    type="text"
                    danger
                    size="small"
                    onClick={() => deleteMeasurement(measurement.id)}
                  >
                    Eliminar
                  </Button>
                ]}
              >
                <List.Item.Meta
                  avatar={<LineChartOutlined style={{ fontSize: 20, color: '#1890ff' }} />}
                  title={`Medición ${measurement.type}: ${measurement.length.toFixed(2)}mm`}
                  description={`Posición: (${measurement.x}, ${measurement.y}) - ${dayjs(measurement.timestamp).format('DD/MM/YYYY HH:mm:ss')}`}
                />
              </List.Item>
            )}
          />
        )
      },
      {
        key: "annotations",
        label: tabAnotacionesLabel,
        children: annotations.length === 0 ? (
          <Empty description="No hay anotaciones. Haz click en la imagen con la herramienta de anotación activa para agregar." />
        ) : (
          <List
            dataSource={annotations}
            renderItem={annotation => (
              <List.Item
                key={annotation.id}
                actions={[
                  <Button
                    key="delete"
                    type="text"
                    danger
                    size="small"
                    onClick={() => deleteAnnotation(annotation.id)}
                  >
                    Eliminar
                  </Button>
                ]}
              >
                <List.Item.Meta
                  avatar={<EditOutlined style={{ fontSize: 20, color: annotation.color }} />}
                  title={annotation.text}
                  description={`Posición: (${annotation.x}, ${annotation.y}) - ${dayjs(annotation.timestamp).format('DD/MM/YYYY HH:mm:ss')}`}
                />
              </List.Item>
            )}
          />
        )
      },
      {
        key: "summary",
        label: tabResumen,
        children: (
          <Row gutter={16}>
            <Col span={12}>
              <Statistic
                title="Total Mediciones"
                value={measurements.length}
                prefix={<LineChartOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Col>
            <Col span={12}>
              <Statistic
                title="Total Anotaciones"
                value={annotations.length}
                prefix={<EditOutlined />}
                valueStyle={{ color: '#52c41a' }}
              />
            </Col>
            <Col span={24} style={{ marginTop: 16 }}>
              <Alert
                message="Herramientas de Análisis"
                description={`Utiliza las herramientas de medición y anotación para marcar áreas de interés en la imagen DICOM. Las mediciones se calculan en tiempo real basándose en el pixel spacing (${metadata.pixelSpacing?.[0]} mm/px).`}
                type="info"
                showIcon
              />
            </Col>
          </Row>
        )
      }
    ]} />
  </Card>
);

export default VisorMedicionesCard;
