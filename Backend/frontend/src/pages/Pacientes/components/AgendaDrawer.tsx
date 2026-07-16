import React from 'react';
import { Drawer, Divider, Card, List, Avatar, Button, Calendar } from 'antd';
import { UserOutlined, CalendarOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { Paciente } from '../pacientesTypes';

const USER_ICON = <UserOutlined />;
const CALENDAR_ICON_5 = <CalendarOutlined />;

interface AgendaDrawerProps {
  visible: boolean;
  onClose: () => void;
  pacientes: Paciente[];
}

const AgendaDrawer: React.FC<AgendaDrawerProps> = ({ visible, onClose, pacientes }) => (
  <Drawer
    title="Sistema de Agendamiento Rápido"
    placement="right"
    width={500}
    open={visible}
    onClose={onClose}
  >
    <Calendar fullscreen={false} />
    <Divider />
    <Card title="Próximas Citas Hoy" size="small">
      <List
        size="small"
        dataSource={pacientes.filter(p => p.embarazos_activos).slice(0, 5)}
        renderItem={(item) => (
          <List.Item>
            <List.Item.Meta
              avatar={<Avatar icon={USER_ICON} />}
              title={item.nombre_completo}
              description={`Control Prenatal • ${dayjs().format('HH:mm')}`}
            />
          </List.Item>
        )}
      />
    </Card>
    <Divider />
    <Button type="primary" icon={CALENDAR_ICON_5} block>
      Abrir Agenda Completa
    </Button>
  </Drawer>
);

export default AgendaDrawer;
