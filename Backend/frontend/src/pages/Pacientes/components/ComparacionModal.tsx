import React from 'react';
import { Modal, Alert, Row, Col, Card, Select, Divider, Descriptions, Empty, Table, Button } from 'antd';
import { FilePdfOutlined } from '@ant-design/icons';
import { Paciente, getEstadoCivilConGenero } from '../pacientesTypes';

const { Option } = Select;
const FILE_PDF_ICON_4 = <FilePdfOutlined />;

interface ComparacionState {
  a: Paciente | null;
  b: Paciente | null;
  c: Paciente | null;
}

interface ComparacionModalProps {
  visible: boolean;
  onClose: () => void;
  pacientes: Paciente[];
  pacientesComparacion: ComparacionState;
  setPacientesComparacion: React.Dispatch<React.SetStateAction<ComparacionState>>;
}

const ComparacionModal: React.FC<ComparacionModalProps> = ({
  visible, onClose, pacientes, pacientesComparacion, setPacientesComparacion,
}) => (
  <Modal
    title="Comparación de Pacientes"
    open={visible}
    onCancel={onClose}
    width={1000}
    footer={null}
  >
    <Alert
      message="Herramienta de Comparación Clínica"
      description="Seleccione hasta 3 pacientes para comparar perfiles médicos, evolución y resultados"
      type="info"
      showIcon
      style={{ marginBottom: 16 }}
    />

    <Row gutter={16}>
      <Col span={8}>
        <Card title="Paciente A" size="small">
          <Select
            placeholder="Seleccionar paciente..."
            style={{ width: '100%' }}
            showSearch
            optionFilterProp="children"
            value={pacientesComparacion.a?.id}
            onChange={(id) => {
              const pac = pacientes.find(p => p.id === id);
              setPacientesComparacion(prev => ({ ...prev, a: pac || null }));
            }}
          >
            {pacientes.map(p => (
              <Option key={p.id} value={p.id}>{p.nombre_completo}</Option>
            ))}
          </Select>
          <Divider />
          {pacientesComparacion.a ? (
            <Descriptions size="small" column={1} bordered>
              <Descriptions.Item label="Edad">{pacientesComparacion.a.edad} años</Descriptions.Item>
              <Descriptions.Item label="Grupo">{pacientesComparacion.a.tipo_sangre || 'N/A'}</Descriptions.Item>
              <Descriptions.Item label="CI">{pacientesComparacion.a.ci}</Descriptions.Item>
            </Descriptions>
          ) : (
            <Empty description="Seleccione un paciente" />
          )}
        </Card>
      </Col>
      <Col span={8}>
        <Card title="Paciente B" size="small">
          <Select
            placeholder="Seleccionar paciente..."
            style={{ width: '100%' }}
            showSearch
            optionFilterProp="children"
            value={pacientesComparacion.b?.id}
            onChange={(id) => {
              const pac = pacientes.find(p => p.id === id);
              setPacientesComparacion(prev => ({ ...prev, b: pac || null }));
            }}
          >
            {pacientes.map(p => (
              <Option key={p.id} value={p.id}>{p.nombre_completo}</Option>
            ))}
          </Select>
          <Divider />
          {pacientesComparacion.b ? (
            <Descriptions size="small" column={1} bordered>
              <Descriptions.Item label="Edad">{pacientesComparacion.b.edad} años</Descriptions.Item>
              <Descriptions.Item label="Grupo">{pacientesComparacion.b.tipo_sangre || 'N/A'}</Descriptions.Item>
              <Descriptions.Item label="CI">{pacientesComparacion.b.ci}</Descriptions.Item>
            </Descriptions>
          ) : (
            <Empty description="Seleccione un paciente" />
          )}
        </Card>
      </Col>
      <Col span={8}>
        <Card title="Paciente C" size="small">
          <Select
            placeholder="Seleccionar paciente..."
            style={{ width: '100%' }}
            showSearch
            optionFilterProp="children"
            value={pacientesComparacion.c?.id}
            onChange={(id) => {
              const pac = pacientes.find(p => p.id === id);
              setPacientesComparacion(prev => ({ ...prev, c: pac || null }));
            }}
          >
            {pacientes.map(p => (
              <Option key={p.id} value={p.id}>{p.nombre_completo}</Option>
            ))}
          </Select>
          <Divider />
          {pacientesComparacion.c ? (
            <Descriptions size="small" column={1} bordered>
              <Descriptions.Item label="Edad">{pacientesComparacion.c.edad} años</Descriptions.Item>
              <Descriptions.Item label="Grupo">{pacientesComparacion.c.tipo_sangre || 'N/A'}</Descriptions.Item>
              <Descriptions.Item label="CI">{pacientesComparacion.c.ci}</Descriptions.Item>
            </Descriptions>
          ) : (
            <Empty description="Seleccione un paciente" />
          )}
        </Card>
      </Col>
    </Row>

    <Divider />

    <Table
      size="small"
      columns={[
        { title: 'Característica', dataIndex: 'item', key: 'item', fixed: 'left', width: 150 },
        { title: 'Paciente A', dataIndex: 'pacA', key: 'pacA' },
        { title: 'Paciente B', dataIndex: 'pacB', key: 'pacB' },
        { title: 'Paciente C', dataIndex: 'pacC', key: 'pacC' }
      ]}
      dataSource={[
        {
          key: '1',
          item: 'Edad',
          pacA: pacientesComparacion.a ? `${pacientesComparacion.a.edad} años` : '-',
          pacB: pacientesComparacion.b ? `${pacientesComparacion.b.edad} años` : '-',
          pacC: pacientesComparacion.c ? `${pacientesComparacion.c.edad} años` : '-'
        },
        {
          key: '2',
          item: 'Grupo Sanguíneo',
          pacA: pacientesComparacion.a?.tipo_sangre || '-',
          pacB: pacientesComparacion.b?.tipo_sangre || '-',
          pacC: pacientesComparacion.c?.tipo_sangre || '-'
        },
        {
          key: '3',
          item: 'CI',
          pacA: pacientesComparacion.a?.ci || '-',
          pacB: pacientesComparacion.b?.ci || '-',
          pacC: pacientesComparacion.c?.ci || '-'
        },
        {
          key: '4',
          item: 'Ciudad',
          pacA: pacientesComparacion.a?.ciudad || '-',
          pacB: pacientesComparacion.b?.ciudad || '-',
          pacC: pacientesComparacion.c?.ciudad || '-'
        },
        {
          key: '5',
          item: 'Teléfono',
          pacA: pacientesComparacion.a?.telefono || '-',
          pacB: pacientesComparacion.b?.telefono || '-',
          pacC: pacientesComparacion.c?.telefono || '-'
        },
        {
          key: '6',
          item: 'Estado Civil',
          pacA: pacientesComparacion.a ? getEstadoCivilConGenero(pacientesComparacion.a.estado_civil, pacientesComparacion.a.genero) : '-',
          pacB: pacientesComparacion.b ? getEstadoCivilConGenero(pacientesComparacion.b.estado_civil, pacientesComparacion.b.genero) : '-',
          pacC: pacientesComparacion.c ? getEstadoCivilConGenero(pacientesComparacion.c.estado_civil, pacientesComparacion.c.genero) : '-'
        },
        {
          key: '7',
          item: 'Peso',
          pacA: pacientesComparacion.a?.peso_kg ? `${pacientesComparacion.a.peso_kg} kg` : '-',
          pacB: pacientesComparacion.b?.peso_kg ? `${pacientesComparacion.b.peso_kg} kg` : '-',
          pacC: pacientesComparacion.c?.peso_kg ? `${pacientesComparacion.c.peso_kg} kg` : '-'
        },
        {
          key: '8',
          item: 'Altura',
          pacA: pacientesComparacion.a?.altura_cm ? `${pacientesComparacion.a.altura_cm} cm` : '-',
          pacB: pacientesComparacion.b?.altura_cm ? `${pacientesComparacion.b.altura_cm} cm` : '-',
          pacC: pacientesComparacion.c?.altura_cm ? `${pacientesComparacion.c.altura_cm} cm` : '-'
        },
        {
          key: '9',
          item: 'IMC',
          pacA: pacientesComparacion.a?.imc ? `${pacientesComparacion.a.imc.toFixed(1)}` : '-',
          pacB: pacientesComparacion.b?.imc ? `${pacientesComparacion.b.imc.toFixed(1)}` : '-',
          pacC: pacientesComparacion.c?.imc ? `${pacientesComparacion.c.imc.toFixed(1)}` : '-'
        }
      ]}
      pagination={false}
    />

    <Divider />

    <Button type="primary" icon={FILE_PDF_ICON_4} block>
      Generar Reporte Comparativo PDF
    </Button>
  </Modal>
);

export default ComparacionModal;
