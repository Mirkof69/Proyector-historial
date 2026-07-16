import React from 'react';
import { Row, Col, Card, Skeleton, Form, Select, Alert, Tag } from 'antd';
import { UserOutlined, ClockCircleOutlined } from '@ant-design/icons';

const { Option } = Select;

interface DatosAnteriores {
  mensaje: string;
  tipo: 'success' | 'info' | 'warning';
}

interface SeccionDatosPacienteTriajeProps {
  pacientes: any[];
  dataLoading: boolean;
  loading: boolean;
  disabled: boolean;
  onPacienteChange: (pacienteId: number) => void;
  datosAnteriores: DatosAnteriores | null;
  onCloseDatosAnteriores: () => void;
}

const SeccionDatosPacienteTriaje: React.FC<SeccionDatosPacienteTriajeProps> = ({
  pacientes, dataLoading, loading, disabled, onPacienteChange, datosAnteriores, onCloseDatosAnteriores,
}) => (
  <Row gutter={24}>
    <Col xs={24} md={14}>
      <Card type="inner" title={<><UserOutlined /> Datos del Paciente</>} className="h-full">
        {dataLoading ? (
          <Skeleton active />
        ) : (
          <Form.Item
            label="Seleccionar Paciente"
            name="paciente"
            rules={[{ required: true, message: 'Es obligatorio seleccionar un paciente' }]}
          >
            <Select
              placeholder="Buscar paciente por nombre o CI..."
              showSearch
              size="large"
              optionFilterProp="children"
              onChange={onPacienteChange}
              loading={loading}
              disabled={disabled}
            >
              {pacientes.map((p) => (
                <Option key={p.id} value={p.id}>
                  {p.nombre_completo || `${p.nombre} ${p.apellido_paterno}`} - {p.id_clinico || p.ci}
                </Option>
              ))}
            </Select>
          </Form.Item>
        )}
        {datosAnteriores && (
          <Alert
            message={datosAnteriores.mensaje}
            type={datosAnteriores.tipo}
            showIcon
            closable
            onClose={onCloseDatosAnteriores}
            style={{ marginTop: 8 }}
          />
        )}
      </Card>
    </Col>
    <Col xs={24} md={10}>
      <Card type="inner" title={<><ClockCircleOutlined /> Prioridad y Estado</>} className="h-full">
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              label="Prioridad"
              name="prioridad"
              initialValue="normal"
              rules={[{ required: true }]}
            >
              <Select size="large">
                <Option value="urgente"><Tag color="red">URGENTE</Tag></Option>
                <Option value="alto"><Tag color="orange">ALTO</Tag></Option>
                <Option value="normal"><Tag color="blue">NORMAL</Tag></Option>
                <Option value="bajo"><Tag color="green">BAJO</Tag></Option>
              </Select>
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              label="Nivel Conciencia"
              name="nivel_conciencia"
              initialValue="alerta"
            >
              <Select size="large">
                <Option value="alerta">Alerta</Option>
                <Option value="somnoliento">Somnoliento</Option>
                <Option value="estuporoso">Estuporoso</Option>
                <Option value="inconsciente">Inconsciente</Option>
              </Select>
            </Form.Item>
          </Col>
        </Row>
      </Card>
    </Col>
  </Row>
);

export default SeccionDatosPacienteTriaje;
