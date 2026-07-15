import React from 'react';
import { Card, Spin, Tag, Tooltip } from 'antd';
import dayjs from 'dayjs';
import { HorarioDisponible } from '../../../services/citasService';

interface HorariosDisponiblesProps {
  medicoSeleccionado: number | null;
  fechaSeleccionada: dayjs.Dayjs | null;
  loadingHorarios: boolean;
  horariosDisponibles: HorarioDisponible[];
  onHoraSelect: (hora: string) => void;
}

const HorariosDisponibles: React.FC<HorariosDisponiblesProps> = ({
  medicoSeleccionado,
  fechaSeleccionada,
  loadingHorarios,
  horariosDisponibles,
  onHoraSelect,
}) => {
  if (!medicoSeleccionado || !fechaSeleccionada) {
    return null;
  }

  if (loadingHorarios) {
    return (
      <Card size="small" title="Horarios Disponibles" style={{ marginTop: 16 }}>
        <Spin />
      </Card>
    );
  }

  if (horariosDisponibles.length === 0) {
    return null;
  }

  const disponibles = horariosDisponibles.filter(h => h.disponible);
  const ocupados = horariosDisponibles.filter(h => !h.disponible);

  return (
    <Card size="small" title="Horarios Disponibles" style={{ marginTop: 16 }}>
      {disponibles.length > 0 && (
        <div style={{ marginBottom: 8 }}>
          <strong>Disponibles:</strong>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 8 }}>
            {disponibles.map((h) => (
              <Tag
                key={h.hora}
                color="green"
                style={{ cursor: 'pointer' }}
                onClick={() => onHoraSelect(h.hora)}
              >
                {h.hora}
              </Tag>
            ))}
          </div>
        </div>
      )}
      {ocupados.length > 0 && (
        <div>
          <strong>Ocupados:</strong>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 8 }}>
            {ocupados.map((h) => (
              <Tooltip key={h.hora} title={h.motivo || 'No disponible'}>
                <Tag color="red">{h.hora}</Tag>
              </Tooltip>
            ))}
          </div>
        </div>
      )}
    </Card>
  );
};

export default HorariosDisponibles;
