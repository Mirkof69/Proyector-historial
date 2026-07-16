/**
 * =============================================================================
 * SERVICIO DE ANTECEDENTES MÉDICOS
 * =============================================================================
 * Gestión de antecedentes gineco-obstétricos y patológicos
 * =============================================================================
 */

import api from './api';
import { logger } from '../utils/logger';

export interface AntecedenteGinecoObstetrico {
    id: number;
    paciente: number;
    paciente_info?: {
        id: number;
        nombre_completo: string;
        id_clinico: string;
        ci: string;
    };

    // Menstruación
    menarquia_edad?: number;
    ciclos_menstruales?: string; // 'regular' | 'irregular' | 'amenorrea'
    duracion_ciclo_dias?: number;
    duracion_menstruacion_dias?: number;
    fecha_ultima_menstruacion?: string;

    // Fórmula Obstétrica (GPAC)
    gestas: number; // G: número total de embarazos
    partos: number; // P: número de partos
    abortos: number; // A: número de abortos
    cesareas: number; // C: número de cesáreas
    hijos_vivos: number;

    // Anticoncepción
    metodo_anticonceptivo_actual?: string;
    tiempo_uso_anticonceptivo_meses?: number;
    fecha_suspension_anticonceptivo?: string;

    // Vida sexual
    inicio_vida_sexual_edad?: number;
    numero_parejas_sexuales?: number;

    // Calculados
    formula_obstetrica?: string;
    edad_menarquia_texto?: string;

    // Metadata
    fecha_registro?: string;
    fecha_modificacion?: string;
    modificado_por?: number;
    modificado_por_info?: {
        id: number;
        nombre: string;
        email: string;
    };
}

export interface AntecedentePatologico {
    id: number;
    paciente: number;
    paciente_info?: {
        id: number;
        nombre_completo: string;
        id_clinico: string;
    };

    // Tipo de Antecedente
    tipo: 'personal' | 'heredofamiliar';

    // Alergias (CRÍTICO)
    tiene_alergias: boolean;
    alergias_medicamentos?: string;
    alergias_alimentos?: string;
    alergias_otras?: string;

    // Enfermedades crónicas - Endocrinas
    diabetes: boolean;
    diabetes_tipo?: 'tipo1' | 'tipo2' | 'gestacional';

    // Cardiovasculares
    hipertension: boolean;
    cardiopatias: boolean;
    cardiopatia_detalle?: string;

    // Renales
    nefropatias: boolean;
    nefropatia_detalle?: string;

    // Hematológicas
    trastornos_coagulacion: boolean;
    anemia: boolean;

    // Autoinmunes
    lupus: boolean;
    artritis_reumatoide: boolean;

    // Respiratorias
    asma: boolean;

    // Antecedentes obstétricos específicos
    preeclampsia_previa: boolean;
    eclampsia_previa: boolean;
    diabetes_gestacional_previa: boolean;
    hemorragia_postparto_previa: boolean;

    // Otros
    otras_enfermedades?: string;
    cirugias_anteriores?: string;

    // Calculados
    tiene_factores_riesgo_calculado?: boolean;
    resumen_enfermedades?: string[];

    // Metadata
    fecha_registro?: string;
    fecha_modificacion?: string;
    registrado_por?: number;
    registrado_por_info?: {
        id: number;
        nombre: string;
        email: string;
    };
}

class AntecedentesService {
    private baseUrl = '/antecedentes';

    private normalizeListResponse<T>(raw: any): T[] {
        if (raw?.results) return raw.results;
        if (raw?.data) return raw.data;
        if (Array.isArray(raw)) return raw;
        return [];
    }

    // ═════════════════════════════════════════════════════════════════════
    // ANTECEDENTES GINECO-OBSTÉTRICOS
    // ═════════════════════════════════════════════════════════════════════

    /**
     * Alias para listar antecedentes (compatibilidad con componentes legacy)
     */
    async listar(pacienteId?: number): Promise<AntecedenteGinecoObstetrico[]> {
        return this.getGinecoObstetricos(pacienteId);
    }

