/**
 * =============================================================================
 * SERVICIO DE GENERACIÓN DE PDFs
 * =============================================================================
 * Genera PDFs descargables profesionales para reportes médicos
 * Usa jsPDF y jspdf-autotable para crear documentos estructurados
 * =============================================================================
 */

import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import dayjs from 'dayjs';

// ═══════════════════════════════════════════════════════════════════════════
// CONFIGURACIÓN Y UTILIDADES
// ═══════════════════════════════════════════════════════════════════════════

const COLORS = {
  primary: [103, 58, 183] as [number, number, number],
  secondary: [63, 81, 181] as [number, number, number],
  success: [76, 175, 80] as [number, number, number],
  danger: [244, 67, 54] as [number, number, number],
  warning: [255, 152, 0] as [number, number, number],
  gray: [158, 158, 158] as [number, number, number],
  darkGray: [97, 97, 97] as [number, number, number],
  lightGray: [238, 238, 238] as [number, number, number],
};

/**
 * Agrega encabezado estándar al PDF
 */
const addHeader = (doc: jsPDF, titulo: string, subtitulo?: string) => {
  doc.setFillColor(...COLORS.primary);
  doc.rect(0, 0, 210, 35, 'F');

  doc.setTextColor(255, 255, 255);
  doc.setFontSize(22);
  doc.setFont('helvetica', 'bold');
  doc.text('Sistema Médico - Historial Clínico', 105, 15, { align: 'center' });

  doc.setFontSize(14);
  doc.setFont('helvetica', 'normal');
  doc.text(titulo, 105, 25, { align: 'center' });

  if (subtitulo) {
    doc.setFontSize(10);
    doc.text(subtitulo, 105, 31, { align: 'center' });
  }

  doc.setDrawColor(...COLORS.gray);
  doc.setLineWidth(0.5);
  doc.line(10, 37, 200, 37);
};

/**
 * Agrega pie de página estándar al PDF
 */
const addFooter = (doc: jsPDF, pageNumber: number, totalPages: number) => {
  const pageHeight = doc.internal.pageSize.height;

  doc.setDrawColor(...COLORS.gray);
  doc.setLineWidth(0.5);
  doc.line(10, pageHeight - 20, 200, pageHeight - 20);

  doc.setTextColor(...COLORS.darkGray);
  doc.setFontSize(8);
  doc.setFont('helvetica', 'normal');

  const fecha = dayjs().format('DD/MM/YYYY HH:mm');
  doc.text(`Generado: ${fecha}`, 10, pageHeight - 12);

  doc.text(
    `Página ${pageNumber} de ${totalPages}`,
    105,
    pageHeight - 12,
    { align: 'center' }
  );

  doc.text('Sistema Médico Obstétrico', 200, pageHeight - 12, { align: 'right' });
};

// ═══════════════════════════════════════════════════════════════════════════
// UTILIDADES DE FORMATEO
// ═══════════════════════════════════════════════════════════════════════════

const calcularEdad = (fechaNacimiento: string): number => {
  if (!fechaNacimiento) return 0;
  return dayjs().diff(dayjs(fechaNacimiento), 'year');
};

const getTipoPartoTexto = (tipo: string): string => {
  const textos: Record<string, string> = {
    vaginal_espontaneo: 'Vaginal Espontáneo',
    vaginal_instrumentado: 'Vaginal Instrumentado',
    cesarea_electiva: 'Cesárea Electiva',
    cesarea_urgencia: 'Cesárea Urgencia',
    cesarea_emergencia: 'Cesárea Emergencia',
  };
  return textos[tipo] || tipo;
};

const formatearTexto = (valor: any, defaultValue: string = 'N/A'): string => {
  if (valor === null || valor === undefined || valor === '' || valor === 'undefined') {
    return defaultValue;
  }
  return String(valor);
};

/**
 * Construye el nombre completo del paciente desde sus partes
 */
const obtenerNombreCompleto = (paciente: any): string => {
  // Intentar primero con el campo nombre_completo
  if (paciente.nombre_completo && paciente.nombre_completo !== 'undefined undefined') {
    return paciente.nombre_completo;
  }

  // Construir desde las partes
  const partes = [
    paciente.nombre,
    paciente.apellido_paterno,
    paciente.apellido_materno
  ].filter(p => p && p !== 'undefined' && p !== null && p !== '');

  return partes.length > 0 ? partes.join(' ') : 'Sin Nombre Registrado';
};

/**
 * Obtiene la edad del paciente
 */
