import React from 'react';
import { Modal, Space, Button, Card, Descriptions, Tag, Badge, Divider, Timeline, Input, Typography } from 'antd';
import {
  HistoryOutlined, FileTextOutlined, ManOutlined, ExperimentOutlined,
  CalendarOutlined, CheckCircleOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import {
  EmbarazoExtendido, RISK_COLORS, RISK_LABELS, STATUS_COLORS, STATUS_LABELS,
} from '../embarazosReducer';

const { Text, Paragraph } = Typography;
const { TextArea } = Input;

const fileTextOutlinedIcon8 = <FileTextOutlined />;
const calendarOutlinedIcon9 = <CalendarOutlined />;
const checkCircleOutlinedIcon8 = <CheckCircleOutlined />;

interface HistorialModalProps {
  visible: boolean;
  onClose: () => void;
  selectedEmbarazo: EmbarazoExtendido | null;
}

const HistorialModal: React.FC<HistorialModalProps> = ({ visible, onClose, selectedEmbarazo }) => (
  <Modal
    title={
      <Space>
        <HistoryOutlined />
        <span>Historial Completo del Embarazo</span>
      </Space>
    }
    open={visible}
    onCancel={onClose}
    width={900}
    footer={[
      <Button key="close" onClick={onClose}>
        Cerrar
      </Button>,
      <Button key="export" icon={fileTextOutlinedIcon8} type="primary">
        Exportar Historial
      </Button>
    ]}
  >
    {selectedEmbarazo && (
      <div>
        <Card size="small" style={{ marginBottom: 16 }}>
          <Descriptions column={2} size="small">
            <Descriptions.Item label="Paciente">
              <Text strong>{selectedEmbarazo?.paciente_nombre}</Text>
            </Descriptions.Item>
            <Descriptions.Item label="Estado">
              <Badge status={(STATUS_COLORS as any)[selectedEmbarazo?.estado || 'activo']} text={(STATUS_LABELS as any)[selectedEmbarazo?.estado || 'activo']} />
            </Descriptions.Item>
            <Descriptions.Item label="Edad Gestacional">
              {selectedEmbarazo.edad_gestacional_semanas_num || 0}s + {selectedEmbarazo.edad_gestacional_dias_num || 0}d
            </Descriptions.Item>
            <Descriptions.Item label="Riesgo">
              <Tag color={(RISK_COLORS as any)[selectedEmbarazo.riesgo_embarazo || 'bajo']}>
                {(RISK_LABELS as any)[selectedEmbarazo.riesgo_embarazo || 'bajo']}
              </Tag>
            </Descriptions.Item>
          </Descriptions>
        </Card>

        <Divider orientation="left">
          <Space>
            <ManOutlined />
            <span>Antecedentes Obstétricos</span>
          </Space>
        </Divider>
        <Paragraph style={{ background: '#f5f5f5', padding: 12, borderRadius: 4 }}>
          <Text strong>Gesta:</Text> {selectedEmbarazo.numero_gesta} •{' '}
          <Text strong>Partos previos:</Text> {selectedEmbarazo.partos_previos || 0} •{' '}
          <Text strong>Cesáreas:</Text> {selectedEmbarazo.cesareas_previas || 0} •{' '}
          <Text strong>Abortos:</Text> {selectedEmbarazo.abortos_previos || 0}
        </Paragraph>

        <Divider orientation="left">
          <Space>
            <ExperimentOutlined />
            <span>Notas Clínicas</span>
          </Space>
        </Divider>
        <TextArea
          rows={4}
          value={selectedEmbarazo.notas || 'Sin notas registradas'}
          readOnly
          style={{ marginBottom: 16 }}
        />

        <Divider orientation="left">Línea de Tiempo</Divider>
        <Timeline>
          <Timeline.Item color="blue" dot={calendarOutlinedIcon9}>
            <Text strong>FUM:</Text> {dayjs(selectedEmbarazo.fecha_ultima_menstruacion).format('DD/MM/YYYY')}
          </Timeline.Item>
          {selectedEmbarazo.fecha_probable_parto && (
            <Timeline.Item color="green" dot={checkCircleOutlinedIcon8}>
              <Text strong>FPP:</Text> {dayjs(selectedEmbarazo.fecha_probable_parto).format('DD/MM/YYYY')}
              {' '}({dayjs(selectedEmbarazo.fecha_probable_parto).diff(dayjs(), 'days')} días restantes)
            </Timeline.Item>
          )}
          <Timeline.Item color="gray">
            <Text type="secondary">Registro creado el {dayjs().format('DD/MM/YYYY')}</Text>
          </Timeline.Item>
        </Timeline>
      </div>
    )}
  </Modal>
);

export default HistorialModal;
