import React from 'react';
import { Button, Space, Tag, Drawer, Descriptions, Divider, Card } from 'antd';
import {
  EyeOutlined, EditOutlined, FileImageOutlined, CalendarOutlined, UserOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { Ecografia } from '../../../services/ecografiasService';
import { FRONTEND_ROUTES } from '../../../config/routes';

interface EcografiaVistaRapidaDrawerProps {
  drawerVistaRapidaVisible: boolean;
  setDrawerVistaRapidaVisible: (visible: boolean) => void;
  ecografiaSeleccionada: Ecografia | null;
  handleVer: (id: number) => void;
  navigate: (path: string) => void;
  canChange: (perm: string) => boolean;
}

const EcografiaVistaRapidaDrawer: React.FC<EcografiaVistaRapidaDrawerProps> = ({
  drawerVistaRapidaVisible, setDrawerVistaRapidaVisible, ecografiaSeleccionada, handleVer, navigate, canChange,
}) => (
  <Drawer
    title={
      <Space>
        <FileImageOutlined />
        Vista Rápida de Ecografía
        {ecografiaSeleccionada && (
          <Tag color="blue">{ecografiaSeleccionada.tipo_ecografia}</Tag>
        )}
      </Space>
    }
    placement="right"
    width={600}
    onClose={() => setDrawerVistaRapidaVisible(false)}
    open={drawerVistaRapidaVisible}
    extra={
      <Space>
        <Button
          icon={<EyeOutlined />}
          onClick={() => {
            if (ecografiaSeleccionada) {
              setDrawerVistaRapidaVisible(false);
              handleVer(ecografiaSeleccionada.id!);
            }
          }}
        >
          Ver Página Completa
        </Button>
        {canChange('ecografia') && (
          <Button
            type="primary"
            icon={<EditOutlined />}
            onClick={() => {
              if (ecografiaSeleccionada) {
                setDrawerVistaRapidaVisible(false);
                navigate(FRONTEND_ROUTES.DASHBOARD.ECOGRAFIAS_EDITAR(ecografiaSeleccionada.id!));
              }
            }}
          >
            Editar Completo
          </Button>
        )}
      </Space>
    }
  >
    {ecografiaSeleccionada && (
      <Space direction="vertical" style={{ width: '100%' }} size="large">
        <Descriptions title="Información de la Ecografía" bordered column={1} size="small">
          <Descriptions.Item label="Paciente">
            <strong>{ecografiaSeleccionada.paciente_nombre || 'No especificado'}</strong>
          </Descriptions.Item>
          <Descriptions.Item label="Fecha">
            {dayjs(ecografiaSeleccionada.fecha_ecografia).format('DD/MM/YYYY')}
          </Descriptions.Item>
          <Descriptions.Item label="Tipo">
            <Tag color="blue">{ecografiaSeleccionada.tipo_ecografia}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Edad Gestacional">
            {ecografiaSeleccionada.edad_gestacional_semanas} semanas
          </Descriptions.Item>
          {ecografiaSeleccionada.observaciones && (
            <Descriptions.Item label="Observaciones">
              {ecografiaSeleccionada.observaciones}
            </Descriptions.Item>
          )}
        </Descriptions>

        <Divider orientation="left">🔗 Acceso Rápido a Módulos</Divider>
        <Card size="small">
          <Space direction="vertical" style={{ width: '100%' }} size="small">
            <Button
              type="link"
              icon={<UserOutlined />}
              block
              style={{ textAlign: 'left' }}
              onClick={() => {
                setDrawerVistaRapidaVisible(false);
                navigate(`/dashboard/pacientes?id=${ecografiaSeleccionada.paciente}`);
              }}
            >
              Ver Paciente: {ecografiaSeleccionada.paciente_nombre}
            </Button>
            <Button
              type="link"
              icon={<FileImageOutlined />}
              block
              style={{ textAlign: 'left' }}
              onClick={() => {
                setDrawerVistaRapidaVisible(false);
                navigate(`/dashboard/embarazos?id=${ecografiaSeleccionada.embarazo}`);
              }}
            >
              Ver Datos del Embarazo
            </Button>
            <Button
              type="link"
              icon={<FileImageOutlined />}
              block
              style={{ textAlign: 'left' }}
              onClick={() => {
                setDrawerVistaRapidaVisible(false);
                navigate(`/dashboard/controles?embarazo=${ecografiaSeleccionada.embarazo}`);
              }}
            >
              Ver Controles Prenatales
            </Button>
            <Button
              type="link"
              icon={<CalendarOutlined />}
              block
              style={{ textAlign: 'left' }}
              onClick={() => {
                setDrawerVistaRapidaVisible(false);
                navigate(`/dashboard/citas?embarazo=${ecografiaSeleccionada.embarazo}`);
              }}
            >
              Ver Citas del Embarazo
            </Button>
            <Button
              type="link"
              icon={<FileImageOutlined />}
              block
              style={{ textAlign: 'left' }}
              onClick={() => {
                setDrawerVistaRapidaVisible(false);
                navigate(`/dashboard/laboratorio?embarazo=${ecografiaSeleccionada.embarazo}`);
              }}
            >
              Ver Exámenes de Laboratorio
            </Button>
            <Divider style={{ margin: '8px 0' }} />
            <Button
              type="primary"
              icon={<UserOutlined />}
              block
              onClick={() => {
                setDrawerVistaRapidaVisible(false);
                navigate(`/dashboard/pacientes/${ecografiaSeleccionada.paciente}/historia`);
              }}
            >
              Ver Historia Clínica Completa
            </Button>
          </Space>
        </Card>
      </Space>
    )}
  </Drawer>
);

export default EcografiaVistaRapidaDrawer;
