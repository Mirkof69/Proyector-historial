/**
 * Textos de la Guía de IA: qué hace cada modelo, sus límites y dónde se usa.
 *
 * AQUÍ NO VA NINGUNA CIFRA. La fiabilidad de cada modelo (exactitud, error en
 * mm, sensibilidad…) llega del backend (GET /api/ia/imagenes/modelos/), que la
 * lee de las métricas que dejó cada entrenamiento. Así un reentrenamiento
 * cambia la guía sin tocar este archivo, y la guía no puede contradecir a la
 * pestaña «Modelos y métricas». Un test (GuiaIA.test.tsx) comprueba que este
 * archivo no tenga porcentajes ni milímetros.
 */

export type TipoRed = 'cnn' | 'unet' | 'puntos' | 'tabla';
export type Grupo = 'obstetricia' | 'parto' | 'ginecologia' | 'monitoreo' | 'demostracion';

export interface FichaModelo {
  grupo: Grupo;
  red: TipoRed;
  queHace: string;
  limites: string[];
  /** Pantalla donde se usa: la ruta exacta y los pasos para llegar al resultado. */
  donde: { ruta: string; pasos: string };
}

export const RUTA_ECOGRAFIA = '/dashboard/ia-medica/imagenes?pestana=ecografia';
export const RUTA_GINECOLOGIA = '/dashboard/ia-medica/imagenes?pestana=ginecologia';
export const RUTA_CTG = '/dashboard/ia-medica/imagenes?pestana=cardiotocografia';

const PASOS_ANALIZAR = 'Análisis CNN (IA) → pestaña «Ecografía» → recuadro «Redes entrenadas con ecografías reales»: '
  + 'suba la imagen y pulse «Analizar». También en cada ecografía guardada, pestaña «IA medida».';
const PASOS_INFORME = (corte: string) => 'Análisis CNN (IA) → pestaña «Ecografía» → suba un corte '
  + `${corte}, escriba el tamaño de píxel y pulse «Informe completo». `
  + 'También en cada ecografía guardada, pestaña «IA medida».';
const SIN_PIXEL = 'Sin el tamaño de píxel (lo da el ecógrafo o la cabecera DICOM) la medida sale en píxeles.';

