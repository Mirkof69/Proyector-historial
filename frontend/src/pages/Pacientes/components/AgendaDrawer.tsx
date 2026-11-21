import React, { useEffect, useState } from 'react';
import { Drawer, Divider, Card, List, Avatar, Button, Calendar } from 'antd';
import { UserOutlined, CalendarOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import dayjs from 'dayjs';
// Cliente axios: la respuesta trae los datos en `.data`.
import apiClient from '../../../services/api';
import type { Cita } from '../../../services/citasService';

const USER_ICON = <UserOutlined />;
const CALENDAR_ICON_5 = <CalendarOutlined />;

interface AgendaDrawerProps {
  visible: boolean;
  onClose: () => void;
}

const TIPO: Record<string, string> = {
  primera_vez: 'Primera vez',
  control: 'Control prenatal',
  urgencia: 'Urgencia',
  seguimiento: 'Seguimiento',
};

/**
 * Agenda rápida: las citas REALES de hoy, pedidas al servidor al abrir.
 *
 * Antes listaba las 5 primeras pacientes con embarazo activo de lo que la
 * pantalla había descargado, con la hora actual como «hora de la cita»: no
 * eran citas. Con el listado paginado en el servidor ya ni siquiera había
 * «todas las pacientes» de donde sacarlas.
 */
const AgendaDrawer: React.FC<AgendaDrawerProps> = ({ visible, onClose }) => {
  const navigate = useNavigate();
  const [citas, setCitas] = useState<Cita[]>([]);
  const [cargando, setCargando] = useState(false);

  useEffect(() => {
    if (!visible) return undefined;
    let vigente = true;
    setCargando(true);
    apiClient
      .get('/citas/citas/', {
        params: { fecha_cita: dayjs().format('YYYY-MM-DD'), ordering: 'hora_cita', page_size: 10 },
      })
      .then((r) => { if (vigente) setCitas(r.data?.results ?? []); })
      .catch(() => { if (vigente) setCitas([]); })
      .finally(() => { if (vigente) setCargando(false); });
    return () => { vigente = false; };
  }, [visible]);

  return (
    <Drawer
      title="Sistema de Agendamiento Rápido"
      placement="right"
      width={500}
      open={visible}
      onClose={onClose}
    >
      <Calendar fullscreen={false} />
      <Divider />
      <Card title="Citas de Hoy" size="small">
        <List
          size="small"
          loading={cargando}
          locale={{ emptyText: 'No hay citas para hoy' }}
          dataSource={citas}
          renderItem={(cita) => (
            <List.Item>
              <List.Item.Meta
                avatar={<Avatar icon={USER_ICON} />}
                title={cita.paciente_info?.nombre_completo || 'Paciente'}
                description={`${TIPO[cita.tipo_cita] || cita.tipo_cita} • ${cita.hora_cita?.substring(0, 5)}`}
              />
            </List.Item>
          )}
        />
      </Card>
      <Divider />
      <Button type="primary" icon={CALENDAR_ICON_5} block onClick={() => navigate('/dashboard/citas/calendario')}>
        Abrir Agenda Completa
      </Button>
    </Drawer>
  );
};

export default AgendaDrawer;
