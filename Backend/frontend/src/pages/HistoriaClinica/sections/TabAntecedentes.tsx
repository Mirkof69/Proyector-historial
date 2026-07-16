import React from 'react';
import { Row, Col, Card, Space, Tag, Descriptions, Empty, Divider, Alert, Table } from 'antd';
import { WomanOutlined, MedicineBoxOutlined, WarningOutlined, CheckCircleOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { Paciente, Embarazo } from '../types';
import { AntecedentePatologico, AntecedenteGinecoObstetrico } from '../../../services/antecedentesService';
import { formatAntecedente } from '../historiaClinicaHelpers';

interface TabAntecedentesProps {
  paciente: Paciente | null;
  antecedenteGineco: AntecedenteGinecoObstetrico | null;
  antecedentePatologico: AntecedentePatologico | null;
  historialEmbarazos: Embarazo[];
}

const TabAntecedentes: React.FC<TabAntecedentesProps> = ({
  paciente, antecedenteGineco, antecedentePatologico, historialEmbarazos,
}) => (
  <div style={{ padding: 24 }}>
    <Row gutter={[16, 16]}>
      {/* ANTECEDENTES GINECO-OBSTÉTRICOS */}
      <Col span={24}>
        <Card
          title={
            <Space>
              <WomanOutlined style={{ color: '#722ed1' }} />
              <span>Antecedentes Gineco-Obstétricos</span>
            </Space>
          }
          extra={
            antecedenteGineco && (
              <Tag color="purple" style={{ fontSize: 16, padding: '4px 12px' }}>
                Fórmula: {antecedenteGineco.gestas || 0}G-{antecedenteGineco.partos || 0}P-{antecedenteGineco.abortos || 0}A-{antecedenteGineco.cesareas || 0}C
              </Tag>
            )
          }
        >
          {antecedenteGineco ? (
            <Descriptions bordered column={2} size="small">
              <Descriptions.Item label="Menarquia (Edad)" span={1}>
                {antecedenteGineco.menarquia_edad ? `${antecedenteGineco.menarquia_edad} años` : 'No registra'}
              </Descriptions.Item>
              <Descriptions.Item label="Ciclos Menstruales" span={1}>
                {antecedenteGineco.ciclos_menstruales || 'No registra'}
              </Descriptions.Item>
              <Descriptions.Item label="Duración del Ciclo" span={1}>
                {antecedenteGineco.duracion_ciclo_dias ? `${antecedenteGineco.duracion_ciclo_dias} días` : 'No registra'}
              </Descriptions.Item>
              <Descriptions.Item label="Duración Menstruación" span={1}>
                {antecedenteGineco.duracion_menstruacion_dias ? `${antecedenteGineco.duracion_menstruacion_dias} días` : 'No registra'}
              </Descriptions.Item>
              <Descriptions.Item label="Última Menstruación (FUM)" span={2}>
                {antecedenteGineco.fecha_ultima_menstruacion
                  ? dayjs(antecedenteGineco.fecha_ultima_menstruacion).format('DD/MM/YYYY')
                  : 'No registra'}
              </Descriptions.Item>
              <Descriptions.Item label="Gestas" span={1}>
                <Tag color="blue">{antecedenteGineco.gestas || 0}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Partos" span={1}>
                <Tag color="green">{antecedenteGineco.partos || 0}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Abortos" span={1}>
                <Tag color="orange">{antecedenteGineco.abortos || 0}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Cesáreas" span={1}>
                <Tag color="red">{antecedenteGineco.cesareas || 0}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Hijos Vivos" span={2}>
                <Tag color="cyan">{antecedenteGineco.hijos_vivos || 0}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Anticonceptivo Actual" span={1}>
                {antecedenteGineco.metodo_anticonceptivo_actual || 'No usa'}
              </Descriptions.Item>
              <Descriptions.Item label="Tiempo de Uso" span={1}>
                {antecedenteGineco.tiempo_uso_anticonceptivo_meses
                  ? `${antecedenteGineco.tiempo_uso_anticonceptivo_meses} meses`
                  : 'N/A'}
              </Descriptions.Item>
              <Descriptions.Item label="Inicio Vida Sexual (Edad)" span={1}>
                {antecedenteGineco.inicio_vida_sexual_edad
                  ? `${antecedenteGineco.inicio_vida_sexual_edad} años`
                  : 'No registra'}
              </Descriptions.Item>
              <Descriptions.Item label="Número de Parejas Sexuales" span={1}>
                {antecedenteGineco.numero_parejas_sexuales || 'No registra'}
              </Descriptions.Item>
            </Descriptions>
          ) : (
            <Empty
              description="No hay antecedentes gineco-obstétricos registrados"
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            />
          )}
        </Card>
      </Col>

      {/* ANTECEDENTES PATOLÓGICOS */}
      <Col span={24}>
        <Card
          title={
            <Space>
              <MedicineBoxOutlined style={{ color: '#f5222d' }} />
              <span>Antecedentes Patológicos</span>
            </Space>
          }
        >
          {antecedentePatologico ? (
            <>
              <Descriptions bordered column={3} size="small" style={{ marginBottom: 16 }}>
                <Descriptions.Item label="Tipo de Antecedente" span={3}>
                  <Tag color={antecedentePatologico.tipo === 'personal' ? 'blue' : 'purple'}>
                    {antecedentePatologico.tipo === 'personal' ? 'Personal' : 'Heredofamiliar'}
                  </Tag>
                </Descriptions.Item>
              </Descriptions>

              <Divider orientation="left">Alergias (CRÍTICO)</Divider>
              <Descriptions bordered column={2} size="small" style={{ marginBottom: 16 }}>
                <Descriptions.Item label="Tiene Alergias" span={2}>
                  {antecedentePatologico.tiene_alergias ? (
                    <Tag color="red" icon={<WarningOutlined />}>SÍ - REVISAR DETALLE</Tag>
                  ) : (
                    <Tag color="green">No</Tag>
                  )}
                </Descriptions.Item>
                {antecedentePatologico.tiene_alergias && (
                  <>
                    <Descriptions.Item label="Alergias a Medicamentos" span={2}>
                      {antecedentePatologico.alergias_medicamentos || 'No especificado'}
                    </Descriptions.Item>
                    <Descriptions.Item label="Alergias a Alimentos" span={2}>
                      {antecedentePatologico.alergias_alimentos || 'No especificado'}
                    </Descriptions.Item>
                    <Descriptions.Item label="Otras Alergias" span={2}>
                      {antecedentePatologico.alergias_otras || 'No especificado'}
                    </Descriptions.Item>
                  </>
                )}
              </Descriptions>

              <Divider orientation="left">Enfermedades Crónicas</Divider>
              <Row gutter={[8, 8]} style={{ marginBottom: 16 }}>
                {[
                  { key: 'diabetes', label: 'Diabetes', color: 'orange' },
                  { key: 'hipertension', label: 'Hipertensión', color: 'red' },
                  { key: 'cardiopatias', label: 'Cardiopatías', color: 'magenta' },
                  { key: 'nefropatias', label: 'Nefropatías', color: 'purple' },
                  { key: 'trastornos_coagulacion', label: 'Trastornos Coagulación', color: 'volcano' },
                  { key: 'anemia', label: 'Anemia', color: 'gold' },
                  { key: 'lupus', label: 'Lupus', color: 'geekblue' },
                  { key: 'artritis_reumatoide', label: 'Artritis Reumatoide', color: 'cyan' },
                  { key: 'asma', label: 'Asma', color: 'blue' },
                ].map(enf =>
                  antecedentePatologico[enf.key as keyof AntecedentePatologico] && (
                    <Col key={enf.key}>
                      <Tag color={enf.color} icon={<CheckCircleOutlined />}>{enf.label}</Tag>
                    </Col>
                  )
                )}
              </Row>

              {antecedentePatologico.diabetes && antecedentePatologico.diabetes_tipo && (
                <Alert
                  message={`Tipo de Diabetes: ${antecedentePatologico.diabetes_tipo}`}
                  type="warning"
                  showIcon
                  style={{ marginBottom: 16 }}
                />
              )}

              <Divider orientation="left">Antecedentes Obstétricos Específicos</Divider>
              <Row gutter={[8, 8]} style={{ marginBottom: 16 }}>
                {[
                  { key: 'preeclampsia_previa', label: 'Preeclampsia Previa', color: 'red' },
                  { key: 'eclampsia_previa', label: 'Eclampsia Previa', color: 'red' },
                  { key: 'diabetes_gestacional_previa', label: 'Diabetes Gestacional Previa', color: 'orange' },
                  { key: 'hemorragia_postparto_previa', label: 'Hemorragia Postparto Previa', color: 'volcano' },
                ].map(ant =>
                  antecedentePatologico[ant.key as keyof AntecedentePatologico] && (
                    <Col key={ant.key}>
                      <Tag color={ant.color} icon={<WarningOutlined />}>{ant.label}</Tag>
                    </Col>
                  )
                )}
              </Row>

              <Descriptions bordered column={1} size="small">
                {antecedentePatologico.cardiopatia_detalle && (
                  <Descriptions.Item label="Detalle Cardiopatía">
                    {antecedentePatologico.cardiopatia_detalle}
                  </Descriptions.Item>
                )}
                {antecedentePatologico.nefropatia_detalle && (
                  <Descriptions.Item label="Detalle Nefropatía">
                    {antecedentePatologico.nefropatia_detalle}
                  </Descriptions.Item>
                )}
                {antecedentePatologico.otras_enfermedades && (
                  <Descriptions.Item label="Otras Enfermedades">
                    {antecedentePatologico.otras_enfermedades}
                  </Descriptions.Item>
                )}
                {antecedentePatologico.cirugias_anteriores && (
                  <Descriptions.Item label="Cirugías Anteriores">
                    {antecedentePatologico.cirugias_anteriores}
                  </Descriptions.Item>
                )}
              </Descriptions>
            </>
          ) : (
            <Empty
              description="No hay antecedentes patológicos registrados"
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            />
          )}
        </Card>
      </Col>

      {/* ANTECEDENTES GENERALES DEL PACIENTE (Texto Libre) */}
      <Col span={24}>
        <Card title="Antecedentes Generales (Texto Libre)">
          <Descriptions bordered column={1} size="small">
            <Descriptions.Item label="Antecedentes Patológicos">
              {formatAntecedente(paciente?.antecedentes_patologicos)}
            </Descriptions.Item>
            <Descriptions.Item label="Antecedentes Quirúrgicos">
              {formatAntecedente(paciente?.antecedentes_quirurgicos)}
            </Descriptions.Item>
            <Descriptions.Item label="Antecedentes Familiares">
              {formatAntecedente(paciente?.antecedentes_familiares)}
            </Descriptions.Item>
            <Descriptions.Item label="Hábitos Tóxicos">
              {formatAntecedente(paciente?.habitos_toxicos)}
            </Descriptions.Item>
          </Descriptions>
        </Card>
      </Col>

      {/* HISTORIAL DE EMBARAZOS */}
      {historialEmbarazos.length > 0 && (
        <Col span={24}>
          <Card title="Historial de Embarazos Previos">
            <Table
              dataSource={historialEmbarazos}
              pagination={false}
              rowKey="id"
              size="small"
              columns={[
                {
                  title: 'Año',
                  render: (_, r: any) => dayjs(r.fecha_ultima_menstruacion).format('YYYY'),
                  width: 80
                },
                {
                  title: 'G/P/A/C',
                  render: (_, r: any) => `${r.gestas_previas || 0}/${r.partos_previos || 0}/${r.abortos_previos || 0}/${r.cesareas_previas || 0}`,
                  width: 100
                },
                {
                  title: 'Observaciones',
                  dataIndex: 'observaciones',
                  render: (text: string) => text || 'Sin observaciones'
                }
              ]}
            />
          </Card>
        </Col>
      )}
    </Row>
  </div>
);

export default TabAntecedentes;
