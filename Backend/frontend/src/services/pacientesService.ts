/**
 * ═══════════════════════════════════════════════════════════════════════════
 * 📋 SERVICIO DE PACIENTES - MEGA EXTENSO
 * ═══════════════════════════════════════════════════════════════════════════
 * 
 * Servicio completo para gestión de pacientes en sistema de historias clínicas
 * Incluye CRUD, antecedentes, búsquedas avanzadas, estadísticas, análisis,
 * reportes, validaciones y utilidades
 * 
 * @author Sistema de Historias Clínicas
 * @version 2.0.0 - Reconstruido desde cero
 */

import api from './api';
import { logger } from '../utils/logger';

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// INTERFACES Y TIPOS
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

export interface Paciente {
    id: number;
    id_clinico: string;
    nombre: string;
    apellido_paterno: string;
    apellido_materno?: string;
    nombre_completo?: string;
    fecha_nacimiento: string;
    edad?: number;
    genero: 'femenino' | 'masculino' | 'otro';
    ci: string;
    telefono?: string;
    email?: string;
    direccion?: string;
    ciudad?: string;
    pais?: string;
    tipo_sangre?: GrupoSanguineo;
    factor_rh?: 'positivo' | 'negativo';
    numero_seguro_social?: string;
    peso_kg?: number;
    altura_cm?: number;
    imc?: number;
    estado_paciente?: 'activo' | 'inactivo' | 'fallecido';
    estado_civil?: 'soltero' | 'casado' | 'divorciado' | 'viudo' | 'union_libre';
    ocupacion?: string;
    nivel_educativo?: 'ninguno' | 'primaria' | 'secundaria' | 'tecnico' | 'universitario' | 'postgrado';
    alergias?: string;
    enfermedades_cronicas?: string;
    fecha_baja?: string;
    contacto_emergencia_nombre?: string;
    contacto_emergencia_telefono?: string;
    contacto_emergencia_relacion?: string;
    observaciones?: string;
    activo?: boolean;
    fecha_registro?: string;
    fecha_actualizacion?: string;
    embarazos_activos?: number;

    // Campos adicionales para ListaHistoriasClinicas
    numero_historia?: string;          // Número de historia clínica
    numero_documento?: string;         // Alias para CI
    tiene_historia_clinica?: boolean;  // Si tiene HC creado
    embarazo_activo?: boolean;         // Si tiene embarazo en curso
    fecha_modificacion?: string;       // Última modificación
}

type GrupoSanguineo = 'A+' | 'A-' | 'B+' | 'B-' | 'O+' | 'O-' | 'AB+' | 'AB-';

interface AntecedentesPersonales {
    id?: number;
    paciente?: number;
    enfermedades_previas?: string;
    cirugias_previas?: string;
    hospitalizaciones?: string;
    medicamentos_actuales?: string;
    alergias?: string;
    transfusiones?: boolean;
    detalles_transfusiones?: string;
    antecedentes_medicos?: string;
    habitos?: string;
    fuma?: boolean;
    alcohol?: boolean;
    drogas?: boolean;
    observaciones?: string;
    created_at?: string;
    updated_at?: string;
}

interface AntecedentesFamiliares {
    id?: number;
    paciente?: number;
    diabetes?: boolean;
    hipertension?: boolean;
    cancer?: boolean;
    tipo_cancer?: string;
    enfermedades_autoinmunes?: boolean;
    enfermedades_cardiacas?: boolean;
    enfermedades_mentales?: boolean;
    enfermedades_geneticas?: boolean;
    otros?: string;
    observaciones?: string;
    created_at?: string;
    updated_at?: string;
}

interface AntecedentesObstetricos {
    id?: number;
    paciente?: number;
    gestas?: number;
    partos?: number;
    cesareas?: number;
    abortos?: number;
    hijos_vivos?: number;
    hijos_muertos?: number;
    formula_obstetrica?: string;
    fecha_ultimo_parto?: string;
    complicaciones_embarazos_previos?: string;
    tipo_parto_habitual?: 'vaginal' | 'cesarea' | 'mixto';
    observaciones?: string;
    created_at?: string;
    updated_at?: string;
}

