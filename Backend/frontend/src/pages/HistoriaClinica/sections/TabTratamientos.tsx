import React from 'react';
import { Card, Row, Col, Statistic, Button, Table, Tag, Descriptions, Space, Divider, Empty, Typography, Alert } from 'antd';
import { MedicineBoxOutlined, PlusOutlined, UserOutlined, ClockCircleOutlined, EditOutlined, EyeOutlined, CloseCircleOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { Tratamiento } from '../types';

const { Text } = Typography;

const verticalDivider = <Divider type="vertical" />;

interface TabTratamientosProps {
  tratamientos: Tratamiento[];
  setModalRecetaVisible: (visible: boolean) => void;
}

const TabTratamientos: React.FC<TabTratamientosProps> = ({ tratamientos, setModalRecetaVisible }) => {
  // Calcular estadísticas de tratamientos
  const totalTratamientos = tratamientos.length;
  const tratamientosActivos = tratamientos.filter(t => t.activo).length;
  const tratamientosSuspendidos = tratamientos.filter(t => !t.activo).length;

  return (
    <div>
      {/* ESTADÍSTICAS DE TRATAMIENTOS */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Total Tratamientos"
              value={totalTratamientos}
              prefix={<MedicineBoxOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Activos"
              value={tratamientosActivos}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Suspendidos"
              value={tratamientosSuspendidos}
              valueStyle={{ color: '#8c8c8c' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Button type="primary" block size="large" icon={<PlusOutlined />} onClick={() => setModalRecetaVisible(true)}>
            Nueva Receta
          </Button>
        </Col>
      </Row>

      {/* TABLA DE TRATAMIENTOS */}
      <Table
        dataSource={tratamientos.slice().sort((a, b) => (b.activo ? 1 : 0) - (a.activo ? 1 : 0))}
        locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="Sin tratamientos registrados" /> }}
        rowKey="id"
        columns={[
          {
            title: 'Estado',
            dataIndex: 'activo',
            key: 'activo',
            render: (activo: boolean) => (
              <Tag color={activo ? 'success' : 'default'}>
                {activo ? 'ACTIVO' : 'SUSPENDIDO'}
              </Tag>
            ),
            filters: [
              { text: 'Activos', value: true },
              { text: 'Suspendidos', value: false },
            ],
            onFilter: (value, record) => record.activo === value,
          },
          {
            title: 'Medicamento',
            dataIndex: 'medicamento',
            key: 'medicamento',
            render: (med: string) => <Text strong>{med}</Text>,
          },
          {
            title: 'Dosis',
            dataIndex: 'dosis',
            key: 'dosis',
          },
          {
            title: 'Frecuencia',
            dataIndex: 'frecuencia',
            key: 'frecuencia',
          },
          {
            title: 'Duración',
            dataIndex: 'duracion',
            key: 'duracion',
          },
          {
            title: 'Fecha Inicio',
            dataIndex: 'fecha_inicio',
            key: 'fecha_inicio',
            render: (fecha: string) => fecha ? dayjs(fecha).format('DD/MM/YYYY') : '-',
            sorter: (a, b) => dayjs(a.fecha_inicio).diff(dayjs(b.fecha_inicio)),
          },
          {
            title: 'Acciones',
            key: 'acciones',
            render: (_, record) => (
              <Space>
                <Button type="link" size="small" icon={<EyeOutlined />}>Ver</Button>
                {record.activo && (
                  <Button type="link" size="small" danger>Suspender</Button>
                )}
              </Space>
            ),
          },
        ]}
        expandable={{
          expandedRowRender: (record: Tratamiento) => (
            <div style={{ padding: 16 }}>
              <Row gutter={16}>
                <Col span={24}>
                  <Descriptions bordered size="small" column={3}>
                    <Descriptions.Item label="Medicamento Completo" span={3}>
                      <Text strong style={{ fontSize: 16 }}>{record.medicamento}</Text>
                      {!record.activo && <Tag color="red" style={{ marginLeft: 8 }}>SUSPENDIDO</Tag>}
                    </Descriptions.Item>

                    <Descriptions.Item label="Dosis Prescrita">
                      <Text strong>{record.dosis}</Text>
                    </Descriptions.Item>

                    <Descriptions.Item label="Frecuencia">
                      {record.frecuencia}
                    </Descriptions.Item>

                    <Descriptions.Item label="Duración del Tratamiento">
                      {record.duracion}
                    </Descriptions.Item>

                    <Descriptions.Item label="Vía de Administración">
                      {record.via_administracion || 'Oral'}
                    </Descriptions.Item>

                    <Descriptions.Item label="Fecha de Inicio" span={2}>
                      {record.fecha_inicio ? dayjs(record.fecha_inicio).format('DD/MM/YYYY') : 'No especificada'}
                    </Descriptions.Item>

                    {record.fecha_fin && (
                      <Descriptions.Item label="Fecha de Finalización" span={3}>
                        {dayjs(record.fecha_fin).format('DD/MM/YYYY')}
                        {dayjs(record.fecha_fin).isAfter(dayjs()) ? (
                          <Tag color="green" style={{ marginLeft: 8 }}>
                            {dayjs(record.fecha_fin).diff(dayjs(), 'days')} días restantes
                          </Tag>
                        ) : (
                          <Tag color="red" style={{ marginLeft: 8 }}>Tratamiento finalizado</Tag>
                        )}
                      </Descriptions.Item>
                    )}

                    {record.indicaciones && (
                      <Descriptions.Item label="Indicaciones de Uso" span={3}>
                        <Alert message={record.indicaciones} type="info" showIcon />
                      </Descriptions.Item>
                    )}

                    {record.motivo && (
                      <Descriptions.Item label="Motivo de Prescripción" span={3}>
                        {record.motivo}
                      </Descriptions.Item>
                    )}

                    {record.efectos_secundarios && (
                      <Descriptions.Item label="Efectos Secundarios Reportados" span={3}>
                        <Alert message={record.efectos_secundarios} type="warning" showIcon />
                      </Descriptions.Item>
                    )}

                    {record.observaciones && (
                      <Descriptions.Item label="Observaciones" span={3}>
                        {record.observaciones}
                      </Descriptions.Item>
                    )}

                    {!record.activo && record.motivo_suspension && (
                      <Descriptions.Item label="Motivo de Suspensión" span={3}>
                        <Alert message={record.motivo_suspension} type="error" showIcon />
                      </Descriptions.Item>
                    )}
                  </Descriptions>
                </Col>

                {/* TRAZABILIDAD */}
                <Col span={24} style={{ marginTop: 16 }}>
                  <Card size="small" title="Trazabilidad" style={{ background: '#fafafa' }}>
                    <Space split={verticalDivider} size="large" wrap>
                      <Space direction="vertical" size={0}>
                        <Text type="secondary">Prescrito por:</Text>
                        <Text strong>
                          <UserOutlined /> {record.medico?.nombre || record.medico?.username || 'Sistema'}
                        </Text>
                        {record.medico?.especialidad && (
                          <Tag color="purple">{record.medico.especialidad}</Tag>
                        )}
                      </Space>

                      <Space direction="vertical" size={0}>
                        <Text type="secondary">Fecha de prescripción:</Text>
                        <Text strong>
                          <ClockCircleOutlined /> {record.fecha_prescripcion ? dayjs(record.fecha_prescripcion).format('DD/MM/YYYY HH:mm:ss') : dayjs(record.fecha_inicio).format('DD/MM/YYYY')}
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

                      {!record.activo && record.fecha_suspension && (
                        <Space direction="vertical" size={0}>
                          <Text type="secondary">Fecha de suspensión:</Text>
                          <Text strong style={{ color: '#f5222d' }}>
                            <CloseCircleOutlined /> {dayjs(record.fecha_suspension).format('DD/MM/YYYY HH:mm:ss')}
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
          showTotal: (total) => `Total: ${total} tratamientos`,
        }}
      />

      {tratamientos.length === 0 && (
        <Empty
          description="No hay tratamientos registrados"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        >
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalRecetaVisible(true)}>
            Prescribir Primer Tratamiento
          </Button>
        </Empty>
      )}
    </div>
  );
};

export default TabTratamientos;
