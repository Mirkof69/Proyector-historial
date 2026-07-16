import React from 'react';
import { Empty, Row, Col, Card, Space, Tag, Button, Table, Descriptions, Alert, Badge, Typography } from 'antd';
import {
  ExperimentOutlined, DownloadOutlined, WarningOutlined, CheckCircleOutlined,
  UserOutlined, ClockCircleOutlined, EditOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { Laboratorio } from '../types';
import { verticalDivider, HGB_DOMAIN, HGB_LABEL, HCT_DOMAIN, HCT_LABEL } from '../historiaClinicaHelpers';
import {
  ComposedChart, Line, XAxis, YAxis, CartesianGrid, RechartsTooltip, Legend,
  ResponsiveContainer, ReferenceArea,
} from '../rechartsLazy';

const { Text } = Typography;

interface TabLaboratoriosProps {
  laboratorios: Laboratorio[];
}
const TabLaboratorios: React.FC<TabLaboratoriosProps> = ({ laboratorios }) => {
  const labChartData = {
    hemoglobina: laboratorios
      .reduce((acc, l) => {
        const tipo = typeof l.tipo_examen === 'string' ? l.tipo_examen.toLowerCase() : String(l.tipo_examen || '').toLowerCase();
        if (tipo.includes('hemoglobina') && l.resultado) {
          acc.push({ fecha: dayjs(l.fecha_toma).format('DD/MM'), valor: parseFloat(l.resultado), fecha_timestamp: new Date(l.fecha_toma).getTime() });
        }
        return acc;
      }, [] as any[])
      .sort((a, b) => a.fecha_timestamp - b.fecha_timestamp),
    glucosa: laboratorios
      .reduce((acc, l) => {
        const tipo = typeof l.tipo_examen === 'string' ? l.tipo_examen.toLowerCase() : String(l.tipo_examen || '').toLowerCase();
        if ((tipo.includes('glucosa') || tipo.includes('glicemia')) && l.resultado) {
          acc.push({ fecha: dayjs(l.fecha_toma).format('DD/MM'), valor: parseFloat(l.resultado), fecha_timestamp: new Date(l.fecha_toma).getTime() });
        }
        return acc;
      }, [] as any[])
      .sort((a, b) => a.fecha_timestamp - b.fecha_timestamp),
    hematocrito: laboratorios
      .reduce((acc, l) => {
        const tipo = typeof l.tipo_examen === 'string' ? l.tipo_examen.toLowerCase() : String(l.tipo_examen || '').toLowerCase();
        if (tipo.includes('hematocrito') && l.resultado) {
          acc.push({ fecha: dayjs(l.fecha_toma).format('DD/MM'), valor: parseFloat(l.resultado), fecha_timestamp: new Date(l.fecha_toma).getTime() });
        }
        return acc;
      }, [] as any[])
      .sort((a, b) => a.fecha_timestamp - b.fecha_timestamp),
  };

  return (
    <div>
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        {labChartData.hemoglobina.length > 0 && (
          <Col xs={24} lg={12}>
            <Card title={<><ExperimentOutlined /> Evolución de Hemoglobina</>} size="small">
              <ResponsiveContainer width="100%" height={250}>
                <ComposedChart data={labChartData.hemoglobina}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="fecha" />
                  <YAxis label={HGB_LABEL} domain={HGB_DOMAIN} />
                  <RechartsTooltip />
                  <Legend />
                  <ReferenceArea y1={11} y2={14} fill="#52c41a" fillOpacity={0.1} />
                  <Line type="monotone" dataKey="valor" stroke="#ff4d4f" strokeWidth={2} name="Hemoglobina (g/dL)" dot={{ fill: '#ff4d4f', r: 5 }} />
                </ComposedChart>
              </ResponsiveContainer>
            </Card>
          </Col>
        )}
        {labChartData.glucosa.length > 0 && (
          <Col xs={24} lg={12}>
            <Card title={<><ExperimentOutlined /> Evolución de Glucosa</>} size="small">
              <ResponsiveContainer width="100%" height={250}>
                <ComposedChart data={labChartData.glucosa}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="fecha" />
                  <YAxis label={{ value: 'mg/dL', angle: -90, position: 'insideLeft' }} />
                  <RechartsTooltip />
                  <Legend />
                  <ReferenceArea y1={70} y2={100} fill="#52c41a" fillOpacity={0.1} />
                  <ReferenceArea y1={125} y2={200} fill="#ff4d4f" fillOpacity={0.1} />
                  <Line type="monotone" dataKey="valor" stroke="#faad14" strokeWidth={2} name="Glucosa (mg/dL)" dot={{ fill: '#faad14', r: 5 }} />
                </ComposedChart>
              </ResponsiveContainer>
            </Card>
          </Col>
        )}
        {labChartData.hematocrito.length > 0 && (
          <Col xs={24} lg={12}>
            <Card title={<><ExperimentOutlined /> Evolución de Hematocrito</>} size="small">
              <ResponsiveContainer width="100%" height={250}>
                <ComposedChart data={labChartData.hematocrito}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="fecha" />
                  <YAxis label={HCT_LABEL} domain={HCT_DOMAIN} />
                  <RechartsTooltip />
                  <Legend />
                  <ReferenceArea y1={33} y2={44} fill="#52c41a" fillOpacity={0.1} />
                  <Line type="monotone" dataKey="valor" stroke="#1890ff" strokeWidth={2} name="Hematocrito (%)" dot={{ fill: '#1890ff', r: 5 }} />
                </ComposedChart>
              </ResponsiveContainer>
            </Card>
          </Col>
        )}
      </Row>

      <Table
        dataSource={[...laboratorios].reverse()}
        locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="Sin exámenes de laboratorio registrados" /> }}
        rowKey="id"
        size="middle"
        bordered
        columns={[
          { title: 'Fecha Toma', dataIndex: 'fecha_toma', render: (t) => dayjs(t).format('DD/MM/YY'), width: 100, sorter: (a: any, b: any) => new Date(a.fecha_toma).getTime() - new Date(b.fecha_toma).getTime() },
          { title: 'Categoría', dataIndex: 'categoria', render: (t) => <Tag color="blue">{t || 'General'}</Tag>, width: 120, filters: [{ text: 'Hematología', value: 'HEMATOLOGIA' }, { text: 'Química', value: 'QUIMICA' }, { text: 'Inmunología', value: 'INMUNOLOGIA' }, { text: 'Microbiología', value: 'MICROBIOLOGIA' }], onFilter: (value: any, record: any) => record.categoria === value },
          { title: 'Examen', dataIndex: 'tipo_examen', width: 200 },
          { title: 'Resultado', dataIndex: 'resultado', render: (t, r: any) => (<Text strong type={r.es_anormal ? 'danger' : 'success'}>{t} {r.unidad || ''}</Text>), width: 120 },
          { title: 'Valores Ref.', dataIndex: 'valores_referencia', responsive: ['md'] as any, width: 120 },
          { title: 'Estado', dataIndex: 'es_anormal', render: (v) => v ? (<Badge status="error" text="Anormal" />) : (<Badge status="success" text="Normal" />), align: 'center' as const, width: 100, filters: [{ text: 'Normal', value: false }, { text: 'Anormal', value: true }], onFilter: (value: any, record: any) => record.es_anormal === value },
          { title: 'Adjunto', render: (_, r: any) => r.archivo_adjunto ? (<Button type="link" icon={<DownloadOutlined />} size="small">PDF</Button>) : (<Text type="secondary">-</Text>), align: 'center' as const, width: 80 }
        ]}
        expandable={{
          expandedRowRender: (record: any) => (
            <div style={{ padding: '16px 24px', background: '#fafafa' }}>
              <Row gutter={[16, 16]}>
                <Col span={24}>
                  <Descriptions bordered column={3} size="small">
                    <Descriptions.Item label="Categoría" span={1}><Tag color="blue">{record.categoria || 'General'}</Tag></Descriptions.Item>
                    <Descriptions.Item label="Tipo de Examen" span={2}><Text strong>{record.tipo_examen}</Text></Descriptions.Item>
                    <Descriptions.Item label="Fecha de Toma" span={1}>{dayjs(record.fecha_toma).format('DD/MM/YYYY HH:mm')}</Descriptions.Item>
                    <Descriptions.Item label="Resultado" span={1}><Text strong style={{ fontSize: 16 }} type={record.es_anormal ? 'danger' : 'success'}>{record.resultado} {record.unidad || ''}</Text></Descriptions.Item>
                    <Descriptions.Item label="Estado" span={1}>{record.es_anormal ? (<Tag color="error" icon={<WarningOutlined />}>ANORMAL</Tag>) : (<Tag color="success" icon={<CheckCircleOutlined />}>NORMAL</Tag>)}</Descriptions.Item>
                    <Descriptions.Item label="Valores de Referencia" span={3}><Text code>{record.valores_referencia || 'No especificado'}</Text></Descriptions.Item>
                    {record.interpretacion && (<Descriptions.Item label="Interpretación" span={3}><Alert type={record.es_anormal ? 'error' : 'success'} message={record.interpretacion} showIcon /></Descriptions.Item>)}
                    {record.observaciones && (<Descriptions.Item label="Observaciones" span={3}><Text>{record.observaciones}</Text></Descriptions.Item>)}
                    {record.metodo && (<Descriptions.Item label="Método" span={1}>{record.metodo}</Descriptions.Item>)}
                    {record.laboratorio_externo && (<Descriptions.Item label="Laboratorio" span={2}>{record.laboratorio_externo}</Descriptions.Item>)}
                    {record.archivo_adjunto && (<Descriptions.Item label="Archivo Adjunto" span={3}><Button type="primary" icon={<DownloadOutlined />} size="small">Descargar Resultado PDF</Button></Descriptions.Item>)}
                  </Descriptions>
                </Col>
                <Col span={24}>
                  <Card size="small" title="Trazabilidad" style={{ background: '#f0f2f5' }}>
                    <Space split={verticalDivider} size="large">
                      <Space direction="vertical" size={0}><Text type="secondary">Registrado por:</Text><Text strong><UserOutlined /> {record.medico?.nombre || record.medico?.username || 'Sistema'}</Text></Space>
                      <Space direction="vertical" size={0}><Text type="secondary">Fecha de registro:</Text><Text strong><ClockCircleOutlined /> {record.fecha_registro ? dayjs(record.fecha_registro).format('DD/MM/YYYY HH:mm:ss') : '-'}</Text></Space>
                      {record.fecha_actualizacion && record.fecha_actualizacion !== record.fecha_registro && (<Space direction="vertical" size={0}><Text type="secondary">Última modificación:</Text><Text strong><EditOutlined /> {dayjs(record.fecha_actualizacion).format('DD/MM/YYYY HH:mm:ss')}</Text></Space>)}
                      {record.semanas_gestacion && (<Space direction="vertical" size={0}><Text type="secondary">Edad gestacional:</Text><Text strong>{record.semanas_gestacion} semanas</Text></Space>)}
                    </Space>
                  </Card>
                </Col>
              </Row>
            </div>
          ),
        }}
        pagination={{ pageSize: 15, showSizeChanger: true, showTotal: (total) => `Total: ${total} exámenes` }}
      />
    </div>
  );
};

export default TabLaboratorios;
