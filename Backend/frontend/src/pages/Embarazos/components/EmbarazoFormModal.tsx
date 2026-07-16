import React from 'react';
import {
  Modal, Space, Form, Alert, Card, Row, Col, Select, Spin, DatePicker,
  InputNumber, Input, Divider, Button,
} from 'antd';
import { MedicineBoxOutlined, InfoCircleOutlined, CheckCircleOutlined } from '@ant-design/icons';
import type { FormInstance } from 'antd';
import { Dayjs } from 'dayjs';
import locale from 'antd/es/date-picker/locale/es_ES';
import { EmbarazoExtendido, EmbarazosAction, PacienteOption } from '../embarazosReducer';

const { Option } = Select;
const checkCircleOutlinedIcon7 = <CheckCircleOutlined />;

interface EmbarazoFormModalProps {
  modalVisible: boolean;
  editingEmbarazo: EmbarazoExtendido | null;
  edadGestacionalCalculada: string;
  imcCalculado: string;
  pacientesOptions: PacienteOption[];
  loadingPacientes: boolean;
  medicos: any[];
  loadingMedicos: boolean;
  actionLoading: boolean;
  form: FormInstance;
  dispatch: React.Dispatch<EmbarazosAction>;
  handleSubmit: () => void;
  handleFUMChange: (date: Dayjs | null) => void;
  handleAntropometriaChange: () => void;
  handlePacienteChange: (pacienteId: number) => void;
  loadPacientesOptions: (search?: string) => void;
}

