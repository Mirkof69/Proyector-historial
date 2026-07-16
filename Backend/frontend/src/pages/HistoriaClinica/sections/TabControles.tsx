import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Row, Col, Card, Space, Tag, Button, Table, Tooltip, Popconfirm, Divider, Typography,
} from 'antd';
import {
  DownloadOutlined, PlusOutlined, HeartOutlined, ScanOutlined, DeleteOutlined,
  ClockCircleOutlined, EditOutlined, UserOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { useAntdApp } from '../../../hooks/useMessage';
import GraficoPesoMaterno from '../../../components/graficos/GraficoPesoMaterno';
import GraficoAlturaUterina from '../../../components/graficos/GraficoAlturaUterina';
import GraficoPresionArterial from '../../../components/graficos/GraficoPresionArterial';
import { ControlPrenatal, Embarazo } from '../types';
import { safeNum } from '../utils';
import { verticalDivider, FCF_DOMAIN, FCF_LABEL } from '../historiaClinicaHelpers';
import {
  ComposedChart, Line, XAxis, YAxis, CartesianGrid, RechartsTooltip, Legend,
  ResponsiveContainer, ReferenceArea,
} from '../rechartsLazy';

const { Title } = Typography;

interface TabControlesProps {
  controles: ControlPrenatal[];
  embarazoActivo: Embarazo | null;
  navigate: ReturnType<typeof useNavigate>;
}
const TabControles: React.FC<TabControlesProps> = ({ controles, embarazoActivo, navigate }) => {
  const {modal,  message } = useAntdApp();
  const chartData = controles
    .reduce((acc, c) => {
      if (c.peso_actual && c.presion_arterial_sistolica && c.presion_arterial_diastolica) {
        acc.push({
          semana: safeNum(c.semanas_gestacion),
          fecha: dayjs(c.fecha_control || c.fecha).format('DD/MM'),
          peso: safeNum(c.peso_actual),
          sistolica: safeNum(c.presion_arterial_sistolica),
          diastolica: safeNum(c.presion_arterial_diastolica),
          altura_uterina: safeNum(c.altura_uterina),
          lcf: safeNum(c.frecuencia_cardiaca_fetal),
        });
      }
      return acc;
    }, [] as any[])
    .sort((a, b) => a.semana - b.semana);

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <Title level={4}>Historial de Controles Prenatales</Title>
        <Space>
          <Button icon={<DownloadOutlined />}>Exportar Excel</Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate(`/controles/nuevo?embarazo=${embarazoActivo?.id}`)}>Nuevo Control</Button>
        </Space>
      </div>

      {chartData.length > 0 && (
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col xs={24} lg={12}>
            <GraficoPesoMaterno
              data={chartData.map(d => ({
                semana: safeNum(d.semana),
                peso_actual: safeNum(d.peso)
              }))}
              pesoPregestacional={safeNum(embarazoActivo?.peso_pregestacional) || 50}
              tallaMaterna={safeNum(embarazoActivo?.talla_materna) || 160}
            />
          </Col>
          <Col xs={24} lg={12}>
            <GraficoPresionArterial
              data={chartData.map(d => ({
                semana: d.semana || 0,
                sistolica: d.sistolica || 0,
                diastolica: d.diastolica || 0
              }))}
            />
          </Col>
          <Col xs={24} lg={12}>
            <GraficoAlturaUterina
              data={chartData.map(d => ({
                semana: d.semana || 0,
                altura_uterina: d.altura_uterina || 0
              }))}
            />
          </Col>
          <Col xs={24} lg={12}>
            <Card title={<><HeartOutlined /> Frecuencia Cardíaca Fetal</>} size="small">
              <ResponsiveContainer width="100%" height={250}>
                <ComposedChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="fecha" />
                  <YAxis domain={FCF_DOMAIN} label={FCF_LABEL} />
                  <RechartsTooltip />
                  <Legend />
                  <ReferenceArea y1={110} y2={160} fill="#52c41a" fillOpacity={0.1} />
                  <Line
                    type="monotone"
                    dataKey="lcf"
                    stroke="#eb2f96"
                    strokeWidth={2}
                    name="LCF (lpm)"
                    dot={{ fill: '#eb2f96', r: 4 }}
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </Card>
          </Col>
        </Row>
      )}

      <Table
        dataSource={[...controles].reverse()}
        rowKey="id"
        size="middle"
        bordered
        columns={[
          { title: 'Semana', render: (_: any, r: any) => r.semanas_gestacion ?? r.edad_gestacional_semanas ?? '-', width: 80, align: 'center' as const },
          { title: 'Fecha', render: (_: any, r: any) => dayjs(r.fecha_control || r.fecha).format('DD/MM/YY'), width: 100 },
          { title: 'Peso (kg)', dataIndex: 'peso_actual', align: 'center' },
          { title: 'PA (mmHg)', render: (_, r: any) => <Tag color={r.presion_arterial_sistolica >= 140 ? 'red' : 'green'}>{r.presion_arterial_sistolica}/{r.presion_arterial_diastolica}</Tag>, align: 'center' },
          { title: 'AU (cm)', dataIndex: 'altura_uterina', align: 'center' },
          { title: 'LCF', dataIndex: 'frecuencia_cardiaca_fetal', align: 'center' },
          { title: 'Presentación', dataIndex: 'presentacion_fetal' },
          { title: 'Edema', dataIndex: 'edema', render: (v) => v ? 'SÍ' : 'NO' },
          { title: 'Médico', dataIndex: ['medico', 'username'], responsive: ['lg'] as any },
          {
            title: 'Acción', render: (_, r: any) => (
              <Space>
                <Tooltip title="Ver"><Button size="small" icon={<ScanOutlined />} onClick={() => navigate(`/controles/${r.id}`)} /></Tooltip>
                <Popconfirm title="¿Eliminar registro?" onConfirm={() => message.warning("Requiere permisos de admin")}><Button size="small" danger icon={<DeleteOutlined />} /></Popconfirm>
              </Space>
            )
          }
        ]}
        expandable={{
          expandedRowRender: (record: any) => (
            <div style={{ margin: 0 }}>
              <p><strong>Observaciones:</strong> {record.observaciones || 'Sin observaciones'}</p>
              <p><strong>Próxima cita:</strong> {record.proximo_control ? dayjs(record.proximo_control).format('DD/MM/YYYY') : 'No programada'}</p>
              <Divider style={{ margin: '8px 0' }} />
              <Space split={verticalDivider} size="small" style={{ fontSize: 12, color: '#8c8c8c' }}>
                <span><ClockCircleOutlined /> Creado: {dayjs(record.fecha_registro || record.fecha).format('DD/MM/YYYY HH:mm')}</span>
                {record.fecha_actualizacion && record.fecha_actualizacion !== record.fecha_registro && (
                  <span><EditOutlined /> Modificado: {dayjs(record.fecha_actualizacion).format('DD/MM/YYYY HH:mm')}</span>
                )}
                <span><UserOutlined /> Por: {record.medico?.username || record.medico?.nombre || 'Sistema'}</span>
              </Space>
            </div>
          ),
        }}
      />
    </div>
  );
};

export default TabControles;
