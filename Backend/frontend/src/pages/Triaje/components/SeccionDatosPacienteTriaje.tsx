import React from 'react';
import { Row, Col, Card, Skeleton, Form, Select, Alert, Tag } from 'antd';
import { UserOutlined, ClockCircleOutlined } from '@ant-design/icons';
import { PacienteSelect } from '../../../components/clinico/SelectoresClinicos';

const { Option } = Select;

interface DatosAnteriores {
  mensaje: string;
  tipo: 'success' | 'info' | 'warning';
}

interface SeccionDatosPacienteTriajeProps {
  dataLoading: boolean;
  loading: boolean;
  disabled: boolean;
  onPacienteChange: (pacienteId: number) => void;
  datosAnteriores: DatosAnteriores | null;
  onCloseDatosAnteriores: () => void;
}

const SeccionDatosPacienteTriaje: React.FC<SeccionDatosPacienteTriajeProps> = ({
  dataLoading, loading, disabled, onPacienteChange, datosAnteriores, onCloseDatosAnteriores,
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
            {/* Busca en el servidor: la lista local traía solo los primeros 200 de
                más de 3.000 pacientes y distinguía acentos («maria» ≠ «María»). */}
            <PacienteSelect
              placeholder="Buscar paciente por nombre o CI..."
              size="large"
              onChange={(id) => id && onPacienteChange(id)}
              disabled={disabled}
            />
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
                <Option value="urgente"><Tag color="error">URGENTE</Tag></Option>
                <Option value="alto"><Tag color="warning">ALTO</Tag></Option>
                <Option value="normal"><Tag color="processing">NORMAL</Tag></Option>
                <Option value="bajo"><Tag color="success">BAJO</Tag></Option>
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
