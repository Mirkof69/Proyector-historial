import dayjs from 'dayjs';
import { pacientesService } from '../../services/pacientesService';
import { embarazosService } from '../../services/embarazosService';
import { citasService } from '../../services/citasService';
import { ecografiasService } from '../../services/ecografiasService';
import { laboratorioService } from '../../services/laboratorioService';
import { evolucionesService } from '../../services/evolucionesService';
import { consultoriosService } from '../../services/consultoriosService';

export interface SearchResult {
  id: number | string;
  tipo: string;
  titulo: string;
  subtitulo?: string;
  descripcion?: string;
  fecha?: string;
  estado?: string;
  relevancia: number;
  data: any;
}

export const calculateRelevance = (query: string, fields: (string | undefined)[]): number => {
  let score = 0;
  const queryLower = query.toLowerCase();
  const words = queryLower.split(' ');
  const wordSet = new Set(words);

  fields.forEach(field => {
    if (!field) return;
    const fieldLower = field.toLowerCase();
    if (fieldLower === queryLower) score += 100;
    else if (fieldLower.startsWith(queryLower)) score += 50;
    else if (fieldLower.includes(queryLower)) score += 25;
    wordSet.forEach(word => {
      if (fieldLower.includes(word)) score += 10;
    });
  });

  return score;
};

// Búsqueda en Pacientes
export const searchPacientes = async (query: string): Promise<SearchResult[]> => {
  try {
    const data = await pacientesService.listar() as any[];
    const results: SearchResult[] = [];
    for (const p of data) {
      const _pSearchText = [p.nombre, p.apellido_paterno, p.apellido_materno, p.ci, p.id_clinico].filter(Boolean).join(' ').toLowerCase();
      if (_pSearchText.includes(query)) {
        results.push({
          id: p.id,
          tipo: 'paciente',
          titulo: `${p.nombre} ${p.apellido_paterno} ${p.apellido_materno || ''}`.trim(),
          subtitulo: `CI: ${p.ci || 'N/A'} | ID: ${p.id_clinico || 'N/A'}`,
          descripcion: `${p.edad || 'N/A'} años | ${p.genero || 'N/A'}`,
          fecha: p.fecha_registro,
          estado: p.embarazo_activo ? 'Embarazo Activo' : 'Sin embarazo',
          relevancia: calculateRelevance(query, [p.nombre, p.apellido_paterno, p.apellido_materno, p.ci, p.id_clinico]),
          data: p
        });
      }
    }
    return results.sort((a, b) => b.relevancia - a.relevancia);
  } catch (error) {
    return [];
  }
};

export const searchEmbarazos = async (query: string): Promise<SearchResult[]> => {
  try {
    const data = await embarazosService.listar() as any[];
    const results: SearchResult[] = [];
    for (const e of data) {
      const pacienteNombre = e.paciente_info?.nombre_completo || e.paciente_info?.nombre || '';
      const _eSearchText = [pacienteNombre, e.codigo_embarazo].filter(Boolean).join(' ').toLowerCase();
      if (_eSearchText.includes(query)) {
        results.push({
          id: e.id || 0,
          tipo: 'embarazo',
          titulo: `Embarazo de ${pacienteNombre || 'N/A'}`,
          subtitulo: `Código: ${e.codigo_embarazo || 'N/A'}`,
          descripcion: `${e.semanas_gestacion || 0} semanas | FUM: ${dayjs(e.fecha_ultima_menstruacion).format('DD/MM/YYYY')}`,
          fecha: e.fecha_registro,
          estado: e.estado,
          relevancia: calculateRelevance(query, [pacienteNombre, e.codigo_embarazo]),
          data: e
        });
      }
    }
    return results.sort((a, b) => b.relevancia - a.relevancia);
  } catch (error) {
    return [];
  }
};

export const searchCitas = async (query: string): Promise<SearchResult[]> => {
  try {
    const data = await citasService.listar() as any[];
    const results: SearchResult[] = [];
    for (const c of data) {
      const _cSearchText = [c.paciente_nombre, c.medico_nombre, c.motivo].filter(Boolean).join(' ').toLowerCase();
      if (_cSearchText.includes(query)) {
        results.push({
          id: c.id,
          tipo: 'cita',
          titulo: `Cita - ${c.paciente_nombre}`,
          subtitulo: `Médico: ${c.medico_nombre || 'N/A'}`,
          descripcion: c.motivo || 'Sin motivo',
          fecha: c.fecha_hora,
          estado: c.estado,
          relevancia: calculateRelevance(query, [c.paciente_nombre, c.medico_nombre, c.motivo]),
          data: c
        });
      }
    }
    return results.sort((a, b) => b.relevancia - a.relevancia);
  } catch (error) {
    return [];
  }
};

