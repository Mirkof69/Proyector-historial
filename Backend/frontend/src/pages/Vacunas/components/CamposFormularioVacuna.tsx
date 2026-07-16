import React from 'react';
import { Card, Space, Row, Col, Form, Select, Alert, DatePicker, InputNumber, Input, Radio, Typography } from 'antd';
import { UserOutlined, MedicineBoxOutlined, ClockCircleOutlined, CalendarOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { TipoVacuna } from '../../../services/vacunasService';

const { Option } = Select;
const { TextArea } = Input;
const { Text } = Typography;

interface HistorialVacunacion {
  mensaje: string;
  tipo: 'success' | 'info' | 'warning';
  totalVacunas?: number;
}

interface ViaAdministracion {
  value: string;
  label: string;
}

interface CamposFormularioVacunaProps {
  pacientes: any[];
  tiposVacunas: TipoVacuna[];
  historialVacunacion: HistorialVacunacion | null;
  viasAdministracion: ViaAdministracion[];
  proximaDosisCalculada: string;
  onPacienteChange: (pacienteId: number) => void;
  onVacunaChange: (tipoVacunaId: number) => void;
  onFechaAplicacionChange: (fecha: dayjs.Dayjs | null) => void;
  onDosisChange: (dosis: number | null) => void;
}

const CamposFormularioVacuna: React.FC<CamposFormularioVacunaProps> = ({
  pacientes, tiposVacunas, historialVacunacion, viasAdministracion, proximaDosisCalculada,
  onPacienteChange, onVacunaChange, onFechaAplicacionChange, onDosisChange,
}) => (
  <>
    <Card title={<Space><UserOutlined /> Identificación y Biológico</Space>} className="form-section-card">
      <Row gutter={16}>
        <Col xs={24} md={12}>
          <Form.Item label="Paciente" name="paciente" rules={[{ required: true, message: 'Requerido' }]}>
            <Select
              placeholder="Buscar paciente..."
              showSearch
              size="large"
              onChange={onPacienteChange}
              filterOption={(input, option) =>
                (option?.children as any).toLowerCase().includes(input.toLowerCase())
              }
            >
              {pacientes.map((p) => (
                <Option key={p.id} value={p.id}>
                  {p.nombre_completo || `${p.nombre} ${p.apellido_paterno}`} - {p.ci || p.id_clinico}
                </Option>
              ))}
            </Select>
          </Form.Item>
        </Col>
        <Col xs={24} md={12}>
          <Form.Item label="Inmunógeno (Vacuna)" name="tipo_vacuna" rules={[{ required: true, message: 'Requerido' }]}>
            <Select
              placeholder="Seleccionar vacuna..."
              showSearch
              size="large"
              onChange={onVacunaChange}
              filterOption={(input, option) =>
                (option?.children as any).toLowerCase().includes(input.toLowerCase())
              }
            >
              {tiposVacunas.map((v) => (
                <Option key={v.id} value={v.id}>
                  {v.nombre}
                </Option>
              ))}
            </Select>
          </Form.Item>
        </Col>
      </Row>

      {historialVacunacion && (
        <Alert
          message={historialVacunacion.mensaje}
          type={historialVacunacion.tipo}
          showIcon
          style={{ marginBottom: 20, borderRadius: '8px' }}
        />
      )}

      <Row gutter={16}>
        <Col xs={24} sm={12}>
          <Form.Item label="Fecha y Hora de Aplicación" name="fecha_aplicacion" rules={[{ required: true, message: 'Requerido' }]}>
            <DatePicker
              showTime
              format="DD/MM/YYYY HH:mm"
              style={{ width: '100%' }}
              size="large"
              onChange={onFechaAplicacionChange}
            />
          </Form.Item>
        </Col>
        <Col xs={24} sm={12}>
          <Form.Item label="Número de Dosis" name="numero_dosis" rules={[{ required: true, message: 'Requerido' }]}>
            <InputNumber
              min={1}
              style={{ width: '100%' }}
              size="large"
              onChange={onDosisChange}
            />
          </Form.Item>
        </Col>
      </Row>
    </Card>

    <Card title={<Space><MedicineBoxOutlined /> Logística y Aplicación</Space>} className="form-section-card" style={{ marginTop: 24 }}>
      <Row gutter={16}>
        <Col xs={24} md={12}>
          <Form.Item label="Laboratorio / Fabricante" name="laboratorio" rules={[{ required: true, message: 'Requerido' }]}>
            <Input placeholder="Ej: Pfizer, Astra-Zeneca..." size="large" />
          </Form.Item>
        </Col>
        <Col xs={24} md={12}>
          <Form.Item label="Lote" name="lote" rules={[{ required: true, message: 'Requerido' }]}>
            <Input placeholder="Ej: AB1234..." size="large" />
          </Form.Item>
        </Col>
      </Row>

      <Row gutter={16}>
        <Col xs={24} md={12}>
          <Form.Item label="Vía de Administración" name="via_administracion" rules={[{ required: true, message: 'Requerido' }]}>
            <Radio.Group buttonStyle="solid" style={{ width: '100%' }}>
              {viasAdministracion.map(v => (
                <Radio.Button key={v.value} value={v.value} style={{ width: '33.33%', textAlign: 'center' }}>
                  {v.label}
                </Radio.Button>
              ))}
            </Radio.Group>
          </Form.Item>
        </Col>
        <Col xs={24} md={12}>
          <Form.Item label="Sitio de Aplicación" name="sitio_aplicacion" rules={[{ required: true, message: 'Requerido' }]}>
            <Select placeholder="Seleccionar sitio..." size="large">
              <Option value="deltoides_derecho">Deltoides derecho</Option>
              <Option value="deltoides_izquierdo">Deltoides izquierdo</Option>
              <Option value="muslo_derecho">Muslo derecho</Option>
              <Option value="muslo_izquierdo">Muslo izquierdo</Option>
              <Option value="otro">Otro</Option>
            </Select>
          </Form.Item>
        </Col>
      </Row>
    </Card>

    <Card title={<Space><ClockCircleOutlined /> Seguimiento y Observaciones</Space>} className="form-section-card" style={{ marginTop: 24 }}>
      <Row gutter={16}>
        <Col xs={24} md={12}>
          <Form.Item label="Próxima Dosis (Programación)" name="proxima_dosis_fecha">
            <DatePicker format="DD/MM/YYYY" style={{ width: '100%' }} size="large" />
          </Form.Item>
        </Col>
        <Col xs={24} md={12}>
          {proximaDosisCalculada && (
            <div style={{ background: '#f0f9ff', padding: '12px', borderRadius: '8px', border: '1px solid #bae6fd', marginTop: '28px' }}>
              <Text type="secondary"><CalendarOutlined /> Sugerencia por esquema: </Text>
              <Text strong>{dayjs(proximaDosisCalculada).format('DD/MM/YYYY')}</Text>
            </div>
          )}
        </Col>
      </Row>

      <Form.Item label="Reacciones Adversas (ESAVI)" name="reacciones_adversas">
        <TextArea rows={3} placeholder="Describa cualquier reacción..." />
      </Form.Item>

      <Form.Item label="Observaciones Clínicas" name="observaciones">
        <TextArea rows={3} placeholder="Notas adicionales..." />
      </Form.Item>
    </Card>
  </>
);

export default CamposFormularioVacuna;
