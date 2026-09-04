/**
 * Tests del servicio que conecta el frontend con el modelo FMF del servidor.
 *
 * Por qué importan
 * ----------------
 * El backend tenía el modelo bayesiano de la FMF escrito y sin que ninguna
 * pantalla pudiera llegar a él. Estos tests fijan el contrato de la conexión:
 * a qué ruta llama cada cálculo y qué se envía. Si alguien renombra un
 * endpoint, la calculadora no se queda en silencio.
 *
 * Cada caso declara el resultado ESPERADO y lo compara con el OBTENIDO.
 */

import apiClient from './api';
import { riesgoFmfService } from './riesgoFmfService';

jest.mock('./api', () => ({
  __esModule: true,
  default: { post: jest.fn() },
}));

const postSimulado = apiClient.post as jest.Mock;

describe('riesgoFmfService', () => {
  beforeEach(() => {
    postSimulado.mockReset();
  });

  describe('calcularPreeclampsia', () => {
    it('llama a la ruta del modelo FMF del servidor', async () => {
      postSimulado.mockResolvedValue({ data: { riesgo_final: 0.03, requiere_aspirina: true } });

      await riesgoFmfService.calcularPreeclampsia({
        edad_materna: 35, peso_kg: 72, talla_cm: 158, semanas: 12,
      });

      // ESPERADO: la ruta del backend, no un cálculo en el navegador.
      expect(postSimulado).toHaveBeenCalledWith(
        '/calculadoras-avanzadas/fmf/preeclampsia/',
        expect.objectContaining({ edad_materna: 35, semanas: 12 }),
      );
    });

    it('funciona sin biomarcadores', async () => {
      postSimulado.mockResolvedValue({ data: { riesgo_final: 0.01, requiere_aspirina: false } });

      // ESPERADO: no lanza. Es el caso de una clínica sin laboratorio
      // especializado, que es la razón de conectar este modelo y no el del
      // navegador, que exige PlGF, sFlt-1, PAPP-A, MAP y Doppler.
      const r = await riesgoFmfService.calcularPreeclampsia({
        edad_materna: 25, peso_kg: 58, talla_cm: 162, semanas: 12,
      });

      expect(r.requiere_aspirina).toBe(false);
    });

    it('devuelve el resultado tal como lo da el servidor', async () => {
      const delServidor = {
        riesgo_final: 0.085,
        clasificacion_riesgo: 'ALTO',
        requiere_aspirina: true,
        factores_riesgo_presentes: ['Hipertensión crónica'],
        recomendaciones: ['Aspirina 150 mg/noche desde la semana 12'],
      };
      postSimulado.mockResolvedValue({ data: delServidor });

      const r = await riesgoFmfService.calcularPreeclampsia({
        edad_materna: 40, peso_kg: 90, talla_cm: 155, semanas: 12,
        hipertension_cronica: true,
      });

      // ESPERADO: sin transformar. El cálculo clínico vive en el servidor;
      // el frontend no puede reinterpretarlo por su cuenta.
      expect(r).toEqual(delServidor);
    });
  });

  describe('calcularTrisomias', () => {
    it('llama a la ruta del cribado combinado', async () => {
      postSimulado.mockResolvedValue({ data: { riesgo_t21_ajustado: 1 / 250 } });

      await riesgoFmfService.calcularTrisomias({
        edad_materna: 38, semanas: 12, translucencia_nucal_mm: 3.2,
      });

      expect(postSimulado).toHaveBeenCalledWith(
        '/calculadoras-avanzadas/fmf/trisomias/',
        expect.objectContaining({ translucencia_nucal_mm: 3.2 }),
      );
    });

    it('envía los marcadores adicionales cuando se tienen', async () => {
      postSimulado.mockResolvedValue({ data: {} });

      await riesgoFmfService.calcularTrisomias({
        edad_materna: 38, semanas: 12, translucencia_nucal_mm: 3.2,
        papp_a_mom: 0.4, free_bhcg_mom: 2.5, hueso_nasal_presente: false,
      });

      // ESPERADO: llegan al servidor; son los que refinan el riesgo.
      expect(postSimulado).toHaveBeenCalledWith(
        '/calculadoras-avanzadas/fmf/trisomias/',
        expect.objectContaining({ papp_a_mom: 0.4, hueso_nasal_presente: false }),
      );
    });
  });

  describe('analizarLaboratorio', () => {
    it('envía solo los paneles que se tienen', async () => {
      postSimulado.mockResolvedValue({ data: { hemograma: { alertas: [] } } });

      await riesgoFmfService.analizarLaboratorio({
        hemograma: { hemoglobina: 9.2, plaquetas: 95000 },
      });

      // ESPERADO: no se inventan paneles vacíos; el servidor rechaza
      // una petición sin ningún panel.
      expect(postSimulado).toHaveBeenCalledWith(
        '/ia/laboratorio/analizar/',
        { hemograma: { hemoglobina: 9.2, plaquetas: 95000 } },
      );
    });

    it('devuelve un bloque por cada panel enviado', async () => {
      postSimulado.mockResolvedValue({
        data: {
          hemograma: { alertas: ['Anemia moderada'], valores_anormales: [], patologias_detectadas: [], recomendaciones: [] },
          glucosa: { alertas: [], valores_anormales: [], patologias_detectadas: [], recomendaciones: [] },
        },
      });

      const r = await riesgoFmfService.analizarLaboratorio({
        hemograma: { hemoglobina: 9.2 },
        glucosa: { glucosa_ayunas: 105 },
      });

      expect(Object.keys(r)).toEqual(['hemograma', 'glucosa']);
      expect(r.hemograma?.alertas).toContain('Anemia moderada');
    });
  });
});
