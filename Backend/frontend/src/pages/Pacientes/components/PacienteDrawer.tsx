import React from 'react';
import {
  Drawer, Space, Button, Card, Tag, Typography, Divider, Avatar, Descriptions,
  Timeline, Alert, Empty, Spin, Menu, Input, DatePicker,
} from 'antd';
import {
  SearchOutlined, FolderOpenOutlined, MedicineBoxOutlined, HeartOutlined,
  WomanOutlined, ManOutlined, CloseCircleOutlined, CalendarOutlined,
  FileTextOutlined, BookOutlined, RiseOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { Paciente, getEstadoCivilConGenero } from '../pacientesTypes';

const { Title, Text } = Typography;
const { TextArea } = Input;
const { RangePicker } = DatePicker;

const FOLDER_OPEN_ICON = <FolderOpenOutlined />;
const SEARCH_ICON_2 = <SearchOutlined />;
const MEDICINE_BOX_ICON_4 = <MedicineBoxOutlined />;
const CALENDAR_ICON_5 = <CalendarOutlined />;
const CLOSE_CIRCLE_ICON_2 = <CloseCircleOutlined />;
const WOMAN_ICON = <WomanOutlined />;
const MAN_ICON_2 = <ManOutlined />;
const HEART_ICON_5 = <HeartOutlined />;
const FILE_TEXT_ICON_6 = <FileTextOutlined />;
const BOOK_ICON = <BookOutlined />;
const RISE_ICON = <RiseOutlined />;

interface PacienteDrawerProps {
  drawerVisible: boolean;
  selectedPaciente: Paciente | null;
  onClose: () => void;
  navigate: (path: string) => void;
  token: any;
}

const PacienteDrawer: React.FC<PacienteDrawerProps> = ({
  drawerVisible, selectedPaciente, onClose, navigate, token,
}) => (
  <Drawer
    className="paciente-expediente-drawer"
    title="Expediente Rápido"
    placement="right"
    width={600}
    onClose={onClose}
    open={drawerVisible}
    extra={
      <Space>
        <Menu mode="horizontal" selectedKeys={[]} style={{ border: 'none' }}>
          <Menu.Item key="book" icon={BOOK_ICON}>Documentos</Menu.Item>
          <Menu.Item key="rise" icon={RISE_ICON}>Métricas</Menu.Item>
        </Menu>
        <Button type="primary" onClick={() => { onClose(); navigate(`/dashboard/pacientes/${selectedPaciente?.id}/historia`); }}>
          Ver Historia Completa
        </Button>
      </Space>
    }
  >
    {selectedPaciente ? (
      <Spin spinning={false} tip="Cargando expediente…">
        <div className="drawer-content">
          {/* CABECERA DRAWER */}
          <div className="drawer-header-section">
            <Avatar
              size={80}
              icon={selectedPaciente.genero === 'femenino' ? <WomanOutlined /> : <ManOutlined />}
              style={{ backgroundColor: selectedPaciente.genero === 'femenino' ? '#ffadd2' : token.colorPrimary, marginBottom: 10 }}
            />
            <Title level={3} style={{ margin: 0 }}>{selectedPaciente.nombre_completo}</Title>
            <Text type="secondary">{selectedPaciente.id_clinico}</Text>
            <div style={{ marginTop: 10 }}>
              {selectedPaciente.activo ? (
                <Tag color="green">ACTIVO</Tag>
              ) : (
                <Tag color="red" icon={CLOSE_CIRCLE_ICON_2}>INACTIVO</Tag>
              )}
              {selectedPaciente.embarazos_activos && <Tag color="purple">GESTANTE</Tag>}
              {selectedPaciente.genero === 'femenino' && (
                <Tag icon={WOMAN_ICON} color="pink">Femenino</Tag>
              )}
              {selectedPaciente.genero === 'masculino' && (
                <Tag icon={MAN_ICON_2} color="blue">Masculino</Tag>
              )}
            </div>
          </div>

          <Descriptions title="Datos Generales" bordered column={1} size="small" className="drawer-descriptions">
            <Descriptions.Item label="CI">{selectedPaciente.ci}</Descriptions.Item>
            <Descriptions.Item label="Edad">{selectedPaciente.edad} años ({dayjs(selectedPaciente.fecha_nacimiento).format('DD/MM/YYYY')})</Descriptions.Item>
            <Descriptions.Item label="Teléfono">{selectedPaciente.telefono || 'N/A'}</Descriptions.Item>
            <Descriptions.Item label="Dirección">
              {selectedPaciente.direccion && selectedPaciente.ciudad
                ? `${selectedPaciente.direccion}, ${selectedPaciente.ciudad}`
                : selectedPaciente.direccion || selectedPaciente.ciudad || 'N/A'
              }
            </Descriptions.Item>
            <Descriptions.Item label="Email">{selectedPaciente.email || 'N/A'}</Descriptions.Item>
            <Descriptions.Item label="Tipo de Sangre">
              {selectedPaciente.tipo_sangre ? (
                <Tag color="red" style={{ fontSize: 14, fontWeight: 'bold' }}>{selectedPaciente.tipo_sangre}</Tag>
              ) : 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="Estado Civil">
              <Tag color="blue">
                {getEstadoCivilConGenero(selectedPaciente.estado_civil, selectedPaciente.genero)}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="Ocupación">
              {selectedPaciente.ocupacion || 'N/A'}
            </Descriptions.Item>
          </Descriptions>

          <Descriptions title="Datos Médicos" bordered column={1} size="small" className="drawer-descriptions" style={{ marginTop: 16 }}>
            <Descriptions.Item label="Peso">
              {selectedPaciente.peso_kg ? `${selectedPaciente.peso_kg} kg` : 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="Altura">
              {selectedPaciente.altura_cm ? `${selectedPaciente.altura_cm} cm` : 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="IMC">
              {selectedPaciente.imc ? (
                <Tag
                  color={
                    selectedPaciente.imc < 18.5 ? 'orange' :
                      selectedPaciente.imc < 25 ? 'green' :
                        selectedPaciente.imc < 30 ? 'gold' : 'red'
                  }
                  style={{ fontSize: 14, fontWeight: 'bold' }}
                >
                  {selectedPaciente.imc}
                  {' - '}
                  {selectedPaciente.imc < 18.5 ? 'Bajo Peso' :
                    selectedPaciente.imc < 25 ? 'Normal' :
                      selectedPaciente.imc < 30 ? 'Sobrepeso' : 'Obesidad'}
                </Tag>
              ) : 'N/A'}
            </Descriptions.Item>
          </Descriptions>

          <Divider orientation="left">🔗 Acceso Rápido a Módulos</Divider>
          <Card size="small" style={{ marginBottom: 16 }}>
            <Space direction="vertical" style={{ width: '100%' }} size="small">
              <Button
                type="link"
                icon={HEART_ICON_5}
                block
                style={{ textAlign: 'left' }}
                onClick={() => {
                  onClose();
                  navigate(`/dashboard/embarazos?paciente=${selectedPaciente.id}`);
                }}
              >
                Ver Embarazos de {selectedPaciente.nombre}
              </Button>
              <Button
                type="link"
                icon={MEDICINE_BOX_ICON_4}
                block
                style={{ textAlign: 'left' }}
                onClick={() => {
                  onClose();
                  navigate(`/dashboard/controles?paciente=${selectedPaciente.id}`);
                }}
              >
                Ver Controles Prenatales
              </Button>
              <Button
                type="link"
                icon={CALENDAR_ICON_5}
                block
                style={{ textAlign: 'left' }}
                onClick={() => {
                  onClose();
                  navigate(`/dashboard/citas?paciente=${selectedPaciente.id}`);
                }}
              >
                Ver Citas Programadas
              </Button>
              <Button
                type="link"
                icon={FILE_TEXT_ICON_6}
                block
                style={{ textAlign: 'left' }}
                onClick={() => {
                  onClose();
                  navigate(`/dashboard/laboratorio?paciente=${selectedPaciente.id}`);
                }}
              >
                Ver Exámenes de Laboratorio
              </Button>
              <Button
                type="link"
                icon={SEARCH_ICON_2}
                block
                style={{ textAlign: 'left' }}
                onClick={() => {
                  onClose();
                  navigate(`/dashboard/ecografias?paciente=${selectedPaciente.id}`);
                }}
              >
                Ver Ecografías
              </Button>
              <Divider style={{ margin: '8px 0' }} />
              <Button
                type="primary"
                icon={FOLDER_OPEN_ICON}
                block
                onClick={() => {
                  onClose();
                  navigate(`/dashboard/pacientes/${selectedPaciente.id}/historia`);
                }}
              >
                Ver Historia Clínica Completa
              </Button>
            </Space>
          </Card>

          <Divider orientation="left">Actividad Reciente</Divider>
          <Timeline
            mode="left"
            items={[
              {
                color: "green",
                children: `Registro en el sistema (${dayjs(selectedPaciente.fecha_registro).format('DD/MM/YYYY')})`
              },
              ...(selectedPaciente.embarazos_activos ? [
                {
                  color: "purple",
                  dot: <HeartOutlined />,
                  children: "Embarazo activo registrado"
                }
              ] : []),
              {
                color: "gray",
                children: "Sin consultas recientes"
              }
            ]}
          />

          {selectedPaciente.observaciones && (
            <Alert message="Observaciones" description={selectedPaciente.observaciones} type="info" showIcon style={{ marginTop: 20 }} />
          )}

          <Divider>Notas Rápidas</Divider>
          <TextArea
            rows={3}
            placeholder="Agregar notas rápidas sobre este paciente..."
            style={{ marginBottom: 16 }}
          />

          <Divider>Filtrar por Fechas</Divider>
          <RangePicker style={{ width: '100%' }} />
        </div>
      </Spin>
    ) : (
      <Empty description="Seleccione un paciente" />
    )}
  </Drawer>
);

export default PacienteDrawer;
