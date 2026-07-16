import React from 'react';
import { Card, Button, Space, Tag, Typography, Alert, Timeline, Row, Col, Statistic, Spin, Empty, Modal, Divider } from 'antd';
import {
  MedicineBoxOutlined, SoundOutlined, ExperimentOutlined, WarningOutlined,
  CheckCircleOutlined, InfoCircleOutlined, HistoryOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';

const { Text, Paragraph } = Typography;

interface TimelineCompletoModalProps {
  open: boolean;
  loadingTimeline: boolean;
  timelineData: any;
  onClose: () => void;
}

const TimelineCompletoModal: React.FC<TimelineCompletoModalProps> = ({
  open, loadingTimeline, timelineData, onClose,
}) => (
  <Modal
    title={
      <Space>
        <HistoryOutlined style={{ color: '#722ed1' }} />
        <span>Timeline Completo del Embarazo</span>
      </Space>
    }
    open={open}
    onCancel={onClose}
    footer={[
      <Button
        key="close"
        onClick={onClose}
      >
        Cerrar
      </Button>,
    ]}
    width={1000}
  >
    <Spin spinning={loadingTimeline}>
      {timelineData ? (
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <Alert
            message="Historial Completo"
            description="Todos los eventos registrados del embarazo en orden cronológico."
            type="info"
            showIcon
            icon={<HistoryOutlined />}
          />

          <Timeline
            mode="left"
            items={timelineData.eventos && timelineData.eventos.length > 0 ? (
              timelineData.eventos.map((evento: any, index: number) => {
                const iconMap: Record<string, any> = {
                  control: <MedicineBoxOutlined />,
                  ecografia: <SoundOutlined />,
                  laboratorio: <ExperimentOutlined />,
                  riesgo: <WarningOutlined />,
                  complicacion: <WarningOutlined />,
                  registro: <CheckCircleOutlined />,
                };

                const colorMap: Record<string, string> = {
                  control: 'blue',
                  ecografia: 'cyan',
                  laboratorio: 'purple',
                  riesgo: 'orange',
                  complicacion: 'red',
                  registro: 'green',
                };

                return {
                  key: evento.id || `evt-${evento.tipo}-${evento.fecha}`,
                  color: colorMap[evento.tipo] || 'gray',
                  dot: iconMap[evento.tipo],
                  label: evento.fecha
                    ? dayjs(evento.fecha).format('DD/MM/YYYY HH:mm')
                    : 'Fecha desconocida',
                  children: (
                    <Card size="small" style={{ marginBottom: 8 }}>
                      <Space direction="vertical" size={4} style={{ width: '100%' }}>
                        <Text strong style={{ fontSize: 14 }}>
                          {evento.titulo || evento.descripcion}
                        </Text>
                        {evento.tipo && (
                          <Tag color={colorMap[evento.tipo]}>
                            {evento.tipo.toUpperCase()}
                          </Tag>
                        )}
                        {evento.detalle && (
                          <Text type="secondary" style={{ fontSize: 12 }}>
                            {evento.detalle}
                          </Text>
                        )}
                        {evento.observaciones && (
                          <Paragraph
                            type="secondary"
                            style={{ fontSize: 12, marginBottom: 0 }}
                            ellipsis={{ rows: 2, expandable: true }}
                          >
                            {evento.observaciones}
                          </Paragraph>
                        )}
                      </Space>
                    </Card>
                  )
                };
              })
            ) : [
              {
                color: 'gray',
                children: <Empty description="No hay eventos registrados" />
              }
            ]}
          />

          {timelineData.estadisticas && (
            <>
              <Divider orientation="left">Estadísticas del Embarazo</Divider>
              <Row gutter={16}>
                <Col span={6}>
                  <Statistic
                    title="Total Controles"
                    value={timelineData.estadisticas.total_controles || 0}
                    prefix={<MedicineBoxOutlined />}
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="Ecografías"
                    value={timelineData.estadisticas.total_ecografias || 0}
                    prefix={<SoundOutlined />}
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="Laboratorios"
                    value={timelineData.estadisticas.total_laboratorios || 0}
                    prefix={<ExperimentOutlined />}
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="Eventos Totales"
                    value={timelineData.eventos?.length || 0}
                    prefix={<InfoCircleOutlined />}
                  />
                </Col>
              </Row>
            </>
          )}
        </Space>
      ) : (
        !loadingTimeline && (
          <Empty description="No hay datos de timeline disponibles" />
        )
      )}
    </Spin>
  </Modal>
);

export default TimelineCompletoModal;