const EmbarazoFormModal: React.FC<EmbarazoFormModalProps> = ({
  modalVisible, editingEmbarazo, edadGestacionalCalculada, imcCalculado,
  pacientesOptions, loadingPacientes, medicos, loadingMedicos, actionLoading,
  form, dispatch, handleSubmit, handleFUMChange, handleAntropometriaChange,
  handlePacienteChange, loadPacientesOptions,
}) => (
  <Modal
    title={
      <Space>
        <MedicineBoxOutlined style={{ color: '#1890ff' }} />
        {editingEmbarazo ? 'Actualizar Ficha Clínica' : 'Apertura de Historia Obstétrica'}
      </Space>
    }
    open={modalVisible}
    onCancel={() => dispatch({ type: 'SET_MODAL_VISIBLE', payload: false })}
    width={900}
    footer={null}
    maskClosable={false}
    centered
  >
    <Form form={form} layout="vertical" onFinish={handleSubmit}>

      <Alert
        message="Cálculo Automático Activo"
        description="Al ingresar la Fecha de Última Menstruación (FUM), el sistema calculará automáticamente la FPP y la Edad Gestacional actual."
        type="info"
        showIcon
        style={{ marginBottom: 24 }}
      />

      {/* 1. SELECCIÓN DE PACIENTE */}
      <Card type="inner" title="1. Identificación del Paciente" size="small" style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col span={16}>
            <Form.Item
              name="paciente"
              label="Buscar Paciente (Mujer)"
              rules={[{ required: true, message: 'Debe seleccionar una paciente' }]}
              help="Solo se muestran pacientes femeninos registrados"
            >
              <Select
                showSearch
                placeholder="Escriba nombre o CI..."
                optionFilterProp="children"
                onSearch={(val) => loadPacientesOptions(val)}
                onChange={handlePacienteChange}
                loading={loadingPacientes}
                filterOption={false} // Filtrado en backend
                disabled={!!editingEmbarazo} // No se puede cambiar paciente al editar
                notFoundContent={loadingPacientes ? <Spin size="small" /> : null}
              >
                {pacientesOptions.map(p => (
                  <Option key={p.id} value={p.id}>
                    {p.nombre_completo} (CI: {p.ci}) - {p.edad} años
                  </Option>
                ))}
              </Select>
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item
              name="medico_responsable"
              label="Médico Responsable"
              tooltip="Seleccione el médico responsable del embarazo"
            >
              <Select
                showSearch
                placeholder="Seleccione un médico"
                optionFilterProp="children"
                loading={loadingMedicos}
                allowClear
                filterOption={(input, option) =>
                  (option?.children as unknown as string)
                    ?.toLowerCase()
                    .includes(input.toLowerCase())
                }
              >
                {medicos.map(medico => (
                  <Option key={medico.id} value={medico.id}>
                    Dr./Dra. {medico.nombre} {medico.apellido_paterno || medico.apellido || ''}
                  </Option>
                ))}
              </Select>
            </Form.Item>
          </Col>
        </Row>
      </Card>

      {/* 2. DATOS OBSTÉTRICOS */}
      <Card type="inner" title="2. Datos Obstétricos Actuales" size="small" style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col span={8}>
            <Form.Item name="fecha_ultima_menstruacion" label="Fecha Última Menstruación (FUM)" rules={[{ required: true }]}>
              <DatePicker
                style={{ width: '100%' }}
                format="DD/MM/YYYY"
                onChange={handleFUMChange}
                locale={locale}
                placeholder="Seleccione fecha"
              />
            </Form.Item>
            {edadGestacionalCalculada && (
              <div style={{ marginTop: -10, marginBottom: 10, color: '#1890ff', fontSize: 12 }}>
                <InfoCircleOutlined /> EG: {edadGestacionalCalculada}
              </div>
            )}
          </Col>
          <Col span={8}>
            <Form.Item name="fecha_probable_parto" label="Fecha Probable de Parto (FPP)" tooltip="Calculada automáticamente (Regla Naegele)">
              <DatePicker style={{ width: '100%' }} format="DD/MM/YYYY" locale={locale} />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item name="numero_gesta" label="Nº Gesta Actual" rules={[{ required: true }]}>
              <InputNumber min={1} max={20} style={{ width: '100%' }} />
            </Form.Item>
          </Col>
        </Row>
        <Row gutter={16}>
          <Col span={8}>
            <Form.Item name="tipo_embarazo" label="Tipo de Embarazo" rules={[{ required: true }]}>
              <Select>
                <Option value="simple">Simple (1)</Option>
                <Option value="gemelar">Gemelar (2)</Option>
                <Option value="multiple">Múltiple (3+)</Option>
              </Select>
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item name="riesgo_embarazo" label="Clasificación de Riesgo" rules={[{ required: true }]}>
              <Select>
                <Option value="bajo">🟢 Bajo Riesgo</Option>
                <Option value="medio">🟠 Riesgo Medio</Option>
                <Option value="alto">🔴 Alto Riesgo</Option>
              </Select>
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item name="estado" label="Estado">
              <Select>
                <Option value="activo">Activo</Option>
                <Option value="finalizado">Finalizado</Option>
                <Option value="perdida">Pérdida</Option>
              </Select>
            </Form.Item>
          </Col>
        </Row>
      </Card>

      {/* 3. ANTECEDENTES */}
      <Card type="inner" title="3. Antecedentes Ginecobstétricos" size="small" style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col span={6}>
            <Form.Item name="partos_previos" label="Partos" initialValue={0}>
              <InputNumber min={0} max={20} style={{ width: '100%' }} />
            </Form.Item>
          </Col>
          <Col span={6}>
            <Form.Item name="cesareas_previas" label="Cesáreas" initialValue={0}>
              <InputNumber min={0} max={10} style={{ width: '100%' }} />
            </Form.Item>
          </Col>
          <Col span={6}>
            <Form.Item name="abortos_previos" label="Abortos" initialValue={0}>
              <InputNumber min={0} max={10} style={{ width: '100%' }} />
            </Form.Item>
          </Col>
          <Col span={6}>
            <Form.Item name="hijos_vivos" label="Hijos Vivos" initialValue={0}>
              <InputNumber min={0} max={20} style={{ width: '100%' }} />
            </Form.Item>
          </Col>
        </Row>
      </Card>

      {/* 4. ANTROPOMETRÍA Y NOTAS */}
      <Row gutter={16}>
        <Col span={12}>
          <Form.Item name="notas" label="Observaciones / Antecedentes Patológicos">
            <Input.TextArea rows={4} placeholder="Alergias, enfermedades crónicas, cirugías previas..." />
          </Form.Item>
        </Col>
        <Col span={12}>
          <Card size="small" title="Datos Iniciales">
            <Row gutter={8}>
              <Col span={12}>
                <Form.Item name="peso_pregestacional" label="Peso (kg)">
                  <InputNumber style={{ width: '100%' }} min={20} max={200} onChange={handleAntropometriaChange} />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item name="talla_materna" label="Talla (cm)">
                  <InputNumber style={{ width: '100%' }} min={100} max={220} onChange={handleAntropometriaChange} />
                </Form.Item>
              </Col>
            </Row>
            {imcCalculado && <Alert message={`IMC: ${imcCalculado}`} type="success" showIcon style={{ marginTop: 5 }} />}
          </Card>
        </Col>
      </Row>

      <Divider />

      <div style={{ textAlign: 'right' }}>
        <Space>
          <Button onClick={() => dispatch({ type: 'SET_MODAL_VISIBLE', payload: false })} size="large">Cancelar</Button>
          <Button type="primary" htmlType="submit" loading={actionLoading} icon={checkCircleOutlinedIcon7} size="large">
            {editingEmbarazo ? 'Guardar Cambios' : 'Registrar Embarazo'}
          </Button>
        </Space>
      </div>

    </Form>
  </Modal>
);

export default EmbarazoFormModal;