    /**
     * Alias para crear antecedente (compatibilidad con componentes legacy)
     */
    async crear(data: Partial<AntecedenteGinecoObstetrico>): Promise<AntecedenteGinecoObstetrico> {
        return this.createGinecoObstetrico(data);
    }

    /**
     * Alias para actualizar antecedente (compatibilidad con componentes legacy)
     */
    async actualizar(id: number, data: Partial<AntecedenteGinecoObstetrico>): Promise<AntecedenteGinecoObstetrico> {
        return this.updateGinecoObstetrico(id, data);
    }

    /**
     * Alias para eliminar antecedente (compatibilidad con componentes legacy)
     */
    async eliminar(id: number): Promise<void> {
        return this.deleteGinecoObstetrico(id);
    }

    /**
     * Alias para obtener antecedente por ID (compatibilidad con componentes legacy)
     */
    async obtener(id: number): Promise<AntecedenteGinecoObstetrico> {
        return this.getGinecoObstetricoById(id);
    }

    /**
     * Alias para obtener antecedente por paciente (compatibilidad con componentes legacy)
     */
    async getByPaciente(pacienteId: number): Promise<AntecedenteGinecoObstetrico | null> {
        return this.getGinecoObstetricoByPaciente(pacienteId);
    }

    async getGinecoObstetricos(pacienteId?: number): Promise<AntecedenteGinecoObstetrico[]> {
        try {
            const url = pacienteId
                ? `${this.baseUrl}/gineco-obstetricos/?paciente=${pacienteId}`
                : `${this.baseUrl}/gineco-obstetricos/`;
            const response = await api.get<any>(url);
            return this.normalizeListResponse<AntecedenteGinecoObstetrico>(response.data);
        } catch (error: any) {
            console.error('❌ Error obteniendo antecedentes gineco-obstétricos:', error);
            throw error;
        }
    }

    async getGinecoObstetricoById(id: number): Promise<AntecedenteGinecoObstetrico> {
        try {
            const response = await api.get<AntecedenteGinecoObstetrico>(`${this.baseUrl}/gineco-obstetricos/${id}/`);
            return response.data;
        } catch (error: any) {
            console.error(`❌ Error obteniendo antecedente gineco-obstétrico ${id}:`, error);
            throw error;
        }
    }

    async getGinecoObstetricoByPaciente(pacienteId: number): Promise<AntecedenteGinecoObstetrico | null> {
        try {
            const antecedentes = await this.getGinecoObstetricos(pacienteId);
            return antecedentes.length > 0 ? antecedentes[0] : null;
        } catch (error: any) {
            console.error(`❌ Error obteniendo antecedente gineco-obstétrico del paciente ${pacienteId}:`, error);
            return null;
        }
    }

    async createGinecoObstetrico(data: Partial<AntecedenteGinecoObstetrico>): Promise<AntecedenteGinecoObstetrico> {
        try {
            const response = await api.post<AntecedenteGinecoObstetrico>(`${this.baseUrl}/gineco-obstetricos/`, data);
            logger.log('✅ Antecedente gineco-obstétrico creado');
            return response.data;
        } catch (error: any) {
            console.error('❌ Error creando antecedente gineco-obstétrico:', error);
            throw error;
        }
    }

    async updateGinecoObstetrico(
        id: number,
        data: Partial<AntecedenteGinecoObstetrico>
    ): Promise<AntecedenteGinecoObstetrico> {
        try {
            const response = await api.put<AntecedenteGinecoObstetrico>(`${this.baseUrl}/gineco-obstetricos/${id}/`, data);
            logger.log('✅ Antecedente gineco-obstétrico actualizado');
            return response.data;
        } catch (error: any) {
            console.error(`❌ Error actualizando antecedente gineco-obstétrico ${id}:`, error);
            throw error;
        }
    }