export const searchEcografias = async (query: string): Promise<SearchResult[]> => {
  try {
    const data = await ecografiasService.listar() as any[];
    const results: SearchResult[] = [];
    for (const e of data) {
      const _ecSearchText = [e.paciente_nombre, e.tipo_ecografia, e.observaciones].filter(Boolean).join(' ').toLowerCase();
      if (_ecSearchText.includes(query)) {
        results.push({
          id: e.id,
          tipo: 'ecografia',
          titulo: `Ecografía - ${e.paciente_nombre}`,
          subtitulo: `Tipo: ${e.tipo_ecografia || 'N/A'}`,
          descripcion: e.observaciones || 'Sin observaciones',
          fecha: e.fecha,
          estado: 'Realizada',
          relevancia: calculateRelevance(query, [e.paciente_nombre, e.tipo_ecografia, e.observaciones]),
          data: e
        });
      }
    }
    return results.sort((a, b) => b.relevancia - a.relevancia);
  } catch (error) {
    return [];
  }
};

export const searchLaboratorio = async (query: string): Promise<SearchResult[]> => {
  try {
    const data = await laboratorioService.listar() as any[];
    const results: SearchResult[] = [];
    for (const l of data) {
      const _lSearchText = [l.paciente_nombre, l.tipo_examen, l.nombre_examen].filter(Boolean).join(' ').toLowerCase();
      if (_lSearchText.includes(query)) {
        results.push({
          id: l.id,
          tipo: 'laboratorio',
          titulo: `Laboratorio - ${l.paciente_nombre}`,
          subtitulo: `Examen: ${l.nombre_examen || l.tipo_examen || 'N/A'}`,
          descripcion: `Resultado: ${l.resultado || 'Pendiente'}`,
          fecha: l.fecha_solicitud,
          estado: l.estado,
          relevancia: calculateRelevance(query, [l.paciente_nombre, l.tipo_examen, l.nombre_examen]),
          data: l
        });
      }
    }
    return results.sort((a, b) => b.relevancia - a.relevancia);
  } catch (error) {
    return [];
  }
};

export const searchEvoluciones = async (query: string): Promise<SearchResult[]> => {
  try {
    const data = await evolucionesService.listar() as any[];
    const results: SearchResult[] = [];
    for (const e of data) {
      const _evSearchText = [e.paciente_nombre, e.diagnostico, e.medico_nombre].filter(Boolean).join(' ').toLowerCase();
      if (_evSearchText.includes(query)) {
        results.push({
          id: e.id,
          tipo: 'evolucion',
          titulo: `Evolución - ${e.paciente_nombre}`,
          subtitulo: `Médico: ${e.medico_nombre || 'N/A'}`,
          descripcion: e.diagnostico || 'Sin diagnóstico',
          fecha: e.fecha || e.fecha_evento,
          estado: e.tipo || 'N/A',
          relevancia: calculateRelevance(query, [e.paciente_nombre, e.diagnostico, e.medico_nombre]),
          data: e
        });
      }
    }
    return results.sort((a, b) => b.relevancia - a.relevancia);
  } catch (error) {
    return [];
  }
};

// Búsqueda en Consultorios
export const searchConsultorios = async (query: string): Promise<SearchResult[]> => {
  try {
    const data = await consultoriosService.getAll() as any[];
    const results: SearchResult[] = [];
    for (const c of data) {
      const _coSearchText = [c.nombre, c.codigo, c.area].filter(Boolean).join(' ').toLowerCase();
      if (_coSearchText.includes(query)) {
        results.push({
          id: c.id || 0,
          tipo: 'consultorio',
          titulo: c.nombre || 'Sin nombre',
          subtitulo: `Código: ${c.codigo || 'N/A'} | ${c.area || 'N/A'}`,
          descripcion: `${c.tipo || 'N/A'} | Capacidad: ${c.capacidad || 'N/A'}`,
          fecha: undefined,
          estado: c.estado,
          relevancia: calculateRelevance(query, [c.nombre, c.codigo, c.area]),
          data: c
        });
      }
    }
    return results.sort((a, b) => b.relevancia - a.relevancia);
  } catch (error) {
    return [];
  }
};
