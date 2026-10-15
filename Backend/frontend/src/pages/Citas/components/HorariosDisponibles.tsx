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
      <Card size="small" title="Horarios Disponibles" className="citas-arriba">
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
    <Card size="small" title="Horarios Disponibles" className="citas-arriba">
      {disponibles.length > 0 && (
        <div>
          <strong>Disponibles:</strong>
          <div className="citas-page__horarios">
            {disponibles.map((h) => (
              <Tag
                key={h.hora}
                color="success"
                className="citas-page__horario-libre tabular-nums"
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
          <div className="citas-page__horarios">
            {ocupados.map((h) => (
              <Tooltip key={h.hora} title={h.motivo || 'No disponible'}>
                <Tag color="error" className="tabular-nums">{h.hora}</Tag>
              </Tooltip>
            ))}
          </div>
        </div>
      )}
    </Card>
  );
};

export default HorariosDisponibles;