    async partialUpdateGinecoObstetrico(
        id: number,
        data: Partial<AntecedenteGinecoObstetrico>
    ): Promise<AntecedenteGinecoObstetrico> {
        try {
            const response = await api.patch<AntecedenteGinecoObstetrico>(`${this.baseUrl}/gineco-obstetricos/${id}/`, data);
            return response.data;
        } catch (error: any) {
            console.error(`❌ Error en actualización parcial de antecedente gineco-obstétrico ${id}:`, error);
            throw error;
        }
    }

    async deleteGinecoObstetrico(id: number): Promise<void> {
        try {
            await api.delete(`${this.baseUrl}/gineco-obstetricos/${id}/`);
            logger.log('🗑️ Antecedente gineco-obstétrico eliminado:', id);
        } catch (error: any) {
            console.error(`❌ Error eliminando antecedente gineco-obstétrico ${id}:`, error);
            throw error;
        }
    }

    // ═════════════════════════════════════════════════════════════════════
    // ANTECEDENTES PATOLÓGICOS
    // ═════════════════════════════════════════════════════════════════════

    async getPatologicos(pacienteId?: number): Promise<AntecedentePatologico[]> {
        try {
            const url = pacienteId
                ? `${this.baseUrl}/patologicos/?paciente=${pacienteId}`
                : `${this.baseUrl}/patologicos/`;
            const response = await api.get<any>(url);
            return this.normalizeListResponse<AntecedentePatologico>(response.data);
        } catch (error: any) {
            console.error('❌ Error obteniendo antecedentes patológicos:', error);
            throw error;
        }
    }

    async getPatologicoById(id: number): Promise<AntecedentePatologico> {
        try {
            const response = await api.get<AntecedentePatologico>(`${this.baseUrl}/patologicos/${id}/`);
            return response.data;
        } catch (error: any) {
            console.error(`❌ Error obteniendo antecedente patológico ${id}:`, error);
            throw error;
        }
    }

    async getPatologicoByPaciente(pacienteId: number): Promise<AntecedentePatologico | null> {
        try {
            const antecedentes = await this.getPatologicos(pacienteId);
            return antecedentes.length > 0 ? antecedentes[0] : null;
        } catch (error: any) {
            console.error(`❌ Error obteniendo antecedente patológico del paciente ${pacienteId}:`, error);
            return null;
        }
    }

    async createPatologico(data: Partial<AntecedentePatologico>): Promise<AntecedentePatologico> {
        try {
            const response = await api.post<AntecedentePatologico>(`${this.baseUrl}/patologicos/`, data);
            logger.log('✅ Antecedente patológico creado');
            return response.data;
        } catch (error: any) {
            console.error('❌ Error creando antecedente patológico:', error);
            throw error;
        }
    }

    async updatePatologico(id: number, data: Partial<AntecedentePatologico>): Promise<AntecedentePatologico> {
        try {
            const response = await api.put<AntecedentePatologico>(`${this.baseUrl}/patologicos/${id}/`, data);
            logger.log('✅ Antecedente patológico actualizado');
            return response.data;
        } catch (error: any) {
            console.error(`❌ Error actualizando antecedente patológico ${id}:`, error);
            throw error;
        }
    }

    async partialUpdatePatologico(id: number, data: Partial<AntecedentePatologico>): Promise<AntecedentePatologico> {
        try {
            const response = await api.patch<AntecedentePatologico>(`${this.baseUrl}/patologicos/${id}/`, data);
            return response.data;
        } catch (error: any) {
            console.error(`❌ Error en actualización parcial de antecedente patológico ${id}:`, error);
            throw error;
        }
    }

    async deletePatologico(id: number): Promise<void> {
        try {
            await api.delete(`${this.baseUrl}/patologicos/${id}/`);
            logger.log('🗑️ Antecedente patológico eliminado:', id);
        } catch (error: any) {
            console.error(`❌ Error eliminando antecedente patológico ${id}:`, error);
            throw error;
        }
    }

