import React from 'react';
import {
  Card, Descriptions, Space, Tag, Alert, Row, Col, Divider, Timeline, Typography,
  Badge, Statistic, Collapse,
} from 'antd';
import {
  MedicineBoxOutlined, CalendarOutlined, ClockCircleOutlined, UserOutlined,
  HeartOutlined, CheckCircleOutlined, ExclamationCircleOutlined, InfoCircleOutlined,
  WarningOutlined, SmileOutlined, FileTextOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { Parto } from '../../../services/partosService';
import { Paciente } from '../../../services/pacientesService';
import { getViaPartoColor, getApgarInterpretacion } from '../detallePartoUtils';

const { Title, Text, Paragraph } = Typography;

interface DetallePartoViewProps {
  parto: Parto;
  paciente: Paciente | null;
  rn: any;
  duracionTP: string | null;
  categoriaEG: { text: string; color: string } | null;
  apgar5Interpretacion: { text: string; color: string; icon: React.ReactNode };
}

const DetallePartoView: React.FC<DetallePartoViewProps> = ({
  parto, paciente, rn, duracionTP, categoriaEG, apgar5Interpretacion,
}) => (
  <Row gutter={[16, 16]}>
    {/* COLUMNA IZQUIERDA */}
    <Col xs={24} lg={16}>
      {/* ESTADÍSTICAS PRINCIPALES */}
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="Tipo de Parto"
              value={parto.tipo_parto?.replace('_', ' ').toUpperCase()}
              valueStyle={{ fontSize: 16 }}
              prefix={
                <Tag color={getViaPartoColor(parto.tipo_parto || '')}>
                  {parto.tipo_parto?.split('_')[0].toUpperCase()}
                </Tag>
              }
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="Presentación"
              value={parto.presentacion_fetal?.toUpperCase()}
              valueStyle={{ fontSize: 16 }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="Duración Trabajo de Parto"
              value={duracionTP || 'No registrado'}
              valueStyle={{ fontSize: 18, color: '#1890ff' }}
              prefix={<ClockCircleOutlined />}
            />
          </Card>
        </Col>
      </Row>

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

      {/* DATOS DEL PARTO */}
      <Card
        title={
          <Space>
            <MedicineBoxOutlined />
            Datos del Parto
          </Space>
        }
        style={{ marginBottom: 16 }}
      >
        <Descriptions column={{ xs: 1, sm: 2 }} bordered>
          <Descriptions.Item label="Fecha y Hora">
            <Space>
              <CalendarOutlined />
              {dayjs(parto.fecha_parto).format('DD/MM/YYYY HH:mm')}
            </Space>
          </Descriptions.Item>
          <Descriptions.Item label="Edad Gestacional">
            <Space>
              <span>
                {parto.edad_gestacional_parto}
              </span>
              {categoriaEG && <Tag color={categoriaEG.color}>{categoriaEG.text}</Tag>}
            </Space>
          </Descriptions.Item>
          <Descriptions.Item label="Tipo de Parto">
            <Tag color={getViaPartoColor(parto.tipo_parto || '')}>
              {parto.tipo_parto?.replace('_', ' ').toUpperCase()}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Presentación">
            {parto.presentacion_fetal?.toUpperCase()}
          </Descriptions.Item>
          {parto.fecha_inicio_trabajo_parto && (
            <Descriptions.Item label="Inicio Trabajo de Parto">
              {dayjs(parto.fecha_inicio_trabajo_parto).format('DD/MM/YYYY HH:mm')}
            </Descriptions.Item>
          )}
          {duracionTP && (
            <Descriptions.Item label="Duración Trabajo de Parto">
              <Text strong>{duracionTP}</Text>
            </Descriptions.Item>
          )}
          {parto.estado_membranas && (
            <Descriptions.Item label="Estado Membranas">
              {parto.estado_membranas.replace('_', ' ').toUpperCase()}
            </Descriptions.Item>
          )}
          {parto.caracteristicas_liquido && (
            <Descriptions.Item label="Líquido Amniótico">
              {parto.caracteristicas_liquido}
            </Descriptions.Item>
          )}
          {parto.tipo_alumbramiento && (
            <Descriptions.Item label="Alumbramiento" span="filled">
              {parto.tipo_alumbramiento.toUpperCase()}
            </Descriptions.Item>
          )}
        </Descriptions>
      </Card>

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

          {parto.tipo_parto_segun_edad && (
            <Alert
              message={parto.tipo_parto_segun_edad.descripcion}
              type="info"
              showIcon
              style={{ marginTop: 16 }}
            />
          )}
        </Card>
      )}

      {/* ✅ RECOMENDACIONES MÉDICAS */}
      {parto.recomendaciones_por_edad && parto.recomendaciones_por_edad.length > 0 && (
        <Card
          title={
            <Space>
              <InfoCircleOutlined />
              Recomendaciones Médicas por Edad Gestacional
            </Space>
          }
          style={{ marginBottom: 16 }}
        >
          <Alert
            message="Recomendaciones generales"
            description="Estas son recomendaciones generales basadas en la edad gestacional. Siempre consulte con el médico tratante."
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

      {/* SCORE DE APGAR */}
      <Card
        title={
          <Space>
            <HeartOutlined />
            Score de Apgar
          </Space>
        }
        style={{ marginBottom: 16 }}
      >
        {(() => {
          const apgar1 = rn?.apgar_1_minuto || parto.apgar_1min || 0;
          const apgar5 = rn?.apgar_5_minutos || parto.apgar_5min || 0;
          const apgar1Interpretacion = getApgarInterpretacion(apgar1);
          const apgar5Interpretacion = getApgarInterpretacion(apgar5);

          return (
            <Row gutter={[24, 24]}>
              <Col span={24} md={12}>
                <Card type="inner" title="Apgar al 1 minuto">
                  <div style={{ textAlign: 'center' }}>
                    <Title level={1} style={{ margin: 0, color: apgar1Interpretacion.color === 'error' ? '#ff4d4f' : (apgar1Interpretacion.color === 'warning' ? '#faad14' : '#52c41a') }}>
                      {apgar1}
                    </Title>
                    <Divider style={{ margin: '12px 0' }} />
                    <Alert
                      message={apgar1Interpretacion.text}
                      type={apgar1Interpretacion.color as any}
                      showIcon
                      icon={apgar1Interpretacion.icon}
                    />
                  </div>
                </Card>
              </Col>
              <Col span={24} md={12}>
                <Card type="inner" title="Apgar a los 5 minutos">
                  <div style={{ textAlign: 'center' }}>
                    <Title level={1} style={{ margin: 0, color: apgar5Interpretacion.color === 'error' ? '#ff4d4f' : (apgar5Interpretacion.color === 'warning' ? '#faad14' : '#52c41a') }}>
                      {apgar5}
                    </Title>
                    <Divider style={{ margin: '12px 0' }} />
                    <Alert
                      message={apgar5Interpretacion.text}
                      type={apgar5Interpretacion.color as any}
                      showIcon
                      icon={apgar5Interpretacion.icon}
                    />
                  </div>
                </Card>
              </Col>
            </Row>
          );
        })()}
      </Card>

      {/* COMPLICACIONES */}
      {(parto.complicaciones_maternas || (rn?.complicaciones_neonatales)) && (
        <Card
          title={
            <Space>
              <WarningOutlined style={{ color: '#ff4d4f' }} />
              Complicaciones
            </Space>
          }
          style={{ marginBottom: 16 }}
        >
          {parto.complicaciones_maternas && (
            <>
              <Title level={5}>Complicaciones Maternas</Title>
              <Alert
                message="Complicaciones en la Madre"
                description={<Paragraph>{parto.complicaciones_maternas}</Paragraph>}
                type="error"
                showIcon
                style={{ marginBottom: 16 }}
              />
            </>
          )}
          {rn?.complicaciones_neonatales && (
            <>
              <Title level={5}>Complicaciones Neonatales</Title>
              <Alert
                message="Complicaciones en el Recién Nacido"
                description={<Paragraph>{rn.complicaciones_neonatales}</Paragraph>}
                type="warning"
                showIcon
              />
            </>
          )}
        </Card>
      )}

      {/* OBSERVACIONES */}
      {parto.observaciones_parto && (
        <Card
          title={
            <Space>
              <FileTextOutlined />
              Observaciones
            </Space>
          }
          style={{ marginBottom: 16 }}
        >
          <Paragraph>{parto.observaciones_parto}</Paragraph>
        </Card>
      )}
    </Col>

    {/* COLUMNA DERECHA */}
    <Col xs={24} lg={8}>
      {/* RESUMEN RÁPIDO */}
      <Card
        title={
          <Space>
            <InfoCircleOutlined />
            Resumen Rápido
          </Space>
        }
        style={{ marginBottom: 16 }}
      >
        <Timeline
          items={[
            {
              color: 'blue',
              dot: <CalendarOutlined />,
              children: (
                <>
                  <Text strong>Fecha del Parto</Text>
                  <br />
                  <Text>{dayjs(parto.fecha_parto).format('DD/MM/YYYY HH:mm')}</Text>
                </>
              ),
            },
            {
              color: 'green',
              dot: <CheckCircleOutlined />,
              children: (
                <>
                  <Text strong>Tipo de Parto</Text>
                  <br />
                  <Tag color={getViaPartoColor(parto.tipo_parto || '')}>
                    {parto.tipo_parto?.replace('_', ' ').toUpperCase()}
                  </Tag>
                </>
              ),
            },
            {
              color: 'purple',
              dot: <SmileOutlined />,
              children: (
                <>
                  <Text strong>Recién Nacido</Text>
                  <br />
                  {rn ? (
                    <Text>
                      {rn.sexo === 'masculino' ? 'Masculino' : 'Femenino'} -{' '}
                      {rn.peso_nacimiento}g
                    </Text>
                  ) : <Text>Sin datos</Text>}
                </>
              ),
            },
            {
              color: apgar5Interpretacion.color === 'success'
                ? 'green'
                : apgar5Interpretacion.color === 'warning'
                  ? 'orange'
                  : 'red',
              dot: <HeartOutlined />,
              children: (
                <>
                  <Text strong>Apgar 5 min</Text>
                  <br />
                  <Text>{rn?.apgar_5_minutos || parto.apgar_5min} - {apgar5Interpretacion.text}</Text>
                </>
              ),
            },
          ]}
        />
      </Card>

      {/* INFORMACIÓN ADICIONAL */}
      <Card
        title={
          <Space>
            <InfoCircleOutlined />
            Información Adicional
          </Space>
        }
      >
        <Descriptions column={1} bordered size="small">
          {parto.medico_responsable && (
            <Descriptions.Item label="Médico Responsable">
              ID: {parto.medico_responsable}
            </Descriptions.Item>
          )}
        </Descriptions>
      </Card>
    </Col>
  </Row>
);

export default DetallePartoView;
