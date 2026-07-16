import React from 'react';
import {
  Row, Col, Card, Space, Tag, Button, Drawer, Modal, Form, Input, Select, List,
  Divider, Descriptions, Checkbox, DatePicker, Tabs, Alert, Timeline, Badge, Result,
  Typography,
} from 'antd';
import {
  SaveOutlined, DownloadOutlined, WarningOutlined, SafetyCertificateOutlined,
  HistoryOutlined, LineChartOutlined, CheckCircleOutlined,
} from '@ant-design/icons';
import type { FormInstance } from 'antd';
import dayjs, { Dayjs } from 'dayjs';
import {
  Paciente, Embarazo, ControlPrenatal, Ecografia, Laboratorio, NotaEvolucion,
  AlertaClinica, ExportConfig,
} from '../types';
import { RIESGO_COLORS, FACTORES_RIESGO } from '../utils';
import {
  formatAntecedente, ProtocoloEmbarazoItem, TendenciaLaboratorioItem,
  AlertaClinicaItem, RiskFactorItem,
} from '../historiaClinicaHelpers';
import {
  ComposedChart, Line, Bar, XAxis, YAxis, CartesianGrid, RechartsTooltip, Legend,
  ResponsiveContainer, ReferenceArea,
} from '../rechartsLazy';

const { Text } = Typography;
const { Option } = Select;

interface HistoriaClinicaModalesProps {
  // Notas SOAP
  drawerNotasVisible: boolean;
  setDrawerNotasVisible: (v: boolean) => void;
  formNota: FormInstance;
  handleAddNota: (values: any) => void;
  saving: boolean;
  // Recetas
  modalRecetaVisible: boolean;
  setModalRecetaVisible: (v: boolean) => void;
  formReceta: FormInstance;
  handleAddTratamiento: (values: any) => void;
  // Calculadora
  drawerCalculadoraVisible: boolean;
  setDrawerCalculadoraVisible: (v: boolean) => void;
  message: any;
  // Exportar
  modalExportarVisible: boolean;
  setModalExportarVisible: (v: boolean) => void;
  handleExportarHistoria: (config: ExportConfig) => void;
  // Riesgo
  modalRiesgoVisible: boolean;
  setModalRiesgoVisible: (v: boolean) => void;
  handleCalcularRiesgo: () => void;
  paciente: Paciente | null;
  embarazoActivo: Embarazo | null;
  controles: ControlPrenatal[];
  // Protocolos
  modalProtocolosVisible: boolean;
  setModalProtocolosVisible: (v: boolean) => void;
  protocolosEmbarazo: any[];
  // Timeline
  drawerTimelineVisible: boolean;
  setDrawerTimelineVisible: (v: boolean) => void;
  ecografias: Ecografia[];
  laboratorios: Laboratorio[];
  notas: NotaEvolucion[];
  // Comparación
  modalComparacionVisible: boolean;
  setModalComparacionVisible: (v: boolean) => void;
  tendenciasLaboratorio: any[];
  // Alertas
  drawerAlertasVisible: boolean;
  setDrawerAlertasVisible: (v: boolean) => void;
  alertasActivas: AlertaClinica[];
  setAlertasActivas: React.Dispatch<React.SetStateAction<AlertaClinica[]>>;
}

