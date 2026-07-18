import React from 'react';
import { Card, Row, Col, Statistic, Button, Alert, Table, Tag, Descriptions, Space, Divider, Empty, Typography } from 'antd';
import { SafetyCertificateOutlined, PlusOutlined, ExclamationCircleOutlined, UserOutlined, ClockCircleOutlined, EditOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { Vacuna } from '../types';
import { VACUNAS_EMBARAZO } from '../utils';

const { Text } = Typography;

const verticalDivider = <Divider type="vertical" />;

interface TabVacunasProps {
  vacunas: Vacuna[];
}

const TabVacunas: React.FC<TabVacunasProps> = ({ vacunas }) => {
  // Calcular estadísticas de vacunas
  const totalVacunas = vacunas.length;
  const vacunasUltimoMes = vacunas.filter(v =>
    dayjs(v.fecha_aplicacion).isAfter(dayjs().subtract(1, 'month'))
  ).length;
  const vacunasPendientes = VACUNAS_EMBARAZO.filter(ve =>
    ve.obligatoria && !vacunas.some(v => String(v.nombre || '').toLowerCase().includes(ve.nombre.toLowerCase().split(' ')[0]))
  );

  return (
    <div>
      {/* ESTADÍSTICAS DE VACUNAS */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Vacunas Aplicadas"
              value={totalVacunas}
              prefix={<SafetyCertificateOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Último Mes"
              value={vacunasUltimoMes}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Pendientes"
              value={vacunasPendientes.length}
              valueStyle={{ color: vacunasPendientes.length > 0 ? '#faad14' : '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Button type="primary" block size="large" icon={<PlusOutlined />}>
            Registrar Vacuna
          </Button>
        </Col>
      </Row>

      {/* VACUNAS PENDIENTES */}
      {vacunasPendientes.length > 0 && (
        <Alert
          message="Vacunas Pendientes Recomendadas"
          description={
            <ul>
              {vacunasPendientes.map((v) => (
                <li key={v.nombre}>
                  <Text strong>{v.nombre}</Text> - <Text type="secondary">{v.trimestre}</Text>
                </li>
              ))}
            </ul>
          }
          type="warning"
          showIcon
          icon={<ExclamationCircleOutlined />}
          style={{ marginBottom: 24 }}
        />
      )}

      {/* TABLA DE VACUNAS APLICADAS */}
      <Table
        dataSource={vacunas.slice().sort((a, b) =>
          dayjs(b.fecha_aplicacion).diff(dayjs(a.fecha_aplicacion))
        )}
        locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="Sin vacunas registradas" /> }}
        rowKey="id"
        columns={[
          {
            title: 'Fecha de Aplicación',
            dataIndex: 'fecha_aplicacion',
            key: 'fecha_aplicacion',
            render: (fecha: string) => dayjs(fecha).format('DD/MM/YYYY'),
            sorter: (a, b) => dayjs(a.fecha_aplicacion).diff(dayjs(b.fecha_aplicacion)),
            defaultSortOrder: 'descend' as const,
          },
          {
            title: 'Vacuna',
            dataIndex: 'nombre',
            key: 'nombre',
            filters: [
              { text: 'Influenza', value: 'Influenza' },
              { text: 'Tdap', value: 'Tdap' },
              { text: 'Hepatitis', value: 'Hepatitis' },
              { text: 'COVID-19', value: 'COVID' },
            ],
            onFilter: (value, record) => String(record.nombre || '').toLowerCase().includes(String(value).toLowerCase()),
          },
          {
            title: 'Dosis',
            dataIndex: 'dosis',
            key: 'dosis',
            render: (dosis: number) => <Tag color="blue">Dosis {dosis}</Tag>,
          },
          {
            title: 'Lote',
            dataIndex: 'lote',
            key: 'lote',
            render: (lote: string) => lote || <Text type="secondary">No registrado</Text>,
          },
          {
            title: 'Próxima Dosis',
            dataIndex: 'fecha_proxima_dosis',
            key: 'fecha_proxima_dosis',
            render: (fecha: string) =>
              fecha ? (
                <Text style={{ color: dayjs(fecha).isBefore(dayjs()) ? '#f5222d' : '#52c41a' }}>
                  {dayjs(fecha).format('DD/MM/YYYY')}
                </Text>
              ) : (
                <Text type="secondary">Esquema completo</Text>
              ),
          },
        ]}
        expandable={{
          expandedRowRender: (record: Vacuna) => (
            <div style={{ padding: 16 }}>
              <Row gutter={16}>
                <Col span={24}>
                  <Descriptions bordered size="small" column={3}>
                    <Descriptions.Item label="Vacuna Completa" span={3}>
                      <Text strong style={{ fontSize: 16 }}>{record.nombre}</Text>
                    </Descriptions.Item>

                    <Descriptions.Item label="Fecha de Aplicación">
                      {dayjs(record.fecha_aplicacion).format('DD/MM/YYYY HH:mm')}
                    </Descriptions.Item>

                    <Descriptions.Item label="Número de Dosis">
                      <Tag color="blue" style={{ fontSize: 14 }}>Dosis {record.dosis}</Tag>
                    </Descriptions.Item>

                    <Descriptions.Item label="Vía de Administración">
                      {record.via_administracion || 'Intramuscular (IM)'}
                    </Descriptions.Item>

                    <Descriptions.Item label="Lote del Fabricante" span={2}>
                      <Text code>{record.lote || 'No registrado'}</Text>
                    </Descriptions.Item>

                    <Descriptions.Item label="Fabricante">
                      {record.fabricante || 'No registrado'}
                    </Descriptions.Item>

                    <Descriptions.Item label="Sitio de Aplicación" span={2}>
                      {record.sitio_aplicacion || 'Deltoides (brazo)'}
                    </Descriptions.Item>

                    {record.fecha_proxima_dosis && (
                      <Descriptions.Item label="Próxima Dosis Programada" span={3}>
                        <Space>
                          <Text strong>{dayjs(record.fecha_proxima_dosis).format('DD/MM/YYYY')}</Text>
                          <Text type="secondary">
                            ({dayjs(record.fecha_proxima_dosis).diff(dayjs(), 'days')} días restantes)
                          </Text>
                        </Space>
                      </Descriptions.Item>
                    )}

                    {record.reacciones_adversas && (
                      <Descriptions.Item label="Reacciones Adversas" span={3}>
                        <Alert message={record.reacciones_adversas} type="warning" showIcon />
                      </Descriptions.Item>
                    )}

                    {record.observaciones && (
                      <Descriptions.Item label="Observaciones" span={3}>
                        {record.observaciones}
                      </Descriptions.Item>
                    )}
                  </Descriptions>
                </Col>

                {/* TRAZABILIDAD */}
                <Col span={24} style={{ marginTop: 16 }}>
                  <Card size="small" title="Trazabilidad" style={{ background: '#fafafa' }}>
                    <Space split={verticalDivider} size="large" wrap>
                      <Space direction="vertical" size={0}>
                        <Text type="secondary">Aplicada por:</Text>
                        <Text strong>
                          <UserOutlined /> {record.aplicada_por?.nombre || record.aplicada_por?.username || 'Sistema'}
                        </Text>
                      </Space>

                      <Space direction="vertical" size={0}>
                        <Text type="secondary">Fecha de registro:</Text>
                        <Text strong>
                          <ClockCircleOutlined /> {record.fecha_registro ? dayjs(record.fecha_registro).format('DD/MM/YYYY HH:mm:ss') : dayjs(record.fecha_aplicacion).format('DD/MM/YYYY HH:mm:ss')}
                        </Text>
                      </Space>

                      {record.fecha_modificacion && (
                        <Space direction="vertical" size={0}>
                          <Text type="secondary">Última modificación:</Text>
                          <Text strong>
                            <EditOutlined /> {dayjs(record.fecha_modificacion).format('DD/MM/YYYY HH:mm:ss')}
                          </Text>
                        </Space>
                      )}

                      {record.semanas_gestacion && (
                        <Space direction="vertical" size={0}>
                          <Text type="secondary">Edad gestacional:</Text>
                          <Text strong style={{ color: '#722ed1' }}>
                            {record.semanas_gestacion} semanas
                          </Text>
                        </Space>
                      )}
                    </Space>
                  </Card>
                </Col>
              </Row>
            </div>
          ),
        }}
        pagination={{
          pageSize: 10,
          showSizeChanger: true,
          showTotal: (total) => `Total: ${total} vacunas`,
        }}
      />

      {vacunas.length === 0 && (
        <Empty
          description="No hay vacunas registradas"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        >
          <Button type="primary" icon={<PlusOutlined />}>
            Registrar Primera Vacuna
          </Button>
        </Empty>
      )}
    </div>
  );
};

export default TabVacunas;
