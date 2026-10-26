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
    <Card title={<Space><UserOutlined /> Identificación y Biológico</Space>} >
      <Row gutter={16}>
        <Col xs={24} md={12}>
          <Form.Item label="Paciente" name="paciente" rules={[{ required: true, message: 'Requerido' }]}>
            <Select
              placeholder="Buscar paciente..."
              showSearch
              size="large"
              onChange={onPacienteChange}
              filterOption={(input, option) =>
                String(option?.children ?? '').toLowerCase().includes(input.toLowerCase())
              }
            >
              {pacientes.map((p) => (
                <Option key={p.id} value={p.id}>
                  {`${p.nombre_completo || `${p.nombre} ${p.apellido_paterno}`} - ${p.ci || p.id_clinico}`}
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
                String(option?.children ?? '').toLowerCase().includes(input.toLowerCase())
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
          className="vacunas-form__aviso"
        />
      )}

      <Row gutter={16}>
        <Col xs={24} sm={12}>
          <Form.Item label="Fecha y Hora de Aplicación" name="fecha_aplicacion" rules={[{ required: true, message: 'Requerido' }]}>
            <DatePicker
              showTime
              format={{ format: 'DD/MM/YYYY HH:mm', type: 'mask' }}
              className="vacunas-ancho"
              size="large"
              onChange={onFechaAplicacionChange}
            />
          </Form.Item>
        </Col>
        <Col xs={24} sm={12}>
          <Form.Item label="Número de Dosis" name="numero_dosis" rules={[{ required: true, message: 'Requerido' }]}>
            <InputNumber
              min={1}
              className="vacunas-ancho"
              size="large"
              onChange={onDosisChange}
            />
          </Form.Item>
        </Col>
      </Row>
    </Card>

    <Card title={<Space><MedicineBoxOutlined /> Logística y Aplicación</Space>} className="vacunas-arriba">
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
            <Radio.Group buttonStyle="solid" className="vacunas-form__vias">
              {viasAdministracion.map(v => (
                <Radio.Button key={v.value} value={v.value}>
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

    <Card title={<Space><ClockCircleOutlined /> Seguimiento y Observaciones</Space>} className="vacunas-arriba">
      <Row gutter={16}>
        <Col xs={24} md={12}>
          <Form.Item label="Próxima Dosis (Programación)" name="proxima_dosis_fecha">
            <DatePicker format={{ format: 'DD/MM/YYYY', type: 'mask' }} className="vacunas-ancho" size="large" />
          </Form.Item>
        </Col>
        <Col xs={24} md={12}>
          {proximaDosisCalculada && (
            <div className="vacunas-form__nota">
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
