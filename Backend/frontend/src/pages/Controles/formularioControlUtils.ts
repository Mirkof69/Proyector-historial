import { Embarazo } from '../../services/embarazosService';
import { Paciente } from '../../services/pacientesService';

/**
 * Devuelve el texto "ID - Nombre Apellido" de la paciente asociada a un embarazo.
 * Función pura extraída del FormularioControl (comportamiento idéntico).
 */
export const getNombrePaciente = (
  embarazoId: number,
  embarazos: Embarazo[],
  pacientes: Paciente[],
): string => {
  const embarazo = embarazos.find((e) => e.id === embarazoId);

  if (!embarazo) {
    return 'Embarazo no encontrado';
  }

  // PRIORIDAD 1: Usar paciente_info del backend (nuevo formato)
  if ((embarazo as any).paciente_info) {
    const pacienteInfo = (embarazo as any).paciente_info;
    const nombre = pacienteInfo.nombre || '';
    const apellidoPaterno = pacienteInfo.apellido_paterno || '';
    const apellidoMaterno = pacienteInfo.apellido_materno || '';
    const idClinico = pacienteInfo.id_clinico || '';

    const nombreCompleto = `${nombre} ${apellidoPaterno} ${apellidoMaterno}`.trim();

    if (nombreCompleto) {
      return `${idClinico} - ${nombreCompleto}`;
    }
  }

  // PRIORIDAD 2: Usar paciente_nombre del backend (formato: "ID - Nombre")
  if ((embarazo as any).paciente_nombre) {
    const nombreCompleto = (embarazo as any).paciente_nombre;
    return nombreCompleto;
  }

  // PRIORIDAD 3: paciente es un objeto completo
  if (typeof embarazo.paciente === 'object' && embarazo.paciente !== null) {
    const paciente = embarazo.paciente as Paciente;
    const nombre = paciente.nombre || '';
    const apellidoPaterno = paciente.apellido_paterno || '';
    const apellidoMaterno = paciente.apellido_materno || '';
    const nombreCompleto = `${nombre} ${apellidoPaterno} ${apellidoMaterno}`.trim();

    if (nombreCompleto && paciente.id_clinico) {
      return `${paciente.id_clinico} - ${nombreCompleto}`;
    }
  }

  // PRIORIDAD 4: paciente es un ID numérico
  if (typeof embarazo.paciente === 'number') {
    const paciente = pacientes.find((p) => p.id === embarazo.paciente);
    if (paciente) {
      const nombre = paciente.nombre || '';
      const apellidoPaterno = paciente.apellido_paterno || '';
      const apellidoMaterno = paciente.apellido_materno || '';
      const nombreCompleto = `${nombre} ${apellidoPaterno} ${apellidoMaterno}`.trim();

      if (nombreCompleto && paciente.id_clinico) {
        return `${paciente.id_clinico} - ${nombreCompleto}`;
      }
    }
  }

  return 'Información no disponible';
};
