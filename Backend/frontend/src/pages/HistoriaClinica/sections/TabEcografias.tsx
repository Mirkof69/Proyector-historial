import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Empty, Row, Col, Card, Space, Tag, Button, Table, Tooltip, Descriptions, Progress, Alert, Typography } from 'antd';
import {
  ScanOutlined, FileTextOutlined, EditOutlined, CalendarOutlined, PlusOutlined,
  EyeOutlined, UserOutlined, ClockCircleOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { Ecografia, Embarazo } from '../types';
import { verticalDivider } from '../historiaClinicaHelpers';
import {
  ComposedChart, Line, XAxis, YAxis, CartesianGrid, RechartsTooltip, Legend,
  ResponsiveContainer, Area,
} from '../rechartsLazy';

const { Text } = Typography;

interface TabEcografiasProps {
  ecografias: Ecografia[];
  navigate: ReturnType<typeof useNavigate>;
  embarazoActivo: Embarazo | null;
}
const TabEcografias: React.FC<TabEcografiasProps> = ({ ecografias, navigate, embarazoActivo }) => {
  const fetalGrowthData = ecografias
    .reduce((acc, e: any) => {
      if (e.peso_fetal_estimado && e.edad_gestacional_semanas) {
        acc.push({
          semana: Number(e.edad_gestacional_semanas),
          fecha: dayjs(e.fecha).format('DD/MM'),
          peso: Number(e.peso_fetal_estimado),
          dbp: e.diametro_biparietal ? Number(e.diametro_biparietal) : null,
          ca: e.circunferencia_abdominal ? Number(e.circunferencia_abdominal) : null,
          lf: e.longitud_femur ? Number(e.longitud_femur) : null,
        });
      }
      return acc;
    }, [] as any[])
    .sort((a, b) => a.semana - b.semana);

  return (
    <div>
      {fetalGrowthData.length > 0 && (
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col xs={24} lg={12}>
            <Card title={<><ScanOutlined /> Curva de Crecimiento Fetal - Peso</>} size="small">
              <ResponsiveContainer width="100%" height={250}>
                <ComposedChart data={fetalGrowthData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="semana" label={{ value: 'Semanas de Gestación', position: 'insideBottom', offset: -5 }} />
                  <YAxis label={{ value: 'Peso (g)', angle: -90, position: 'insideLeft' }} />
                  <RechartsTooltip />
                  <Legend />
                  <Area type="monotone" dataKey="peso" stroke="#722ed1" fill="#722ed1" fillOpacity={0.3} name="Peso Fetal (g)" />
                </ComposedChart>
              </ResponsiveContainer>
            </Card>
          </Col>
          {fetalGrowthData.some(d => d.dbp) && (
            <Col xs={24} lg={12}>
              <Card title={<><ScanOutlined /> Diámetro Biparietal (DBP)</>} size="small">
                <ResponsiveContainer width="100%" height={250}>
                  <ComposedChart data={fetalGrowthData.filter(d => d.dbp)}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="semana" label={{ value: 'Semanas EG', position: 'insideBottom', offset: -5 }} />
                    <YAxis label={{ value: 'mm', angle: -90, position: 'insideLeft' }} />
                    <RechartsTooltip />
                    <Legend />
                    <Line type="monotone" dataKey="dbp" stroke="#1890ff" strokeWidth={2} name="DBP (mm)" dot={{ fill: '#1890ff', r: 5 }} />
                  </ComposedChart>
                </ResponsiveContainer>
              </Card>
            </Col>
          )}
          {fetalGrowthData.some(d => d.ca) && (
            <Col xs={24} lg={12}>
              <Card title={<><ScanOutlined /> Circunferencia Abdominal (CA)</>} size="small">
                <ResponsiveContainer width="100%" height={250}>
                  <ComposedChart data={fetalGrowthData.filter(d => d.ca)}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="semana" label={{ value: 'Semanas EG', position: 'insideBottom', offset: -5 }} />
                    <YAxis label={{ value: 'mm', angle: -90, position: 'insideLeft' }} />
                    <RechartsTooltip />
                    <Legend />
                    <Line type="monotone" dataKey="ca" stroke="#52c41a" strokeWidth={2} name="CA (mm)" dot={{ fill: '#52c41a', r: 5 }} />
                  </ComposedChart>
                </ResponsiveContainer>
              </Card>
            </Col>
          )}
          {fetalGrowthData.some(d => d.lf) && (
            <Col xs={24} lg={12}>
              <Card title={<><ScanOutlined /> Longitud del Fémur (LF)</>} size="small">
                <ResponsiveContainer width="100%" height={250}>
                  <ComposedChart data={fetalGrowthData.filter(d => d.lf)}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="semana" label={{ value: 'Semanas EG', position: 'insideBottom', offset: -5 }} />
                    <YAxis label={{ value: 'mm', angle: -90, position: 'insideLeft' }} />
                    <RechartsTooltip />
                    <Legend />
                    <Line type="monotone" dataKey="lf" stroke="#faad14" strokeWidth={2} name="LF (mm)" dot={{ fill: '#faad14', r: 5 }} />
                  </ComposedChart>
                </ResponsiveContainer>
              </Card>
            </Col>
          )}
        </Row>
      )}

      <div className="ecografias-gallery" style={{ marginBottom: 24 }}>
        <Row gutter={[16, 16]}>
          {ecografias.map(eco => (
            <Col xs={24} sm={12} md={8} lg={6} key={eco.id}>
              <Card
                hoverable
                cover={<div style={{ height: 150, background: '#333', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center' }}><ScanOutlined style={{ fontSize: 40 }} /></div>}
                actions={[
                  <Tooltip title="Ver Reporte" key="report"><FileTextOutlined onClick={() => navigate(`/ecografias/${eco.id}`)} /></Tooltip>,
                  <Tooltip title="Editar" key="edit"><EditOutlined /></Tooltip>
                ]}
              >
                <Card.Meta
                  title={eco.tipo}
                  description={
                    <div style={{ fontSize: 12 }}>
                      <p><CalendarOutlined /> {dayjs(eco.fecha).format('DD/MM/YYYY')}</p>
                      <p><strong>EG:</strong> {eco.edad_gestacional ?? eco.edad_gestacional_semanas ?? '-'} sem</p>
                      <p><strong>Peso:</strong> {eco.peso_fetal_estimado ? `${eco.peso_fetal_estimado}g` : 'no medido'}</p>
                    </div>
                  }
                />
              </Card>
            </Col>
          ))}
          <Col xs={24} sm={12} md={8} lg={6}>
            <Button type="dashed" block style={{ height: '100%' }} icon={<PlusOutlined style={{ fontSize: 30 }} />} onClick={() => navigate(`/ecografias/nuevo?embarazo=${embarazoActivo?.id || ''}`)}>
              Nueva Ecografía
            </Button>
          </Col>
        </Row>
      </div>

      <Table
        dataSource={[...ecografias].reverse()}
        locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="Sin ecografías registradas en este embarazo" /> }}
        rowKey="id"
        size="middle"
        bordered
        columns={[
          { title: 'Fecha', dataIndex: 'fecha', render: (t) => dayjs(t).format('DD/MM/YY'), width: 100, sorter: (a: any, b: any) => new Date(a.fecha).getTime() - new Date(b.fecha).getTime() },
          { title: 'Tipo', dataIndex: 'tipo', width: 180, filters: [{ text: 'Primer Trimestre', value: 'PRIMER_TRIMESTRE' }, { text: 'Segundo Trimestre', value: 'SEGUNDO_TRIMESTRE' }, { text: 'Tercer Trimestre', value: 'TERCER_TRIMESTRE' }, { text: 'Doppler', value: 'DOPPLER' }], onFilter: (value: any, record: any) => record.tipo === value, render: (tipo) => <Tag color="purple">{tipo}</Tag> },
          { title: 'EG Calculada', dataIndex: 'edad_gestacional', render: (eg, r: any) => <Text strong>{eg ?? r.edad_gestacional_semanas ?? '-'} sem</Text>, align: 'center' as const, width: 100 },
          { title: 'Peso Fetal', dataIndex: 'peso_fetal_estimado', render: (peso) => peso ? `${peso}g` : '-', align: 'center' as const, width: 100 },
          { title: 'Medidas Biométricas', render: (_, r: any) => (<Space size={4} direction="vertical">{r.diametro_biparietal && <Text type="secondary" style={{ fontSize: 12 }}>DBP: {r.diametro_biparietal}mm</Text>}{r.circunferencia_abdominal && <Text type="secondary" style={{ fontSize: 12 }}>CA: {r.circunferencia_abdominal}mm</Text>}{r.longitud_femur && <Text type="secondary" style={{ fontSize: 12 }}>LF: {r.longitud_femur}mm</Text>}</Space>), width: 150 },
          { title: 'Líquido Amniótico', dataIndex: 'liquido_amniotico', render: (la) => { if (!la) return '-'; const colors: any = { NORMAL: 'success', OLIGOHIDRAMNIOS: 'error', POLIHIDRAMNIOS: 'warning' }; return <Tag color={colors[la] || 'default'}>{la}</Tag>; }, align: 'center' as const, width: 130 },
          { title: 'Acciones', render: (_, r: any) => (<Space><Tooltip title="Ver detalles"><Button size="small" icon={<EyeOutlined />} onClick={() => navigate(`/ecografias/${r.id}`)} /></Tooltip></Space>), fixed: 'right' as const, width: 80 },
        ]}
        expandable={{
          expandedRowRender: (record: any) => (
            <div style={{ padding: '16px 24px', background: 'var(--bg-secondary, #fafafa)' }}>
              <Row gutter={[16, 16]}>
                <Col span={24}>
                  <Descriptions bordered column={3} size="small">
                    <Descriptions.Item label="Tipo de Ecografía" span={1}><Tag color="purple">{record.tipo}</Tag></Descriptions.Item>
                    <Descriptions.Item label="Fecha" span={1}>{dayjs(record.fecha).format('DD/MM/YYYY')}</Descriptions.Item>
                    <Descriptions.Item label="EG Calculada" span={1}><Text strong>{record.edad_gestacional ?? record.edad_gestacional_semanas ?? '-'} semanas</Text></Descriptions.Item>
                    <Descriptions.Item label="Peso Fetal Estimado" span={1}><Text strong style={{ fontSize: 16 }}>{record.peso_fetal_estimado ? `${record.peso_fetal_estimado}g` : 'no medido'}</Text></Descriptions.Item>
                    <Descriptions.Item label="Percentil de Peso" span={2}>{record.percentil_peso ? <Progress percent={record.percentil_peso} size="small" /> : 'No calculado'}</Descriptions.Item>
                    <Descriptions.Item label="Diámetro Biparietal (DBP)" span={1}>{record.diametro_biparietal ? `${record.diametro_biparietal} mm` : '-'}</Descriptions.Item>
                    <Descriptions.Item label="Circunferencia Abdominal (CA)" span={1}>{record.circunferencia_abdominal ? `${record.circunferencia_abdominal} mm` : '-'}</Descriptions.Item>
                    <Descriptions.Item label="Longitud del Fémur (LF)" span={1}>{record.longitud_femur ? `${record.longitud_femur} mm` : '-'}</Descriptions.Item>
                    <Descriptions.Item label="Circunferencia Cefálica (CC)" span={1}>{record.circunferencia_cefalica ? `${record.circunferencia_cefalica} mm` : '-'}</Descriptions.Item>
                    <Descriptions.Item label="Longitud Húmero" span={1}>{record.longitud_humero ? `${record.longitud_humero} mm` : '-'}</Descriptions.Item>
                    <Descriptions.Item label="Longitud Cúbito/Radio" span={1}>{record.longitud_cubito ? `${record.longitud_cubito} mm` : '-'}</Descriptions.Item>
                    <Descriptions.Item label="Líquido Amniótico" span={1}>{record.liquido_amniotico ? (<Tag color={record.liquido_amniotico === 'NORMAL' ? 'success' : record.liquido_amniotico === 'OLIGOHIDRAMNIOS' ? 'error' : 'warning'}>{record.liquido_amniotico}</Tag>) : '-'}</Descriptions.Item>
                    <Descriptions.Item label="Índice de Líquido Amniótico (ILA)" span={1}>{record.indice_liquido_amniotico ? `${record.indice_liquido_amniotico} cm` : '-'}</Descriptions.Item>
                    <Descriptions.Item label="Placenta" span={1}>{record.placenta || '-'}</Descriptions.Item>
                    <Descriptions.Item label="Posición Placenta" span={1}>{record.posicion_placenta || '-'}</Descriptions.Item>
                    <Descriptions.Item label="Grado Placentario" span={1}>{record.grado_placentario || '-'}</Descriptions.Item>
                    <Descriptions.Item label="Cordón Umbilical" span={1}>{record.cordon_umbilical || '-'}</Descriptions.Item>
                    <Descriptions.Item label="Sexo Fetal" span={1}>{record.sexo_fetal ? (<Tag color={record.sexo_fetal === 'M' ? 'blue' : 'pink'}>{record.sexo_fetal === 'M' ? 'Masculino ♂' : 'Femenino ♀'}</Tag>) : 'No determinado'}</Descriptions.Item>
                    <Descriptions.Item label="Presentación" span={1}>{record.presentacion || '-'}</Descriptions.Item>
                    <Descriptions.Item label="Latido Cardíaco Fetal" span={1}>{record.latido_cardiaco_fetal ? `${record.latido_cardiaco_fetal} lpm` : '-'}</Descriptions.Item>
                    {record.anatomia_fetal && (<Descriptions.Item label="Anatomía Fetal" span={3}><Text>{record.anatomia_fetal}</Text></Descriptions.Item>)}
                    {record.hallazgos && (<Descriptions.Item label="Hallazgos" span={3}><Alert type="info" message={record.hallazgos} showIcon /></Descriptions.Item>)}
                    {record.observaciones && (<Descriptions.Item label="Observaciones" span={3}><Text>{record.observaciones}</Text></Descriptions.Item>)}
                    {record.diagnostico && (<Descriptions.Item label="Diagnóstico" span={3}><Text strong>{record.diagnostico}</Text></Descriptions.Item>)}
                  </Descriptions>
                </Col>
                <Col span={24}>
                  <Card size="small" title="Trazabilidad" style={{ background: 'var(--bg-tertiary, #f0f2f5)' }}>
                    <Space split={verticalDivider} size="large">
                      <Space direction="vertical" size={0}>
                        <Text type="secondary">Realizado por:</Text>
                        <Text strong><UserOutlined /> {record.medico?.nombre || record.medico?.username || 'Sistema'}</Text>
                      </Space>
                      <Space direction="vertical" size={0}>
                        <Text type="secondary">Fecha de registro:</Text>
                        <Text strong><ClockCircleOutlined /> {record.fecha_registro ? dayjs(record.fecha_registro).format('DD/MM/YYYY HH:mm:ss') : '-'}</Text>
                      </Space>
                      {record.fecha_actualizacion && record.fecha_actualizacion !== record.fecha_registro && (
                        <Space direction="vertical" size={0}>
                          <Text type="secondary">Última modificación:</Text>
                          <Text strong><EditOutlined /> {dayjs(record.fecha_actualizacion).format('DD/MM/YYYY HH:mm:ss')}</Text>
                        </Space>
                      )}
                    </Space>
                  </Card>
                </Col>
              </Row>
            </div>
          ),
        }}
        pagination={{ pageSize: 10, showSizeChanger: true, showTotal: (total) => `Total: ${total} ecografías` }}
      />
    </div>
  );
};

export default TabEcografias;
