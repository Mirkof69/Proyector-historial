import React from 'react';
import {
  Card, Descriptions, Tabs, Button, Table, Tag, Timeline, Empty, Tooltip as AntTooltip,
} from 'antd';
import {
  MedicineBoxOutlined, DashboardOutlined, FileTextOutlined, SafetyOutlined,
  ScanOutlined, ExperimentOutlined, LineChartOutlined, RobotOutlined, EyeOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { columnsEmbarazos, columnsTriajes, columnsNotas, columnsVacunas } from '../detallePacienteColumns';

interface DetallePacienteTabsProps {
  embarazos: any[];
  triajes: any[];
  notasEvolucion: any[];
  vacunas: any[];
  antecedentes: any[];
  ecografias: any[];
  navigate: (path: string) => void;
}

const DetallePacienteTabs: React.FC<DetallePacienteTabsProps> = ({
  embarazos, triajes, notasEvolucion, vacunas, antecedentes, ecografias, navigate,
}) => (
  <Card bordered={false}>
    <Tabs
      defaultActiveKey="1"
      items={[
        {
          key: '1',
          label: (
            <span>
              <MedicineBoxOutlined /> Embarazos ({embarazos.length})
            </span>
          ),
          children: (
            <Table
              dataSource={embarazos}
              columns={columnsEmbarazos}
              rowKey="id"
              pagination={{ pageSize: 5 }}
              locale={{ emptyText: <Empty description="No hay embarazos registrados" /> }}
            />
          ),
        },
        {
          key: '2',
          label: (
            <span>
              <DashboardOutlined /> Triajes ({triajes.length})
            </span>
          ),
          children: (
            <Table
              dataSource={triajes}
              columns={columnsTriajes}
              rowKey="id"
              pagination={{ pageSize: 10 }}
              locale={{ emptyText: <Empty description="No hay triajes registrados" /> }}
            />
          ),
        },
        {
          key: '3',
          label: (
            <span>
              <FileTextOutlined /> Notas Médicas ({notasEvolucion.length})
            </span>
          ),
          children: (
            <Table
              dataSource={notasEvolucion}
              columns={columnsNotas}
              rowKey="id"
              pagination={{ pageSize: 10 }}
              locale={{ emptyText: <Empty description="No hay notas de evolución registradas" /> }}
            />
          ),
        },
        {
          key: '4',
          label: (
            <span>
              <SafetyOutlined /> Vacunas ({vacunas.length})
            </span>
          ),
          children: (
            <Table
              dataSource={vacunas}
              columns={columnsVacunas}
              rowKey="id"
              pagination={{ pageSize: 10 }}
              locale={{ emptyText: <Empty description="No hay vacunas registradas" /> }}
            />
          ),
        },
        {
          key: '5',
          label: (
            <span>
              <ExperimentOutlined /> Antecedentes ({antecedentes.length})
            </span>
          ),
          children: antecedentes.length > 0 ? (
            <Card>
              <Descriptions bordered column={2}>
                {antecedentes[0].diabetes !== undefined && (
                  <Descriptions.Item label="Diabetes">
                    <Tag color={antecedentes[0].diabetes ? 'red' : 'green'}>
                      {antecedentes[0].diabetes ? 'Sí' : 'No'}
                    </Tag>
                  </Descriptions.Item>
                )}
                {antecedentes[0].hipertension !== undefined && (
                  <Descriptions.Item label="Hipertensión">
                    <Tag color={antecedentes[0].hipertension ? 'red' : 'green'}>
                      {antecedentes[0].hipertension ? 'Sí' : 'No'}
                    </Tag>
                  </Descriptions.Item>
                )}
                {antecedentes[0].cardiopatia !== undefined && (
                  <Descriptions.Item label="Cardiopatía">
                    <Tag color={antecedentes[0].cardiopatia ? 'orange' : 'green'}>
                      {antecedentes[0].cardiopatia ? 'Sí' : 'No'}
                    </Tag>
                  </Descriptions.Item>
                )}
                {antecedentes[0].alergias && (
                  <Descriptions.Item label="Alergias" span={2}>
                    {antecedentes[0].alergias}
                  </Descriptions.Item>
                )}
                {antecedentes[0].medicamentos && (
                  <Descriptions.Item label="Medicamentos" span={2}>
                    {antecedentes[0].medicamentos}
                  </Descriptions.Item>
                )}
                {antecedentes[0].quirurgicos && (
                  <Descriptions.Item label="Quirúrgicos" span={2}>
                    {antecedentes[0].quirurgicos}
                  </Descriptions.Item>
                )}
              </Descriptions>
            </Card>
          ) : (
            <Empty description="No hay antecedentes registrados" />
          ),
        },
        {
          key: '6',
          label: (
            <span>
              <ScanOutlined /> Ecografías ({ecografias.length})
            </span>
          ),
          children: (
            <Table
              dataSource={ecografias}
              columns={[
                { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
                { title: 'Fecha', dataIndex: 'fecha_ecografia', key: 'fecha_ecografia', width: 120,
                  render: (f: string) => dayjs(f).format('DD/MM/YYYY') },
                { title: 'Tipo', dataIndex: 'tipo_ecografia', key: 'tipo_ecografia', width: 150,
                  render: (t: string) => <Tag>{t?.replace(/_/g, ' ')}</Tag> },
                { title: 'Edad Gestacional', key: 'eg', width: 120,
                  render: (_: any, r: any) => `${r.edad_gestacional_semanas || 0}+${r.edad_gestacional_dias || 0}` },
                { title: 'Diagnóstico', dataIndex: 'diagnostico', key: 'diagnostico', ellipsis: true },
                { title: 'IA', key: 'ia', width: 60, align: 'center' as const,
                  render: (_: any, r: any) => (r as any).tiene_analisis_ia
                    ? <AntTooltip title="Tiene análisis IA"><RobotOutlined style={{ color: '#722ed1', fontSize: 18 }} /></AntTooltip>
                    : null },
                { title: 'Acción', key: 'accion', width: 100,
                  render: (_: any, r: any) => (
                    <Button type="link" size="small" icon={<EyeOutlined />}
                      onClick={() => navigate(`/dashboard/ecografias/${r.id}`)}>
                      Ver
                    </Button>
                  ) },
              ]}
              rowKey="id"
              pagination={{ pageSize: 5 }}
              locale={{ emptyText: <Empty description="No hay ecografías registradas" /> }}
              size="small"
            />
          ),
        },
        {
          key: '7',
          label: (
            <span>
              <LineChartOutlined /> Timeline Completo
            </span>
          ),
          children: (
            <Timeline
              mode="left"
              items={[...triajes, ...notasEvolucion, ...vacunas]
                .sort((a, b) => {
                  const dateA = new Date(a.fecha_hora || a.fecha_consulta || a.fecha_aplicacion || a.fecha_registro);
                  const dateB = new Date(b.fecha_hora || b.fecha_consulta || b.fecha_aplicacion || b.fecha_registro);
                  return dateB.getTime() - dateA.getTime();
                })
                .slice(0, 20)
                .map((item) => {
                  let label = '';
                  let content = '';
                  let color = 'blue';

                  if (item.prioridad) {
                    label = dayjs(item.fecha_hora || item.fecha_registro).format('DD/MM/YYYY HH:mm');
                    content = `Triaje - Prioridad: ${item.prioridad}`;
                    color = item.prioridad === 'urgente' ? 'red' : item.prioridad === 'alto' ? 'orange' : 'blue';
                  } else if (item.tipo_consulta) {
                    label = dayjs(item.fecha_consulta).format('DD/MM/YYYY');
                    content = `Nota Médica - ${item.tipo_consulta}: ${item.motivo_consulta?.substring(0, 50)}...`;
                    color = 'purple';
                  } else if (item.lote) {
                    label = dayjs(item.fecha_aplicacion).format('DD/MM/YYYY');
                    content = `Vacuna - ${item.tipo_vacuna_nombre || 'Vacuna'} (Dosis ${item.numero_dosis})`;
                    color = 'green';
                  }

                  return {
                    key: item.id || `${item.fecha_hora || item.fecha_registro || item.fecha_consulta || item.fecha_aplicacion}-${content}`,
                    label,
                    children: content,
                    color,
                  };
                })}
            />
          ),
        },
      ]}
    />
  </Card>
);

export default DetallePacienteTabs;
