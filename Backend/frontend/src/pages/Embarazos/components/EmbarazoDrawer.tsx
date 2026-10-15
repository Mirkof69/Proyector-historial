import React from 'react';
import {
  Drawer, Button, Card, Space, Tag, Typography, Divider, Avatar, Descriptions,
  Timeline, Alert, Empty, Row, Col, Statistic,
} from 'antd';
import {
  UserOutlined, MedicineBoxOutlined, HeartOutlined, ExperimentOutlined,
  FileTextOutlined, CalendarOutlined, BookOutlined, WomanOutlined, LinkOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { EmbarazoExtendido, EmbarazosAction, RISK_COLORS, RISK_LABELS } from '../embarazosReducer';

const { Title, Text } = Typography;

const userOutlinedIcon4 = <UserOutlined />;
const medicineBoxOutlinedIcon7 = <MedicineBoxOutlined />;
const experimentOutlinedIcon3 = <ExperimentOutlined />;
const fileTextOutlinedIcon8 = <FileTextOutlined />;
const calendarOutlinedIcon8 = <CalendarOutlined />;
const heartOutlinedIcon7 = <HeartOutlined />;
const bookOutlinedIcon3 = <BookOutlined />;

interface EmbarazoDrawerProps {
  drawerVisible: boolean;
  selectedEmbarazo: EmbarazoExtendido | null;
  dispatch: React.Dispatch<EmbarazosAction>;
  navigate: (path: string) => void;
}

const EmbarazoDrawer: React.FC<EmbarazoDrawerProps> = ({
  drawerVisible, selectedEmbarazo, dispatch, navigate,
}) => (
  <Drawer rootClassName="capa-clinica"
    className="embarazo-resumen-drawer"
    title="Resumen del Embarazo"
    placement="right"
    width={550}
    onClose={() => dispatch({ type: 'SET_DRAWER_VISIBLE', payload: false })}
    open={drawerVisible}
    extra={
      <Button type="primary" onClick={() => navigate(`/dashboard/pacientes/${selectedEmbarazo?.paciente}/historia`)}>
        Ver Historia Completa
      </Button>
    }
  >
    {selectedEmbarazo ? (
      <div className="drawer-content">
        <div className="drawer-header-section">
          <Avatar size={64} icon={userOutlinedIcon4} className="pc-avatar u-mb-2" />
          <Title level={3} className="u-m-0">{selectedEmbarazo?.paciente_nombre}</Title>
          <Text type="secondary">Gesta {selectedEmbarazo?.numero_gesta} • {(selectedEmbarazo?.tipo_embarazo || 'simple').toUpperCase()}</Text>
          <div className="u-mt-3">
            <Tag color={(RISK_COLORS as any)[selectedEmbarazo?.riesgo_embarazo || 'bajo']} className="u-p-etiqueta u-t-base">
              {(RISK_LABELS as any)[selectedEmbarazo?.riesgo_embarazo || 'bajo'] || 'Sin especificar'}
            </Tag>
          </div>
        </div>

        <Descriptions title="Estado Actual" bordered column={1} size="small" className="drawer-descriptions u-mb-5" >
          <Descriptions.Item label="Edad Gestacional">
            <span className="u-t-md u-fuerte u-c-primario">
              {selectedEmbarazo?.edad_gestacional_semanas_num} semanas
            </span>
            <span className="u-ml-2 u-c-texto-3">+ {selectedEmbarazo?.edad_gestacional_dias_num} días</span>
          </Descriptions.Item>
          <Descriptions.Item label="Trimestre Actual">
            {selectedEmbarazo?.trimestre_actual}º Trimestre
          </Descriptions.Item>
          <Descriptions.Item label="Fecha Probable Parto">
            {selectedEmbarazo?.fecha_probable_parto ? dayjs(selectedEmbarazo?.fecha_probable_parto).format('DD [de] MMMM [de] YYYY') : 'No definida'}
          </Descriptions.Item>
        </Descriptions>

        <Descriptions title="Datos Antropométricos Pregestacionales" bordered column={1} size="small" className="drawer-descriptions u-mb-5" >
          <Descriptions.Item label="Peso Pregestacional">
            <span className="u-t-base u-fuerte">
              {selectedEmbarazo?.peso_pregestacional ? `${selectedEmbarazo?.peso_pregestacional} kg` : 'No registrado'}
            </span>
          </Descriptions.Item>
          <Descriptions.Item label="Talla Materna">
            <span className="u-t-base u-fuerte">
              {selectedEmbarazo?.talla_materna ? `${selectedEmbarazo?.talla_materna} cm` : 'No registrado'}
            </span>
          </Descriptions.Item>
          <Descriptions.Item label="IMC Pregestacional">
            <span className="u-t-base u-fuerte">
              {selectedEmbarazo?.imc_pregestacional ?
                <>
                  {selectedEmbarazo?.imc_pregestacional.toFixed(1)}
                  <Tag color={
                    selectedEmbarazo?.imc_pregestacional < 18.5 ? 'warning' :
                      selectedEmbarazo?.imc_pregestacional < 25 ? 'success' :
                        selectedEmbarazo?.imc_pregestacional < 30 ? 'warning' : 'error'
                  } className="u-ml-2">
                    {selectedEmbarazo?.imc_pregestacional < 18.5 ? 'Bajo peso' :
                      selectedEmbarazo?.imc_pregestacional < 25 ? 'Normal' :
                        selectedEmbarazo?.imc_pregestacional < 30 ? 'Sobrepeso' : 'Obesidad'}
                  </Tag>
                </>
                : 'No registrado'
              }
            </span>
          </Descriptions.Item>
        </Descriptions>

        <Divider orientation="left">Línea de Tiempo</Divider>
        <Timeline
          mode="left"
          items={[
            {
              color: 'green',
              label: dayjs(selectedEmbarazo?.fecha_ultima_menstruacion).format('DD/MM/YY'),
              children: 'Inicio del ciclo (FUM)'
            },
            {
              color: 'blue',
              children: `Fecha actual (${selectedEmbarazo?.edad_gestacional_semanas_num} semanas)`
            },
            {
              color: 'gray',
              label: dayjs(selectedEmbarazo?.fecha_probable_parto).format('DD/MM/YY'),
              children: 'Fecha Probable de Parto (40s)'
            }
          ]}
        />

        <Divider orientation="left"><LinkOutlined /> Acceso Rápido a Módulos</Divider>
        <Card size="small" className="u-mb-4">
          <Space direction="vertical" className="u-ancho" size="small">
            <Button
              type="link"
              icon={userOutlinedIcon4}
              block
              className="u-izquierda"
              onClick={() => {
                dispatch({ type: 'SET_DRAWER_VISIBLE', payload: false });
                navigate(`/dashboard/pacientes?id=${selectedEmbarazo?.paciente}`);
              }}
            >
              Ver Paciente: {selectedEmbarazo?.paciente_nombre}
            </Button>
            <Button
              type="link"
              icon={medicineBoxOutlinedIcon7}
              block
              className="u-izquierda"
              onClick={() => {
                dispatch({ type: 'SET_DRAWER_VISIBLE', payload: false });
                navigate(`/dashboard/controles?embarazo=${selectedEmbarazo?.id}`);
              }}
            >
              Ver Controles Prenatales
            </Button>
            <Button
              type="link"
              icon={experimentOutlinedIcon3}
              block
              className="u-izquierda"
              onClick={() => {
                dispatch({ type: 'SET_DRAWER_VISIBLE', payload: false });
                navigate(`/dashboard/ecografias?embarazo=${selectedEmbarazo?.id}`);
              }}
            >
              Ver Ecografías del Embarazo
            </Button>
            <Button
              type="link"
              icon={fileTextOutlinedIcon8}
              block
              className="u-izquierda"
              onClick={() => {
                dispatch({ type: 'SET_DRAWER_VISIBLE', payload: false });
                navigate(`/dashboard/laboratorio?embarazo=${selectedEmbarazo?.id}`);
              }}
            >
              Ver Exámenes de Laboratorio
            </Button>
            <Button
              type="link"
              icon={calendarOutlinedIcon8}
              block
              className="u-izquierda"
              onClick={() => {
                dispatch({ type: 'SET_DRAWER_VISIBLE', payload: false });
                navigate(`/dashboard/citas?embarazo=${selectedEmbarazo?.id}`);
              }}
            >
              Ver Citas del Embarazo
            </Button>
            <Button
              type="link"
              icon={heartOutlinedIcon7}
              block
              className="u-izquierda"
              onClick={() => {
                dispatch({ type: 'SET_DRAWER_VISIBLE', payload: false });
                navigate(`/dashboard/partos?embarazo=${selectedEmbarazo?.id}`);
              }}
            >
              Ver Información de Parto
            </Button>
            <Divider className="u-mv-2" />
            <Button
              type="primary"
              icon={bookOutlinedIcon3}
              block
              onClick={() => {
                dispatch({ type: 'SET_DRAWER_VISIBLE', payload: false });
                navigate(`/dashboard/embarazos/${selectedEmbarazo?.id}`);
              }}
            >
              Ver Historia Completa del Embarazo
            </Button>
          </Space>
        </Card>

        <Divider orientation="left">Notas Clínicas</Divider>
        <Alert
          message={selectedEmbarazo.notas || "No hay notas registradas."}
          type="info"
        />

        <div className="u-mt-6">
          <Row gutter={16}>
            <Col span={12}>
              <Statistic title="Partos Previos" value={selectedEmbarazo.partos_previos} prefix={<WomanOutlined />} />
            </Col>
            <Col span={12}>
              <Statistic title="Cesáreas" value={selectedEmbarazo.cesareas_previas} prefix={<MedicineBoxOutlined />} />
            </Col>
          </Row>
        </div>
      </div>
    ) : <Empty description="Seleccione un embarazo para ver su resumen" />}
  </Drawer>
);

export default EmbarazoDrawer;
