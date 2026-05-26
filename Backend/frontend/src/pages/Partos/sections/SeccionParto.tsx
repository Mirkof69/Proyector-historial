import React from 'react';
import { Form, Row, Col, DatePicker, Select, Divider, InputNumber, Checkbox, Input } from 'antd';

const { Option } = Select;

interface SeccionPartoProps {
  form: any;
  calcularAlertasYRecomendaciones: (eg: string) => void;
  tipoEvento: 'aborto' | 'parto' | null;
}

export const SeccionParto: React.FC<SeccionPartoProps> = ({ form, calcularAlertasYRecomendaciones, tipoEvento }) => {
  return (
    <>
      <Divider orientation="left">Información General del Parto</Divider>

      <Row gutter={16}>
        <Col span={12}>
          <Form.Item name="numero_parto" label="Número de Parto">
            <Input placeholder="(Autogenerado)" disabled />
          </Form.Item>
        </Col>

        <Col span={12}>
          <Form.Item name="tipo_parto" label="Tipo de Parto" rules={[{ required: true, message: 'Seleccione tipo de parto' }]}>
            <Select placeholder="Seleccione tipo">
              <Option value="vaginal_espontaneo">Vaginal Espontáneo</Option>
              <Option value="vaginal_instrumentado">Vaginal Instrumentado</Option>
              <Option value="cesarea_electiva">Cesárea Electiva</Option>
              <Option value="cesarea_urgencia">Cesárea de Urgencia</Option>
              <Option value="cesarea_emergencia">Cesárea de Emergencia</Option>
            </Select>
          </Form.Item>
        </Col>
      </Row>

      <Row gutter={16}>
        <Col span={8}>
          <Form.Item name="fecha_ingreso" label="Fecha de Ingreso">
            <DatePicker style={{ width: '100%' }} format="DD/MM/YYYY HH:mm" showTime />
          </Form.Item>
        </Col>

        <Col span={8}>
          <Form.Item name="fecha_inicio_trabajo_parto" label="Inicio Trabajo de Parto">
            <DatePicker style={{ width: '100%' }} format="DD/MM/YYYY HH:mm" showTime />
          </Form.Item>
        </Col>

        <Col span={8}>
          <Form.Item name="fecha_parto" label="Fecha del Parto" rules={[{ required: true, message: 'Ingrese fecha del parto' }]}>
            <DatePicker style={{ width: '100%' }} format="DD/MM/YYYY HH:mm" showTime />
          </Form.Item>
        </Col>
      </Row>

      <Row gutter={16}>
        <Col span={6}>
          <Form.Item
            name="semanas_gestacion"
            label="Semanas"
            rules={[{ required: true, message: 'Ingrese semanas' }, { type: 'number', min: 10, max: 45, message: 'Semanas debe estar entre 10 y 45' }]}
          >
            <InputNumber
              style={{ width: '100%' }}
              onChange={(value) => {
                const dias = form.getFieldValue('dias_gestacion');
                if (value !== null && dias !== undefined) calcularAlertasYRecomendaciones(`${value}+${dias}`);
              }}
            />
          </Form.Item>
        </Col>

        <Col span={6}>
          <Form.Item
            name="dias_gestacion"
            label="Días"
            rules={[{ required: true, message: 'Ingrese días' }, { type: 'number', min: 0, max: 6, message: 'Días debe estar entre 0 y 6' }]}
          >
            <InputNumber
              style={{ width: '100%' }}
              onChange={(value) => {
                const semanas = form.getFieldValue('semanas_gestacion');
                if (semanas !== undefined && value !== null) calcularAlertasYRecomendaciones(`${semanas}+${value}`);
              }}
            />
          </Form.Item>
        </Col>

        <Col span={12}>
          <Form.Item name="presentacion_fetal" label="Presentación Fetal">
            <Select placeholder="Seleccione presentación">
              <Option value="cefalica">Cefálica</Option>
              <Option value="podalica">Podálica</Option>
              <Option value="transversa">Transversa</Option>
              <Option value="oblicua">Oblicua</Option>
            </Select>
          </Form.Item>
        </Col>
      </Row>

      <Divider orientation="left">Evento de Parto</Divider>

      <Row gutter={16}>
        <Col span={8}>
          <Form.Item name="posicion_fetal" label="Posición Fetal">
            <Select placeholder="Seleccione posición">
              <Option value="oia">Occípito Ilíaca Anterior</Option>
              <Option value="oip">Occípito Ilíaca Posterior</Option>
              <Option value="oit">Occípito Ilíaca Transversa</Option>
              <Option value="oda">Occípito Derecha Anterior</Option>
              <Option value="odp">Occípito Derecha Posterior</Option>
              <Option value="odt">Occípito Derecha Transversa</Option>
            </Select>
          </Form.Item>
        </Col>

        <Col span={8}>
          <Form.Item name="estado_membranas" label="Estado de Membranas">
            <Select placeholder="Seleccione estado">
              <Option value="integras">Íntegras</Option>
              <Option value="rotas_espontaneas">Rotura Espontánea</Option>
              <Option value="rotas_artificiales">Rotura Artificial</Option>
            </Select>
          </Form.Item>
        </Col>

        <Col span={8}>
          <Form.Item name="caracteristicas_liquido" label="Características del Líquido">
            <Input placeholder="Claro, meconial, etc." />
          </Form.Item>
        </Col>
      </Row>

      <Row gutter={16}>
        <Col span={12}>
          <Form.Item name="duracion_trabajo_parto_horas" label="Duración Trabajo de Parto (horas)">
            <InputNumber min={0} step={0.5} style={{ width: '100%' }} />
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item name="duracion_periodo_expulsivo_minutos" label="Duración Periodo Expulsivo (minutos)">
            <InputNumber min={0} step={1} style={{ width: '100%' }} />
          </Form.Item>
        </Col>
      </Row>

      {/* Aquí irá SeccionRecienNacido si se pasa como prop o se incluye directamente */}

      <Divider orientation="left">Intervenciones y Complicaciones</Divider>

      <Row gutter={16}>
        <Col span={12}>
          <Form.Item name="analgesia_utilizada" valuePropName="checked">
            <Checkbox>Se utilizó analgesia</Checkbox>
          </Form.Item>
          <Form.Item name="tipo_analgesia" label="Tipo de Analgesia">
            <Input />
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item name="episiotomia" valuePropName="checked">
            <Checkbox>Se realizó episiotomía</Checkbox>
          </Form.Item>
          <Form.Item name="tipo_episiotomia" label="Tipo de Episiotomía">
            <Input />
          </Form.Item>
        </Col>
      </Row>

      <Row gutter={16}>
        <Col span={12}>
          <Form.Item name="grado_desgarro" label="Grado de Desgarro">
            <Select placeholder="Seleccione grado">
              <Option value="no">Sin Desgarros</Option>
              <Option value="primer_grado">Primer Grado</Option>
              <Option value="segundo_grado">Segundo Grado</Option>
              <Option value="tercer_grado">Tercer Grado</Option>
              <Option value="cuarto_grado">Cuarto Grado</Option>
            </Select>
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item name="hemorragia_postparto" valuePropName="checked">
            <Checkbox>Hemorragia postparto</Checkbox>
          </Form.Item>
          <Form.Item name="perdida_sanguinea_estimada" label="Pérdida de Sangre Estimada (mL)">
            <InputNumber min={0} step={100} style={{ width: '100%' }} />
          </Form.Item>
        </Col>
      </Row>

      <Divider orientation="left">Placenta y Tercera Fase</Divider>

      <Row gutter={16}>
        <Col span={12}>
          <Form.Item name="tipo_alumbramiento" label="Tipo de Alumbramiento">
            <Select>
              <Option value="espontaneo">Espontáneo</Option>
              <Option value="dirigido">Dirigido</Option>
              <Option value="manual">Manual</Option>
            </Select>
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item name="placenta_completa" valuePropName="checked" initialValue={true}>
            <Checkbox>Placenta completa</Checkbox>
          </Form.Item>
        </Col>
      </Row>

      <Row gutter={16}>
        <Col span={12}>
          <Form.Item name="peso_placenta" label="Peso de Placenta (gramos)">
            <InputNumber min={0} step={10} style={{ width: '100%' }} />
          </Form.Item>
        </Col>
      </Row>

      <Divider orientation="left">Medicamentos</Divider>

      <Row gutter={16}>
        <Col span={12}>
          <Form.Item name="oxitocina_utilizada" valuePropName="checked">
            <Checkbox>Se utilizó oxitocina</Checkbox>
          </Form.Item>
          <Form.Item name="dosis_oxitocina" label="Dosis de Oxitocina">
            <Input />
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item name="otros_medicamentos" label="Otros Medicamentos">
            <Input.TextArea rows={3} maxLength={500} showCount />
          </Form.Item>
        </Col>
      </Row>

      <Divider orientation="left">Observaciones</Divider>
      <Form.Item name="complicaciones_maternas" label="Complicaciones Maternas">
        <Input.TextArea rows={3} maxLength={500} showCount />
      </Form.Item>
      <Form.Item name="observaciones_parto" label="Observaciones Generales">
        <Input.TextArea rows={3} maxLength={500} showCount />
      </Form.Item>
      <Form.Item name="indicaciones_cesarea" label="Indicaciones de Cesárea">
        <Input.TextArea rows={3} maxLength={500} showCount />
      </Form.Item>

      <Divider orientation="left">Estado Final</Divider>
      <Row gutter={16}>
        <Col span={12}>
          <Form.Item name="parto_finalizado" valuePropName="checked">
            <Checkbox>Parto finalizado</Checkbox>
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item name="trabajo_parto_espontaneo" valuePropName="checked" initialValue={true}>
            <Checkbox>Trabajo de parto espontáneo</Checkbox>
          </Form.Item>
        </Col>
      </Row>
      <Row gutter={16}>
        <Col span={12}>
          <Form.Item name="induccion_parto" valuePropName="checked">
            <Checkbox>Inducción del parto</Checkbox>
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item name="metodo_induccion" label="Método de Inducción">
            <Input />
          </Form.Item>
        </Col>
      </Row>
      <Row gutter={16}>
        <Col span={12}>
          <Form.Item name="monitoreo_fetal_continuo" valuePropName="checked">
            <Checkbox>Monitoreo fetal continuo</Checkbox>
          </Form.Item>
        </Col>
      </Row>
    </>
  );
};
