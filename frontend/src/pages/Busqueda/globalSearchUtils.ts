import api from '../../services/api';
import dayjs from 'dayjs';
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

/**
 * Pide al SERVIDOR los resultados de un módulo (`?search=`, 20 como mucho).
 *
 * Antes cada búsqueda descargaba TODOS los registros de seis módulos
 * (miles de pacientes, embarazos, controles…) y filtraba en el navegador con
 * `includes`, que no encontraba «López» al escribir «lopez». El servidor
 * entiende los nombres cifrados, las tildes y las variantes (Quispe/Kispe).
 */
const buscarEnServidor = async (url: string, query: string): Promise<any[]> => {
  const respuesta = await api.get(url, { params: { search: query, page_size: 20 } });
  const datos = respuesta.data;
  return Array.isArray(datos) ? datos : datos?.results ?? [];
};

const ordenar = (resultados: SearchResult[]) => resultados.sort((a, b) => b.relevancia - a.relevancia);

// Búsqueda en Pacientes
export const searchPacientes = async (query: string): Promise<SearchResult[]> => {
  try {
    const data = await buscarEnServidor('/pacientes/', query);
    return ordenar(data.map((p) => ({
      id: p.id,
      tipo: 'paciente',
      titulo: p.nombre_completo || `${p.nombre} ${p.apellido_paterno} ${p.apellido_materno || ''}`.trim(),
      subtitulo: `CI: ${p.ci || 'N/A'} | ID: ${p.id_clinico || 'N/A'}`,
      descripcion: `${p.edad ?? 'N/A'} años`,
      fecha: p.fecha_registro,
      estado: p.embarazos_activos || p.embarazo_activo ? 'Embarazo activo' : 'Sin embarazo activo',
      relevancia: calculateRelevance(query, [p.nombre, p.apellido_paterno, p.apellido_materno, p.ci, p.id_clinico]),
      data: p,
    })));
  } catch (error) {
    return [];
  }
};

export const searchEmbarazos = async (query: string): Promise<SearchResult[]> => {
  try {
    const data = await buscarEnServidor('/embarazos/', query);
    return ordenar(data.map((e) => {
      const pacienteNombre = e.paciente_nombre || e.paciente_info?.nombre_completo || e.paciente_info?.nombre || '';
      return {
        id: e.id || 0,
        tipo: 'embarazo',
        titulo: `Embarazo de ${pacienteNombre || 'N/A'}`,
        subtitulo: `Código: ${e.codigo_embarazo || 'N/A'}`,
        descripcion: `${e.semanas_gestacion ?? 0} semanas | FUM: ${e.fecha_ultima_menstruacion ? dayjs(e.fecha_ultima_menstruacion).format('DD/MM/YYYY') : '—'}`,
        fecha: e.fecha_registro,
        estado: e.estado,
        relevancia: calculateRelevance(query, [pacienteNombre, e.codigo_embarazo]),
        data: e,
      };
    }));
  } catch (error) {
    return [];
  }
};

export const searchCitas = async (query: string): Promise<SearchResult[]> => {
  try {
    const data = await buscarEnServidor('/citas/citas/', query);
    return ordenar(data.map((c) => ({
      id: c.id,
      tipo: 'cita',
      titulo: `Cita - ${c.paciente_nombre || ''}`,
      subtitulo: `Médico: ${c.medico_nombre || 'N/A'}`,
      descripcion: c.motivo || 'Sin motivo',
      fecha: c.fecha_cita || c.fecha_hora,
      estado: c.estado,
      relevancia: calculateRelevance(query, [c.paciente_nombre, c.medico_nombre, c.motivo]),
      data: c,
    })));
  } catch (error) {
    return [];
  }
};

export const searchEcografias = async (query: string): Promise<SearchResult[]> => {
  try {
    const data = await buscarEnServidor('/ecografias/', query);
    return ordenar(data.map((e) => ({
      id: e.id,
      tipo: 'ecografia',
      titulo: `Ecografía - ${e.paciente_nombre || ''}`,
      subtitulo: `Tipo: ${e.tipo_ecografia_display || e.tipo_ecografia || 'N/A'}`,
      descripcion: e.observaciones || e.diagnostico || 'Sin observaciones',
      fecha: e.fecha_ecografia || e.fecha,
      estado: 'Realizada',
      relevancia: calculateRelevance(query, [e.paciente_nombre, e.tipo_ecografia, e.observaciones]),
      data: e,
    })));
  } catch (error) {
    return [];
  }
};

export const searchLaboratorio = async (query: string): Promise<SearchResult[]> => {
  try {
    const data = await buscarEnServidor('/laboratorios/examenes/', query);
    return ordenar(data.map((l) => ({
      id: l.id,
      tipo: 'laboratorio',
      titulo: `Laboratorio - ${l.paciente_nombre || ''}`,
      subtitulo: `Examen: ${l.tipo_examen_nombre || l.nombre_examen || l.tipo_examen || 'N/A'}`,
      descripcion: `Estado: ${l.estado || 'pendiente'}`,
      fecha: l.fecha_solicitud,
      estado: l.estado,
      relevancia: calculateRelevance(query, [l.paciente_nombre, l.tipo_examen_nombre, l.nombre_examen]),
      data: l,
    })));
  } catch (error) {
    return [];
  }
};

export const searchEvoluciones = async (query: string): Promise<SearchResult[]> => {
  // Notas de evolución (las «evoluciones del embarazo» se unificaron en ellas).
  // Se busca en el servidor: entiende los nombres cifrados de las pacientes.
  try {
    const respuesta = await api.get('/notas-evolucion/', { params: { search: query, page_size: 20 } });
    const data: any[] = respuesta.data?.results ?? respuesta.data ?? [];
    return data.map((n) => ({
      id: n.id,
      tipo: 'evolucion',
      titulo: `Nota de evolución - ${n.paciente_nombre || ''}`,
      subtitulo: `Médico: ${n.medico_nombre || 'N/A'}`,
      descripcion: n.motivo_consulta || n.diagnosticos || '',
      fecha: n.fecha_consulta,
      estado: n.tipo_consulta_display || n.tipo_consulta || '',
      relevancia: calculateRelevance(query, [n.paciente_nombre, n.motivo_consulta, n.medico_nombre]),
      data: n,
    }));
  } catch {
    return [];
  }
};

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