const obtenerEdad = (paciente: any): string => {
  if (paciente.edad && paciente.edad > 0) {
    return `${paciente.edad} años`;
  }
  if (paciente.fecha_nacimiento) {
    const edad = calcularEdad(paciente.fecha_nacimiento);
    return edad > 0 ? `${edad} años` : 'N/A';
  }
  return 'N/A';
};

/**
 * Obtiene el género en formato legible
 */
const obtenerGenero = (genero: string): string => {
  const generos: Record<string, string> = {
    'femenino': 'Femenino',
    'masculino': 'Masculino',
    'otro': 'Otro',
    'F': 'Femenino',
    'M': 'Masculino'
  };
  return generos[genero?.toLowerCase()] || formatearTexto(genero);
};

/**
 * FUNCIÓN MEJORADA PARA OBTENER TIPO DE SANGRE
 * Intenta múltiples nombres de campo comunes
 */
const obtenerTipoSangre = (paciente: any): string => {
  const tipoSangre =
    paciente.tipo_sangre ||
    paciente.grupo_sanguineo ||
    paciente.tipo_de_sangre ||
    paciente.blood_type ||
    paciente.grupoSanguineo;

  return formatearTexto(tipoSangre, 'No especificado');
};

/**
 * FUNCIÓN MEJORADA PARA OBTENER TELÉFONO
 * Intenta múltiples nombres de campo comunes
 */
const obtenerTelefono = (paciente: any): string => {
  const telefono =
    paciente.telefono ||
    paciente.celular ||
    paciente.phone ||
    paciente.movil ||
    paciente.numero_telefono;

  return formatearTexto(telefono);
};

// ═══════════════════════════════════════════════════════════════════════════
// GENERADORES DE PDFs ESPECÍFICOS
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Genera PDF de Reporte de Paciente Individual
 */
