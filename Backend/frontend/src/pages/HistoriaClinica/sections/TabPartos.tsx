import React from 'react';
import { Empty, Card, Row, Col, Statistic, Button, Table, Tag, Descriptions, Space, Tooltip, Typography, Alert } from 'antd';
import { PlusOutlined, WomanOutlined, WarningOutlined, CheckCircleOutlined, EyeOutlined, DownloadOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import duration from 'dayjs/plugin/duration';
import { Parto } from '../types';

dayjs.extend(duration);

const { Title, Text } = Typography;

interface TabPartosProps {
  partos: Parto[];
  pacienteId: string | number | undefined;
  navigate: (path: string) => void;
}

const TabPartos: React.FC<TabPartosProps> = ({ partos, pacienteId, navigate }) => (
  <div>
    <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
      <Title level={4}>Historial de Partos</Title>
      <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate(`/partos/nuevo?paciente=${pacienteId}`)}>
        Registrar Parto
      </Button>
    </div>

    {partos.length > 0 ? (
      <>
        {/* ESTADÍSTICAS RÁPIDAS DE PARTOS */}
        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col span={6}>
            <Card>
              <Statistic
                title="Total Partos"
                value={partos.length}
                prefix={<WomanOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="Eutócicos"
                value={partos.filter(p => p.tipo_parto === 'eutocico').length}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="Cesáreas"
                value={partos.filter(p => p.tipo_parto === 'cesarea').length}
                valueStyle={{ color: '#faad14' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="Instrumentados"
                value={partos.filter(p => p.tipo_parto === 'instrumentado').length}
                valueStyle={{ color: '#722ed1' }}
              />
            </Card>
          </Col>
        </Row>

        {/* TABLA DE PARTOS CON DETALLES */}
        <Table
          dataSource={[...partos].reverse()}
          locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="Sin partos registrados" /> }}
          rowKey="id"
          size="middle"
          bordered
          columns={[
            {
              title: 'Fecha y Hora',
              dataIndex: 'fecha_parto',
              render: (t) => t ? dayjs(t).format('DD/MM/YYYY HH:mm') : 'N/D',
              width: 150,
              sorter: (a: Parto, b: Parto) =>
                new Date(a.fecha_parto || 0).getTime() - new Date(b.fecha_parto || 0).getTime(),
            },
            {
              title: 'Tipo de Parto',
              dataIndex: 'tipo_parto',
              width: 150,
              filters: [
                { text: 'Eutócico', value: 'eutocico' },
                { text: 'Cesárea', value: 'cesarea' },
                { text: 'Instrumentado', value: 'instrumentado' },
              ],
              onFilter: (value: any, record: Parto) => record.tipo_parto === value,
              render: (tipo: string) => {
                if (!tipo) return <Text type="secondary">N/D</Text>;
                const config: Record<string, { color: string; text: string }> = {
                  eutocico: { color: 'success', text: 'Eutócico (Natural)' },
                  cesarea: { color: 'warning', text: 'Cesárea' },
                  instrumentado: { color: 'processing', text: 'Instrumentado' },
                };
                return <Tag color={config[tipo]?.color || 'default'}>{config[tipo]?.text || tipo}</Tag>;
              },
            },
            {
              title: 'Duración',
              render: (_: any, record: Parto) => {
                if (record.duracion_trabajo_parto_horas !== undefined && record.duracion_trabajo_parto_horas !== null) {
                  const horas = Math.floor(record.duracion_trabajo_parto_horas);
                  const minutos = record.duracion_periodo_expulsivo_minutos || 0;
                  return `${horas}h ${minutos}m`;
                }
                if (record.fecha_inicio_trabajo_parto && record.fecha_parto) {
                  const inicio = dayjs(record.fecha_inicio_trabajo_parto);
                  const fin = dayjs(record.fecha_parto);
                  const duracion = dayjs.duration(fin.diff(inicio));
                  const horas = Math.floor(duracion.asHours());
                  const minutos = duracion.minutes();
                  return `${horas}h ${minutos}m`;
                }
                return 'N/D';
              },
              width: 100,
            },
            {
              title: 'Recién Nacido',
              render: (_: any, record: Parto) => {
                const rn = record.recien_nacidos?.[0];
                if (!rn) return <Text type="secondary">Sin datos</Text>;
                return (
                  <Space direction="vertical" size={0}>
                    <span>
                      <Tag color={rn.sexo === 'masculino' ? 'blue' : 'pink'}>
                        {rn.sexo === 'masculino' ? 'Masculino' : 'Femenino'}
                      </Tag>
                    </span>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      Peso: {rn.peso_nacimiento || 0}g | Talla: {rn.talla_nacimiento || 0}cm
                    </Text>
                  </Space>
                );
              },
              width: 200,
            },
            {
              title: 'APGAR',
              render: (_: any, record: Parto) => {
                const rn = record.recien_nacidos?.[0];
                if (!rn) return <Text type="secondary">Sin datos</Text>;
                return (
                  <Space>
                    <Tooltip title="APGAR 1 minuto">
                      <Tag color={(rn.apgar_1_minuto || 0) >= 7 ? 'green' : (rn.apgar_1_minuto || 0) >= 4 ? 'orange' : 'red'}>
                        1': {rn.apgar_1_minuto ?? '-'}
                      </Tag>
                    </Tooltip>
                    <Tooltip title="APGAR 5 minutos">
                      <Tag color={(rn.apgar_5_minutos || 0) >= 7 ? 'green' : (rn.apgar_5_minutos || 0) >= 4 ? 'orange' : 'red'}>
                        5': {rn.apgar_5_minutos ?? '-'}
                      </Tag>
                    </Tooltip>
                  </Space>
                );
              },
              align: 'center' as const,
              width: 130,
            },
            {
              title: 'Complicaciones',
              dataIndex: 'complicaciones_maternas',
              render: (comp: string) =>
                comp ? (
                  <Tag color="error" icon={<WarningOutlined />}>
                    Sí
                  </Tag>
                ) : (
                  <Tag color="success" icon={<CheckCircleOutlined />}>
                    No
                  </Tag>
                ),
              align: 'center' as const,
              width: 130,
            },
            {
              title: 'Acciones',
              render: (_: any, record: Parto) => (
                <Space>
                  <Tooltip title="Ver detalles">
                    <Button size="small" icon={<EyeOutlined />} onClick={() => navigate(`/partos/${record.id}`)} />
                  </Tooltip>
                  <Tooltip title="Descargar reporte">
                    <Button size="small" icon={<DownloadOutlined />} />
                  </Tooltip>
                </Space>
              ),
              fixed: 'right' as const,
              width: 110,
            },
          ]}
          expandable={{
            expandedRowRender: (record: Parto) => {
              const rn = record.recien_nacidos?.[0];
              return (
                <div style={{ padding: '12px 24px', background: '#fafafa' }}>
                  <Row gutter={[16, 16]}>
                    <Col span={24}>
                      <Descriptions bordered column={3} size="small">
                        <Descriptions.Item label="Fecha Inicio" span={1}>
                          {record.fecha_inicio_trabajo_parto ? dayjs(record.fecha_inicio_trabajo_parto).format('DD/MM/YYYY HH:mm:ss') : 'N/D'}
                        </Descriptions.Item>
                        <Descriptions.Item label="Fecha Parto" span={1}>
                          {record.fecha_parto ? dayjs(record.fecha_parto).format('DD/MM/YYYY HH:mm:ss') : 'N/D'}
                        </Descriptions.Item>
                        <Descriptions.Item label="Duración Total" span={1}>
                          {(() => {
                            if (record.duracion_trabajo_parto_horas !== undefined && record.duracion_trabajo_parto_horas !== null) {
                              const horas = Math.floor(record.duracion_trabajo_parto_horas);
                              const minutos = record.duracion_periodo_expulsivo_minutos || 0;
                              return `${horas}h ${minutos}m`;
                            }
                            if (record.fecha_inicio_trabajo_parto && record.fecha_parto) {
                              const duracion = dayjs.duration(dayjs(record.fecha_parto).diff(dayjs(record.fecha_inicio_trabajo_parto)));
                              return `${Math.floor(duracion.asHours())}h ${duracion.minutes()}m`;
                            }
                            return 'N/D';
                          })()}
                        </Descriptions.Item>

                        <Descriptions.Item label="Tipo de Parto" span={1}>
                          {record.tipo_parto ? (
                            <Tag color={record.tipo_parto === 'eutocico' ? 'success' : record.tipo_parto === 'cesarea' ? 'warning' : 'processing'}>
                              {record.tipo_parto === 'eutocico' ? 'Eutócico (Natural)' : record.tipo_parto === 'cesarea' ? 'Cesárea' : 'Instrumentado'}
                            </Tag>
                          ) : <Text type="secondary">N/D</Text>}
                        </Descriptions.Item>

                        {rn && (
                          <>
                            <Descriptions.Item label="Sexo RN" span={1}>
                              <Tag color={rn.sexo === 'masculino' ? 'blue' : 'pink'}>
                                {rn.sexo === 'masculino' ? 'Masculino ♂' : 'Femenino ♀'}
                              </Tag>
                            </Descriptions.Item>

                            <Descriptions.Item label="Clasificación APGAR" span={1}>
                              <Space>
                                <span>1 min: <Tag color={(rn.apgar_1_minuto || 0) >= 7 ? 'green' : (rn.apgar_1_minuto || 0) >= 4 ? 'orange' : 'red'}>{rn.apgar_1_minuto ?? '-'}</Tag></span>
                                <span>5 min: <Tag color={(rn.apgar_5_minutos || 0) >= 7 ? 'green' : (rn.apgar_5_minutos || 0) >= 4 ? 'orange' : 'red'}>{rn.apgar_5_minutos ?? '-'}</Tag></span>
                              </Space>
                            </Descriptions.Item>

                            <Descriptions.Item label="Peso al Nacer" span={1}>
                              <strong>{rn.peso_nacimiento || 0}g</strong>
                              {rn.peso_nacimiento && rn.peso_nacimiento < 2500 && <Tag color="orange" style={{ marginLeft: 8 }}>Bajo Peso</Tag>}
                              {rn.peso_nacimiento && rn.peso_nacimiento >= 2500 && rn.peso_nacimiento <= 4000 && <Tag color="green" style={{ marginLeft: 8 }}>Normal</Tag>}
                              {rn.peso_nacimiento && rn.peso_nacimiento > 4000 && <Tag color="red" style={{ marginLeft: 8 }}>Macrosomía</Tag>}
                            </Descriptions.Item>

                            <Descriptions.Item label="Talla al Nacer" span={1}>
                              <strong>{rn.talla_nacimiento || 0}cm</strong>
                            </Descriptions.Item>
                          </>
                        )}

                        <Descriptions.Item label="Estado" span={1}>
                          {!record.complicaciones_maternas ? (
                            <Tag color="success" icon={<CheckCircleOutlined />}>Sin Complicaciones</Tag>
                          ) : (
                            <Tag color="error" icon={<WarningOutlined />}>Con Complicaciones</Tag>
                          )}
                        </Descriptions.Item>

                        {record.complicaciones_maternas && (
                          <Descriptions.Item label="Detalle de Complicaciones" span={3}>
                            <Alert type="error" message={record.complicaciones_maternas} showIcon />
                          </Descriptions.Item>
                        )}
                      </Descriptions>
                    </Col>
                  </Row>
                </div>
              );
            },
          }}
        />
      </>
    ) : (
      <Card variant="borderless" style={{ textAlign: 'center', padding: '40px 0' }}>
        <WomanOutlined style={{ fontSize: 48, color: '#d9d9d9', marginBottom: 16 }} />
        <p>No se han registrado partos para esta paciente.</p>
        <Button type="primary" onClick={() => navigate(`/partos/nuevo?paciente=${pacienteId}`)}>
          Registrar Primer Parto
        </Button>
      </Card>
    )}
  </div>
);

export default TabPartos;