export const FICHAS: Record<string, FichaModelo> = {
  plano_anatomico_fetal_planes: {
    grupo: 'obstetricia', red: 'cnn',
    queHace: 'Reconoce qué muestra la imagen: cerebro, abdomen, fémur o tórax fetal, cuello uterino materno u otro. '
      + 'Según el plano, el sistema elige qué red de medida aplicar después.',
    limites: ['Reconoce peor las cabezas del primer trimestre (ver la cifra medida).',
      'No juzga la calidad del corte para medir, salvo en el abdomen.'],
    donde: { ruta: RUTA_ECOGRAFIA, pasos: PASOS_ANALIZAR },
  },
  segmentacion_cabeza: {
    grupo: 'obstetricia', red: 'unet',
    queHace: 'Dibuja el cráneo, el cavum del septum pellucidum y el ventrículo lateral; sobre el contorno el sistema '
      + 'mide la circunferencia cefálica (CC) y el diámetro biparietal (DBP) y calcula la edad gestacional (Hadlock).',
    limites: [SIN_PIXEL, 'El error es mayor en el primer trimestre.'],
    donde: { ruta: RUTA_ECOGRAFIA, pasos: PASOS_INFORME('transtalámico de la cabeza') },
  },
  segmentacion_torax: {
    grupo: 'obstetricia', red: 'unet',
    queHace: 'Dibuja el tórax y el corazón y calcula el índice cardiotorácico por áreas y por circunferencias.',
    limites: ['Se entrenó solo con corazones normales: mide el índice, no detecta una cardiopatía.'],
    donde: { ruta: RUTA_ECOGRAFIA, pasos: PASOS_INFORME('de cuatro cámaras del tórax') },
  },
  segmentacion_abdomen: {
    grupo: 'obstetricia', red: 'unet',
    queHace: 'Busca el estómago, la vena umbilical, el hígado y la aorta para decir si el corte es adecuado para medir '
      + 'la circunferencia abdominal.',
    limites: ['Casi todas las imágenes de prueba tenían vena umbilical: no se sabe cuán bien detecta su ausencia.'],
    donde: { ruta: RUTA_ECOGRAFIA, pasos: PASOS_INFORME('transversal del abdomen') },
  },
  biometria_femur: {
    grupo: 'obstetricia', red: 'puntos',
    queHace: 'Encuentra los dos extremos de la diáfisis del fémur y mide la longitud femoral (LF).',
    limites: [SIN_PIXEL, 'Datos de dos hospitales europeos: conviene comprobarla con el ecógrafo propio.'],
    donde: { ruta: RUTA_ECOGRAFIA, pasos: PASOS_INFORME('del fémur') },
  },
  biometria_abdomen: {
    grupo: 'obstetricia', red: 'puntos',
    queHace: 'Encuentra los extremos de los diámetros transverso y anteroposterior del abdomen y calcula la '
      + 'circunferencia abdominal (CA) como una elipse.',
    limites: [SIN_PIXEL, 'Solo se mide si la red abdominal considera adecuado el corte.'],
    donde: { ruta: RUTA_ECOGRAFIA, pasos: PASOS_INFORME('transversal del abdomen') },
  },
  anomalias_cerebrales_fetales: {
    grupo: 'obstetricia', red: 'cnn',
    queHace: 'En un corte axial de la cabeza separa lo normal de cuatro familias de anomalías: ventriculomegalia o '
      + 'hidrocefalia, fosa posterior, encefalocele y lesión quística o vascular.',
    limites: ['Cuántas anomalías detecta en ecografías clínicas no se puede medir con datos públicos: «sin alarma» no descarta.',
      'Una alarma se deriva al especialista; nunca es un diagnóstico.'],
    donde: { ruta: RUTA_ECOGRAFIA, pasos: PASOS_ANALIZAR },
  },
  circunferencia_cefalica_hc18: {
    grupo: 'obstetricia', red: 'cnn',
    queHace: 'Estima la circunferencia cefálica directamente de la imagen, sin dibujar el contorno (regresión).',
    limites: ['Mide peor que la segmentación de cabeza: se conserva como segunda opinión.', SIN_PIXEL],
    donde: { ruta: RUTA_ECOGRAFIA, pasos: `${PASOS_ANALIZAR} Escriba antes el tamaño de píxel.` },
  },
  segmentacion_intraparto: {
    grupo: 'parto', red: 'unet',
    queHace: 'En la ecografía transperineal del trabajo de parto dibuja la sínfisis del pubis y la cabeza fetal y mide '
      + 'el ángulo de progresión (AoP).',
    limites: ['Con el corte de 120° no reconoce todos los partos que progresarán (ver la sensibilidad medida): se informa '
      + 'como medida, no como decisión.', 'Revise el dibujo antes de guardar el valor.'],
    donde: {
      ruta: '/dashboard/partos',
      pasos: 'Partos → abra un parto → pestaña «Trabajo de parto» → Partograma → «Registrar tacto» → «Subir imagen y medir». El ángulo se copia al '
        + 'formulario del tacto.',
    },
  },
  segmentacion_ovario: {
    grupo: 'ginecologia', red: 'unet',
    queHace: 'Dibuja el contorno de la masa anexial sobre la ecografía.',
    limites: ['Con el tamaño de píxel da el ancho y el alto en milímetros; sin él, en píxeles.'],
    donde: {
      ruta: RUTA_GINECOLOGIA,
      pasos: 'Análisis CNN (IA) → pestaña «Ecografía ginecológica» → «Masa ovárica» → elija la imagen → «Analizar».',
    },
  },
  clasificador_ovario: {
    grupo: 'ginecologia', red: 'cnn',
    queHace: 'Sugiere el tipo de lesión entre ocho clases (quiste endometriósico, teratoma, cistoadenoma seroso o '
      + 'mucinoso, quiste simple, tumor de células de la teca, ovario normal, carcinoma seroso de alto grado) y levanta '
      + 'una alarma si los rasgos parecen de carcinoma.',
    limites: ['La alarma de carcinoma no detecta todos los casos (ver la cifra): sin alarma NO descarta un cáncer.',
      'Es orientación: deciden la clasificación O-RADS, el especialista y la anatomía patológica.'],
    donde: {
      ruta: RUTA_GINECOLOGIA,
      pasos: 'Análisis CNN (IA) → pestaña «Ecografía ginecológica» → «Masa ovárica» → «Analizar»: el tipo probable y la '
        + 'alarma salen junto al contorno.',
    },
  },
  segmentacion_mioma: {
    grupo: 'ginecologia', red: 'unet',
    queHace: 'Ubica el mioma (recuadro y contorno) en un útero que lo tiene.',
    limites: ['Solo vio úteros con mioma: sirve para ubicarlo, no para descartarlo.'],
    donde: {
      ruta: RUTA_GINECOLOGIA,
      pasos: 'Análisis CNN (IA) → pestaña «Ecografía ginecológica» → «Mioma uterino» → elija la imagen → «Analizar».',
    },
  },
  clasificador_ovario_pco: {
    grupo: 'ginecologia', red: 'cnn',
    queHace: 'Clasifica el ovario como normal, con folículo dominante o de morfología poliquística.',
    limites: ['El síndrome de ovario poliquístico se diagnostica con los criterios de Rotterdam (clínica, laboratorio e '
      + 'imagen), no con una imagen.'],
    donde: {
      ruta: RUTA_GINECOLOGIA,
      pasos: 'Análisis CNN (IA) → pestaña «Ecografía ginecológica» → «Ovario poliquístico» → elija la imagen → «Analizar».',
    },
  },
  cardiotocografia: {
    grupo: 'monitoreo', red: 'tabla',
    queHace: 'Con las 21 variables del análisis automático del monitor (línea de base, aceleraciones, desaceleraciones, '
      + 'variabilidad e histograma) clasifica el registro como normal, sospechoso o patológico.',
    limites: ['Datos de un hospital y un programa de análisis (SisPorto): conviene validarlo con el monitor propio.',
      'Apoya la lectura del trazado; la conducta la decide el obstetra.'],
    donde: {
      ruta: RUTA_CTG,
      pasos: 'Análisis CNN (IA) → pestaña «Cardiotocografía» → copie los valores del informe del monitor → «Clasificar».',
    },
  },
  peso_nacimiento: {
    grupo: 'demostracion', red: 'tabla',
    queHace: 'Predice el peso al nacer con las medidas de la ecografía y los datos de la madre, y muestra al lado el '
      + 'peso estimado por Hadlock.',
    limites: ['Entrenado con partos simulados del sistema: es una demostración hasta reentrenarlo con partos reales.',
      'No predice en embarazos múltiples ni antes de las 20 semanas.'],
    donde: {
      ruta: '/dashboard/ecografias',
      pasos: 'Ecografías → abra una ecografía con biometría → pestaña «Biometría» → recuadro «Peso al nacer previsto».',
    },
  },
};