const generarReportePaciente = (paciente: any): void => {
  const doc = new jsPDF();

  const nombreCompleto = obtenerNombreCompleto(paciente);

  addHeader(
    doc,
    'Reporte de Paciente',
    `CI: ${formatearTexto(paciente.ci)} - ID: ${formatearTexto(paciente.id_clinico)}`
  );

  let yPos = 45;

  // INFORMACIÓN PERSONAL
  doc.setFontSize(12);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(...COLORS.primary);
  doc.text('INFORMACIÓN PERSONAL', 10, yPos);

  yPos += 8;
  doc.setFontSize(10);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(0, 0, 0);

  const infoPaciente = [
    ['Nombre Completo:', nombreCompleto],
    ['CI:', formatearTexto(paciente.ci)],
    ['Fecha de Nacimiento:', paciente.fecha_nacimiento ? dayjs(paciente.fecha_nacimiento).format('DD/MM/YYYY') : 'N/A'],
    ['Edad:', obtenerEdad(paciente)],
    ['Género:', obtenerGenero(paciente.genero)],
    ['Grupo Sanguíneo:', obtenerTipoSangre(paciente)],
    ['Estado Civil:', formatearTexto(paciente.estado_civil, 'No especificado')],
    ['Ocupación:', formatearTexto(paciente.ocupacion, 'No especificada')],
  ];

  infoPaciente.forEach(([label, value]) => {
    doc.setFont('helvetica', 'bold');
    doc.text(label, 10, yPos);
    doc.setFont('helvetica', 'normal');
    doc.text(value, 70, yPos);
    yPos += 7;
  });

  // INFORMACIÓN DE CONTACTO
  yPos += 5;
  doc.setFontSize(12);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(...COLORS.primary);
  doc.text('INFORMACIÓN DE CONTACTO', 10, yPos);

  yPos += 8;
  doc.setFontSize(10);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(0, 0, 0);

  const infoContacto = [
    ['Teléfono:', obtenerTelefono(paciente)],
    ['Email:', formatearTexto(paciente.email)],
    ['Dirección:', formatearTexto(paciente.direccion)],
    ['Ciudad:', formatearTexto(paciente.ciudad)],
    ['País:', formatearTexto(paciente.pais, 'Bolivia')],
  ];

  infoContacto.forEach(([label, value]) => {
    doc.setFont('helvetica', 'bold');
    doc.text(label, 10, yPos);
    doc.setFont('helvetica', 'normal');
    doc.text(value, 70, yPos);
    yPos += 7;
  });

  // INFORMACIÓN MÉDICA
  yPos += 5;
  doc.setFontSize(12);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(...COLORS.primary);
  doc.text('INFORMACIÓN MÉDICA', 10, yPos);

  yPos += 8;
  doc.setFontSize(10);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(0, 0, 0);

  if (paciente.alergias) {
    doc.setFont('helvetica', 'bold');
    doc.text('Alergias:', 10, yPos);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(COLORS.danger[0], COLORS.danger[1], COLORS.danger[2]);
    const textoAlergias = doc.splitTextToSize(formatearTexto(paciente.alergias, 'Ninguna'), 180);
    doc.text(textoAlergias, 10, yPos + 5);
    doc.setTextColor(0, 0, 0);
    yPos += 5 + (textoAlergias.length * 5) + 5;
  } else {
    doc.setFont('helvetica', 'bold');
    doc.text('Alergias:', 10, yPos);
    doc.setFont('helvetica', 'normal');
    doc.text('Ninguna registrada', 70, yPos);
    yPos += 7;
  }

  if (paciente.enfermedades_cronicas) {
    doc.setFont('helvetica', 'bold');
    doc.text('Enfermedades Crónicas:', 10, yPos);
    doc.setFont('helvetica', 'normal');
    const textoEnfermedades = doc.splitTextToSize(formatearTexto(paciente.enfermedades_cronicas, 'Ninguna'), 180);
    doc.text(textoEnfermedades, 10, yPos + 5);
    yPos += 5 + (textoEnfermedades.length * 5) + 5;
  } else {
    doc.setFont('helvetica', 'bold');
    doc.text('Enfermedades Crónicas:', 10, yPos);
    doc.setFont('helvetica', 'normal');
    doc.text('Ninguna registrada', 70, yPos);
    yPos += 7;
  }

  if (paciente.observaciones) {
    doc.setFont('helvetica', 'bold');
    doc.text('Observaciones:', 10, yPos);
    doc.setFont('helvetica', 'normal');
    const textoObs = doc.splitTextToSize(formatearTexto(paciente.observaciones), 180);
    doc.text(textoObs, 10, yPos + 5);
    yPos += 5 + (textoObs.length * 5) + 5;
  }

  // CONTACTO DE EMERGENCIA
  if (yPos > 250) {
    doc.addPage();
    yPos = 20;
  } else {
    yPos += 5;
  }

  doc.setFontSize(12);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(...COLORS.primary);
  doc.text('CONTACTO DE EMERGENCIA', 10, yPos);

  yPos += 8;
  doc.setFontSize(10);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(0, 0, 0);

  const infoEmergencia = [
    ['Nombre:', formatearTexto(paciente.contacto_emergencia_nombre)],
    ['Teléfono:', formatearTexto(paciente.contacto_emergencia_telefono)],
    ['Relación:', formatearTexto(paciente.contacto_emergencia_relacion)],
  ];

  infoEmergencia.forEach(([label, value]) => {
    doc.setFont('helvetica', 'bold');
    doc.text(label, 10, yPos);
    doc.setFont('helvetica', 'normal');
    doc.text(value, 70, yPos);
    yPos += 7;
  });

  // ESTADO EN EL SISTEMA
  yPos += 5;
  doc.setFontSize(12);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(...COLORS.primary);
  doc.text('ESTADO EN EL SISTEMA', 10, yPos);

  yPos += 8;
  doc.setFontSize(10);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(0, 0, 0);

  doc.setFont('helvetica', 'bold');
  doc.text('Estado:', 10, yPos);
  doc.setFont('helvetica', 'normal');
  const estadoColor = paciente.activo ? COLORS.success : COLORS.danger;
  doc.setTextColor(estadoColor[0], estadoColor[1], estadoColor[2]);
  doc.text(paciente.activo ? 'ACTIVO' : 'INACTIVO', 70, yPos);
  doc.setTextColor(0, 0, 0);
  yPos += 7;

  if (paciente.embarazos_activos) {
    doc.setFont('helvetica', 'bold');
    doc.text('Estado Obstétrico:', 10, yPos);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(COLORS.warning[0], COLORS.warning[1], COLORS.warning[2]);
    doc.text('EMBARAZO ACTIVO', 70, yPos);
    doc.setTextColor(0, 0, 0);
    yPos += 7;
  }

  doc.setFont('helvetica', 'bold');
  doc.text('Fecha de Registro:', 10, yPos);
  doc.setFont('helvetica', 'normal');
  doc.text(paciente.fecha_registro ? dayjs(paciente.fecha_registro).format('DD/MM/YYYY HH:mm') : 'N/A', 70, yPos);

  addFooter(doc, 1, 1);

  const nombreArchivo = `Paciente_${paciente.ci || paciente.id_clinico}_${dayjs().format('YYYYMMDD')}.pdf`;
  doc.save(nombreArchivo);
};

/**
 * Genera PDF de Listado de Pacientes
 */
