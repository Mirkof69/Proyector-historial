export const FAQS = [
  {
    categoria: 'Gestión de Pacientes',
    items: [
      {
        pregunta: '¿Cómo registro una paciente sin Cédula de Identidad?',
        respuesta: 'El sistema permite el registro provisional. Deje el campo CI vacío y el sistema generará un código temporal (TEMP-XXXX). Debe actualizarlo cuando la paciente presente su documento.',
        dificultad: 'Básico'
      },
      {
        pregunta: '¿Puedo fusionar dos historias clínicas duplicadas?',
        respuesta: 'Sí, esta es una acción administrativa. Vaya a "Configuración > Herramientas > Fusión de Pacientes". Se requiere rol de Supervisor.',
        dificultad: 'Avanzado'
      }
    ]
  },
  {
    categoria: 'Módulo Obstétrico',
    items: [
      {
        pregunta: '¿La FPP se calcula por FUM o por Ecografía?',
        respuesta: 'El sistema calcula ambas. Por defecto muestra FUM. Si la diferencia con la Eco I Trimestre es > 7 días, el sistema sugerirá automáticamente usar la edad gestacional ecográfica.',
        dificultad: 'Intermedio'
      },
      {
        pregunta: '¿Cómo registro un embarazo gemelar?',
        respuesta: 'Al crear el embarazo, active el switch "¿Embarazo Múltiple?". Esto habilitará campos dobles para FCF y Peso Fetal en los controles posteriores.',
        dificultad: 'Básico'
      },
      {
        pregunta: '¿Por qué me sale una alerta roja en la Presión Arterial?',
        respuesta: 'El sistema sigue los protocolos de la OMS. Sistólica >= 140 o Diastólica >= 90 activan la alerta de posible Preeclampsia.',
        dificultad: 'Intermedio'
      }
    ]
  },
  {
    categoria: 'Reportes e Impresión',
    items: [
      {
        pregunta: 'No puedo descargar el reporte en PDF',
        respuesta: 'Verifique que no tenga bloqueadores de ventanas emergentes (Pop-up blockers) en su navegador. El reporte se genera en una nueva pestaña.',
        dificultad: 'Básico'
      }
    ]
  }
];

export const MANUALES = [
  { title: 'Manual de Usuario General v2.4', size: '4.5 MB', date: '10/11/2024' },
  { title: 'Protocolo de Atención Prenatal', size: '1.2 MB', date: '05/08/2024' },
  { title: 'Guía de Uso: Calculadoras Médicas', size: '0.8 MB', date: '22/09/2024' },
  { title: 'Configuración de Impresoras', size: '2.1 MB', date: '15/01/2024' },
];
