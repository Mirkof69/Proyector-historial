import React from 'react';
import { Modal, Space, Card, Form, Select, Checkbox, Row, Col, Button, DatePicker } from 'antd';
import {
  FilePdfOutlined, FileExcelOutlined, IdcardOutlined,
  SafetyCertificateOutlined, FileProtectOutlined,
} from '@ant-design/icons';
import { EmbarazoExtendido } from '../embarazosReducer';

const { Option } = Select;
const { RangePicker } = DatePicker;

const filePdfIcon2 = <FilePdfOutlined />;
const fileExcelIcon = <FileExcelOutlined />;
const idcardOutlinedIcon2 = <IdcardOutlined />;
const safetyCertificateOutlinedIcon3 = <SafetyCertificateOutlined />;
const fileProtectOutlinedIcon2 = <FileProtectOutlined />;

interface ReportesModalProps {
  visible: boolean;
  onClose: () => void;
  embarazos: EmbarazoExtendido[];
}

const ReportesModal: React.FC<ReportesModalProps> = ({ visible, onClose, embarazos }) => (
  <Modal
    title="Generador de Reportes Obstétricos"
    open={visible}
    onCancel={onClose}
    width={800}
    footer={null}
  >
    <Space direction="vertical" style={{ width: '100%' }} size="large">
      <Card title="Reporte Individual de Embarazo" size="small">
        <Form layout="vertical">
          <Form.Item label="Seleccionar Embarazo">
            <Select placeholder="Buscar por paciente..." showSearch>
              {embarazos.map(emb => (
                <Option key={emb.id} value={emb.id}>
                  {emb.paciente_nombre} - Gesta {emb.numero_gesta} ({emb.edad_gestacional_semanas_num}s)
                </Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item label="Incluir en el reporte">
            <Checkbox.Group>
              <Row>
                <Col span={12}><Checkbox value="datos_basicos">Datos Básicos</Checkbox></Col>
                <Col span={12}><Checkbox value="antecedentes">Antecedentes</Checkbox></Col>
                <Col span={12}><Checkbox value="controles">Controles Prenatales</Checkbox></Col>
                <Col span={12}><Checkbox value="ecografias">Ecografías</Checkbox></Col>
                <Col span={12}><Checkbox value="laboratorios">Laboratorios</Checkbox></Col>
                <Col span={12}><Checkbox value="graficas">Gráficas de Evolución</Checkbox></Col>
              </Row>
            </Checkbox.Group>
          </Form.Item>
          <Button type="primary" icon={filePdfIcon2} block>Generar PDF</Button>
        </Form>
      </Card>

      <Card title="Reporte Estadístico General" size="small">
        <Form layout="vertical">
          <Form.Item label="Período">
            <RangePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item label="Tipo de Análisis">
            <Select defaultValue="resumen">
              <Option value="resumen">Resumen Ejecutivo</Option>
              <Option value="detallado">Análisis Detallado</Option>
              <Option value="comparativo">Comparativo Mensual</Option>
              <Option value="indicadores">Indicadores MSP</Option>
            </Select>
          </Form.Item>
          <Button type="primary" icon={fileExcelIcon} block>Exportar a Excel</Button>
        </Form>
      </Card>

      <Card title="Certificados y Carnés" size="small">
        <Space direction="vertical" style={{ width: '100%' }}>
          <Button icon={idcardOutlinedIcon2} block>Carné Perinatal (OMS)</Button>
          <Button icon={safetyCertificateOutlinedIcon3} block>Certificado de Monitoreo Prenatal</Button>
          <Button icon={fileProtectOutlinedIcon2} block>Constancia de Controles</Button>
        </Space>
      </Card>
    </Space>
  </Modal>
);

export default ReportesModal;
