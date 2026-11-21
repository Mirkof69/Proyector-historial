import React from 'react';
import { Card, Statistic } from 'antd';
import { UserOutlined, CheckCircleOutlined } from '@ant-design/icons';
import { ROLES, LISTA_ROLES } from '../../../config/roles';

export interface UsuariosStats {
  total: number;
  activos: number;
  /** Cuántas usuarias hay de cada rol, indexado por la clave del backend. */
  porRol: Record<string, number>;
}

interface UsuariosStatsCardsProps {
  estadisticas: UsuariosStats;
}

/**
 * Total, activos y una tarjeta por rol.
 *
 * Antes había cuatro tarjetas fijas y dos de ellas mentían: «Enfermeros»
 * contaba `rol === 'enfermero'` cuando el backend guarda `enfermera`, así que
 * marcaba **0 siempre**, y laboratoristas y recepción no aparecían en ninguna
 * parte. Ahora las tarjetas salen de `LISTA_ROLES`: añadir un rol al catálogo
 * lo hace aparecer aquí solo.
 */
const UsuariosStatsCards: React.FC<UsuariosStatsCardsProps> = ({ estadisticas }) => {
  // Total y Activos, más una tarjeta por rol. Con cinco roles son siete
  // tarjetas: en pantalla ancha caben cuatro por fila y el resto baja.
  const tarjetas = [
    { clave: 'total', titulo: 'Total Usuarios', valor: estadisticas.total, icono: <UserOutlined /> },
    { clave: 'activos', titulo: 'Activos', valor: estadisticas.activos, icono: <CheckCircleOutlined /> },
    ...LISTA_ROLES.map((rol) => ({
      clave: rol,
      titulo: ROLES[rol].nombre,
      valor: estadisticas.porRol[rol] ?? 0,
      icono: ROLES[rol].icono,
    })),
  ];

  return (
    <div className="usuarios-page__cifras">
      {tarjetas.map((tarjeta) => (
        <Card key={tarjeta.clave} size="small">
          <Statistic title={<>{tarjeta.icono}{tarjeta.titulo}</>} value={tarjeta.valor} />
        </Card>
      ))}
    </div>
  );
};

export default UsuariosStatsCards;
