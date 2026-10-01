import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Modal, Space, Card, Form, Select, Checkbox, Row, Col, Button, DatePicker } from 'antd';
import {
  FilePdfOutlined, FileExcelOutlined, IdcardOutlined,
  SafetyCertificateOutlined, FileProtectOutlined,
} from '@ant-design/icons';
// Cliente axios: la respuesta trae los datos en `.data`.
import apiClient from '../../../services/api';
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
}

/**
 * Busca el embarazo EN EL SERVIDOR mientras se escribe. Antes el selector
 * listaba todos los embarazos que la pantalla había descargado en bucle;
 * ahora la pantalla solo tiene una página, así que se consulta `?search=`
 * (que entiende los nombres cifrados de la paciente).
 */
const useBuscarEmbarazos = (visible: boolean) => {
  const [opciones, setOpciones] = useState<EmbarazoExtendido[]>([]);
  const [cargando, setCargando] = useState(false);
  const ultima = useRef(0);

  const buscar = useCallback(async (termino: string) => {
    const id = ++ultima.current;
    setCargando(true);
    try {
      const r = await apiClient.get('/embarazos/', {
        params: { search: termino.trim() || undefined, page_size: 20 },
      });
      if (id === ultima.current) setOpciones(r.data?.results ?? []);
    } catch {
      if (id === ultima.current) setOpciones([]);
    } finally {
      if (id === ultima.current) setCargando(false);
    }
  }, []);

  // Al abrir el modal trae los primeros; luego busca a medida que se escribe.
  useEffect(() => {
    if (visible) buscar('');
  }, [visible, buscar]);

  return { opciones, cargando, buscar };
};

const ReportesModal: React.FC<ReportesModalProps> = ({ visible, onClose }) => {
  const { opciones, cargando, buscar } = useBuscarEmbarazos(visible);
  return (
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
            <Select
              placeholder="Buscar por paciente..."
              showSearch
              filterOption={false}
              onSearch={buscar}
              loading={cargando}
              notFoundContent={cargando ? 'Buscando…' : 'Sin resultados'}
            >
              {opciones.map(emb => (
                <Option key={emb.id} value={emb.id}>
                  {emb.paciente_nombre} - Gesta {emb.numero_gesta}
                  {emb.semanas_gestacion ? ` (${emb.semanas_gestacion} sem)` : ''}
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
};

export default ReportesModal;
