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

const { Paragraph } = Typography;
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
          className="partos-separado"
        >
          <Descriptions column={{ xs: 1, sm: 2 }} bordered>
            <Descriptions.Item label="Nombre Completo">
              <Text strong>
                {paciente.nombre} {paciente.apellido_paterno}{' '}
                {paciente.apellido_materno}
              </Text>
            </Descriptions.Item>
            <Descriptions.Item label="ID Clínico">
              <span className="texto-mono">{paciente.id_clinico}</span>
            </Descriptions.Item>
            <Descriptions.Item label="CI">{paciente.ci}</Descriptions.Item>
          </Descriptions>
        </Card>
      )}

      {/* DATOS DEL ABORTO */}
      <Card
        title={
          <Space>
            <WarningOutlined className="partos-peligro" />
            Datos del Aborto
          </Space>
        }
        className="partos-separado"
      >
        <Descriptions column={{ xs: 1, sm: 2 }} bordered>
          <Descriptions.Item label="Fecha del Evento">
            <Space>
              <CalendarOutlined />
              {dayjs(parto.fecha_parto).format('DD/MM/YYYY HH:mm')}
            </Space>
          </Descriptions.Item>
          <Descriptions.Item label="Edad Gestacional">
            <Tag color="warning">{parto.edad_gestacional_parto} semanas</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Tipo de Aborto">
            <Tag color="error">
              {parto.tipo_aborto?.replace('_', ' ').toUpperCase() || 'No especificado'}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Método de Evacuación">
            {parto.metodo_evacuacion?.replace('_', ' ').toUpperCase() || 'No especificado'}
          </Descriptions.Item>
          <Descriptions.Item label="Apoyo Psicológico">
            {parto.apoyo_psicologico_realizado ? (
              <Tag color="success"><CheckCircleOutlined /> Sí proporcionado</Tag>
            ) : (
              <Tag color="warning">No proporcionado</Tag>
            )}
          </Descriptions.Item>
          <Descriptions.Item label="Protocolo de Duelo">
            {parto.protocolo_duelo_aplicado ? (
              <Tag color="success"><CheckCircleOutlined /> Sí aplicado</Tag>
            ) : (
              <Tag color="warning">No aplicado</Tag>
            )}
          </Descriptions.Item>
          {parto.perdida_sanguinea_estimada && (
            <Descriptions.Item label="Pérdida Sanguínea Estimada">
              {parto.perdida_sanguinea_estimada} mL
            </Descriptions.Item>
          )}
          {parto.hemorragia_postparto && (
            <Descriptions.Item label="Hemorragia Post-Evacuación" span="filled">
              <Tag color="error"><WarningOutlined /> Sí presente</Tag>
            </Descriptions.Item>
          )}
        </Descriptions>
      </Card>

      {/* COMPLICACIONES MATERNAS */}
      {parto.complicaciones_maternas && (
        <Card
          title={
            <Space>
              <WarningOutlined className="partos-peligro" />
              Complicaciones
            </Space>
          }
          className="partos-separado"
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
          className="partos-separado"
        >
          <Paragraph>{parto.observaciones_aborto}</Paragraph>
        </Card>
      )}

      {/* ALERTAS MÉDICAS */}
      {parto.alertas_parto && parto.alertas_parto.length > 0 && (
        <Card
          title={
            <Space>
              <WarningOutlined />
              Alertas Médicas
              {parto.tiene_alertas_criticas && (
                <Badge className="partos-critico" count="CRÍTICO" />
              )}
            </Space>
          }
          className="partos-separado"
        >
          <Space direction="vertical" className="partos-ancho" size="middle">
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

      {/* RECOMENDACIONES MÉDICAS */}
      {parto.recomendaciones_por_edad && parto.recomendaciones_por_edad.length > 0 && (
        <Card
          title={
            <Space>
              <InfoCircleOutlined />
              Recomendaciones Médicas
            </Space>
          }
          className="partos-separado"
        >
          <Alert
            message="Recomendaciones generales"
            description="Estas son recomendaciones generales basadas en la situación. Siempre consulte con el médico tratante."
            type="info"
            showIcon
            className="partos-separado"
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
                      <ul className="partos-lista">
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
