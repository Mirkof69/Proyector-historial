/**
 * =============================================================================
 * FORMULARIO DE NOTA DE EVOLUCIÓN MÉDICA - COMPLETO Y EXTENSO
 * =============================================================================
 * Formulario completo para registrar notas de evolución médica
 * Incluye: signos vitales, datos obstétricos, examen físico, diagnósticos
 * =============================================================================
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useAntdApp } from "../../hooks/useMessage";
import { useAuth } from "../../hooks/useAuth";
import {Form,
  Button,
  Card,
  Space,
  Row,
  Col,
  Alert} from "antd";
import {
  SaveOutlined,
  CloseOutlined,
  WarningOutlined,
  FileTextOutlined,
} from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import dayjs from 'dayjs';
import { notasEvolucionService, NotaEvolucionCreate } from '../../services/notasEvolucionService';
import { pacientesService } from '../../services/pacientesService';
import { datosClinicosService } from '../../services/datosClinicosService';
import SeccionInfoConsultaNota from './components/SeccionInfoConsultaNota';
import SeccionSignosVitalesNota from './components/SeccionSignosVitalesNota';
import SeccionObstetricosNota from './components/SeccionObstetricosNota';
import SeccionExamenDiagnosticoNota from './components/SeccionExamenDiagnosticoNota';

const FormularioNotaEvolucion: React.FC = () => {
  const { message } = useAntdApp();
  const { user } = useAuth();
  const [form] = Form.useForm();
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [loading, setLoading] = useState(false);
  const [pacientes, setPacientes] = useState<any[]>([]);
  const [alertas, setAlertas] = useState<string[]>([]);
  const [presionArterial, setPresionArterial] = useState<string>('');
  const [edadGestacional, setEdadGestacional] = useState<string>('');
  const [notaAnterior, setNotaAnterior] = useState<{
    mensaje: string;
    tipo: 'success' | 'info' | 'warning';
  } | null>(null);

  const calcularAlertas = useCallback((valores?: any) => {
    const alertasDetectadas: string[] = [];
    const data = valores || form.getFieldsValue();
    if (data.presion_arterial_sistolica >= 140 || data.presion_arterial_diastolica >= 90) {
      alertasDetectadas.push('Presión arterial elevada (Hipertensión)');
    }
    if (data.presion_arterial_sistolica < 90 || data.presion_arterial_diastolica < 60) {
      alertasDetectadas.push('Presión arterial baja (Hipotensión)');
    }
    if (data.temperatura >= 38) {
      alertasDetectadas.push('Fiebre detectada');
    }
    if (data.temperatura < 36) {
      alertasDetectadas.push('Hipotermia detectada');
    }
    if (data.frecuencia_cardiaca > 100) {
      alertasDetectadas.push('Taquicardia detectada');
    }
    if (data.frecuencia_cardiaca < 60) {
      alertasDetectadas.push('Bradicardia detectada');
    }
    if (data.frecuencia_respiratoria > 20) {
      alertasDetectadas.push('Taquipnea detectada');
    }
    if (data.frecuencia_respiratoria < 12) {
      alertasDetectadas.push('Bradipnea detectada');
    }
    if (data.saturacion_oxigeno && data.saturacion_oxigeno < 95) {
      alertasDetectadas.push('Saturación de oxígeno baja');
    }
    if (data.frecuencia_cardiaca_fetal && (data.frecuencia_cardiaca_fetal < 110 || data.frecuencia_cardiaca_fetal > 160)) {
      alertasDetectadas.push('Frecuencia cardíaca fetal fuera de rango normal');
    }
    setAlertas(alertasDetectadas);
  }, [form]);

  const cargarDatos = useCallback(async () => {
    try {
      const pacientesData = await pacientesService.getAll();
      setPacientes(pacientesData);
    } catch (error) {
      message.error('Error al cargar los datos');
    }
  }, []);

  const cargarNota = useCallback(async (notaId: number) => {
    setLoading(true);
    try {
      const nota = await notasEvolucionService.getNotaById(notaId);

      // Convertir fecha a dayjs
      const formValues = {
        ...nota,
        fecha_consulta: nota.fecha_consulta ? dayjs(nota.fecha_consulta) : null,
      };

      form.setFieldsValue(formValues);
      calcularAlertas(nota);

      if (nota.presion_arterial_sistolica && nota.presion_arterial_diastolica) {
        setPresionArterial(`${nota.presion_arterial_sistolica}/${nota.presion_arterial_diastolica}`);
      }

      if (nota.edad_gestacional_semanas && nota.edad_gestacional_dias) {
        setEdadGestacional(`${nota.edad_gestacional_semanas}s ${nota.edad_gestacional_dias}d`);
      }
    } catch (error) {
      message.error('Error al cargar la nota de evolución');
    } finally {
      setLoading(false);
    }
  }, [calcularAlertas, form]);

  useEffect(() => {
    cargarDatos();
    if (id) {
      cargarNota(parseInt(id));
    }
  }, [id, cargarDatos, cargarNota]);

  const handlePacienteChange = async (pacienteId: number) => {
    // Si estamos editando, no cargar datos anteriores
    if (id) return;

    setLoading(true);
    setNotaAnterior(null);

    try {
      // ✅ OBTENER DATOS CONSOLIDADOS DESDE TODAS LAS FUENTES
      const datosCompletos = await datosClinicosService.obtenerDatosCompletos(pacienteId);
      const { signosVitales, antecedentes, embarazoActual, alertas: alertasGeneradas, fuentes } = datosCompletos;

      // ✅ Usar antecedentes para validación - verificar si tiene condiciones de riesgo
      const tieneAntecedentesRiesgo = antecedentes && (
        antecedentes.enfermedades_cronicas ||
        antecedentes.enfermedades_previas ||
        antecedentes.medicamentos_actuales
      );

      // ========================================================================
      // MOSTRAR ALERTA SI TIENE ANTECEDENTES DE RIESGO
      // ========================================================================
      if (tieneAntecedentesRiesgo && alertasGeneradas.length > 0) {
        setAlertas([
          'Paciente con antecedentes médicos de riesgo',
          ...alertasGeneradas
        ]);
      }

      // ========================================================================
      // AUTO-COMPLETAR SIGNOS VITALES Y DATOS OBSTÉTRICOS
      // ========================================================================
      const datosFormulario: any = {};

      // Signos vitales (de triaje, notas de evolución o controles prenatales)
      if (signosVitales.presion_sistolica) datosFormulario.presion_arterial_sistolica = signosVitales.presion_sistolica;
      if (signosVitales.presion_diastolica) datosFormulario.presion_arterial_diastolica = signosVitales.presion_diastolica;
      if (signosVitales.temperatura) datosFormulario.temperatura = signosVitales.temperatura;
      if (signosVitales.frecuencia_cardiaca) datosFormulario.frecuencia_cardiaca = signosVitales.frecuencia_cardiaca;
      if (signosVitales.frecuencia_respiratoria) datosFormulario.frecuencia_respiratoria = signosVitales.frecuencia_respiratoria;
      if (signosVitales.saturacion_oxigeno) datosFormulario.saturacion_oxigeno = signosVitales.saturacion_oxigeno;

      // Actualizar presión arterial en formato "120/80"
      if (signosVitales.presion_sistolica && signosVitales.presion_diastolica) {
        setPresionArterial(`${signosVitales.presion_sistolica}/${signosVitales.presion_diastolica}`);
      }

      // Datos obstétricos si hay embarazo activo
      if (embarazoActual?.embarazo) {
        datosFormulario.embarazo = embarazoActual.embarazo.id;

        // Datos del último control prenatal
        if (embarazoActual.datosObstetricos) {
          if (embarazoActual.datosObstetricos.edad_gestacional_semanas) {
            datosFormulario.edad_gestacional_semanas = embarazoActual.datosObstetricos.edad_gestacional_semanas;
          }
          if (embarazoActual.datosObstetricos.edad_gestacional_dias !== undefined) {
            datosFormulario.edad_gestacional_dias = embarazoActual.datosObstetricos.edad_gestacional_dias;
          }
          if (embarazoActual.datosObstetricos.altura_uterina) {
            datosFormulario.altura_uterina = embarazoActual.datosObstetricos.altura_uterina;
          }
          if (embarazoActual.datosObstetricos.frecuencia_cardiaca_fetal) {
            datosFormulario.frecuencia_cardiaca_fetal = embarazoActual.datosObstetricos.frecuencia_cardiaca_fetal;
          }

          // Actualizar edad gestacional en formato "Xs Yd"
          if (embarazoActual.datosObstetricos.edad_gestacional_semanas) {
            const semanas = embarazoActual.datosObstetricos.edad_gestacional_semanas;
            const dias = embarazoActual.datosObstetricos.edad_gestacional_dias || 0;
            setEdadGestacional(`${semanas}s ${dias}d`);
          }
        }
      }

      // Aplicar todos los datos al formulario
      if (Object.keys(datosFormulario).length > 0) {
        form.setFieldsValue(datosFormulario);
      }

      // ========================================================================
      // ACTUALIZAR ALERTAS
      // ========================================================================
      if (alertasGeneradas.length > 0) {
        setAlertas(alertasGeneradas);
      }
      calcularAlertas();

      // ========================================================================
      // MENSAJE DE CONFIRMACIÓN
      // ========================================================================
      if (fuentes.length > 0) {
        const fuentesTraducidas = fuentes.map(f => {
          switch (f) {
            case 'triaje': return 'triaje';
            case 'nota_evolucion': return 'notas de evolución';
            case 'control_prenatal': return 'control prenatal';
            case 'controles_prenatales': return 'controles prenatales';
            case 'perfil_paciente': return 'perfil del paciente';
            case 'embarazo': return 'embarazo';
            case 'antecedentes_personales': return 'antecedentes personales';
            case 'antecedentes_obstetricos': return 'antecedentes obstétricos';
            case 'antecedentes_familiares': return 'antecedentes familiares';
            default: return f;
          }
        });

        setNotaAnterior({
          mensaje: `✓ Datos cargados desde: ${fuentesTraducidas.join(', ')}`,
          tipo: 'success'
        });
      } else {
        setNotaAnterior({
          mensaje: 'ℹ No tiene datos anteriores registrados',
          tipo: 'info'
        });
      }
    } catch (error) {
      setNotaAnterior({
        mensaje: '⚠ No se pudieron cargar todos los datos del paciente',
        tipo: 'warning'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleValuesChange = (changedValues: any, allValues: any) => {
    // Actualizar presión arterial compuesta
    if ('presion_arterial_sistolica' in changedValues || 'presion_arterial_diastolica' in changedValues) {
      if (allValues.presion_arterial_sistolica && allValues.presion_arterial_diastolica) {
        setPresionArterial(`${allValues.presion_arterial_sistolica}/${allValues.presion_arterial_diastolica}`);
      }
    }

    // Actualizar edad gestacional compuesta
    if ('edad_gestacional_semanas' in changedValues || 'edad_gestacional_dias' in changedValues) {
      if (allValues.edad_gestacional_semanas !== undefined && allValues.edad_gestacional_dias !== undefined) {
        setEdadGestacional(`${allValues.edad_gestacional_semanas}s ${allValues.edad_gestacional_dias}d`);
      }
    }

    // Calcular alertas
    if (
      'presion_arterial_sistolica' in changedValues ||
      'presion_arterial_diastolica' in changedValues ||
      'temperatura' in changedValues ||
      'frecuencia_cardiaca' in changedValues ||
      'saturacion_oxigeno' in changedValues ||
      'frecuencia_cardiaca_fetal' in changedValues
    ) {
      calcularAlertas(allValues);
    }
  };

  const handleSubmit = async (values: any) => {
    setLoading(true);
    try {
      // Convertir fecha a string ISO
      const notaData: NotaEvolucionCreate = {
        ...values,
        fecha_consulta: values.fecha_consulta ? values.fecha_consulta.toISOString() : new Date().toISOString(),
        medico: user?.id,
      };

      if (id) {
        await notasEvolucionService.actualizarNota(parseInt(id), notaData);
        message.success('Nota de evolución actualizada correctamente');
      } else {
        await notasEvolucionService.crearNota(notaData);
        message.success('Nota de evolución registrada correctamente');
      }

      navigate('/dashboard/notas-evolucion');
    } catch (error: any) {
      message.error(error?.response?.data?.message || 'Error al guardar la nota de evolución');
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    navigate('/dashboard/notas-evolucion');
  };

  const tiposConsulta = notasEvolucionService.getTiposConsulta();

  return (
    <div style={{ padding: 24 }}>
      <Card
        title={
          <Space>
            <FileTextOutlined style={{ fontSize: 24, color: '#1890ff' }} />
            <span style={{ fontSize: 20, fontWeight: 600 }}>
              {id ? 'Editar Nota de Evolución' : 'Nueva Nota de Evolución Médica'}
            </span>
          </Space>
        }
      >
        {alertas.length > 0 && (
          <Alert
            message="Alertas Clínicas Detectadas"
            description={
              <ul style={{ margin: 0, paddingLeft: 20 }}>
                {alertas.map((alerta) => (
                  <li key={alerta}>{alerta}</li>
                ))}
              </ul>
            }
            type="error"
            showIcon
            icon={<WarningOutlined />}
            style={{ marginBottom: 16 }}
          />
        )}

        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          onValuesChange={handleValuesChange}
          autoComplete="off"
          initialValues={{
            fecha_consulta: dayjs(),
            tipo_consulta: 'control_prenatal',
          }}
        >
          <SeccionInfoConsultaNota
            pacientes={pacientes}
            handlePacienteChange={handlePacienteChange}
            loading={loading}
            tiposConsulta={tiposConsulta}
            notaAnterior={notaAnterior}
            setNotaAnterior={setNotaAnterior}
          />

          <SeccionSignosVitalesNota presionArterial={presionArterial} />

          <SeccionObstetricosNota edadGestacional={edadGestacional} />

          <SeccionExamenDiagnosticoNota />

          {/* BOTONES DE ACCIÓN */}
          <Row justify="end" gutter={8} style={{ marginTop: 24 }}>
            <Col>
              <Button icon={<CloseOutlined />} onClick={handleCancel} size="large">
                Cancelar
              </Button>
            </Col>
            <Col>
              <Button
                type="primary"
                htmlType="submit"
                loading={loading}
                icon={<SaveOutlined />}
                size="large"
              >
                {id ? 'Actualizar' : 'Registrar'} Nota
              </Button>
            </Col>
          </Row>
        </Form>
      </Card>
    </div>
  );
};

export default FormularioNotaEvolucion;
