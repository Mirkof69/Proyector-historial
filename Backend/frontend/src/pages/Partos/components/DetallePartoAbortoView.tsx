import React from 'react';
import {
  Card, Descriptions, Space, Tag, Alert, Row, Col, Typography, Badge, Collapse,
} from 'antd';
import {
  CalendarOutlined, UserOutlined, CheckCircleOutlined, ExclamationCircleOutlined,
  InfoCircleOutlined, WarningOutlined, FileTextOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { Parto } from '../../../services/partosService';
import { Paciente } from '../../../services/pacientesService';

const { Title, Paragraph } = Typography;
const { Text } = Typography;

interface DetallePartoAbortoViewProps {
  parto: Parto;
  paciente: Paciente | null;
}

const DetallePartoAbortoView: React.FC<DetallePartoAbortoViewProps> = ({ parto, paciente }) => (
  <Row gutter={[16, 16]}>
    <Col xs={24} lg={24}>
      {/* INFORMACIÓN DEL PACIENTE */}
      {paciente && (
        <Card
          title={
            <Space>
              <UserOutlined />
              Información de la Paciente
            </Space>
          }
          style={{ marginBottom: 16 }}
        >
          <Descriptions column={{ xs: 1, sm: 2 }} bordered>
            <Descriptions.Item label="Nombre Completo">
              <Text strong>
                {paciente.nombre} {paciente.apellido_paterno}{' '}
                {paciente.apellido_materno}
              </Text>
            </Descriptions.Item>
            <Descriptions.Item label="ID Clínico">
              <Tag color="blue">{paciente.id_clinico}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="CI">{paciente.ci}</Descriptions.Item>
          </Descriptions>
        </Card>
      )}

      {/* DATOS DEL ABORTO */}
      <Card
        title={
          <Space>
            <WarningOutlined style={{ color: '#ff4d4f' }} />
            Datos del Aborto
          </Space>
        }
        style={{ marginBottom: 16 }}
      >
        <Descriptions column={{ xs: 1, sm: 2 }} bordered>
          <Descriptions.Item label="Fecha del Evento">
            <Space>
              <CalendarOutlined />
              {dayjs(parto.fecha_parto).format('DD/MM/YYYY HH:mm')}
            </Space>
          </Descriptions.Item>
          <Descriptions.Item label="Edad Gestacional">
            <Tag color="orange">{parto.edad_gestacional_parto} semanas</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Tipo de Aborto">
            <Tag color="red">
              {parto.tipo_aborto?.replace('_', ' ').toUpperCase() || 'No especificado'}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Método de Evacuación">
            {parto.metodo_evacuacion?.replace('_', ' ').toUpperCase() || 'No especificado'}
          </Descriptions.Item>
          <Descriptions.Item label="Apoyo Psicológico">
            {parto.apoyo_psicologico_realizado ? (
              <Tag color="green"><CheckCircleOutlined /> Sí proporcionado</Tag>
            ) : (
              <Tag color="orange">No proporcionado</Tag>
            )}
          </Descriptions.Item>
          <Descriptions.Item label="Protocolo de Duelo">
            {parto.protocolo_duelo_aplicado ? (
              <Tag color="green"><CheckCircleOutlined /> Sí aplicado</Tag>
            ) : (
              <Tag color="orange">No aplicado</Tag>
            )}
          </Descriptions.Item>
          {parto.perdida_sanguinea_estimada && (
            <Descriptions.Item label="Pérdida Sanguínea Estimada">
              {parto.perdida_sanguinea_estimada} mL
            </Descriptions.Item>
          )}
          {parto.hemorragia_postparto && (
            <Descriptions.Item label="Hemorragia Post-Evacuación" span={2}>
              <Tag color="red"><WarningOutlined /> Sí presente</Tag>
            </Descriptions.Item>
          )}
        </Descriptions>
      </Card>

      {/* COMPLICACIONES MATERNAS */}
      {parto.complicaciones_maternas && (
        <Card
          title={
            <Space>
              <WarningOutlined style={{ color: '#ff4d4f' }} />
              Complicaciones
            </Space>
          }
          style={{ marginBottom: 16 }}
        >
          <Alert
            message="Complicaciones Maternas"
            description={<Paragraph>{parto.complicaciones_maternas}</Paragraph>}
            type="error"
            showIcon
          />
        </Card>
      )}

      {/* OBSERVACIONES DEL ABORTO */}
      {parto.observaciones_aborto && (
        <Card
          title={
            <Space>
              <FileTextOutlined />
              Observaciones del Aborto
            </Space>
          }
          style={{ marginBottom: 16 }}
        >
          <Paragraph>{parto.observaciones_aborto}</Paragraph>
        </Card>
      )}

      {/* ✅ ALERTAS MÉDICAS */}
      {parto.alertas_parto && parto.alertas_parto.length > 0 && (
        <Card
          title={
            <Space>
              <WarningOutlined />
              Alertas Médicas
              {parto.tiene_alertas_criticas && (
                <Badge count="CRÍTICO" style={{ backgroundColor: '#f5222d' }} />
              )}
            </Space>
          }
          style={{ marginBottom: 16 }}
        >
          <Space direction="vertical" style={{ width: '100%' }} size="middle">
            {parto.alertas_parto.map((alerta: any) => (
              <Alert
                key={alerta.tipo + alerta.mensaje}
                message={alerta.mensaje}
                description={
                  <div>
                    <strong>Recomendación:</strong> {alerta.recomendacion}
                  </div>
                }
                type={alerta.nivel === 'error' ? 'error' : 'warning'}
                showIcon
                icon={alerta.tipo === 'critica' ? <ExclamationCircleOutlined /> : <WarningOutlined />}
              />
            ))}
          </Space>
        </Card>
      )}

      {/* ✅ RECOMENDACIONES MÉDICAS */}
      {parto.recomendaciones_por_edad && parto.recomendaciones_por_edad.length > 0 && (
        <Card
          title={
            <Space>
              <InfoCircleOutlined />
              Recomendaciones Médicas
            </Space>
          }
          style={{ marginBottom: 16 }}
        >
          <Alert
            message="Recomendaciones generales"
            description="Estas son recomendaciones generales basadas en la situación. Siempre consulte con el médico tratante."
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />

          <Collapse accordion defaultActiveKey={['0']}
            items={parto.recomendaciones_por_edad.map((rec: any) => {
              const getAlertType = () => {
                switch (rec.tipo) {
                  case 'urgente':
                    return 'error';
                  case 'atencion':
                    return 'warning';
                  case 'importante':
                    return 'warning';
                  default:
                    return 'info';
                }
              };

              const getIcon = () => {
                switch (rec.tipo) {
                  case 'urgente':
                  case 'atencion':
                    return <WarningOutlined />;
                  default:
                    return <InfoCircleOutlined />;
                }
              };

              return {
                key: rec.id || rec.periodo,
                label: (
                  <Space>
                    {getIcon()}
                    <strong>{rec.periodo}:</strong> {rec.titulo}
                  </Space>
                ),
                children: (
                  <Alert
                    type={getAlertType()}
                    message={rec.titulo}
                    description={
                      <ul style={{ marginBottom: 0, paddingLeft: 20 }}>
                        {rec.recomendaciones.map((r: string) => (
                          <li key={`rec-${rec.id || rec.periodo}-${r}`}>{r}</li>
                        ))}
                      </ul>
                    }
                    showIcon
                  />
                )
              };
            })}
          />
        </Card>
      )}
    </Col>
  </Row>
);

export default DetallePartoAbortoView;
