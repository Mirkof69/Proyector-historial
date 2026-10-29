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
          <Card
            size="small"
            className={`citas-page__cifra-sola ${cita.dias_hasta_cita < 0 ? 'citas-page__cifra--peligro' : cita.dias_hasta_cita <= 3 ? 'citas-page__cifra--aviso' : 'citas-page__cifra--exito'}`}
          >
            <Statistic
              title={<><CalendarOutlined />Días hasta la cita</>}
              value={cita.dias_hasta_cita}
              suffix="días"
            />
          </Card>
        </Col>
      </Row>
    )}

    <Card title="Acciones Rápidas" size="small" className="citas-arriba">
      <Space direction="vertical" className="citas-ancho">
        {cita.estado === 'agendada' && !dayjs(cita.fecha_cita).isBefore(dayjs(), 'day') && (
          <Button icon={<CheckCircleOutlined />} onClick={onConfirmar} block>
            Confirmar Cita
          </Button>
        )}
        {['agendada', 'confirmada'].includes(cita.estado) && dayjs(cita.fecha_cita).isAfter(dayjs(), 'day') && (
          <Button icon={<BellOutlined />} onClick={onEnviarRecordatorio} block>
            Enviar Recordatorio
          </Button>
        )}
        {['agendada', 'confirmada', 'en_espera'].includes(cita.estado) && (
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
            <HistoryOutlined /> 
            Historial de Cambios
          </>
        }
        size="small"
        className="citas-arriba"
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
                    <small className="citas-page__secundario">{h.observacion}</small>
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