interface AntecedentesGinecologicos {
    id?: number;
    paciente?: number;
    fecha_ultima_menstruacion?: string;
    edad_menarquia?: number;
    ciclo_menstrual_regular?: boolean;
    duracion_ciclo?: number;
    duracion_menstruacion?: number;
    dismenorrea?: boolean;
    metodo_anticonceptivo?: string;
    papanicolaou_ultimo?: string;
    resultado_papanicolaou?: string;
    mamografia_ultima?: string;
    resultado_mamografia?: string;
    cirugias_ginecologicas?: string;
    enfermedades_ginecologicas?: string;
    observaciones?: string;
    created_at?: string;
    updated_at?: string;
}

interface HistorialClinico {
    paciente: Paciente;
    antecedentes_personales?: AntecedentesPersonales;
    antecedentes_familiares?: AntecedentesFamiliares;
    antecedentes_obstetricos?: AntecedentesObstetricos;
    antecedentes_ginecologicos?: AntecedentesGinecologicos;
    embarazos?: any[];
    controles?: any[];
    ecografias?: any[];
    examenes?: any[];
    citas?: any[];
    partos?: any[];
    evoluciones?: any[];
}

interface EstadisticasPaciente {
    total_embarazos: number;
    embarazos_activos: number;
    total_controles: number;
    total_ecografias: number;
    total_examenes: number;
    total_citas: number;
    total_partos: number;
    ultimo_control?: any;
    proxima_cita?: any;
    tiene_alergias: boolean;
    nivel_riesgo?: 'bajo' | 'medio' | 'alto';
}

