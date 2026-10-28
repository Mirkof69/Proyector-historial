import React from 'react';
import { Empty, Row, Col, Card, Space, Tag, Button, Table, Descriptions, Alert, Badge, Typography } from 'antd';
import {
  ExperimentOutlined, DownloadOutlined, WarningOutlined, CheckCircleOutlined,
  UserOutlined, ClockCircleOutlined, EditOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { Laboratorio, ParametroLaboratorio } from '../types';
import { valoresDeLaboratorio } from '../utils';
import { verticalDivider, HGB_DOMAIN, HGB_LABEL, HCT_DOMAIN, HCT_LABEL } from '../historiaClinicaHelpers';
import {
  ComposedChart, Line, XAxis, YAxis, CartesianGrid, RechartsTooltip, Legend,
  ResponsiveContainer, ReferenceArea,
} from '../rechartsLazy';

const { Text } = Typography;

const COLOR_ESTADO: Record<ParametroLaboratorio['estado'], string> = { NORMAL: 'success', ANORMAL: 'warning', 'CRÍTICO': 'error' };

const estadoExamen = (l: Laboratorio) => {
  if (l.pendiente) return 'pendiente';
  if (l.es_critico) return 'critico';
  return l.es_anormal ? 'anormal' : 'normal';
};

const EstadoExamen: React.FC<{ lab: Laboratorio }> = ({ lab }) => {
  const estado = estadoExamen(lab);
  if (estado === 'pendiente') return <Badge status="default" text="Pendiente" />;
  if (estado === 'critico') return <Tag color="error" icon={<WarningOutlined />}>CRÍTICO</Tag>;
  if (estado === 'anormal') return <Tag color="warning" icon={<WarningOutlined />}>ANORMAL</Tag>;
  return <Tag color="success" icon={<CheckCircleOutlined />}>NORMAL</Tag>;
};

interface TabLaboratoriosProps {
  laboratorios: Laboratorio[];
}
const TabLaboratorios: React.FC<TabLaboratoriosProps> = ({ laboratorios }) => {
  // Los gráficos usan cada parámetro medido (la Hemoglobina viene dentro del
  // Hemograma), no el nombre del examen.
  const valores = valoresDeLaboratorio(laboratorios);
  const serie = (...nombres: string[]) => valores
    .filter((v) => nombres.some((n) => v.nombre.toLowerCase().startsWith(n)))
    .sort((a, b) => new Date(a.fecha).getTime() - new Date(b.fecha).getTime())
    .map((v) => ({ fecha: dayjs(v.fecha).format('DD/MM'), valor: v.valor }));
  const labChartData = {
    hemoglobina: serie('hemoglobina'),
    glucosa: serie('glucosa', 'glicemia'),
    hematocrito: serie('hematocrito'),
  };
  const categorias = [...new Set(laboratorios.map((l) => l.categoria).filter(Boolean))];

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
                  <ReferenceArea y1={11} y2={14} fill="var(--color-exito)" fillOpacity={0.1} />
                  <Line type="monotone" dataKey="valor" stroke="var(--grafico-5)" strokeWidth={2} name="Hemoglobina (g/dL)" dot={{ fill: 'var(--grafico-5)', r: 5 }} />
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
                  <ReferenceArea y1={70} y2={100} fill="var(--color-exito)" fillOpacity={0.1} />
                  <ReferenceArea y1={125} y2={200} fill="var(--color-peligro)" fillOpacity={0.1} />
                  <Line type="monotone" dataKey="valor" stroke="var(--grafico-3)" strokeWidth={2} name="Glucosa (mg/dL)" dot={{ fill: 'var(--grafico-3)', r: 5 }} />
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
                  <ReferenceArea y1={33} y2={44} fill="var(--color-exito)" fillOpacity={0.1} />
                  <Line type="monotone" dataKey="valor" stroke="var(--grafico-2)" strokeWidth={2} name="Hematocrito (%)" dot={{ fill: 'var(--grafico-2)', r: 5 }} />
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
          { title: 'Categoría', dataIndex: 'categoria', render: (t) => <Tag>{t || 'General'}</Tag>, width: 120, filters: categorias.map((c) => ({ text: c, value: c })), onFilter: (value: any, record: any) => record.categoria === value },
          { title: 'Examen', dataIndex: 'tipo_examen_nombre', render: (n, r: any) => n ?? r.tipo_examen, width: 200 },
          {
            title: 'Resultado', key: 'resultado', width: 260,
            render: (_: unknown, r: Laboratorio) => (r.pendiente
              ? <Text type="secondary">Pendiente</Text>
              : (
                <Space size={[4, 4]} wrap>
                  {(r.resultados || []).slice(0, 3).map((f) => (
                    <Tag key={f.parametro} color={COLOR_ESTADO[f.estado]}>{f.parametro}: {f.valor} {f.unidad}</Tag>
                  ))}
                  {(r.resultados || []).length > 3 && <Text type="secondary">+{(r.resultados || []).length - 3}</Text>}
                </Space>
              )),
          },
          {
            title: 'Estado', key: 'estado', align: 'center' as const, width: 110,
            render: (_: unknown, r: Laboratorio) => <EstadoExamen lab={r} />,
            filters: [{ text: 'Crítico', value: 'critico' }, { text: 'Anormal', value: 'anormal' }, { text: 'Normal', value: 'normal' }, { text: 'Pendiente', value: 'pendiente' }],
            onFilter: (value: any, r: Laboratorio) => estadoExamen(r) === value,
          },
          { title: 'Adjunto', render: (_, r: any) => r.archivo_adjunto ? (<Button type="link" icon={<DownloadOutlined />} size="small">PDF</Button>) : (<Text type="secondary">-</Text>), align: 'center' as const, width: 80 }
        ]}
        expandable={{
          expandedRowRender: (record: any) => (
            <div className="historia-detalle-fila">
              <Row gutter={[16, 16]}>
                <Col span={24}>
                  <Descriptions bordered column={3} size="small">
                    <Descriptions.Item label="Categoría" span={1}><Tag>{record.categoria || 'General'}</Tag></Descriptions.Item>
                    <Descriptions.Item label="Tipo de Examen" span={2}><Text strong>{record.tipo_examen_nombre ?? record.tipo_examen}</Text></Descriptions.Item>
                    <Descriptions.Item label="Fecha de Toma" span={1}>{dayjs(record.fecha_toma).format('DD/MM/YYYY HH:mm')}</Descriptions.Item>
                    <Descriptions.Item label="Estado" span={1}><EstadoExamen lab={record} /></Descriptions.Item>
                    {record.interpretacion && (<Descriptions.Item label="Interpretación" span={3}><Alert type={record.es_anormal ? 'error' : 'success'} message={record.interpretacion} showIcon /></Descriptions.Item>)}
                    {record.observaciones && (<Descriptions.Item label="Observaciones" span={3}><Text>{record.observaciones}</Text></Descriptions.Item>)}
                    {record.metodo && (<Descriptions.Item label="Método" span={1}>{record.metodo}</Descriptions.Item>)}
                    {record.laboratorio_externo && (<Descriptions.Item label="Laboratorio" span={2}>{record.laboratorio_externo}</Descriptions.Item>)}
                    {record.archivo_adjunto && (<Descriptions.Item label="Archivo Adjunto" span={3}><Button type="primary" icon={<DownloadOutlined />} size="small">Descargar Resultado PDF</Button></Descriptions.Item>)}
                  </Descriptions>
                </Col>
                {!record.pendiente && (
                  <Col span={24}>
                    <Table
                      size="small"
                      pagination={false}
                      rowKey="parametro"
                      dataSource={record.resultados}
                      columns={[
                        { title: 'Parámetro', dataIndex: 'parametro' },
                        { title: 'Valor', render: (_: unknown, f: ParametroLaboratorio) => <Text strong type={f.estado === 'NORMAL' ? undefined : 'danger'}>{f.valor} {f.unidad}</Text> },
                        { title: 'Referencia', render: (_: unknown, f: ParametroLaboratorio) => (f.rango_referencia ? `${f.rango_referencia} ${f.unidad}` : '—') },
                        { title: 'Estado', dataIndex: 'estado', render: (e: ParametroLaboratorio['estado']) => <Tag color={COLOR_ESTADO[e]}>{e}</Tag> },
                      ]}
                    />
                  </Col>
                )}
                <Col span={24}>
                  <Card size="small" title="Trazabilidad" className="historia-trazabilidad">
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