const HistoriaClinicaModales: React.FC<HistoriaClinicaModalesProps> = ({
  drawerNotasVisible, setDrawerNotasVisible, formNota, handleAddNota, saving,
  modalRecetaVisible, setModalRecetaVisible, formReceta, handleAddTratamiento,
  drawerCalculadoraVisible, setDrawerCalculadoraVisible, message,
  modalExportarVisible, setModalExportarVisible, handleExportarHistoria,
  modalRiesgoVisible, setModalRiesgoVisible, handleCalcularRiesgo, paciente, embarazoActivo, controles,
  modalProtocolosVisible, setModalProtocolosVisible, protocolosEmbarazo,
  drawerTimelineVisible, setDrawerTimelineVisible, ecografias, laboratorios, notas,
  modalComparacionVisible, setModalComparacionVisible, tendenciasLaboratorio,
  drawerAlertasVisible, setDrawerAlertasVisible, alertasActivas, setAlertasActivas,
}) => (
  <>
    {/* DRAWER DE NOTAS SOAP */}
    < Drawer
      title="Nueva Nota de Evolución (SOAP)"
      width={500}
      onClose={() => setDrawerNotasVisible(false)}
      open={drawerNotasVisible}
      maskClosable={false}
    >
      <Form form={formNota} layout="vertical" onFinish={handleAddNota}>
        <Form.Item name="tipo" label="Tipo de Atención" initialValue="CONSULTA">
          <Select>
            <Option value="CONSULTA">Consulta Prenatal</Option>
            <Option value="URGENCIA">Urgencia Obstétrica</Option>
            <Option value="TELECONSULTA">Telemedicina</Option>
          </Select>
        </Form.Item>

        <Divider orientation="left">Estructura SOAP</Divider>

        <Form.Item name="subjetivo" label="Subjetivo (S)" tooltip="Lo que refiere la paciente" rules={[{ required: true }]}>
          <Input.TextArea rows={3} placeholder="Ej: Paciente refiere dolor pélvico leve..." />
        </Form.Item>
        <Form.Item name="objetivo" label="Objetivo (O)" tooltip="Hallazgos del examen físico">
          <Input.TextArea rows={3} placeholder="Ej: PA 110/70, AU 24cm, LCF 140..." />
        </Form.Item>
        <Form.Item name="analisis" label="Análisis (A)" tooltip="Diagnóstico o impresión clínica">
          <Input.TextArea rows={2} placeholder="Ej: Embarazo de curso normal..." />
        </Form.Item>
        <Form.Item name="plan" label="Plan (P)" tooltip="Conducta a seguir">
          <Input.TextArea rows={3} placeholder="Ej: Se solicita ecografía de control..." />
        </Form.Item>

        <Button type="primary" htmlType="submit" block size="large" loading={saving} icon={<SaveOutlined />}>
          Guardar Nota en Historia
        </Button>
      </Form>
    </Drawer >

    {/* MODAL DE RECETAS */}
    < Modal
      title="Prescripción de Medicamentos"
      open={modalRecetaVisible}
      onCancel={() => setModalRecetaVisible(false)}
      onOk={formReceta.submit}
    >
      <Form form={formReceta} layout="vertical" onFinish={handleAddTratamiento}>
        <Form.Item name="medicamento" label="Medicamento" rules={[{ required: true }]}>
          <Input placeholder="Ej: Sulfato Ferroso + Ácido Fólico" />
        </Form.Item>
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item name="dosis" label="Dosis">
              <Input placeholder="Ej: 1 tableta" />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item name="frecuencia" label="Frecuencia">
              <Input placeholder="Ej: Cada 24 horas" />
            </Form.Item>
          </Col>
        </Row>
        <Form.Item name="duracion" label="Duración del Tratamiento">
          <Input placeholder="Ej: Por 30 días" />
        </Form.Item>
        <Form.Item name="imprimir" valuePropName="checked">
          <Checkbox>Imprimir Receta al Guardar</Checkbox>
        </Form.Item>
      </Form>
    </Modal >

    {/* CALCULADORA DRAWER */}
    < Drawer title="Herramientas Clínicas" placement="right" onClose={() => setDrawerCalculadoraVisible(false)} open={drawerCalculadoraVisible} >
      <Card title="Calculadora Gestacional" size="small">
        <p>Herramienta para cálculo rápido de FPP y EG por FUM.</p>
        <DatePicker
          style={{ width: '100%' }}
          placeholder="Seleccionar FUM"
          onChange={(date: Dayjs | null) => {
            if (date) {
              const eg = dayjs().diff(date, 'weeks');
              message.info(`Edad Gestacional: ${eg} semanas`);
            }
          }}
        />
      </Card>
    </Drawer >

    {/* MODAL DE EXPORTAR */}
    < Modal
      title="Exportar Historia Clínica"
      open={modalExportarVisible}
      onCancel={() => setModalExportarVisible(false)}
      footer={null}
      width={600}
    >
      <Form
        layout="vertical"
        onFinish={(values) => {
          const config: ExportConfig = {
            formato: values.formato,
            secciones: values.secciones || [],
            incluir_graficas: values.incluir_graficas || false,
            periodo_inicio: values.periodo ? values.periodo[0].format('YYYY-MM-DD') : undefined,
            periodo_fin: values.periodo ? values.periodo[1].format('YYYY-MM-DD') : undefined
          };
          handleExportarHistoria(config);
        }}
      >
        <Form.Item name="formato" label="Formato de Exportación" initialValue="PDF" rules={[{ required: true }]}>
          <Select>
            <Option value="PDF">PDF (Informe Imprimible)</Option>
            <Option value="EXCEL">Excel (Análisis de Datos)</Option>
            <Option value="JSON">JSON (Respaldo Digital)</Option>
          </Select>
        </Form.Item>

        <Form.Item name="secciones" label="Secciones a Incluir">
          <Checkbox.Group style={{ width: '100%' }}>
            <Row>
              <Col span={12}><Checkbox value="datos_paciente">Datos del Paciente</Checkbox></Col>
              <Col span={12}><Checkbox value="embarazo">Embarazo Actual</Checkbox></Col>
              <Col span={12}><Checkbox value="controles">Controles Prenatales</Checkbox></Col>
              <Col span={12}><Checkbox value="ecografias">Ecografías</Checkbox></Col>
              <Col span={12}><Checkbox value="laboratorios">Laboratorios</Checkbox></Col>
              <Col span={12}><Checkbox value="notas">Notas SOAP</Checkbox></Col>
              <Col span={12}><Checkbox value="tratamientos">Tratamientos</Checkbox></Col>
              <Col span={12}><Checkbox value="vacunas">Vacunas</Checkbox></Col>
            </Row>
          </Checkbox.Group>
        </Form.Item>

        <Form.Item name="incluir_graficas" valuePropName="checked">
          <Checkbox>Incluir gráficas y estadísticas visuales</Checkbox>
        </Form.Item>

        <Form.Item name="periodo" label="Período de Datos (Opcional)">
          <DatePicker.RangePicker style={{ width: '100%' }} />
        </Form.Item>

        <Form.Item>
          <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
            <Button onClick={() => setModalExportarVisible(false)}>Cancelar</Button>
            <Button type="primary" htmlType="submit" icon={<DownloadOutlined />} loading={saving}>
              Exportar
            </Button>
          </Space>
        </Form.Item>
      </Form>
    </Modal >

    {/* MODAL AVANZADO DE RIESGO */}
    < Modal
      title={
        < Space >
          <WarningOutlined style={{ color: '#fa8c16' }} />
          <Text strong>Evaluación Integral de Riesgo Obstétrico</Text>
        </Space >
      }
      open={modalRiesgoVisible}
      onCancel={() => setModalRiesgoVisible(false)}
      width={800}
      footer={
        [
          <Button key="close" onClick={() => setModalRiesgoVisible(false)}>
            Cerrar
          </Button>,
          <Button key="calc" type="primary" onClick={handleCalcularRiesgo}>
            Calcular Riesgo Preeclampsia
          </Button>
        ]}
    >
      <Tabs
        defaultActiveKey="factores"
        items={[
          {
            key: 'factores',
            label: 'Factores de Riesgo',
            children: (
              <>
                <Alert
                  message="Factores de Riesgo Obstétrico"
                  description="Clasificación según guías clínicas internacionales"
                  type="info"
                  showIcon
                  style={{ marginBottom: 16 }}
                />

                <Card title="Riesgo MUY ALTO" size="small" style={{ marginBottom: 16 }} headStyle={{ backgroundColor: '#fff2e8' }}>
                  <List
                    size="small"
                    dataSource={FACTORES_RIESGO.MUY_ALTO}
                    renderItem={(item) => <RiskFactorItem item={item} />}
                  />
                </Card>

                <Card title="Riesgo ALTO" size="small" headStyle={{ backgroundColor: '#fff7e6' }}>
                  <List
                    size="small"
                    dataSource={FACTORES_RIESGO.ALTO}
                    renderItem={(item) => <RiskFactorItem item={item} />}
                  />
                </Card>
              </>
            ),
          },
          {
            key: 'evaluacion',
            label: 'Evaluación Actual',
            children: (
              paciente && embarazoActivo && (
                <div>
                  <Descriptions bordered column={2} size="small">
                    <Descriptions.Item label="Edad" span={1}>
                      {paciente?.edad} años
                      {(paciente?.edad && (paciente.edad < 18 || paciente.edad > 35)) && (
                        <Tag color="warning" style={{ marginLeft: 8 }}>Factor de Riesgo</Tag>
                      )}
                    </Descriptions.Item>
                    <Descriptions.Item label="Riesgo Actual" span={1}>
                      <Tag color={RIESGO_COLORS[embarazoActivo?.riesgo || 'BAJO']}>{embarazoActivo?.riesgo}</Tag>
                    </Descriptions.Item>
                    <Descriptions.Item label="Paridad" span={2}>
                      G{embarazoActivo?.gestas_previas} P{embarazoActivo?.partos_previos} C{embarazoActivo?.cesareas_previas} A{embarazoActivo?.abortos_previos}
                      {(embarazoActivo?.cesareas_previas && embarazoActivo.cesareas_previas >= 2) && (
                        <Tag color="error" style={{ marginLeft: 8 }}>≥2 Cesáreas Previas</Tag>
                      )}
                    </Descriptions.Item>
                    <Descriptions.Item label="Antecedentes Patológicos" span={2}>
                      {formatAntecedente(paciente?.antecedentes_patologicos || '')}
                    </Descriptions.Item>
                  </Descriptions>

                  {controles.length > 0 && (
                    <div style={{ marginTop: 16 }}>
                      <Divider orientation="left">Último Control</Divider>
                      <Descriptions bordered column={2} size="small">
                        <Descriptions.Item label="PA">
                          {controles[controles.length - 1].presion_arterial_sistolica}/{controles[controles.length - 1].presion_arterial_diastolica}
                          {(controles[controles.length - 1].presion_arterial_sistolica >= 140 || controles[controles.length - 1].presion_arterial_diastolica >= 90) && (
                            <Tag color="error" style={{ marginLeft: 8 }}>HTA</Tag>
                          )}
                        </Descriptions.Item>
                        <Descriptions.Item label="IMC">
                          {(() => {
                            const ultimoControl = controles[controles.length - 1];
                            const imc = ultimoControl.imc_actual || ultimoControl.imc;
                            return imc != null ? imc.toFixed(1) : '-';
                          })()}
                          {(() => {
                            const ultimoControl = controles[controles.length - 1];
                            const imc = ultimoControl.imc_actual || ultimoControl.imc;
                            return imc != null && imc >= 30 && (
                              <Tag color="warning" style={{ marginLeft: 8 }}>Obesidad</Tag>
                            );
                          })()}
                        </Descriptions.Item>
                        <Descriptions.Item label="Edema">
                          {controles[controles.length - 1].edema ? 'Presente' : 'Ausente'}
                          {controles[controles.length - 1].edema && (
                            <Tag color="warning" style={{ marginLeft: 8 }}>Vigilar</Tag>
                          )}
                        </Descriptions.Item>
                        <Descriptions.Item label="Proteinuria">
                          {controles[controles.length - 1].proteinuria}
                        </Descriptions.Item>
                      </Descriptions>
                    </div>
                  )}
                </div>
              )
            ),
          },
          {
            key: 'recomendaciones',
            label: 'Recomendaciones',
            children: (
              <>
                <Alert
                  message="Plan de Manejo según Nivel de Riesgo"
                  type="info"
                  showIcon
                  style={{ marginBottom: 16 }}
                />

                <Card title="Riesgo BAJO" size="small" style={{ marginBottom: 16 }}>
                  <ul>
                    <li>Control prenatal mensual hasta semana 28</li>
                    <li>Control quincenal desde semana 28-36</li>
                    <li>Control semanal desde semana 36 hasta parto</li>
                    <li>Ecografías según protocolo estándar</li>
                    <li>Laboratorios de rutina en cada trimestre</li>
                  </ul>
                </Card>

                <Card title="Riesgo ALTO" size="small" style={{ marginBottom: 16 }}>
                  <ul>
                    <li>Control prenatal quincenal desde el inicio</li>
                    <li>Control semanal desde semana 32</li>
                    <li>Ecografías con Doppler cada 4 semanas desde semana 24</li>
                    <li>Monitoreo fetal (NST) semanal desde semana 32</li>
                    <li>Laboratorios cada mes (hemograma, función renal, hepática)</li>
                    <li>Interconsulta con especialidades según patología</li>
                  </ul>
                </Card>

                <Card title="Riesgo MUY ALTO" size="small">
                  <ul>
                    <li>Control prenatal semanal desde el inicio</li>
                    <li>Evaluación en hospital de tercer nivel</li>
                    <li>Ecografías con Doppler cada 2-3 semanas</li>
                    <li>Monitoreo fetal (NST) bisemanal desde semana 28</li>
                    <li>Perfil biofísico semanal desde semana 32</li>
                    <li>Hospitalización si se deteriora condición materna o fetal</li>
                    <li>Plan de parto individualizado con equipo multidisciplinario</li>
                    <li>Considerar maduración pulmonar fetal si parto pretérmino anticipado</li>
                  </ul>
                </Card>
              </>
            ),
          }
        ]}
      />
    </Modal >

    {/* MODAL DE PROTOCOLOS OBSTÉTRICOS */}
    <Modal
      title={
        <Space>
          <SafetyCertificateOutlined />
          Protocolos Obstétricos - Cumplimiento
        </Space>
      }
      open={modalProtocolosVisible}
      onCancel={() => setModalProtocolosVisible(false)}
      width={900}
      footer={[
        <Button key="close" onClick={() => setModalProtocolosVisible(false)}>
          Cerrar
        </Button>
      ]}
    >
      <List
        dataSource={protocolosEmbarazo}
        renderItem={(protocolo) => <ProtocoloEmbarazoItem protocolo={protocolo} />}
      />
    </Modal>

    {/* DRAWER DE LÍNEA DE TIEMPO */}
    <Drawer
      title={
        <Space>
          <HistoryOutlined />
          Línea de Tiempo Obstétrica
        </Space>
      }
      placement="right"
      onClose={() => setDrawerTimelineVisible(false)}
      open={drawerTimelineVisible}
      width={600}
    >
      <Timeline
        mode="left"
        items={[...controles, ...ecografias, ...laboratorios, ...notas]
          .sort((a, b) => {
            const dateA = new Date((a as any).fecha_control || (a as any).fecha || (a as any).fecha_consulta);
            const dateB = new Date((b as any).fecha_control || (b as any).fecha || (b as any).fecha_consulta);
            return dateB.getTime() - dateA.getTime();
          })
          .slice(0, 20)
          .map((item, idx) => {
            const itemAny = item as any;
            const tipo = item.hasOwnProperty('fecha_control')
              ? 'Control'
              : item.hasOwnProperty('dbt')
                ? 'Ecografía'
                : item.hasOwnProperty('hemoglobina')
                  ? 'Laboratorio'
                  : 'Nota';
            const fecha = itemAny.fecha_control || itemAny.fecha || itemAny.fecha_consulta;

            return {
              key: `${tipo}-${itemAny.id || idx}`,
              color: tipo === 'Control' ? 'green' : tipo === 'Ecografía' ? 'blue' : 'gray',
              children: (
                <>
                  <Text strong>{tipo}</Text>
                  <br />
                  <Text type="secondary">{dayjs(fecha).format('DD/MM/YYYY')}</Text>
                </>
              ),
            };
          })}
      />
    </Drawer>

    {/* MODAL DE COMPARACIÓN DE DATOS */}
    <Modal
      title={
        <Space>
          <LineChartOutlined />
          Comparación de Datos Clínicos
        </Space>
      }
      open={modalComparacionVisible}
      onCancel={() => setModalComparacionVisible(false)}
      width={1000}
      footer={[
        <Button key="close" onClick={() => setModalComparacionVisible(false)}>
          Cerrar
        </Button>
      ]}
    >
      <Row gutter={[16, 16]}>
        <Col span={12}>
          <Card title="Presión Arterial" size="small">
            <ResponsiveContainer width="100%" height={200}>
              <ComposedChart
                data={controles.map((c) => ({
                  fecha: dayjs(c.fecha_control || c.fecha).format('DD/MM'),
                  sistolica: c.presion_arterial_sistolica,
                  diastolica: c.presion_arterial_diastolica,
                }))}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="fecha" />
                <YAxis />
                <RechartsTooltip />
                <Legend />
                <Line type="monotone" dataKey="sistolica" stroke="#8884d8" name="Sistólica" />
                <Line type="monotone" dataKey="diastolica" stroke="#82ca9d" name="Diastólica" />
                <ReferenceArea y1={140} y2={200} fill="#ff4d4f" fillOpacity={0.1} />
              </ComposedChart>
            </ResponsiveContainer>
          </Card>
        </Col>
        <Col span={12}>
          <Card title="Hemoglobina" size="small">
            <ResponsiveContainer width="100%" height={200}>
              <ComposedChart
                data={laboratorios
                  .reduce((acc, l) => {
                    const tipo = typeof l.tipo_examen === 'string' ? l.tipo_examen.toLowerCase() : String(l.tipo_examen || '').toLowerCase();
                    if (tipo.includes('hemoglobina')) {
                      acc.push({
                        fecha: dayjs(l.fecha_toma).format('DD/MM'),
                        valor: parseFloat(l.resultado) || 0,
                      });
                    }
                    return acc;
                  }, [] as any[])}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="fecha" />
                <YAxis />
                <RechartsTooltip />
                <Legend />
                <Bar dataKey="valor" fill="#8884d8" name="Hb (g/dL)" />
                <ReferenceArea y1={0} y2={11} fill="#ff4d4f" fillOpacity={0.1} />
              </ComposedChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      {tendenciasLaboratorio.length > 0 && (
        <Card title="Tendencias" size="small" style={{ marginTop: 16 }}>
          <List
            dataSource={tendenciasLaboratorio}
            renderItem={(tendencia) => <TendenciaLaboratorioItem tendencia={tendencia} />}
          />
        </Card>
      )}
    </Modal>

    {/* DRAWER DE ALERTAS CLÍNICAS */}
    <Drawer
      title={
        <Space>
          <WarningOutlined />
          Panel de Alertas Clínicas
          <Badge count={alertasActivas.length} style={{ backgroundColor: '#ff4d4f' }} />
        </Space>
      }
      placement="right"
      onClose={() => setDrawerAlertasVisible(false)}
      open={drawerAlertasVisible}
      width={500}
    >
      {alertasActivas.length === 0 ? (
        <Result
          status="success"
          title="Sin Alertas"
          subTitle="No hay alertas clínicas activas para este paciente."
          icon={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
        />
      ) : (
        <List
          dataSource={alertasActivas}
          renderItem={(alerta) => (
            <AlertaClinicaItem
              alerta={alerta}
              onResuelta={(id) => {
                setAlertasActivas(prev => prev.map((a) =>
                  a.id === id ? { ...a, resuelta: true } : a
                ));
              }}
            />
          )}
        />
      )}
    </Drawer>
  </>
);

export default HistoriaClinicaModales;