export const GRUPOS: { clave: Grupo; titulo: string; descripcion: string }[] = [
  { clave: 'obstetricia', titulo: 'Ecografía obstétrica',
    descripcion: 'Redes que leen la imagen de la ecografía: reconocen el plano, dibujan estructuras y miden.' },
  { clave: 'parto', titulo: 'Trabajo de parto', descripcion: 'Ecografía transperineal en el partograma.' },
  { clave: 'ginecologia', titulo: 'Ecografía ginecológica', descripcion: 'Masa anexial, mioma y ovario poliquístico.' },
  { clave: 'monitoreo', titulo: 'Monitoreo fetal',
    descripcion: 'Modelo supervisado de tabla sobre el análisis del cardiotocógrafo.' },
  { clave: 'demostracion', titulo: 'En demostración',
    descripcion: 'Funciona, pero todavía no está entrenado con datos reales del hospital.' },
];

export const NOMBRE_RED: Record<TipoRed, string> = {
  cnn: 'Red convolucional (CNN)',
  unet: 'Segmentación U-Net',
  puntos: 'Red de puntos (mapas de calor)',
  tabla: 'Modelo supervisado de tabla',
};

/** Lo que el sistema ofrece y NO es un modelo entrenado: para que nadie lo confunda. */
export const NO_ES_IA: { nombre: string; que_es: string; ruta: string }[] = [
  { nombre: 'Asistente de consulta', ruta: '/dashboard/ia-asistente',
    que_es: 'Busca palabras clave en una base de conocimiento obstétrica escrita a partir de guías clínicas. No aprende ni tiene una exactitud medida.' },
  { nombre: 'Interpretación de laboratorio', ruta: '/dashboard/laboratorios',
    que_es: 'Compara cada valor con los rangos propios del embarazo. Son reglas fijas, no un modelo.' },
  { nombre: 'Calculadoras clínicas (FMF, preeclampsia, Hadlock, Capurro)', ruta: '/dashboard/calculadoras',
    que_es: 'Fórmulas publicadas. Su validez es la de la publicación original.' },
];