    // ═════════════════════════════════════════════════════════════════════
    // UTILIDADES
    // ═════════════════════════════════════════════════════════════════════

    /**
     * Obtener todos los antecedentes de un paciente
     */
    async getAntecedentesPaciente(pacienteId: number): Promise<{
        ginecoObstetrico: AntecedenteGinecoObstetrico | null;
        patologico: AntecedentePatologico | null;
    }> {
        try {
            const [ginecoObstetrico, patologico] = await Promise.all([
                this.getGinecoObstetricoByPaciente(pacienteId),
                this.getPatologicoByPaciente(pacienteId)
            ]);

            return { ginecoObstetrico, patologico };
        } catch (error: any) {
            console.error(`❌Error obteniendo antecedentes del paciente ${pacienteId}:`, error);
            throw error;
        }
    }

    /**
     * Crear o actualizar antecedente gineco-obstétrico
     */
    async saveGinecoObstetrico(
        pacienteId: number,
        data: Partial<AntecedenteGinecoObstetrico>
    ): Promise<AntecedenteGinecoObstetrico> {
        const existing = await this.getGinecoObstetricoByPaciente(pacienteId);

        if (existing) {
            return this.updateGinecoObstetrico(existing.id, data);
        } else {
            return this.createGinecoObstetrico({ ...data, paciente: pacienteId });
        }
    }

    /**
     * Crear o actualizar antecedente patológico
     */
    async savePatologico(
        pacienteId: number,
        data: Partial<AntecedentePatologico>
    ): Promise<AntecedentePatologico> {
        const existing = await this.getPatologicoByPaciente(pacienteId);

        if (existing) {
            return this.updatePatologico(existing.id, data);
        } else {
            return this.createPatologico({ ...data, paciente: pacienteId });
        }
    }

    /**
     * Formatear fórmula obstétrica (GPAC)
     */
    formatearFormulaObstetrica(antecedente: Partial<AntecedenteGinecoObstetrico>): string {
        const g = antecedente.gestas || 0;
        const p = antecedente.partos || 0;
        const a = antecedente.abortos || 0;
        const c = antecedente.cesareas || 0;

        return `G${g}P${p}A${a}C${c}`;
    }

    /**
     * Calcular riesgo obstétrico
     */
    calcularRiesgoObstetrico(
        ginecoObstetrico: Partial<AntecedenteGinecoObstetrico>,
        patologico: Partial<AntecedentePatologico>
    ): { nivel: 'bajo' | 'medio' | 'alto'; factores: string[] } {
        const factores: string[] = [];
        let puntos = 0;

        // Evaluar antecedentes gineco-obstétricos
        if ((ginecoObstetrico?.abortos || 0) >= 2) {
            factores.push('Múltiples abortos previos');
            puntos += 2;
        }
        if ((ginecoObstetrico.cesareas || 0) >= 2) {
            factores.push('Múltiples cesáreas previas');
            puntos += 2;
        }

        // Evaluar antecedentes patológicos
        if (patologico.hipertension) {
            factores.push('Hipertensión');
            puntos += 2;
        }
        if (patologico.diabetes) {
            factores.push('Diabetes');
            puntos += 2;
        }
        if (patologico.cardiopatias) {
            factores.push('Cardiopatías');
            puntos += 3;
        }
        if (patologico.lupus) {
            factores.push('Lupus');
            puntos += 3;
        }
        if (patologico.preeclampsia_previa) {
            factores.push('Preeclampsia previa');
            puntos += 2;
        }
        if (patologico.eclampsia_previa) {
            factores.push('Eclampsia previa');
            puntos += 3;
        }

        // Determinar nivel de riesgo
        let nivel: 'bajo' | 'medio' | 'alto';
        if (puntos === 0) {
            nivel = 'bajo';
        } else if (puntos <= 3) {
            nivel = 'medio';
        } else {
            nivel = 'alto';
        }

        return { nivel, factores };
    }
}

export const antecedentesService = new AntecedentesService();