const generarListadoPacientes = (pacientes: any[]): void => {
  const doc = new jsPDF();

  addHeader(doc, 'Listado de Pacientes', `Total: ${pacientes.length} pacientes`);

  const datosTabla = pacientes.map((p) => {
    const nombreCompleto = obtenerNombreCompleto(p);
    const edad = obtenerEdad(p);
    const tipoSangre = obtenerTipoSangre(p);
    const telefono = obtenerTelefono(p);

    return [
      formatearTexto(p.id_clinico || p.id),
      formatearTexto(p.ci),
      nombreCompleto,
      edad,
      telefono,
      tipoSangre,
    ];
  });

  autoTable(doc, {
    startY: 45,
    head: [['ID Clínico', 'CI', 'Nombre Completo', 'Edad', 'Teléfono', 'Tipo Sangre']],
    body: datosTabla,
    styles: {
      fontSize: 9,
      cellPadding: 3,
    },
    headStyles: {
      fillColor: COLORS.primary,
      textColor: [255, 255, 255],
      fontStyle: 'bold',
      halign: 'center',
    },
    alternateRowStyles: {
      fillColor: COLORS.lightGray,
    },
    columnStyles: {
      0: { cellWidth: 30 },
      1: { cellWidth: 25 },
      2: { cellWidth: 50 },
      3: { cellWidth: 20 },
      4: { cellWidth: 30 },
      5: { cellWidth: 25 },
    },
  });

  addFooter(doc, 1, 1);

  doc.save(`Listado_Pacientes_${dayjs().format('YYYYMMDD_HHmmss')}.pdf`);
};

/**
 * Genera PDF de Reporte de Partos
 */
const generarReportePartos = (partos: any[]): void => {
  const doc = new jsPDF();

  addHeader(doc, 'Reporte de Partos', `Total: ${partos.length} partos registrados`);

  let yPos = 50;
  doc.setFontSize(12);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(...COLORS.primary);
  doc.text('RESUMEN ESTADÍSTICO', 10, yPos);

  yPos += 8;
  const totalVaginales = partos.filter((p) => p.tipo_parto?.includes('vaginal')).length;
  const totalCesareas = partos.filter((p) => p.tipo_parto?.includes('cesarea')).length;

  doc.setFontSize(10);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(0, 0, 0);
  doc.text(`Total de Partos: ${partos.length}`, 10, yPos);
  doc.text(`Partos Vaginales: ${totalVaginales} (${partos.length > 0 ? ((totalVaginales / partos.length) * 100).toFixed(1) : 0}%)`, 10, yPos + 7);
  doc.text(`Cesáreas: ${totalCesareas} (${partos.length > 0 ? ((totalCesareas / partos.length) * 100).toFixed(1) : 0}%)`, 10, yPos + 14);

  autoTable(doc, {
    startY: yPos + 25,
    head: [['Nº Parto', 'Paciente', 'Fecha', 'Tipo Parto', 'Edad Gest.', 'Estado']],
    body: partos.map((p) => [
      formatearTexto(p.numero_parto || p.id),
      obtenerNombreCompleto(p.paciente_info || p),
      p.fecha_parto ? dayjs(p.fecha_parto).format('DD/MM/YYYY') : 'N/A',
      getTipoPartoTexto(p.tipo_parto || ''),
      formatearTexto(p.edad_gestacional_parto),
      p.parto_finalizado ? 'Finalizado' : 'En proceso',
    ]),
    styles: { fontSize: 8 },
    headStyles: {
      fillColor: COLORS.primary,
      textColor: [255, 255, 255],
      fontStyle: 'bold',
    },
    alternateRowStyles: {
      fillColor: COLORS.lightGray,
    },
  });

  addFooter(doc, 1, 1);

  doc.save(`Reporte_Partos_${dayjs().format('YYYYMMDD_HHmmss')}.pdf`);
};

/**
 * Genera PDF de Reporte de Citas
 */
const generarReporteCitas = (citas: any[]): void => {
  const doc = new jsPDF();

  addHeader(doc, 'Reporte de Citas', `Total: ${citas.length} citas`);

  autoTable(doc, {
    startY: 45,
    head: [['Fecha', 'Hora', 'Paciente', 'Tipo Cita', 'Médico', 'Estado']],
    body: citas.map((c) => [
      c.fecha_cita ? dayjs(c.fecha_cita).format('DD/MM/YYYY') : 'N/A',
      formatearTexto(c.hora_cita),
      obtenerNombreCompleto(c.paciente || { nombre: c.paciente_nombre }),
      formatearTexto(c.tipo_cita),
      formatearTexto(c.medico_nombre),
      formatearTexto(c.estado),
    ]),
    styles: { fontSize: 9 },
    headStyles: {
      fillColor: COLORS.primary,
      textColor: [255, 255, 255],
      fontStyle: 'bold',
    },
    alternateRowStyles: {
      fillColor: COLORS.lightGray,
    },
  });

  addFooter(doc, 1, 1);

  doc.save(`Reporte_Citas_${dayjs().format('YYYYMMDD_HHmmss')}.pdf`);
};

