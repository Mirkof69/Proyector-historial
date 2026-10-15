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
    <Card className="shadow-sm u-mb-5" title="Imágenes de la Ecografía" >
      <Upload {...uploadProps}><div><UploadOutlined className="u-t-xl" /><div className="u-mt-2">Click o arrastrar para subir</div></div></Upload>
    </Card>
    <Card className="shadow-sm" title={<Space><FileTextOutlined /> Conclusiones del Estudio</Space>} extra={<Tooltip title="Vista previa del diagnóstico"><Button type="text" icon={EYE_ICON_3} onClick={() => { const diagnostico = form.getFieldValue('diagnostico'); const observaciones = form.getFieldValue('observaciones'); Modal.info({ title: 'Vista Previa de Conclusiones', width: 600, className: 'capa-clinica', content: (<div><div className="u-mb-4"><Text strong>Diagnóstico Ecográfico:</Text><div className="pc-texto-libre u-mt-2"><Text>{diagnostico || 'No se ha registrado diagnóstico aún...'}</Text></div></div><div><Text strong>Observaciones y Recomendaciones:</Text><div className="pc-texto-libre u-mt-2"><Text>{observaciones || 'No se han registrado observaciones...'}</Text></div></div></div>), }); }}>Vista Previa</Button></Tooltip>}>
      <Form.Item name="diagnostico" label="Diagnóstico Ecográfico" rules={[{ required: true, message: 'Requerido' }]}><TextArea rows={4} placeholder="Ej: Embarazo de 20 semanas con biometría acorde..." /></Form.Item>
      <Form.Item name="observaciones" label="Observaciones y Recomendaciones"><TextArea rows={3} /></Form.Item>
      <Row gutter={24}>
        <Col xs={24} md={8}><Form.Item name="requiere_seguimiento" valuePropName="checked"><Checkbox>Requiere Seguimiento Especial</Checkbox></Form.Item></Col>
        <Col xs={24} md={8}><Form.Item name="proxima_ecografia_recomendada" label="Próxima Ecografía Sugerida" tooltip="Seleccione una fecha y use el botón para agendar automáticamente"><Space.Compact className="u-ancho"><DatePicker className="eco-agendar__fecha" format="DD/MM/YYYY" /><Tooltip title="Agendar cita en el calendario"><Button icon={CALENDAR_ICON_6} onClick={handleCrearCita} className="eco-agendar__boton">Agendar</Button></Tooltip></Space.Compact></Form.Item></Col>
      </Row>
    </Card>
  </div>
);

export default TabImagenesConclusionesEco;
