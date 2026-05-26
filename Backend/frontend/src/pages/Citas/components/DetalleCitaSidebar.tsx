import React from 'react';
import { Card, Row, Col, Space, Button, Timeline, Statistic } from 'antd';
import {
  CalendarOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  BellOutlined,
  HistoryOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { Cita } from '../../../services/citasService';

interface DetalleCitaSidebarProps {
  cita: Cita;
  onConfirmar: () => void;
  onCancelar: () => void;
  onEnviarRecordatorio: () => void;
}

const DetalleCitaSidebar: React.FC<DetalleCitaSidebarProps> = ({
  cita,
  onConfirmar,
  onCancelar,
  onEnviarRecordatorio,
}) => (
  <>
    {cita.dias_hasta_cita !== undefined && (
      <Row gutter={[16, 16]}>
        <Col xs={24}>
          <Card hoverable>
            <Statistic
              title="Días hasta la cita"
              value={cita.dias_hasta_cita}
              suffix="días"
              prefix={<CalendarOutlined />}
              valueStyle={{
                color: cita.dias_hasta_cita < 0 ? '#ff4d4f' : cita.dias_hasta_cita <= 3 ? '#faad14' : '#52c41a'
              }}
            />
          </Card>
        </Col>
      </Row>
    )}

    <Card title="Acciones Rápidas" size="small" style={{ marginTop: 16 }}>
      <Space direction="vertical" style={{ width: '100%' }}>
        {cita.estado === 'agendada' && (
          <Button type="primary" icon={<CheckCircleOutlined />} onClick={onConfirmar} block>
            Confirmar Cita
          </Button>
        )}
        {['agendada', 'confirmada'].includes(cita.estado) && (
          <Button icon={<BellOutlined />} onClick={onEnviarRecordatorio} block>
            Enviar Recordatorio
          </Button>
        )}
        {!['completada', 'cancelada', 'no_asistio'].includes(cita.estado) && (
          <Button danger icon={<CloseCircleOutlined />} onClick={onCancelar} block>
            Cancelar Cita
          </Button>
        )}
      </Space>
    </Card>

    {cita.historial && cita.historial.length > 0 && (
      <Card
        title={
          <>
            <HistoryOutlined style={{ marginRight: 8 }} />
            Historial de Cambios
          </>
        }
        size="small"
        style={{ marginTop: 16 }}
      >
        <Timeline
          items={cita.historial.map((h) => ({
            color: 'blue',
            children: (
              <>
                <strong>{h.accion}</strong>
                <br />
                <small>{dayjs(h.fecha).format('DD/MM/YYYY HH:mm')}</small>
                <br />
                <small>Por: {h.usuario_nombre}</small>
                {h.observacion && (
                  <>
                    <br />
                    <small style={{ color: '#8c8c8c' }}>{h.observacion}</small>
                  </>
                )}
              </>
            ),
          }))}
        />
      </Card>
    )}
  </>
);

export default DetalleCitaSidebar;
