import React from 'react';
import { Form, Row, Col, Select, Space, Tag, Alert, Divider } from 'antd';
import { ExclamationCircleOutlined, WarningOutlined, HeartOutlined, InfoCircleOutlined } from '@ant-design/icons';
import { Embarazo } from '../../../services/embarazosService';

const { Option } = Select;

interface SeccionEmbarazoEventoProps {
  embarazos: Embarazo[];
  embarazoId?: string;
  tipoEvento: 'aborto' | 'parto' | null;
  setTipoEvento: (tipo: 'aborto' | 'parto' | null) => void;
  setTipoEventoManual: (manual: boolean) => void;
  getNombrePaciente: (id: number) => string;
  handleEmbarazoChange: (id: number) => void;
  form: any;
}

export const SeccionEmbarazoEvento: React.FC<SeccionEmbarazoEventoProps> = ({
  embarazos,
  embarazoId,
  tipoEvento,
  setTipoEvento,
  setTipoEventoManual,
  getNombrePaciente,
  handleEmbarazoChange,
  form,
}) => {
  return (
    <>
      <Divider orientation="left">Selección de Embarazo y Tipo de Evento</Divider>

      <Row gutter={16}>
        <Col span={24}>
          <Form.Item
            name="embarazo"
            label="Embarazo"
            rules={[{ required: true, message: 'Seleccione un embarazo' }]}
            tooltip="Seleccione el embarazo para el cual se está registrando el evento"
          >
            <Select
              placeholder="Buscar y seleccionar embarazo activo"
              showSearch
              size="large"
              disabled={!!embarazoId}
              filterOption={(input, option) => {
                const title = option?.title;
                if (typeof title === 'string') {
                  return title.toLowerCase().includes(input.toLowerCase());
                }
                return false;
              }}
              onChange={handleEmbarazoChange}
            >
              {embarazos.map((e) => {
                const nombrePaciente = getNombrePaciente(e.id!);
                return (
                  <Option key={e.id} value={e.id} title={nombrePaciente}>
                    <Space>
                      <Tag color="blue">G{e.numero_gesta}P{e.numero_para}</Tag>
                      {nombrePaciente}
                    </Space>
                  </Option>
                );
              })}
            </Select>
          </Form.Item>
        </Col>
      </Row>

      <Row gutter={16}>
        <Col span={24}>
          <Form.Item
            label={
              <Space>
                <ExclamationCircleOutlined style={{ color: '#1890ff' }} />
                <strong>Tipo de Evento</strong>
              </Space>
            }
            tooltip="Seleccione el tipo de evento obstétrico. Se auto-selecciona según edad gestacional."
          >
            <Select
              value={tipoEvento}
              onChange={(value) => {
                setTipoEvento(value);
                setTipoEventoManual(true);
                if (value === 'aborto') {
                  form.resetFields([
                    'numero_parto', 'tipo_parto', 'fecha_ingreso', 'fecha_inicio_trabajo_parto',
                    'presentacion_fetal', 'posicion_fetal', 'estado_membranas', 'caracteristicas_liquido',
                    'duracion_trabajo_parto_horas', 'duracion_periodo_expulsivo_minutos',
                    'sexo_bebe', 'peso_bebe', 'talla_bebe', 'apgar_1min', 'apgar_5min',
                    'analgesia_utilizada', 'tipo_analgesia', 'episiotomia', 'tipo_episiotomia',
                    'grado_desgarro', 'tipo_alumbramiento', 'placenta_completa', 'peso_placenta',
                    'oxitocina_utilizada', 'dosis_oxitocina', 'otros_medicamentos',
                    'indicaciones_cesarea', 'trabajo_parto_espontaneo', 'induccion_parto',
                    'metodo_induccion', 'monitoreo_fetal_continuo'
                  ]);
                } else if (value === 'parto') {
                  form.resetFields([
                    'tipo_aborto', 'metodo_evacuacion', 'apoyo_psicologico_realizado',
                    'protocolo_duelo_aplicado', 'observaciones_aborto'
                  ]);
                }
              }}
              size="large"
              placeholder="Seleccione tipo de evento"
              style={{ width: '100%' }}
            >
              <Option value="aborto">
                <Space>
                  <WarningOutlined style={{ color: '#ff4d4f' }} />
                  <strong>ABORTO</strong> - Pérdida gestacional {'<'} 20 semanas
                </Space>
              </Option>
              <Option value="parto">
                <Space>
                  <HeartOutlined style={{ color: '#52c41a' }} />
                  <strong>PARTO</strong> - Nacimiento {'≥'} 20 semanas
                </Space>
              </Option>
            </Select>
          </Form.Item>
        </Col>
      </Row>

      {tipoEvento === 'aborto' && (
        <Alert
          message="PROTOCOLO DE ABORTO SELECCIONADO"
          description="Se mostrará el formulario simplificado para registro de aborto espontáneo o inducido (< 20 semanas)."
          type="warning"
          showIcon
          icon={<ExclamationCircleOutlined />}
          style={{ marginBottom: 16 }}
        />
      )}

      {tipoEvento === 'parto' && (
        <Alert
          message="REGISTRO DE PARTO SELECCIONADO"
          description="Se mostrará el formulario completo para registro de parto o nacimiento (≥ 20 semanas)."
          type="info"
          showIcon
          icon={<InfoCircleOutlined />}
          style={{ marginBottom: 16 }}
        />
      )}
    </>
  );
};