interface FiltrosPaciente {
    search?: string;
    genero?: string;
    grupo_sanguineo?: GrupoSanguineo;
    tiene_embarazo_activo?: boolean;
    estado_paciente?: string;
    ciudad?: string;
    activo?: boolean;
    edad_min?: number;
    edad_max?: number;
    fecha_registro_inicio?: string;
    fecha_registro_fin?: string;
    ordering?: string;
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// UTILIDADES INTERNAS
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * Normaliza respuesta de lista (puede venir paginada o no)
 */
function normalizeListResponse<T>(data: any): T[] {
    if (!data) {
        logger.log('⚠️ Respuesta vacía o null');
        return [];
    }
    if (Array.isArray(data)) {
        logger.log(`✓ Respuesta como array directo (${data.length} elementos)`);
        return data;
    }
    if (data.results && Array.isArray(data.results)) {
        logger.log(`✓ Respuesta paginada (${data.results.length} elementos, total: ${data.count})`);
        return data.results;
    }
    if (typeof data === 'object' && Object.keys(data).length === 0) {
        logger.log('⚠️ Respuesta es objeto vacío');
        return [];
    }
    console.warn('⚠️ Formato de respuesta inesperado:', JSON.stringify(data).substring(0, 200));
    return [];
}

/**
 * Normaliza respuesta individual
 */
function normalizeSingleResponse<T>(data: any): T {
    return data || {} as T;
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// SERVICIO DE PACIENTES
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

const pacientesService = {

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // CRUD BÁSICO
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    /**
     * Lista todos los pacientes con filtros opcionales
     * Obtiene TODOS los pacientes iterando por todas las páginas
     */
    async listar(filtros?: FiltrosPaciente): Promise<Paciente[]> {
        try {
            const firstParams = { ...filtros, page: 1 };
            const firstResponse = await api.get('/pacientes/', { params: firstParams });
            const firstData: any = firstResponse.data;
            let allPacientes = normalizeListResponse<Paciente>(firstData);

            const pageSize = firstData.results?.length || allPacientes.length || 1;
            const pageCount = firstData?.count ? Math.ceil(firstData.count / pageSize) : 1;

            if (pageCount > 1) {
                const pageRequests = Array.from({ length: pageCount - 1 }, (_, i) =>
                    api.get('/pacientes/', { params: { ...filtros, page: i + 2 } })
                );
                const responses = await Promise.all(pageRequests);
                for (const response of responses) {
                    const data: any = response.data;
                    const pacientes = normalizeListResponse<Paciente>(data);
                    allPacientes = allPacientes.concat(pacientes);
                }
            }

            logger.log(`✅ ${allPacientes.length} pacientes obtenidos`);
            return allPacientes;
        } catch (error: any) {
            console.error('❌ Error listando pacientes:', error);
            throw error;
        }
    },

    /**
     * Obtiene todos los pacientes (alias de listar)
     */
    async getAll(filtros?: FiltrosPaciente): Promise<Paciente[]> {
        return this.listar(filtros);
    },

    /**
     * Obtiene un paciente por ID
     */
    async obtener(id: number): Promise<Paciente> {
        try {
            const response = await api.get(`/pacientes/${id}/`);
            logger.log(`✅ Paciente ${id} obtenido`);
            return normalizeSingleResponse<Paciente>(response.data);
        } catch (error: any) {
            console.error(`❌ Error obteniendo paciente ${id}:`, error);
            throw error;
        }
    },

    /**
     * Obtiene paciente por ID (alias de obtener)
     */
    async getById(id: number): Promise<Paciente> {
        return this.obtener(id);
    },

    /**
     * Crea un nuevo paciente
     */
    async crear(data: Partial<Paciente>): Promise<Paciente> {
        try {
            // Validar datos antes de enviar
            this.validarDatosPaciente(data);

            const response = await api.post('/pacientes/', data);
            logger.log('✅ Paciente creado exitosamente');
            return normalizeSingleResponse<Paciente>(response.data);
        } catch (error: any) {
            console.error('❌ Error creando paciente:', error);
            throw error;
        }
    },

    /**
     * Crea paciente (alias de crear)
     */
    async create(data: Partial<Paciente>): Promise<Paciente> {
        return this.crear(data);
    },

    /**
     * Actualiza un paciente existente
     */
    async actualizar(id: number, data: Partial<Paciente>): Promise<Paciente> {
        try {
            const response = await api.patch(`/pacientes/${id}/`, data);
            logger.log(`✅ Paciente ${id} actualizado`);
            return normalizeSingleResponse<Paciente>(response.data);
        } catch (error: any) {
            console.error(`❌ Error actualizando paciente ${id}:`, error);
            throw error;
        }
    },

    /**
     * Actualiza paciente (alias de actualizar)
     */
    async update(id: number, data: Partial<Paciente>): Promise<Paciente> {
        return this.actualizar(id, data);
    },

    /**
     * Elimina un paciente (soft delete)
     */
    async eliminar(id: number): Promise<void> {
        try {
            await api.delete(`/pacientes/${id}/`);
            logger.log(`✅ Paciente ${id} eliminado`);
        } catch (error: any) {
            console.error(`❌ Error eliminando paciente ${id}:`, error);
            throw error;
        }
    },

    /**
     * Elimina paciente (alias de eliminar)
     */
    async delete(id: number): Promise<void> {
        return this.eliminar(id);
    },

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // BÚSQUEDAS ESPECÍFICAS
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    /**
     * Busca pacientes por nombre o cédula
     */
    async buscar(termino: string): Promise<Paciente[]> {
        return this.listar({ search: termino });
    },

    /**
     * Busca paciente por cédula
     */
    async buscarPorCedula(cedula: string): Promise<Paciente | null> {
        try {
            const response = await api.get('/pacientes/buscar-por-cedula/', {
                params: { cedula }
            });
            return response.data;
        } catch (error: any) {
            if (error.response?.status === 404) {
                return null;
            }
            console.error('❌ Error buscando por cédula:', error);
            throw error;
        }
    },

    /**
     * Busca paciente por ID clínico
     */
    async buscarPorIdClinico(idClinico: string): Promise<Paciente | null> {
        try {
            const response = await api.get('/pacientes/buscar-por-id-clinico/', {
                params: { id_clinico: idClinico }
            });
            return response.data;
        } catch (error: any) {
            if (error.response?.status === 404) {
                return null;
            }
            console.error('❌ Error buscando por ID clínico:', error);
            throw error;
        }
    },

    /**
     * Obtiene pacientes con embarazo activo
     */
    async obtenerConEmbarazoActivo(): Promise<Paciente[]> {
        return this.listar({ tiene_embarazo_activo: true });
    },

    /**
     * Obtiene pacientes por grupo sanguíneo
     */
    async obtenerPorGrupoSanguineo(grupo: GrupoSanguineo): Promise<Paciente[]> {
        return this.listar({ grupo_sanguineo: grupo });
    },

    /**
     * Obtiene pacientes por ciudad
     */
    async obtenerPorCiudad(ciudad: string): Promise<Paciente[]> {
        return this.listar({ ciudad });
    },

    /**
     * Obtiene pacientes por rango de edad
     */
    async obtenerPorRangoEdad(edadMin: number, edadMax: number): Promise<Paciente[]> {
        return this.listar({ edad_min: edadMin, edad_max: edadMax });
    },

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // ANTECEDENTES
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    /**
     * Obtiene antecedentes personales
     */
    async obtenerAntecedentesPersonales(pacienteId: number): Promise<AntecedentesPersonales | null> {
        try {
            const response = await api.get(
                `/pacientes/${pacienteId}/antecedentes-personales/`
            );
            return response.data;
        } catch (error: any) {
            if (error.response?.status === 404) return null;
            console.error('❌ Error obteniendo antecedentes personales:', error);
            throw error;
        }
    },

    /**
     * Crea/actualiza antecedentes personales
     */
    async guardarAntecedentesPersonales(
        pacienteId: number,
        data: Partial<AntecedentesPersonales>
    ): Promise<AntecedentesPersonales> {
        try {
            const response = await api.post(
                `/pacientes/${pacienteId}/antecedentes-personales/`,
                data
            );
            logger.log('✅ Antecedentes personales guardados');
            return response.data;
        } catch (error: any) {
            console.error('❌ Error guardando antecedentes personales:', error);
            throw error;
        }
    },

    /**
     * Obtiene antecedentes familiares
     */
    async obtenerAntecedentesFamiliares(pacienteId: number): Promise<AntecedentesFamiliares | null> {
        try {
            const response = await api.get(
                `/pacientes/${pacienteId}/antecedentes-familiares/`
            );
            return response.data;
        } catch (error: any) {
            if (error.response?.status === 404) return null;
            console.error('❌ Error obteniendo antecedentes familiares:', error);
            throw error;
        }
    },

    /**
     * Crea/actualiza antecedentes familiares
     */
    async guardarAntecedentesFamiliares(
        pacienteId: number,
        data: Partial<AntecedentesFamiliares>
    ): Promise<AntecedentesFamiliares> {
        try {
            const response = await api.post(
                `/pacientes/${pacienteId}/antecedentes-familiares/`,
                data
            );
            logger.log('✅ Antecedentes familiares guardados');
            return response.data;
        } catch (error: any) {
            console.error('❌ Error guardando antecedentes familiares:', error);
            throw error;
        }
    },

    /**
     * Obtiene antecedentes obstétricos
     */
    async obtenerAntecedentesObstetricos(pacienteId: number): Promise<AntecedentesObstetricos | null> {
        try {
            const response = await api.get(
                `/pacientes/${pacienteId}/antecedentes-obstetricos/`
            );
            return response.data;
        } catch (error: any) {
            if (error.response?.status === 404) return null;
            console.error('❌ Error obteniendo antecedentes obstétricos:', error);
            throw error;
        }
    },

    /**
     * Crea/actualiza antecedentes obstétricos
     */
    async guardarAntecedentesObstetricos(
        pacienteId: number,
        data: Partial<AntecedentesObstetricos>
    ): Promise<AntecedentesObstetricos> {
        try {
            const response = await api.post(
                `/pacientes/${pacienteId}/antecedentes-obstetricos/`,
                data
            );
            logger.log('✅ Antecedentes obstétricos guardados');
            return response.data;
        } catch (error: any) {
            console.error('❌ Error guardando antecedentes obstétricos:', error);
            throw error;
        }
    },

    /**
     * Obtiene antecedentes ginecológicos
     */
    async obtenerAntecedentesGinecologicos(pacienteId: number): Promise<AntecedentesGinecologicos | null> {
        try {
            const response = await api.get(
                `/pacientes/${pacienteId}/antecedentes-ginecologicos/`
            );
            return response.data;
        } catch (error: any) {
            if (error.response?.status === 404) return null;
            console.error('❌ Error obteniendo antecedentes ginecológicos:', error);
            throw error;
        }
    },

    /**
     * Crea/actualiza antecedentes ginecológicos
     */
    async guardarAntecedentesGinecologicos(
        pacienteId: number,
        data: Partial<AntecedentesGinecologicos>
    ): Promise<AntecedentesGinecologicos> {
        try {
            const response = await api.post(
                `/pacientes/${pacienteId}/antecedentes-ginecologicos/`,
                data
            );
            logger.log('✅ Antecedentes ginecológicos guardados');
            return response.data;
        } catch (error: any) {
            console.error('❌ Error guardando antecedentes ginecológicos:', error);
            throw error;
        }
    },

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // HISTORIAL CLÍNICO COMPLETO
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    /**
     * Obtiene historial clínico completo del paciente
     */
    async obtenerHistorialCompleto(pacienteId: number): Promise<HistorialClinico> {
        try {
            const response = await api.get(
                `/pacientes/${pacienteId}/historial-completo/`
            );
            return response.data;
        } catch (error: any) {
            console.error('❌ Error obteniendo historial completo:', error);
            throw error;
        }
    },

    /**
     * Obtiene historial clínico (alias)
     */
    async getHistoriaClinica(pacienteId: number): Promise<Blob> {
        return this.generarReportePDF(pacienteId);
    },

    /**
     * Obtiene resumen de embarazos del paciente
     */
    async obtenerEmbarazos(pacienteId: number): Promise<any[]> {
        try {
            const response = await api.get(`/pacientes/${pacienteId}/embarazos/`);
            return normalizeListResponse(response.data);
        } catch (error: any) {
            console.error('❌ Error obteniendo embarazos:', error);
            throw error;
        }
    },

    /**
     * Alias para compatibilidad
     */
    async getEmbarazos(pacienteId: number): Promise<any[]> {
        return this.obtenerEmbarazos(pacienteId);
    },

    /**
     * Obtiene controles prenatales del paciente
     */
    async obtenerControles(pacienteId: number): Promise<any[]> {
        try {
            const response = await api.get(`/pacientes/${pacienteId}/controles/`);
            return normalizeListResponse(response.data);
        } catch (error: any) {
            console.error('❌ Error obteniendo controles:', error);
            throw error;
        }
    },

    /**
     * Obtiene ecografías del paciente
     */
    async obtenerEcografias(pacienteId: number): Promise<any[]> {
        try {
            const response = await api.get(`/pacientes/${pacienteId}/ecografias/`);
            return normalizeListResponse(response.data);
        } catch (error: any) {
            console.error('❌ Error obteniendo ecografías:', error);
            throw error;
        }
    },

    /**
     * Obtiene exámenes de laboratorio del paciente
     */
    async obtenerExamenesLaboratorio(pacienteId: number): Promise<any[]> {
        try {
            const response = await api.get(`/pacientes/${pacienteId}/examenes-laboratorio/`);
            return normalizeListResponse(response.data);
        } catch (error: any) {
            console.error('❌ Error obteniendo exámenes:', error);
            throw error;
        }
    },

    /**
     * Obtiene citas del paciente
     */
    async obtenerCitas(pacienteId: number): Promise<any[]> {
        try {
            const response = await api.get(`/pacientes/${pacienteId}/citas/`);
            return normalizeListResponse(response.data);
        } catch (error: any) {
            console.error('❌ Error obteniendo citas:', error);
            throw error;
        }
    },

    /**
     * Obtiene partos del paciente
     */
    async obtenerPartos(pacienteId: number): Promise<any[]> {
        try {
            const response = await api.get(`/pacientes/${pacienteId}/partos/`);
            return normalizeListResponse(response.data);
        } catch (error: any) {
            console.error('❌ Error obteniendo partos:', error);
            throw error;
        }
    },

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // ESTADÍSTICAS Y ANÁLISIS
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    /**
     * Obtiene estadísticas del paciente
     */
    async obtenerEstadisticas(pacienteId: number): Promise<EstadisticasPaciente> {
        try {
            const response = await api.get(
                `/pacientes/${pacienteId}/estadisticas/`
            );
            return response.data;
        } catch (error: any) {
            console.error('❌ Error obteniendo estadísticas:', error);
            throw error;
        }
    },

    /**
     * Evalúa factores de riesgo del paciente
     */
    async evaluarFactoresRiesgo(pacienteId: number): Promise<{
        nivel_riesgo: string;
        factores: string[];
        recomendaciones: string[];
    }> {
        try {
            const response = await api.get(`/pacientes/${pacienteId}/evaluar-riesgos/`);
            return response.data;
        } catch (error: any) {
            console.error('❌ Error evaluando riesgos:', error);
            throw error;
        }
    },

    /**
     * Calcula IMC del paciente
     */
    calcularIMC(peso_kg: number, talla_cm: number): {
        imc: number;
        clasificacion: string;
        riesgo: string;
    } {
        const talla_m = talla_cm / 100;
        const imc = peso_kg / (talla_m * talla_m);

        let clasificacion: string;
        let riesgo: string;

        if (imc < 18.5) {
            clasificacion = 'Bajo peso';
            riesgo = 'Aumentado';
        } else if (imc < 25) {
            clasificacion = 'Peso normal';
            riesgo = 'Promedio';
        } else if (imc < 30) {
            clasificacion = 'Sobrepeso';
            riesgo = 'Aumentado';
        } else if (imc < 35) {
            clasificacion = 'Obesidad grado I';
            riesgo = 'Alto';
        } else if (imc < 40) {
            clasificacion = 'Obesidad grado II';
            riesgo = 'Muy alto';
        } else {
            clasificacion = 'Obesidad grado III';
            riesgo = 'Extremadamente alto';
        }

        return { imc: parseFloat(imc.toFixed(2)), clasificacion, riesgo };
    },

    /**
     * Calcula edad de la paciente
     */
    calcularEdad(fechaNacimiento: string): number {
        const hoy = new Date();
        const nacimiento = new Date(fechaNacimiento);
        let edad = hoy.getFullYear() - nacimiento.getFullYear();
        const mes = hoy.getMonth() - nacimiento.getMonth();

        if (mes < 0 || (mes === 0 && hoy.getDate() < nacimiento.getDate())) {
            edad--;
        }

        return edad;
    },

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // REPORTES Y EXPORTACIÓN
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    /**
     * Genera reporte médico completo en PDF
     */
    async generarReportePDF(pacienteId: number): Promise<Blob> {
        try {
            const response = await api.get(`/pacientes/${pacienteId}/reporte-pdf/`, {
                responseType: 'blob'
            });
            logger.log(`✅ PDF del paciente ${pacienteId} generado`);
            return response.data;
        } catch (error: any) {
            console.error('❌ Error generando PDF:', error);
            throw error;
        }
    },

    /**
     * Exporta historia clínica completa a Excel
     */
    async exportarHistorialExcel(pacienteId: number): Promise<Blob> {
        try {
            const response = await api.get(`/pacientes/${pacienteId}/exportar-excel/`, {
                responseType: 'blob'
            });
            logger.log(`✅ Excel exportado para paciente ${pacienteId}`);
            return response.data;
        } catch (error: any) {
            console.error('❌ Error exportando Excel:', error);
            throw error;
        }
    },

    /**
     * Exporta lista de pacientes a Excel
     */
    async exportarListaExcel(filtros?: any): Promise<Blob> {
        try {
            const response = await api.get('/pacientes/exportar-excel/', {
                params: filtros,
                responseType: 'blob'
            });
            logger.log('✅ Lista de pacientes exportada');
            return response.data;
        } catch (error: any) {
            console.error('❌ Error exportando lista:', error);
            throw error;
        }
    },

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // VALIDACIONES
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    /**
     * Valida datos del paciente antes de crear/actualizar
     */
    validarDatosPaciente(data: Partial<Paciente>): {
        valido: boolean;
        errores: string[];
    } {
        const errores: string[] = [];

        // Validar nombre
        if (data.nombre && data.nombre.trim().length < 2) {
            errores.push('El nombre debe tener al menos 2 caracteres');
        }

        // Validar apellidos
        if (data.apellido_paterno && data.apellido_paterno.trim().length < 2) {
            errores.push('El apellido paterno debe tener al menos 2 caracteres');
        }

        // Validar cédula
        if (data.ci) {
            if (!this.validarCedula(data.ci)) {
                errores.push('Formato de cédula inválido');
            }
        }

        // Validar teléfono
        if (data.telefono) {
            if (!this.validarTelefono(data.telefono)) {
                errores.push('Formato de teléfono inválido');
            }
        }

        // Validar email
        if (data.email) {
            if (!this.validarEmail(data.email)) {
                errores.push('Formato de email inválido');
            }
        }

        // Validar fecha de nacimiento
        if (data.fecha_nacimiento) {
            const edad = this.calcularEdad(data.fecha_nacimiento);
            if (edad < 10) {
                errores.push('El paciente debe tener al menos 10 años');
            }
            if (edad > 100) {
                errores.push('Fecha de nacimiento inválida');
            }
        }

        return {
            valido: errores.length === 0,
            errores
        };
    },

    /**
     * Valida formato de cédula boliviana
     */
    validarCedula(cedula: string): boolean {
        // Remover espacios y guiones
        const ci = cedula.replace(/[\s-]/g, '');
        // Validar que sean solo números y longitud
        return /^\d{5,10}$/.test(ci);
    },

    /**
     * Valida formato de teléfono boliviano
     */
    validarTelefono(telefono: string): boolean {
        // Remover espacios, guiones y paréntesis
        const tel = telefono.replace(/[\s-()]/g, '');
        // Validar que sean solo números y longitud
        return /^\d{7,8}$/.test(tel);
    },

    /**
     * Valida formato de email
     */
    validarEmail(email: string): boolean {
        const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return regex.test(email);
    },

};

export { pacientesService };
export default pacientesService;