/**
 * Genera PDF de Historial Clínico de Embarazo
 */
const generarHistorialEmbarazo = (embarazo: any, controles: any[]): void => {
  const doc = new jsPDF();

  addHeader(doc, 'Historial de Embarazo', `Gesta N° ${formatearTexto(embarazo.numero_gesta)}`);

  let yPos = 50;

  doc.setFontSize(12);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(...COLORS.primary);
  doc.text('INFORMACIÓN DEL EMBARAZO', 10, yPos);

  yPos += 8;
  doc.setFontSize(10);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(0, 0, 0);

  const nombrePaciente = obtenerNombreCompleto(embarazo.paciente || { nombre: embarazo.paciente_nombre });

  const infoEmbarazo = [
    ['Paciente:', nombrePaciente],
    ['Fecha Última Menstruación:', embarazo.fecha_ultima_menstruacion ? dayjs(embarazo.fecha_ultima_menstruacion).format('DD/MM/YYYY') : 'N/A'],
    ['Fecha Probable de Parto:', embarazo.fecha_probable_parto ? dayjs(embarazo.fecha_probable_parto).format('DD/MM/YYYY') : 'N/A'],
    ['Tipo de Embarazo:', formatearTexto(embarazo.tipo_embarazo)],
    ['Riesgo:', formatearTexto(embarazo.riesgo_embarazo)],
    ['Estado:', formatearTexto(embarazo.estado)],
  ];

  infoEmbarazo.forEach(([label, value]) => {
    doc.setFont('helvetica', 'bold');
    doc.text(label, 10, yPos);
    doc.setFont('helvetica', 'normal');
    doc.text(value, 75, yPos);
    yPos += 7;
  });

  yPos += 10;
  doc.setFontSize(12);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(...COLORS.primary);
  doc.text('CONTROLES PRENATALES', 10, yPos);

  autoTable(doc, {
    startY: yPos + 5,
    head: [['Control', 'Fecha', 'Edad Gest.', 'Peso', 'PA', 'FCF']],
    body: controles.map((c) => [
      `Control ${formatearTexto(c.numero_control)}`,
      c.fecha_control ? dayjs(c.fecha_control).format('DD/MM/YYYY') : 'N/A',
      `${formatearTexto(c.semanas_gestacion, '0')}+${formatearTexto(c.dias_gestacion, '0')}`,
      `${formatearTexto(c.peso_actual, '0')} kg`,
      `${formatearTexto(c.presion_arterial_sistolica, '0')}/${formatearTexto(c.presion_arterial_diastolica, '0')}`,
      `${formatearTexto(c.frecuencia_cardiaca_fetal, '0')} lpm`,
    ]),
    styles: { fontSize: 9 },
    headStyles: {
      fillColor: COLORS.primary,
      textColor: [255, 255, 255],
      fontStyle: 'bold',
    },
    alternateRowStyles: {
      fillColor: COLORS.lightGray,
    },
  });

  addFooter(doc, 1, 1);

  doc.save(`Embarazo_${embarazo.id}_${dayjs().format('YYYYMMDD')}.pdf`);
};

/**
 * Genera PDF COMPLETO de Historia Clínica con TODAS las secciones
 */
