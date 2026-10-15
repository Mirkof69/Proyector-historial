import React from 'react';
import { Card, Form, Select, DatePicker, InputNumber, Row, Col, Space, Divider, Typography, Checkbox, Alert } from 'antd';
import dayjs from 'dayjs';
import { Embarazo } from '../../../services/embarazosService';
import { PacienteSelect } from '../../../components/clinico/SelectoresClinicos';

const { Option } = Select;
const { Text } = Typography;

interface TabDatosGeneralesEcoProps {
  embarazos: Embarazo[];
  selectedPaciente: number | null;
  selectedEmbarazo: Embarazo | null;
  isEditing: boolean;
  handlePacienteChange: (value: number | null) => void;
  actualizarEdadGestacional: (embarazoId?: number) => void;
}

const TabDatosGeneralesEco: React.FC<TabDatosGeneralesEcoProps> = ({
  embarazos, selectedPaciente, selectedEmbarazo, isEditing,
  handlePacienteChange, actualizarEdadGestacional,
}) => (
  <Card className="shadow-sm">
    <Row gutter={24}>
      <Col xs={24} md={12}>
        <Form.Item name="paciente" label="Paciente" rules={[{ required: true, message: 'Seleccione un paciente' }]}>
          <PacienteSelect onChange={(v) => handlePacienteChange(v ?? null)} disabled={isEditing} />
        </Form.Item>
      </Col>
      <Col xs={24} md={12}>
        <Form.Item name="embarazo" label="Embarazo Asociado" rules={[{ required: true, message: 'Seleccione un embarazo' }]}>
          <Select placeholder={selectedPaciente ? 'Seleccione embarazo...' : 'Primero seleccione paciente'} disabled={!selectedPaciente || embarazos.length === 0 || isEditing} onChange={(v: number) => actualizarEdadGestacional(v)} options={embarazos.map((e) => ({ label: `FUM: ${dayjs(e.fecha_ultima_menstruacion).format('DD/MM/YYYY')} - ${(e.estado || 'activo').toUpperCase()}`, value: e.id }))} />
        </Form.Item>
      </Col>
    </Row>
    <Row gutter={24}>
      <Col xs={24} md={8}>
        <Form.Item name="fecha_ecografia" label="Fecha del Estudio" rules={[{ required: true, message: 'Requerido' }]}>
          <DatePicker className="u-ancho" format="DD/MM/YYYY" onChange={() => actualizarEdadGestacional()} disabledDate={(d) => d && d.isAfter(dayjs(), 'day')} />
        </Form.Item>
      </Col>
      <Col xs={24} md={8}>
        <Form.Item name="tipo_ecografia" label="Tipo de Ecografía" rules={[{ required: true, message: 'Requerido' }]}>
          <Select>{['primer_trimestre|Primer Trimestre (6-14 sem)','segundo_trimestre|Segundo Trimestre (14-28 sem)','tercer_trimestre|Tercer Trimestre (28-42 sem)','doppler|Doppler','morfologica|Morfológica','genetica|Genética','4d|Ecografía 4D'].map(o => { const [v,l]=o.split('|'); return <Option key={v} value={v}>{l}</Option>; })}</Select>
        </Form.Item>
      </Col>
      <Col xs={24} md={8}>
        <Form.Item name="indicacion" label="Indicación Médica">
          <Select>{['control_rutina|Control de Rutina','sospecha_malformacion|Sospecha de Malformación','control_crecimiento|Control de Crecimiento','evaluacion_bienestar|Evaluación Bienestar Fetal','sangrado|Sangrado','screening_genetico|Screening Genético','doppler_fetal|Doppler Fetal','otro|Otro'].map(o => { const [v,l]=o.split('|'); return <Option key={v} value={v}>{l}</Option>; })}</Select>
        </Form.Item>
      </Col>
    </Row>
    <Divider orientation="left">Datos Básicos del Feto</Divider>
    {selectedEmbarazo && (
      <Alert message="Información del Embarazo" description={<Space direction="vertical" size="small" className="u-ancho"><Row gutter={16}><Col xs={24} md={8}><Text strong>FUM:</Text> {dayjs(selectedEmbarazo.fecha_ultima_menstruacion).format('DD/MM/YYYY')}</Col><Col xs={24} md={8}><Text strong>FPP:</Text> {selectedEmbarazo.fecha_probable_parto ? dayjs(selectedEmbarazo.fecha_probable_parto).format('DD/MM/YYYY') : 'No calculada'}</Col><Col xs={24} md={8}><Text strong>Estado:</Text> {(selectedEmbarazo.estado || 'activo').toUpperCase()}</Col></Row><Row gutter={16}><Col xs={24} md={12}><Text strong>Semanas actuales:</Text> {selectedEmbarazo.semanas_gestacion || 'N/A'}</Col><Col xs={24} md={12}><Text strong>Tipo:</Text> {selectedEmbarazo.tipo_embarazo || 'único'}</Col></Row></Space>} type="info" showIcon className="u-mb-4" />
    )}
    <Row gutter={24}>
      <Col xs={24} md={6}><Form.Item name="edad_gestacional_semanas" label="Semanas (por Eco)" rules={[{ required: true, message: 'Requerido' }]} tooltip="Se autocompleta desde el embarazo, pero puede modificarse"><InputNumber min={4} max={43} className="u-ancho" placeholder="Autocompleta desde embarazo" /></Form.Item></Col>
      <Col xs={24} md={6}><Form.Item name="edad_gestacional_dias" label="Días" initialValue={0} tooltip="Se autocompleta desde el embarazo, pero puede modificarse"><InputNumber min={0} max={6} className="u-ancho" placeholder="Días adicionales" /></Form.Item></Col>
      <Col xs={24} md={6}><Form.Item name="numero_fetos" label="Número de Fetos"><InputNumber min={1} max={5} className="u-ancho" /></Form.Item></Col>
      <Col xs={24} md={6}><Form.Item name="vitalidad_fetal" label="Vitalidad Fetal" valuePropName="checked"><Checkbox>Presente</Checkbox></Form.Item></Col>
    </Row>
    <Row gutter={24}>
      <Col xs={24} md={8}><Form.Item name="frecuencia_cardiaca_fetal" label="FCF (latidos/min)" rules={[{ type: 'number', min: 50, max: 300, message: 'FCF entre 50 y 300 lpm (fuera de 110-160 se guarda y alerta)' }]}><InputNumber className="u-ancho" suffix="lpm" /></Form.Item></Col>
    </Row>
  </Card>
);

export default TabDatosGeneralesEco;
