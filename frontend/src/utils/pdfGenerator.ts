/**
 * =============================================================================
 * GENERADOR DE PDF - HISTORIAL MÉDICO
 * =============================================================================
 * Genera PDFs del historial médico completo de pacientes
 * =============================================================================
 */

import { Paciente, Embarazo, ControlPrenatal } from '../types';

/**
 * Genera un PDF del historial médico completo de un paciente
 */
export const generateHistorialPDF = async (
  paciente: Paciente,
  embarazos: Embarazo[],
  controles: ControlPrenatal[]
): Promise<void> => {
  // Crear contenido HTML para el PDF
  const htmlContent = `
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <title>Historial Médico - ${paciente.nombre} ${paciente.apellido}</title>
      <style>
        body {
          font-family: Arial, sans-serif;
          margin: 20px;
          color: #333;
        }
        .header {
          text-align: center;
          border-bottom: 3px solid #1890ff;
          padding-bottom: 20px;
          margin-bottom: 30px;
        }
        .header h1 {
          color: #1890ff;
          margin: 0;
        }
        .header p {
          margin: 5px 0;
          color: #666;
        }
        .section {
          margin-bottom: 30px;
          page-break-inside: avoid;
        }
        .section-title {
          background: #1890ff;
          color: white;
          padding: 10px;
          margin-bottom: 15px;
          font-size: 16px;
          font-weight: bold;
        }
        table {
          width: 100%;
          border-collapse: collapse;
          margin-bottom: 20px;
        }
        th, td {
          border: 1px solid #ddd;
          padding: 8px;
          text-align: left;
        }
        th {
          background-color: #f0f0f0;
          font-weight: bold;
        }
        .info-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 10px;
        }
        .info-item {
          padding: 10px;
          background: #f9f9f9;
          border-left: 3px solid #1890ff;
        }
        .info-item label {
          font-weight: bold;
          color: #666;
          font-size: 12px;
        }
        .info-item value {
          display: block;
          font-size: 14px;
          margin-top: 4px;
        }
        .alerta {
          padding: 10px;
          margin: 5px 0;
          border-left: 4px solid #ff4d4f;
          background: #fff1f0;
        }
        .footer {
          margin-top: 50px;
          text-align: center;
          font-size: 12px;
          color: #999;
          border-top: 1px solid #ddd;
          padding-top: 20px;
        }
      </style>
    </head>
    <body>
      <!-- HEADER -->
      <div class="header">
        <h1>HISTORIAL MÉDICO OBSTÉTRICO</h1>
        <p><strong>Fetal Medical Foundation</strong></p>
        <p>Sistema de Gestión Médica</p>
        <p>Fecha de Generación: ${new Date().toLocaleDateString('es-ES')}</p>
      </div>

      <!-- INFORMACIÓN PERSONAL -->
      <div class="section">
        <div class="section-title">INFORMACIÓN PERSONAL</div>
        <div class="info-grid">
          <div class="info-item">
            <label>Nombre Completo:</label>
            <value>${paciente.nombre} ${paciente.apellido}</value>
          </div>
          <div class="info-item">
            <label>DNI:</label>
            <value>${paciente.dni}</value>
          </div>
          <div class="info-item">
            <label>Fecha de Nacimiento:</label>
            <value>${new Date(paciente.fecha_nacimiento).toLocaleDateString('es-ES')}</value>
          </div>
          <div class="info-item">
            <label>Edad:</label>
            <value>${paciente.edad} años</value>
          </div>
          <div class="info-item">
            <label>Teléfono:</label>
            <value>${paciente.telefono}</value>
          </div>
          <div class="info-item">
            <label>Email:</label>
            <value>${paciente.email || '-'}</value>
          </div>
          <div class="info-item">
            <label>Dirección:</label>
            <value>${paciente.direccion || '-'}</value>
          </div>
          <div class="info-item">
            <label>Grupo Sanguíneo:</label>
            <value>${paciente.grupo_sanguineo ? `${paciente.grupo_sanguineo}${paciente.factor_rh}` : '-'}</value>
          </div>
        </div>
      </div>

      <!-- HISTORIA OBSTÉTRICA -->
      <div class="section">
        <div class="section-title">HISTORIA OBSTÉTRICA (GPAC)</div>
        <table>
          <tr>
            <th>Gestas</th>
            <th>Partos</th>
            <th>Abortos</th>
            <th>Cesáreas</th>
          </tr>
          <tr>
            <td>${paciente.gestas || 0}</td>
            <td>${paciente.partos || 0}</td>
            <td>${paciente.abortos || 0}</td>
            <td>${paciente.cesareas || 0}</td>
          </tr>
        </table>
      </div>

      <!-- ANTECEDENTES -->
      <div class="section">
        <div class="section-title">ANTECEDENTES</div>
        <div class="info-grid">
          <div class="info-item">
            <label>Antecedentes Personales:</label>
            <value>${paciente.antecedentes_personales || 'Ninguno registrado'}</value>
          </div>
          <div class="info-item">
            <label>Antecedentes Familiares:</label>
            <value>${paciente.antecedentes_familiares || 'Ninguno registrado'}</value>
          </div>
          <div class="info-item">
            <label>Alergias:</label>
            <value>${paciente.alergias || 'Ninguna registrada'}</value>
          </div>
          <div class="info-item">
            <label>Medicación Habitual:</label>
            <value>${paciente.medicacion_habitual || 'Ninguna registrada'}</value>
          </div>
        </div>
      </div>

      <!-- EMBARAZOS -->
      <div class="section">
        <div class="section-title">HISTORIAL DE EMBARAZOS (${embarazos.length})</div>
        ${embarazos.length > 0 ? `
          <table>
            <thead>
              <tr>
                <th>FUR</th>
                <th>FPP</th>
                <th>Tipo</th>
                <th>Riesgo</th>
                <th>Estado</th>
              </tr>
            </thead>
            <tbody>
              ${embarazos.map(e => `
                <tr>
                  <td>${new Date(e.fur).toLocaleDateString('es-ES')}</td>
                  <td>${new Date(e.fpp).toLocaleDateString('es-ES')}</td>
                  <td>${e.embarazo_multiple ? `Múltiple (${e.numero_fetos})` : 'Único'}</td>
                  <td>${e.alto_riesgo ? '<strong style="color: red;">ALTO RIESGO</strong>' : 'Normal'}</td>
                  <td>${e.estado.toUpperCase()}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        ` : '<p>No hay embarazos registrados</p>'}
      </div>

      <!-- CONTROLES PRENATALES -->
      <div class="section">
        <div class="section-title">HISTORIAL DE CONTROLES PRENATALES (${controles.length})</div>
        ${controles.length > 0 ? `
          <table>
            <thead>
              <tr>
                <th>N°</th>
                <th>Fecha</th>
                <th>EG</th>
                <th>Peso (kg)</th>
                <th>PA (mmHg)</th>
                <th>FCF (lpm)</th>
                <th>Alertas</th>
              </tr>
            </thead>
            <tbody>
              ${controles.map(c => `
                <tr>
                  <td>${c.numero_control}</td>
                  <td>${new Date(c.fecha_control).toLocaleDateString('es-ES')}</td>
                  <td>${c.eg_semanas}s ${c.eg_dias}d</td>
                  <td>${c.peso}</td>
                  <td>${c.presion_arterial_sistolica}/${c.presion_arterial_diastolica}</td>
                  <td>${c.fcf || '-'}</td>
                  <td>${c.alertas && c.alertas.length > 0 ? `<strong style="color: red;">${c.alertas.length}</strong>` : 'Sin alertas'}</td>
                </tr>
                ${c.alertas && c.alertas.length > 0 ? `
                  <tr>
                    <td colspan="7">
                      ${c.alertas.map(a => `
                        <div class="alerta">
                          <strong>${a.severidad.toUpperCase()}</strong>: ${a.mensaje}
                          ${a.accion ? `<br><em>Acción: ${a.accion}</em>` : ''}
                        </div>
                      `).join('')}
                    </td>
                  </tr>
                ` : ''}
              `).join('')}
            </tbody>
          </table>
        ` : '<p>No hay controles prenatales registrados</p>'}
      </div>

      <!-- FOOTER -->
      <div class="footer">
        <p><strong>Fetal Medical Foundation</strong> - Sistema de Historial Médico Obstétrico</p>
        <p>Este documento es confidencial y contiene información médica sensible</p>
        <p>Generado el ${new Date().toLocaleString('es-ES')}</p>
      </div>
    </body>
    </html>
  `;

  // Abrir ventana de impresión
  const printWindow = window.open('', '_blank');
  if (printWindow) {
    printWindow.document.write(htmlContent);
    printWindow.document.close();

    // Esperar a que se cargue el contenido y luego imprimir
    printWindow.onload = () => {
      printWindow.print();
    };
  }
};

/**
 * Genera PDF simplificado (alternativa ligera)
 */
export const generateSimplePDF = (paciente: Paciente): void => {
  const content = `
    HISTORIAL MÉDICO - ${paciente.nombre} ${paciente.apellido}
    =========================================

    DNI: ${paciente.dni}
    Edad: ${paciente.edad} años
    Teléfono: ${paciente.telefono}
    Email: ${paciente.email || 'No registrado'}

    HISTORIA OBSTÉTRICA (GPAC):
    - Gestas: ${paciente.gestas || 0}
    - Partos: ${paciente.partos || 0}
    - Abortos: ${paciente.abortos || 0}
    - Cesáreas: ${paciente.cesareas || 0}

    Generado: ${new Date().toLocaleString('es-ES')}
  `;

  // Crear blob y descargar
  const blob = new Blob([content], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `historial_${paciente.dni}_${Date.now()}.txt`;
  a.click();
  URL.revokeObjectURL(url);
};

export default {
  generateHistorialPDF,
  generateSimplePDF,
};
