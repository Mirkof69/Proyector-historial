import React from 'react';
import { Row, Col, Card, Space, Tag, Button, Descriptions, Divider, List, Alert, Typography } from 'antd';
import {
  CheckCircleOutlined, CloseCircleOutlined, ClockCircleOutlined, FileTextOutlined,
} from '@ant-design/icons';
import { useAntdApp } from '../../../hooks/useMessage';
import { Laboratorio, Ecografia } from '../types';
import { PROTOCOLOS_EMBARAZO } from '../utils';

const { Text } = Typography;

interface ProtocoloItemProps {
  protocolo: any;
  calcularEGActual: () => { semanas: number };
  laboratorios: Laboratorio[];
  ecografias: Ecografia[];
}
const ProtocoloItem: React.FC<ProtocoloItemProps> = ({ protocolo, calcularEGActual, laboratorios, ecografias }) => {
  const { modal } = useAntdApp();
  const { semanas } = calcularEGActual();
  const enVentana = semanas >= protocolo.semanas_inicio && semanas <= protocolo.semanas_fin;
  const fueraDeTiempo = semanas > protocolo.semanas_fin;
  const cumplido = protocolo.examenes_requeridos.some((examen: any) => {
    const examenLower = String(examen || '').toLowerCase();
    return laboratorios.some(l => String(l.tipo_examen || '').toLowerCase().includes(examenLower)) ||
      ecografias.some(e => String(e.tipo || '').toLowerCase().includes(examenLower));
  });
  return (
    <Card key={protocolo.id} style={{ marginBottom: 16 }} type={enVentana ? 'inner' : undefined} styles={{ body: { boxShadow: enVentana ? 'inset 4px 0 0 #1890ff' : undefined } }}>
      <Row align="middle" gutter={16}>
        <Col flex="auto">
          <Space direction="vertical" style={{ width: '100%' }}>
            <Space>
              <Text strong style={{ fontSize: 16 }}>{protocolo.nombre}</Text>
              {cumplido && <Tag color="success" icon={<CheckCircleOutlined />}>CUMPLIDO</Tag>}
              {!cumplido && fueraDeTiempo && <Tag color="error" icon={<CloseCircleOutlined />}>FUERA DE TIEMPO</Tag>}
              {!cumplido && enVentana && <Tag color="warning" icon={<ClockCircleOutlined />}>PENDIENTE</Tag>}
              {!cumplido && !enVentana && !fueraDeTiempo && <Tag color="default">PRÓXIMAMENTE</Tag>}
            </Space>
            <Text type="secondary">{protocolo.descripcion}</Text>
            <Text type="secondary" style={{ fontSize: 12 }}>Ventana: {protocolo.semanas_inicio}-{protocolo.semanas_fin} semanas</Text>
          </Space>
        </Col>
        <Col>
          <Button type={enVentana ? 'primary' : 'default'} icon={<FileTextOutlined />} onClick={() => {
            modal.info({
              title: protocolo.nombre, width: 700,
              content: (
                <div>
                  <Descriptions bordered column={1} size="small">
                    <Descriptions.Item label="Descripción">{protocolo.descripcion}</Descriptions.Item>
                    <Descriptions.Item label="Ventana Temporal">{protocolo.semanas_inicio} - {protocolo.semanas_fin} semanas</Descriptions.Item>
                    <Descriptions.Item label="Estado">{cumplido ? <Tag color="success">CUMPLIDO</Tag> : fueraDeTiempo ? <Tag color="error">FUERA DE TIEMPO</Tag> : enVentana ? <Tag color="warning">PENDIENTE</Tag> : <Tag color="default">PRÓXIMAMENTE</Tag>}</Descriptions.Item>
                  </Descriptions>
                  <Divider orientation="left">Exámenes Requeridos</Divider>
                  <List size="small" dataSource={protocolo.examenes_requeridos || []} renderItem={(examen: any) => {
                    const examenLower = String(examen || '').toLowerCase();
                    const realizado = laboratorios.some(l => String(l.tipo_examen || '').toLowerCase().includes(examenLower)) || ecografias.some(e => String(e.tipo || '').toLowerCase().includes(examenLower));
                    return (<List.Item key={`exam-${examen}`}>{realizado ? <CheckCircleOutlined style={{ color: '#52c41a', marginRight: 8 }} /> : <CloseCircleOutlined style={{ color: '#ff4d4f', marginRight: 8 }} />}{examen}{realizado && <Tag color="success" style={{ marginLeft: 8 }}>Realizado</Tag>}</List.Item>);
                  }} />
                </div>
              )
            });
          }}>Ver Detalles</Button>
        </Col>
      </Row>
    </Card>
  );
};

interface TabProtocolosCumplimientoProps {
  calcularEGActual: () => { semanas: number };
  laboratorios: Laboratorio[];
  ecografias: Ecografia[];
}
const TabProtocolosCumplimiento: React.FC<TabProtocolosCumplimientoProps> = ({ calcularEGActual, laboratorios, ecografias }) => (
  <div>
    <Alert message="Protocolos de Atención Prenatal" description="Seguimiento del cumplimiento de guías clínicas MSP/OMS para control prenatal" type="info" showIcon style={{ marginBottom: 16 }} />
    <List
      dataSource={PROTOCOLOS_EMBARAZO}
      renderItem={(protocolo) => (
        <ProtocoloItem
          protocolo={protocolo}
          calcularEGActual={calcularEGActual}
          laboratorios={laboratorios}
          ecografias={ecografias}
        />
      )}
    />
  </div>
);

export default TabProtocolosCumplimiento;
