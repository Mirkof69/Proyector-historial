export interface Mensaje {
  id: string;
  tipo: 'usuario' | 'ia' | 'sistema';
  contenido: string;
  timestamp: Date;
  categoria?: 'analisis' | 'recomendacion' | 'alerta' | 'informacion';
  /** De dónde sale la respuesta: la base de conocimiento del servicio, o nada (sin conexión). */
  fuente?: 'base_conocimiento' | 'sin_conexion';
  /** Tema que reconoció la base de conocimiento (preeclampsia, rciu, …). */
  tema?: string;
  consultaId?: number; // ID de la consulta en el backend
  tiempoRespuesta?: number; // Tiempo de respuesta en ms
  contextoSistema?: string; // Contexto inyectado para la IA (no visible)
}

/** Clave del historial en el navegador. Antes «limpiar» borraba otra clave y el historial volvía. */
export const CLAVE_HISTORIAL = 'ia_chat_history:v1';

/**
 * El asistente NO es un modelo entrenado: el servicio busca palabras clave en
 * una base de conocimiento obstétrica escrita a mano (servicio-ia,
 * app/routes.py, /api/consultar) y devuelve el texto de ese tema. Se dice así
 * en la bienvenida para que nadie lo tome por una red con una exactitud medida.
 */
export const crearMensajeBienvenida = (): Mensaje => ({
  id: `ia-${Date.now()}`,
  tipo: 'ia',
  contenido: `Asistente de consulta obstétrica.

Responde con una base de conocimiento escrita a partir de guías clínicas: reconoce el tema por palabras clave (preeclampsia, RCIU, diabetes gestacional, laboratorio, edad gestacional, ecografía, parto, emergencia). No es un modelo entrenado y no tiene una exactitud medida.

Los modelos entrenados (ecografía, ginecología, cardiotocografía) se usan desde «Análisis CNN (IA)»; qué hace cada uno y cuánto acierta está en «Guía de IA».`,
  timestamp: new Date(),
  categoria: 'informacion',
});

export const loadInitialMessages = (): Mensaje[] => {
  try {
    const savedMessages = localStorage.getItem(CLAVE_HISTORIAL);
    if (savedMessages) {
      const parsed = JSON.parse(savedMessages);
      if (Array.isArray(parsed) && parsed.length > 0) {
        return parsed.map((m: any) => ({
          ...m,
          timestamp: new Date(m.timestamp),
        }));
      }
    }
  } catch (e) {
    // Historial ilegible o almacenamiento bloqueado: se empieza de cero.
  }
  return [crearMensajeBienvenida()];
};

/**
 * Respuesta cuando el servicio no contesta. Antes devolvía textos clínicos con
 * «Confianza: 92 %», «95 %» o «98 %» inventados y la presentaba como si fuera
 * una respuesta de la IA. Ahora dice lo que pasó y no inventa nada.
 */
export const procesarConsultaLocal = (consulta: string): string =>
  `No se pudo consultar el asistente: el servicio de IA no respondió, así que no hay respuesta para «${consulta.trim()}».

Vuelva a intentarlo en unos minutos. Mientras tanto, las calculadoras clínicas y las guías del menú «Herramientas» funcionan sin el servicio de IA.`;
