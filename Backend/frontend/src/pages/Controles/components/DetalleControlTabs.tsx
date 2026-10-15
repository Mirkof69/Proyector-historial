import React from 'react';
import {
  Card, Descriptions, Tag, Space, Divider, Row, Col, Statistic, Typography, Empty, Table, Tabs,
} from 'antd';
import {
  HeartOutlined, UserOutlined, EnvironmentOutlined, PhoneOutlined, MailOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { ControlPrenatal } from '../../../services/controlesService';
import { Embarazo } from '../../../services/embarazosService';
import { Paciente } from '../../../services/pacientesService';
import { ComparacionControl, tabInfoGeneral, tabExamenObstetrico, tabEvolucion } from '../detalleControlUtils';
import { columnasComparacion } from '../detalleControlColumns';

const { Text, Paragraph } = Typography;

interface DetalleControlTabsProps {
  activeTab: string;
  setActiveTab: (key: string) => void;
  paciente: Paciente;
  embarazo: Embarazo;
  control: ControlPrenatal;
  imcMaterno: number | null;
  clasificacionIMC: { texto: string; color: string };
  isFCFAnormal: boolean | 0 | null | undefined;
  hayControlAnterior: boolean;
  comparacionConAnterior: ComparacionControl[];
}

const DetalleControlTabs: React.FC<DetalleControlTabsProps> = ({
  activeTab, setActiveTab, paciente, embarazo, control, imcMaterno, clasificacionIMC,
  isFCFAnormal, hayControlAnterior, comparacionConAnterior,
}) => (
  <Card>
    <Tabs activeKey={activeTab} onChange={setActiveTab} items={[
      {
        key: '1',
        label: tabInfoGeneral,
        children: <div>
          <Row gutter={[16, 16]}>
            <Col xs={24} md={12}>
              <Card title={<Space><UserOutlined /> Información de la Paciente</Space>} size="small" className="u-alto">
                <Descriptions column={1} bordered size="small">
                  <Descriptions.Item label="Nombre Completo"><Text strong>{paciente.nombre} {paciente.apellido_paterno} {paciente.apellido_materno}</Text></Descriptions.Item>
                  <Descriptions.Item label="ID Clínico"><Tag color="processing">{paciente.id_clinico}</Tag></Descriptions.Item>
                  <Descriptions.Item label="Edad">{paciente.edad} años</Descriptions.Item>
                  <Descriptions.Item label="Grupo Sanguíneo">{paciente.tipo_sangre} {paciente.factor_rh}</Descriptions.Item>
                  {paciente.direccion && <Descriptions.Item label={<><EnvironmentOutlined /> Dirección</>}>{paciente.direccion}</Descriptions.Item>}
                  {paciente.telefono && <Descriptions.Item label={<><PhoneOutlined /> Teléfono</>}>{paciente.telefono}</Descriptions.Item>}
                  {paciente.email && <Descriptions.Item label={<><MailOutlined /> Email</>}>{paciente.email}</Descriptions.Item>}
                </Descriptions>
              </Card>
            </Col>
            <Col xs={24} md={12}>
              <Card title={<Space><HeartOutlined /> Datos del Embarazo</Space>} size="small" className="u-alto">
                <Descriptions column={1} bordered size="small">
                  <Descriptions.Item label="Gesta Actual"><Tag>G{embarazo.numero_gesta}</Tag></Descriptions.Item>
                  <Descriptions.Item label="FUM">{dayjs(embarazo.fecha_ultima_menstruacion).format('DD/MM/YYYY')}</Descriptions.Item>
                  <Descriptions.Item label="FPP">{dayjs(embarazo.fecha_probable_parto).format('DD/MM/YYYY')}</Descriptions.Item>
                  <Descriptions.Item label="Riesgo"><Tag color={embarazo.riesgo_embarazo === 'alto' ? 'error' : embarazo.riesgo_embarazo === 'medio' ? 'warning' : 'success'}>{embarazo.riesgo_embarazo?.toUpperCase()}</Tag></Descriptions.Item>
                </Descriptions>
              </Card>
            </Col>
          </Row>
          <Divider orientation="left">Signos Vitales y Antropometría</Divider>
          <Row gutter={[16, 16]}>
            <Col xs={24} md={8}>
              <Card size="small">
                <Statistic title="Peso Actual" value={control.peso_actual ?? 0} suffix="kg" />
                <div className="u-mt-2"><Text type="secondary">IMC: </Text><Tag color={clasificacionIMC.color}>{imcMaterno?.toFixed(2)} ({clasificacionIMC.texto})</Tag></div>
              </Card>
            </Col>
            <Col xs={24} md={8}><Card size="small"><Statistic title="Talla" value={control.talla ?? 0} suffix="cm" /></Card></Col>
            <Col xs={24} md={8}><Card size="small"><Statistic title="Temperatura" value={control.temperatura ?? 0} suffix="°C" valueStyle={{ color: (control.temperatura || 0) >= 38 ? 'var(--color-peligro)' : 'var(--color-exito)' }} /></Card></Col>
          </Row>
        </div>,
      },
      {
        key: '2',
        label: tabExamenObstetrico,
        children: <div>
          <Descriptions bordered column={{ xxl: 2, xl: 2, lg: 2, md: 1, sm: 1, xs: 1 }}>
            <Descriptions.Item label="Altura Uterina"><Text strong>{control.altura_uterina} cm</Text></Descriptions.Item>
            <Descriptions.Item label="Frecuencia Cardíaca Fetal"><Text strong type={isFCFAnormal ? 'danger' : undefined}>{control.frecuencia_cardiaca_fetal} lpm</Text></Descriptions.Item>
            <Descriptions.Item label="Presentación Fetal"><Tag color="processing">{control.presentacion_fetal?.toUpperCase()}</Tag></Descriptions.Item>
            <Descriptions.Item label="Movimientos Fetales"><Tag color={control.movimientos_fetales === 'ausentes' ? 'error' : control.movimientos_fetales === 'disminuidos' ? 'warning' : 'success'}>{control.movimientos_fetales?.toUpperCase()}</Tag></Descriptions.Item>
            <Descriptions.Item label="Edema"><Tag color={control.edema === 'severo' || control.edema === 'generalizado' ? 'error' : control.edema === 'no' ? 'success' : 'warning'}>{control.edema?.toUpperCase()}</Tag></Descriptions.Item>
            <Descriptions.Item label="Proteinuria"><Tag color={control.proteinuria === 'negativa' ? 'success' : control.proteinuria === 'trazas' ? 'warning' : 'error'}>{control.proteinuria?.toUpperCase()}</Tag></Descriptions.Item>
          </Descriptions>
          <Divider orientation="left">Observaciones Clínicas</Divider>
          <Paragraph className="pc-texto-libre">{control.observaciones || <Text type="secondary">Sin observaciones registradas.</Text>}</Paragraph>
        </div>,
      },
      {
        key: '3',
        label: tabEvolucion,
        children: <div>
          {hayControlAnterior ? (
            <Table dataSource={comparacionConAnterior} columns={columnasComparacion} pagination={false} rowKey="campo" />
          ) : (
            <Empty description="No hay controles anteriores para comparar" />
          )}
        </div>,
      },
    ]} />
  </Card>
);

export default DetalleControlTabs;