const generarHistoriaClinicaCompleta = (data: {
  paciente: any;
  embarazo: any;
  controles: any[];
  partos: any[];
  ecografias: any[];
  examenes: any[];
  citas: any[];
  vacunas: any[];
  antecedentes?: any;
  notasEvolucion?: any[];
}): void => {
  const doc = new jsPDF();
  let currentPage = 1;

  const {
    paciente,
    embarazo,
    controles = [],
    partos = [],
    ecografias = [],
    examenes = [],
    citas = [],
    vacunas = [],
    antecedentes,
    notasEvolucion = [],
  } = data;

  // PÁGINA 1: INFORMACIÓN DEL PACIENTE Y EMBARAZO ACTUAL
  addHeader(doc, 'Historia Clínica Completa', `Paciente: ${obtenerNombreCompleto(paciente)}`);

  let yPos = 50;

  // === DATOS DEL PACIENTE ===
  doc.setFontSize(14);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(...COLORS.primary);
  doc.text('DATOS DEL PACIENTE', 10, yPos);

  yPos += 8;
  doc.setFontSize(10);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(0, 0, 0);

  const infoPaciente = [
    ['Nombre Completo:', obtenerNombreCompleto(paciente)],
    ['CI:', formatearTexto(paciente.ci)],
    ['Fecha Nacimiento:', paciente.fecha_nacimiento ? dayjs(paciente.fecha_nacimiento).format('DD/MM/YYYY') : 'N/A'],
    ['Edad:', `${calcularEdad(paciente.fecha_nacimiento)} años`],
    ['Género:', formatearTexto(paciente.genero)],
    ['Estado Civil:', formatearTexto(paciente.estado_civil)],
    ['Teléfono:', formatearTexto(paciente.telefono)],
    ['Dirección:', formatearTexto(paciente.direccion)],
    ['Grupo Sanguíneo:', `${formatearTexto(paciente.grupo_sanguineo)} ${formatearTexto(paciente.rh)}`],
  ];

  infoPaciente.forEach(([label, value]) => {
    doc.setFont('helvetica', 'bold');
    doc.text(label, 10, yPos);
    doc.setFont('helvetica', 'normal');
    doc.text(value, 70, yPos);
    yPos += 6;
  });

  yPos += 10;

  // === EMBARAZO ACTUAL ===
  if (embarazo) {
    doc.setFontSize(14);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(...COLORS.primary);
    doc.text(`EMBARAZO ACTUAL - Gesta N° ${formatearTexto(embarazo.numero_gesta)}`, 10, yPos);

    yPos += 8;
    doc.setFontSize(10);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(0, 0, 0);

    const infoEmbarazo = [
      ['FUM:', embarazo.fecha_ultima_menstruacion ? dayjs(embarazo.fecha_ultima_menstruacion).format('DD/MM/YYYY') : 'N/A'],
      ['FPP:', embarazo.fecha_probable_parto ? dayjs(embarazo.fecha_probable_parto).format('DD/MM/YYYY') : 'N/A'],
      ['Edad Gestacional:', formatearTexto(embarazo.edad_gestacional_actual)],
      ['Riesgo:', formatearTexto(embarazo.riesgo_embarazo)],
      ['Estado:', formatearTexto(embarazo.estado)],
      ['Gestas Previas:', formatearTexto(embarazo.gestas_previas, '0')],
      ['Partos:', formatearTexto(embarazo.partos_previos, '0')],
      ['Cesáreas:', formatearTexto(embarazo.cesareas_previas, '0')],
      ['Abortos:', formatearTexto(embarazo.abortos_previos, '0')],
    ];

    infoEmbarazo.forEach(([label, value]) => {
      doc.setFont('helvetica', 'bold');
      doc.text(label, 10, yPos);
      doc.setFont('helvetica', 'normal');
      doc.text(value, 70, yPos);
      yPos += 6;
    });
  }

  addFooter(doc, currentPage, 1);

  // PÁGINA 2: ANTECEDENTES
  if (antecedentes || Object.keys(antecedentes || {}).length > 0) {
    doc.addPage();
    currentPage++;
    addHeader(doc, 'Historia Clínica Completa', 'Antecedentes Médicos');
    yPos = 50;

    doc.setFontSize(14);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(...COLORS.primary);
    doc.text('ANTECEDENTES', 10, yPos);

    yPos += 10;
    doc.setFontSize(10);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(0, 0, 0);

    const antInfo = [
      ['Médicos:', formatearTexto(antecedentes?.medicos || 'Ninguno')],
      ['Quirúrgicos:', formatearTexto(antecedentes?.quirurgicos || 'Ninguno')],
      ['Familiares:', formatearTexto(antecedentes?.familiares || 'Ninguno')],
      ['Alergias:', formatearTexto(antecedentes?.alergias || 'Ninguna')],
    ];

    antInfo.forEach(([label, value]) => {
      doc.setFont('helvetica', 'bold');
      doc.text(label, 10, yPos);
      yPos += 6;
      doc.setFont('helvetica', 'normal');
      const lines = doc.splitTextToSize(value, 180);
      doc.text(lines, 10, yPos);
      yPos += lines.length * 5 + 5;
    });

    addFooter(doc, currentPage, 1);
  }

  // PÁGINA 3: CONTROLES PRENATALES
  if (controles.length > 0) {
    doc.addPage();
    currentPage++;
    addHeader(doc, 'Historia Clínica Completa', 'Controles Prenatales');
    yPos = 50;

    autoTable(doc, {
      startY: yPos,
      head: [['Control', 'Fecha', 'EG', 'Peso', 'PA', 'AU', 'FCF', 'Presentación']],
      body: controles.map((c) => [
        formatearTexto(c.numero_control),
        c.fecha_control ? dayjs(c.fecha_control).format('DD/MM/YYYY') : 'N/A',
        `${formatearTexto(c.semanas_gestacion, '0')}+${formatearTexto(c.dias_gestacion, '0')}`,
        `${formatearTexto(c.peso_materno, '0')} kg`,
        `${formatearTexto(c.presion_sistolica, '0')}/${formatearTexto(c.presion_diastolica, '0')}`,
        `${formatearTexto(c.altura_uterina, '0')} cm`,
        `${formatearTexto(c.frecuencia_cardiaca_fetal, '0')} lpm`,
        formatearTexto(c.presentacion_fetal),
      ]),
      styles: { fontSize: 8 },
      headStyles: { fillColor: COLORS.primary, textColor: [255, 255, 255], fontStyle: 'bold' },
      alternateRowStyles: { fillColor: COLORS.lightGray },
    });

    addFooter(doc, currentPage, 1);
  }

  // PÁGINA 4: ECOGRAFÍAS
  if (ecografias.length > 0) {
    doc.addPage();
    currentPage++;
    addHeader(doc, 'Historia Clínica Completa', 'Ecografías');
    yPos = 50;

    autoTable(doc, {
      startY: yPos,
      head: [['Fecha', 'Tipo', 'EG', 'Peso Est.', 'DBP', 'LF', 'Líquido', 'Placenta']],
      body: ecografias.map((e) => [
        e.fecha_ecografia ? dayjs(e.fecha_ecografia).format('DD/MM/YYYY') : 'N/A',
        formatearTexto(e.tipo_ecografia),
        `${formatearTexto(e.edad_gestacional_semanas, '0')}+${formatearTexto(e.edad_gestacional_dias, '0')}`,
        `${formatearTexto(e.peso_fetal_estimado, '0')} g`,
        `${formatearTexto(e.biometria_dbp, '0')} mm`,
        `${formatearTexto(e.biometria_lf, '0')} mm`,
        formatearTexto(e.liquido_amniotico),
        formatearTexto(e.placenta_localizacion),
      ]),
      styles: { fontSize: 8 },
      headStyles: { fillColor: COLORS.primary, textColor: [255, 255, 255], fontStyle: 'bold' },
      alternateRowStyles: { fillColor: COLORS.lightGray },
    });

    addFooter(doc, currentPage, 1);
  }

  // PÁGINA 5: LABORATORIO
  if (examenes.length > 0) {
    doc.addPage();
    currentPage++;
    addHeader(doc, 'Historia Clínica Completa', 'Exámenes de Laboratorio');
    yPos = 50;

    autoTable(doc, {
      startY: yPos,
      head: [['Fecha', 'Tipo Examen', 'Hb', 'Glucosa', 'VIH', 'VDRL', 'Grupo/RH']],
      body: examenes.map((e) => [
        e.fecha_solicitud ? dayjs(e.fecha_solicitud).format('DD/MM/YYYY') : 'N/A',
        formatearTexto(e.tipo_examen_nombre),
        formatearTexto(e.hemoglobina, '-'),
        formatearTexto(e.glucosa, '-'),
        formatearTexto(e.vih, '-'),
        formatearTexto(e.vdrl, '-'),
        `${formatearTexto(e.grupo_sanguineo, '-')} ${formatearTexto(e.factor_rh, '')}`,
      ]),
      styles: { fontSize: 8 },
      headStyles: { fillColor: COLORS.primary, textColor: [255, 255, 255], fontStyle: 'bold' },
      alternateRowStyles: { fillColor: COLORS.lightGray },
    });

    addFooter(doc, currentPage, 1);
  }

  // PÁGINA 6: PARTOS
  if (partos.length > 0) {
    doc.addPage();
    currentPage++;
    addHeader(doc, 'Historia Clínica Completa', 'Historial de Partos');
    yPos = 50;

    autoTable(doc, {
      startY: yPos,
      head: [['Fecha', 'Tipo Parto', 'EG', 'Peso RN', 'Talla RN', 'Apgar 1\'', 'Apgar 5\'', 'Sexo']],
      body: partos.map((p) => [
        p.fecha_parto ? dayjs(p.fecha_parto).format('DD/MM/YYYY') : 'N/A',
        getTipoPartoTexto(p.tipo_parto),
        `${formatearTexto(p.edad_gestacional_semanas, '0')} sem`,
        `${formatearTexto(p.peso_recien_nacido, '0')} g`,
        `${formatearTexto(p.talla_recien_nacido, '0')} cm`,
        formatearTexto(p.apgar_1min, '-'),
        formatearTexto(p.apgar_5min, '-'),
        formatearTexto(p.sexo_recien_nacido),
      ]),
      styles: { fontSize: 8 },
      headStyles: { fillColor: COLORS.primary, textColor: [255, 255, 255], fontStyle: 'bold' },
      alternateRowStyles: { fillColor: COLORS.lightGray },
    });

    addFooter(doc, currentPage, 1);
  }

  // PÁGINA 7: VACUNAS
  if (vacunas.length > 0) {
    doc.addPage();
    currentPage++;
    addHeader(doc, 'Historia Clínica Completa', 'Vacunación');
    yPos = 50;

    autoTable(doc, {
      startY: yPos,
      head: [['Vacuna', 'Dosis', 'Fecha Aplicación', 'Lote', 'Próxima Dosis']],
      body: vacunas.map((v) => [
        formatearTexto(v.tipo_vacuna_nombre),
        `${formatearTexto(v.numero_dosis)}° dosis`,
        v.fecha_aplicacion ? dayjs(v.fecha_aplicacion).format('DD/MM/YYYY') : 'N/A',
        formatearTexto(v.lote, '-'),
        v.proxima_dosis_fecha ? dayjs(v.proxima_dosis_fecha).format('DD/MM/YYYY') : 'Completo',
      ]),
      styles: { fontSize: 9 },
      headStyles: { fillColor: COLORS.primary, textColor: [255, 255, 255], fontStyle: 'bold' },
      alternateRowStyles: { fillColor: COLORS.lightGray },
    });

    addFooter(doc, currentPage, 1);
  }

  // PÁGINA 8: CITAS
  if (citas.length > 0) {
    doc.addPage();
    currentPage++;
    addHeader(doc, 'Historia Clínica Completa', 'Historial de Citas');
    yPos = 50;

    autoTable(doc, {
      startY: yPos,
      head: [['Fecha', 'Hora', 'Tipo', 'Motivo', 'Estado']],
      body: citas.map((c) => [
        c.fecha_cita ? dayjs(c.fecha_cita).format('DD/MM/YYYY') : 'N/A',
        c.hora_cita ? c.hora_cita.substring(0, 5) : 'N/A',
        formatearTexto(c.tipo_cita),
        formatearTexto(c.motivo),
        formatearTexto(c.estado),
      ]),
      styles: { fontSize: 9 },
      headStyles: { fillColor: COLORS.primary, textColor: [255, 255, 255], fontStyle: 'bold' },
      alternateRowStyles: { fillColor: COLORS.lightGray },
    });

    addFooter(doc, currentPage, 1);
  }

  // PÁGINA 9: NOTAS DE EVOLUCIÓN
  if (notasEvolucion && notasEvolucion.length > 0) {
    doc.addPage();
    currentPage++;
    addHeader(doc, 'Historia Clínica Completa', 'Notas de Evolución');
    yPos = 50;

    notasEvolucion.slice(0, 10).forEach((nota, idx) => {
      if (yPos > 250) {
        doc.addPage();
        currentPage++;
        addHeader(doc, 'Historia Clínica Completa', 'Notas de Evolución (cont.)');
        yPos = 50;
      }

      doc.setFontSize(10);
      doc.setFont('helvetica', 'bold');
      doc.text(`Nota ${idx + 1} - ${nota.fecha ? dayjs(nota.fecha).format('DD/MM/YYYY') : 'S/F'}`, 10, yPos);
      yPos += 6;

      doc.setFont('helvetica', 'normal');
      doc.setFontSize(9);
      const lines = doc.splitTextToSize(formatearTexto(nota.descripcion || nota.nota || 'Sin descripción'), 180);
      doc.text(lines, 10, yPos);
      yPos += lines.length * 5 + 8;
    });

    addFooter(doc, currentPage, 1);
  }

  // GUARDAR PDF
  const nombreArchivo = `Historia_Clinica_${paciente.ci || paciente.id}_${dayjs().format('YYYYMMDD_HHmmss')}.pdf`;
  doc.save(nombreArchivo);
};

// ═══════════════════════════════════════════════════════════════════════════
// EXPORTAR SERVICIOS
// ═══════════════════════════════════════════════════════════════════════════

const pdfService = {
  generarReportePaciente,
  generarListadoPacientes,
  generarReportePartos,
  generarReporteCitas,
  generarHistorialEmbarazo,
  generarHistoriaClinicaCompleta,
};

export default pdfService;