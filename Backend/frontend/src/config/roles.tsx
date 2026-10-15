import React from 'react';
import {
  MedicineBoxOutlined,
  HeartOutlined,
  ExperimentOutlined,
  SafetyCertificateOutlined,
  ScheduleOutlined,
} from '@ant-design/icons';

/**
 * Catálogo único de roles.
 *
 * Por qué existe este archivo
 * ---------------------------
 * El mismo mapa rol -> nombre y color estaba copiado tres veces (`Usuarios.tsx`,
 * `UsuariosTable.tsx`, `UsuarioDetailDrawer.tsx`) y las tres copias se habían
 * quedado atrás respecto al backend. `Usuario.ROLES` define cinco roles:
 *
 *     medico · enfermera · laboratorista · administrador · recepcion
 *
 * Las copias del frontend conocían tres, y una con el género cambiado
 * (`enfermero` en vez de `enfermera`). Consecuencias medibles en pantalla:
 *
 *   - El filtro «Enfermero» mandaba `rol=enfermero` al backend, que guarda
 *     `enfermera`: devolvía **cero resultados siempre**.
 *   - La tarjeta «Enfermeros» contaba `rol === 'enfermero'`: **siempre 0**,
 *     hubiera las enfermeras que hubiera.
 *   - `laboratorista` y `recepcion` no estaban en el desplegable: no había
 *     forma de filtrar por ellos.
 *   - En el detalle, `ROLES_CONFIG[rol]?.nombre` sin alternativa dejaba una
 *     **etiqueta vacía** para esos tres roles.
 *
 * Ninguno daba error: la pantalla se veía bien y mentía. Con un solo catálogo,
 * añadir un rol en el backend es cambiar este archivo y nada más.
 */

export interface ConfiguracionRol {
  /** Cómo se llama el rol para una persona. */
  nombre: string;
  /** Color de la etiqueta y del avatar. */
  color: string;
  /** Icono que acompaña al nombre. */
  icono: React.ReactNode;
}

/**
 * Las claves son EXACTAMENTE los valores de `Usuario.ROLES` del backend
 * (`Backend/usuarios/models.py`). Si aquí se escribe otra cosa, el filtro deja
 * de encontrar gente y nadie se entera.
 */
export const ROLES: Record<string, ConfiguracionRol> = {
  medico: { nombre: 'Médico', color: 'var(--grafico-1)', icono: <MedicineBoxOutlined /> },
  enfermera: { nombre: 'Enfermera', color: 'var(--grafico-2)', icono: <HeartOutlined /> },
  laboratorista: { nombre: 'Laboratorista', color: 'var(--grafico-3)', icono: <ExperimentOutlined /> },
  administrador: { nombre: 'Administrador', color: 'var(--grafico-4)', icono: <SafetyCertificateOutlined /> },
  recepcion: { nombre: 'Recepción', color: 'var(--grafico-5)', icono: <ScheduleOutlined /> },
};

/** Los roles en el orden en que se muestran en filtros y estadísticas. */
export const LISTA_ROLES = Object.keys(ROLES);

/**
 * Configuración de un rol, con una alternativa que nunca deja el hueco vacío.
 *
 * Un rol desconocido —porque el backend añadió uno y aquí todavía no está—
 * se muestra con su propio nombre técnico y en gris, no en blanco. Que se vea
 * feo es preferible a que la casilla del rol aparezca vacía y quien mire crea
 * que la usuaria no tiene ninguno.
 */
export function configuracionDeRol(rol: string | undefined | null): ConfiguracionRol {
  if (rol && ROLES[rol]) {
    return ROLES[rol];
  }
  // Gris en hexadecimal a proposito, no la palabra 'default' de antd: este
  // color tambien se usa como `backgroundColor` del avatar, y ahi 'default' no
  // es un color CSS valido -- el avatar se quedaria sin fondo.
  return { nombre: rol || 'Sin rol', color: 'var(--color-texto-3)', icono: null };
}

/** Cuenta cuántas usuarias hay de cada rol, incluidos los roles con cero. */
export function contarPorRol<T extends { rol?: string }>(usuarios: T[]): Record<string, number> {
  const cuenta: Record<string, number> = {};
  LISTA_ROLES.forEach((rol) => { cuenta[rol] = 0; });
  usuarios.forEach((usuario) => {
    if (usuario.rol) {
      cuenta[usuario.rol] = (cuenta[usuario.rol] || 0) + 1;
    }
  });
  return cuenta;
}
