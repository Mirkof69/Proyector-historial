import React from 'react';
import { Card, Form, Button, DatePicker, Row, Col, Space, Upload, Typography, Checkbox, Tooltip, Modal, Input } from 'antd';
import {
  UploadOutlined,
  FileTextOutlined,
  CalendarOutlined,
  EyeOutlined,
} from '@ant-design/icons';
import type { FormInstance, UploadProps } from 'antd';

const { Text } = Typography;
const { TextArea } = Input;

const EYE_ICON_3 = <EyeOutlined />;
const CALENDAR_ICON_6 = <CalendarOutlined />;

interface TabImagenesConclusionesEcoProps {
  uploadProps: UploadProps;
  form: FormInstance;
  handleCrearCita: () => void;
}

const TabImagenesConclusionesEco: React.FC<TabImagenesConclusionesEcoProps> = ({ uploadProps, form, handleCrearCita }) => (
  <div>
    <Card className="shadow-sm" title="Imágenes de la Ecografía" style={{ marginBottom: 24 }}>
      <Upload {...uploadProps}><div><UploadOutlined style={{ fontSize: 24 }} /><div style={{ marginTop: 8 }}>Click o arrastrar para subir</div></div></Upload>
    </Card>
    <Card className="shadow-sm" title={<Space><FileTextOutlined /> Conclusiones del Estudio</Space>} extra={<Tooltip title="Vista previa del diagnóstico"><Button type="text" icon={EYE_ICON_3} onClick={() => { const diagnostico = form.getFieldValue('diagnostico'); const observaciones = form.getFieldValue('observaciones'); Modal.info({ title: 'Vista Previa de Conclusiones', width: 600, content: (<div><div style={{ marginBottom: 16 }}><Text strong>Diagnóstico Ecográfico:</Text><div style={{ marginTop: 8, padding: '12px', backgroundColor: '#f5f5f5', borderRadius: 4 }}><Text>{diagnostico || 'No se ha registrado diagnóstico aún...'}</Text></div></div><div><Text strong>Observaciones y Recomendaciones:</Text><div style={{ marginTop: 8, padding: '12px', backgroundColor: '#f5f5f5', borderRadius: 4 }}><Text>{observaciones || 'No se han registrado observaciones...'}</Text></div></div></div>), }); }}>Vista Previa</Button></Tooltip>}>
      <Form.Item name="diagnostico" label="Diagnóstico Ecográfico" rules={[{ required: true, message: 'Requerido' }]}><TextArea rows={4} placeholder="Ej: Embarazo de 20 semanas con biometría acorde..." /></Form.Item>
      <Form.Item name="observaciones" label="Observaciones y Recomendaciones"><TextArea rows={3} /></Form.Item>
      <Row gutter={24}>
        <Col xs={24} md={8}><Form.Item name="requiere_seguimiento" valuePropName="checked"><Checkbox>Requiere Seguimiento Especial</Checkbox></Form.Item></Col>
        <Col xs={24} md={8}><Form.Item name="proxima_ecografia_recomendada" label="Próxima Ecografía Sugerida" tooltip="Seleccione una fecha y use el botón para agendar automáticamente"><Space.Compact style={{ width: '100%' }}><DatePicker style={{ width: '70%' }} format="DD/MM/YYYY" /><Tooltip title="Agendar cita en el calendario"><Button icon={CALENDAR_ICON_6} onClick={handleCrearCita} style={{ width: '30%' }}>Agendar</Button></Tooltip></Space.Compact></Form.Item></Col>
      </Row>
    </Card>
  </div>
);

export default TabImagenesConclusionesEco;
