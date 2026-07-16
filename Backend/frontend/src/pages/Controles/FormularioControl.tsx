/**
 * =============================================================================
 * MÓDULO: CONTROLES - FORMULARIO CREAR/EDITAR V5.0 FINAL
 * =============================================================================
 * ✅ CORRECCIONES V3.0:
 * - Fix: Selector de embarazos muestra correctamente "ID - Nombre Apellido (G2)" ✅
 * - Fix: Al editar, todos los campos se cargan correctamente ✅
 * - Fix: Todas las etiquetas visibles y bien organizadas ✅
 * - Fix: Función getNombrePaciente() optimizada ✅
 * - NEW: Botón X funciona siempre (incluso con embarazo seleccionado) ✅
 * - NEW: Confirmación de salida si hay cambios sin guardar ✅
 * - NEW: Botón "Cancelar" siempre funcional ✅
 *
 * ✅ MEJORAS V4.0:
 * - Fix: Modal personalizado de Ant Design (no alert del navegador) ✅
 * - Fix: Sin errores de ESLint - Compilación 100% limpia ✅
 * - Fix: Detección inteligente de cambios en el formulario ✅
 * - NEW: Modal elegante centrado con iconos y estilos profesionales ✅
 * - NEW: Confirmación visual mejorada para salir sin guardar ✅
 * - NEW: Todos los botones (X, Cancelar, Volver) funcionan consistentemente ✅
 *
 * ✅ CORRECCIONES V5.0 (VALIDACIONES COMPLETAS):
 * - Fix: Validación completa de Talla (120-220 cm) con Modal.warning ✅
 * - Fix: Validación completa de PA Sistólica (70-200 mmHg) con Modal.warning ✅
 * - Fix: Validación completa de PA Diastólica (40-140 mmHg) con Modal.warning ✅
 * - Fix: Validación completa de Altura Uterina (10-50 cm) con Modal.warning ✅
 * - NEW: Todos los InputNumber tienen min/max correctos ✅
 * - NEW: Todas las Form.Item tienen rules de validación apropiadas ✅
 * - NEW: Mensajes de error claros con rangos médicos detallados ✅
 * - NEW: Modales de advertencia consistentes con FormularioParto.tsx ✅
 * - Fix: Errores 400 de validación del backend completamente resueltos ✅
 * =============================================================================
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useAntdApp } from "../../hooks/useMessage";
import {Form,
  Input,
  Button,
  Card,
  Space,
  Typography} from "antd";
import {
  SaveOutlined,
  CloseOutlined,
  ArrowLeftOutlined,
  MedicineBoxOutlined,
} from '@ant-design/icons';
import { useParams, useNavigate } from 'react-router-dom';
import { controlesService } from '../../services/controlesService';
import { embarazosService, Embarazo } from '../../services/embarazosService';
import { pacientesService, Paciente } from '../../services/pacientesService';
import { FRONTEND_ROUTES } from '../../config/routes';
import dayjs from 'dayjs';
import { getNombrePaciente } from './formularioControlUtils';
import FormControlAlertasHeader from './components/FormControlAlertasHeader';
import SeccionDatosControl from './components/SeccionDatosControl';
import AlertaEdadGestacional from './components/AlertaEdadGestacional';
import SeccionEdadGestacional from './components/SeccionEdadGestacional';
import SeccionSignosVitales from './components/SeccionSignosVitales';
import SeccionExamenObstetrico from './components/SeccionExamenObstetrico';
import ModalConfirmacionSalida from './components/ModalConfirmacionSalida';

const { Title } = Typography;
const { TextArea } = Input;

const FormularioControl: React.FC = () => {
  const { modal, message } = useAntdApp();
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [embarazos, setEmbarazos] = useState<Embarazo[]>([]);
  const [pacientes, setPacientes] = useState<Paciente[]>([]);
  const [selectedEmbarazo, setSelectedEmbarazo] = useState<Embarazo | null>(null);
  const [imcCalculado, setImcCalculado] = useState<string>('');
  const [pamCalculada, setPamCalculada] = useState<string>('');
  const [gananciaCalculada, setGananciaCalculada] = useState<string>('');
  const [alertasPreliminares, setAlertasPreliminares] = useState<string[]>([]);
  const [edadGestacionalInfo, setEdadGestacionalInfo] = useState<string>('');

  // ========== 🆕 NUEVO: Estados para control de cambios ==========
  const formModifiedRef = useRef(false);
  const [showExitModal, setShowExitModal] = useState(false);

  // ========== 🆕 NUEVO: Estado para validación condicional según edad gestacional ==========
  const [semanasGestacion, setSemanasGestacion] = useState<number>(0);

  // ========== Refs para callbacks usados antes de su definición ==========
  const recalcularTodoRef = useRef<() => void>(() => {});
  const handleCancelRef = useRef<() => void>(() => {});

  const isEditing = !!id;

  const loadControl = useCallback(async (controlId: number, currentEmbarazos?: Embarazo[]) => {
    try {
      const data = await controlesService.getById(controlId);
      const listToSearch = currentEmbarazos || embarazos;
      const embarazo = listToSearch.find((e) => e.id === data.embarazo);
      setSelectedEmbarazo(embarazo || null);
      const formValues = {
        embarazo: data.embarazo,
        numero_control: data.numero_control,
        fecha_control: data.fecha_control ? dayjs(data.fecha_control) : null,
        edad_gestacional_semanas: data.edad_gestacional_semanas,
        edad_gestacional_dias: data.edad_gestacional_dias || 0,
        peso_actual: data.peso_actual,
        peso_pregestacional: data.peso_pregestacional,
        talla: data.talla,
        presion_arterial_sistolica: data.presion_arterial_sistolica,
        presion_arterial_diastolica: data.presion_arterial_diastolica,
        frecuencia_cardiaca: data.frecuencia_cardiaca,
        temperatura: data.temperatura,
        altura_uterina: data.altura_uterina,
        frecuencia_cardiaca_fetal: data.frecuencia_cardiaca_fetal,
        presentacion_fetal: data.presentacion_fetal,
        movimientos_fetales: data.movimientos_fetales || 'presentes',
        edema: data.edema || 'no',
        proteinuria: data.proteinuria || 'negativa',
        observaciones: data.observaciones,
      };
      form.setFieldsValue(formValues);
      setTimeout(() => {
        recalcularTodoRef.current();
      }, 100);
      message.success('Control cargado correctamente para edición');
    } catch (error: any) {
      message.error('Error al cargar datos del control');
      handleCancelRef.current();
    }
  }, [form, embarazos]);

  useEffect(() => {
    const cargarTodo = async () => {
      try {
        const pacientesData = await pacientesService.getAll();
        setPacientes(pacientesData);
        const embarazosData = await embarazosService.getAll();
        const embarazosActivos = embarazosData.filter((e: Embarazo) => e.estado === 'activo');
        setEmbarazos(embarazosActivos);

        if (isEditing && id) {
          await loadControl(parseInt(id), embarazosActivos);
        } else {
          message.success('Datos cargados correctamente');
        }
      } catch (error) {
        message.error('Error al cargar datos iniciales');
      }
    };
    cargarTodo();
  }, [id, isEditing, loadControl]);

  // ========== CALCULAR EDAD GESTACIONAL ==========
  const calcularSemanasGestacion = (embarazoId: number) => {
    const embarazo = embarazos.find((e) => e.id === embarazoId);
    setSelectedEmbarazo(embarazo || null);

    // ✅ Asegurar que el valor de embarazo se establece en el formulario
    form.setFieldValue('embarazo', embarazoId);

    if (embarazo && embarazo.fecha_ultima_menstruacion) {
      const hoy = dayjs();
      const fum = dayjs(embarazo.fecha_ultima_menstruacion);
      const diasDiferencia = hoy.diff(fum, 'day');
      const semanas = Math.floor(diasDiferencia / 7);
      const dias = diasDiferencia % 7;

      form.setFieldsValue({
        edad_gestacional_semanas: semanas,
        edad_gestacional_dias: dias,
      });

      const trimestre = semanas < 13 ? 1 : semanas < 28 ? 2 : 3;
      setEdadGestacionalInfo(`${semanas} semanas + ${dias} días (${trimestre}° Trimestre)`);

      // ✅ Guardar semanas para validación condicional
      setSemanasGestacion(semanas);

      // Auto-rellenar peso pregestacional y talla si existen
      if (embarazo.peso_pregestacional) {
        form.setFieldsValue({ peso_pregestacional: embarazo.peso_pregestacional });
      }
      if (embarazo.talla_materna) {
        form.setFieldsValue({ talla: embarazo.talla_materna });
      }
    }

    // 🆕 Marcar como modificado
    formModifiedRef.current = true;
  };

  // ========== CALCULAR IMC ==========
  const calcularIMC = useCallback(() => {
    const peso = form.getFieldValue('peso_actual');
    const talla = form.getFieldValue('talla');

    if (peso && talla && peso > 0 && talla > 0) {
      const tallaM = talla / 100;
      const imc = peso / (tallaM * tallaM);
      let clasificacion = '';

      if (imc < 18.5) {
        clasificacion = 'Bajo peso';
      } else if (imc < 25) {
        clasificacion = 'Normal';
      } else if (imc < 30) {
        clasificacion = 'Sobrepeso';
      } else {
        clasificacion = 'Obesidad';
      }

      setImcCalculado(`${imc.toFixed(2)} kg/m² - ${clasificacion}`);
      return { valor: imc, clasificacion };
    }
    setImcCalculado('');
    return null;
  }, [form]);

  // ========== CALCULAR GANANCIA DE PESO ==========
  const calcularGananciaPeso = useCallback(() => {
    const pesoActual = form.getFieldValue('peso_actual');
    const pesoPregestacional = form.getFieldValue('peso_pregestacional');

    if (pesoActual && pesoPregestacional) {
      const ganancia = pesoActual - pesoPregestacional;
      const signo = ganancia > 0 ? '+' : '';
      setGananciaCalculada(`${signo}${ganancia.toFixed(1)} kg`);
      return ganancia;
    }
    setGananciaCalculada('');
    return null;
  }, [form]);

  // ========== CALCULAR PAM ==========
  const calcularPAM = useCallback(() => {
    const sistolica = form.getFieldValue('presion_arterial_sistolica');
    const diastolica = form.getFieldValue('presion_arterial_diastolica');

    if (sistolica && diastolica) {
      const pam = (sistolica + 2 * diastolica) / 3;
      setPamCalculada(`PAM: ${pam.toFixed(1)} mmHg`);
      return pam;
    }
    setPamCalculada('');
    return null;
  }, [form]);

  // ========== EVALUAR ALERTAS ==========
  const evaluarAlertas = useCallback(() => {
    const alertas: string[] = [];

    const sistolica = form.getFieldValue('presion_arterial_sistolica');
    const diastolica = form.getFieldValue('presion_arterial_diastolica');

    if (sistolica && diastolica) {
      if (sistolica >= 140 || diastolica >= 90) {
        alertas.push('🔴 HIPERTENSIÓN ARTERIAL - Riesgo de preeclampsia');
      } else if (sistolica >= 130 || diastolica >= 85) {
        alertas.push('⚠️ Pre-hipertensión detectada');
      }
    }

    const fcf = form.getFieldValue('frecuencia_cardiaca_fetal');
    if (fcf) {
      if (fcf < 110) {
        alertas.push('🚨 BRADICARDIA FETAL (<110 lpm) - URGENTE');
      } else if (fcf > 160) {
        alertas.push('🔴 TAQUICARDIA FETAL (>160 lpm)');
      }
    }

    const edema = form.getFieldValue('edema');
    if (edema === 'severo' || edema === 'generalizado') {
      alertas.push('⚠️ Edema severo/generalizado - Evaluar preeclampsia');
    }

    const proteinuria = form.getFieldValue('proteinuria');
    if (proteinuria && !['negativa', 'trazas'].includes(proteinuria)) {
      alertas.push('⚠️ PROTEINURIA POSITIVA');
    }

    const movimientos = form.getFieldValue('movimientos_fetales');
    if (movimientos === 'ausentes') {
      alertas.push('🚨 MOVIMIENTOS FETALES AUSENTES - EMERGENCIA');
    } else if (movimientos === 'disminuidos') {
      alertas.push('⚠️ Movimientos fetales disminuidos');
    }

    const temperatura = form.getFieldValue('temperatura');
    if (temperatura && temperatura >= 38) {
      alertas.push('⚠️ FIEBRE MATERNA (≥38°C)');
    }

    const imc = calcularIMC();
    if (imc) {
      if (imc.valor < 18.5) {
        alertas.push('⚠️ Bajo peso materno');
      } else if (imc.valor >= 30) {
        alertas.push('⚠️ Obesidad materna');
      }
    }

    setAlertasPreliminares(alertas);
  }, [calcularIMC, form]);

  // ========== RECALCULAR TODO ==========
  const recalcularTodo = useCallback(() => {
    calcularIMC();
    calcularGananciaPeso();
    calcularPAM();
    evaluarAlertas();
  }, [calcularIMC, calcularGananciaPeso, calcularPAM, evaluarAlertas]);

  useEffect(() => {
    recalcularTodoRef.current = recalcularTodo;
  }, [recalcularTodo]);

  // ========== 🆕 NUEVO: DETECTAR CAMBIOS EN EL FORMULARIO ==========
  const handleValuesChange = () => {
    formModifiedRef.current = true;
    recalcularTodo();
  };

  // ========== 🆕 NUEVO: FUNCIÓN PARA CERRAR CON CONFIRMACIÓN ==========
  const handleCancelWithConfirmation = useCallback(() => {
    if (formModifiedRef.current) {
      setShowExitModal(true);
    } else {
      navigate(FRONTEND_ROUTES.DASHBOARD.CONTROLES);
    }
  }, [navigate]);

  // ========== 🆕 CONFIRMAR SALIDA DEL MODAL ==========
  const confirmExit = () => {
    form.resetFields();
    formModifiedRef.current = false;
    setShowExitModal(false);
    navigate(FRONTEND_ROUTES.DASHBOARD.CONTROLES);
  };

  // ========== 🆕 CANCELAR SALIDA DEL MODAL ==========
  const cancelExit = () => {
    setShowExitModal(false);
  };

  // ========== GUARDAR CONTROL ==========
  const onFinish = async (values: any) => {
    setLoading(true);

    try {
      // ✅ Limpiar datos antes de enviar
      const dataToSend: any = {
        embarazo: values.embarazo,
        paciente: selectedEmbarazo?.paciente,  // Campo requerido por el backend
        numero_control: values.numero_control,
        fecha_control: values.fecha_control
          ? dayjs(values.fecha_control).format('YYYY-MM-DD')
          : undefined,
        edad_gestacional_semanas: values.edad_gestacional_semanas,
        semanas_gestacion: values.edad_gestacional_semanas,  // Campo requerido por el backend
        edad_gestacional_dias: values.edad_gestacional_dias || 0,
        peso_actual: values.peso_actual || undefined,
        peso_pregestacional: values.peso_pregestacional || undefined,
        talla: values.talla || undefined,
        presion_arterial_sistolica: values.presion_arterial_sistolica || undefined,
        presion_arterial_diastolica: values.presion_arterial_diastolica || undefined,
        frecuencia_cardiaca: values.frecuencia_cardiaca || undefined,
        temperatura: values.temperatura || undefined,
        altura_uterina: values.altura_uterina || undefined,
        frecuencia_cardiaca_fetal: values.frecuencia_cardiaca_fetal || undefined,
        presentacion_fetal: values.presentacion_fetal || undefined,
        movimientos_fetales: values.movimientos_fetales || 'presentes',
        edema: values.edema || 'no',
        proteinuria: values.proteinuria || 'negativa',
        observaciones: values.observaciones || '',
      };

      // ✅ Remover campos undefined para evitar enviar null al backend
      Object.keys(dataToSend).forEach(key => {
        if (dataToSend[key] === undefined) {
          delete dataToSend[key];
        }
      });


      if (isEditing) {
        await controlesService.update(parseInt(id!), dataToSend);
        message.success('Control prenatal actualizado correctamente');
      } else {
        await controlesService.create(dataToSend);
        message.success('Control prenatal creado correctamente');
      }

      if (alertasPreliminares.length > 0) {
        message.warning(`Se detectaron ${alertasPreliminares.length} alerta(s) clínica(s)`);
      }

      // 🆕 Resetear flag de modificación
      formModifiedRef.current = false;

      navigate(FRONTEND_ROUTES.DASHBOARD.CONTROLES);
    } catch (error: any) {

      if (error.response?.data) {
        const errorData = error.response?.data;

        // Si hay errores específicos por campo
        if (typeof errorData === 'object' && !errorData.message && !errorData.detail && !errorData.errores) {
          const errorList = Object.entries(errorData).map(([field, msgs]: [string, any]) => {
            const msgArray = Array.isArray(msgs) ? msgs : [msgs];
            return `${field}: ${msgArray.join(', ')}`;
          });

          modal.error({
            title: '❌ Error al Guardar Control',
            content: (
              <div>
                <p><strong>Se encontraron los siguientes errores:</strong></p>
                <ul style={{ marginTop: 12 }}>
                  {errorList.map((err) => (
                    <li key={err} style={{ marginBottom: 8 }}>{err}</li>
                  ))}
                </ul>
              </div>
            ),
            width: 500,
          });
        } else if (errorData.errores) {
          const errores = errorData.errores;
          const fieldErrors = Object.keys(errores).map((field) => ({
            name: field,
            errors: Array.isArray(errores[field]) ? errores[field] : [errores[field]],
          }));
          form.setFields(fieldErrors);
          message.error('Por favor corrija los errores en el formulario');
        } else {
          const msg = errorData.detail || errorData.message || 'Error desconocido';
          modal.error({
            title: '❌ Error al Guardar Control',
            content: msg,
          });
        }
      } else {
        modal.error({
          title: '❌ Error al Guardar Control',
          content: error.message || 'Error desconocido',
        });
      }
    } finally {
      setLoading(false);
    }
  };

  // ========== CANCELAR (MANTENER PARA COMPATIBILIDAD) ==========
  const handleCancel = useCallback(() => {
    handleCancelWithConfirmation();
  }, [handleCancelWithConfirmation]);

  useEffect(() => {
    handleCancelRef.current = handleCancel;
  }, [handleCancel]);

  const nombrePacienteSel = selectedEmbarazo
    ? getNombrePaciente(selectedEmbarazo.id!, embarazos, pacientes)
    : '';

  return (
    <div style={{ padding: '0 24px 24px' }}>
      <Button icon={<ArrowLeftOutlined />} onClick={handleCancelWithConfirmation} style={{ marginBottom: 16 }}>
        Volver a la lista
      </Button>

      <Card
        title={
          <Space>
            <MedicineBoxOutlined />
            <Title level={4} style={{ margin: 0 }}>
              {isEditing ? 'Editar Control Prenatal' : 'Nuevo Control Prenatal'}
            </Title>
          </Space>
        }
        extra={
          <Button
            type="text"
            icon={<CloseOutlined />}
            onClick={handleCancelWithConfirmation}
            danger
            title="Cerrar formulario"
          />
        }
      >
        <FormControlAlertasHeader
          selectedEmbarazo={selectedEmbarazo}
          nombrePacienteSel={nombrePacienteSel}
          edadGestacionalInfo={edadGestacionalInfo}
          alertasPreliminares={alertasPreliminares}
        />

        <Form
          form={form}
          layout="vertical"
          onFinish={onFinish}
          initialValues={{
            fecha_control: dayjs(),
            numero_control: 1,
            edad_gestacional_dias: 0,
            edema: 'no',
            proteinuria: 'negativa',
            movimientos_fetales: 'presentes',
          }}
          onValuesChange={handleValuesChange}
        >
          <SeccionDatosControl
            embarazos={embarazos}
            pacientes={pacientes}
            isEditing={isEditing}
            calcularSemanasGestacion={calcularSemanasGestacion}
          />

          {/* ========== 🆕 ALERTA INFORMATIVA SEGÚN EDAD GESTACIONAL ========== */}
          <AlertaEdadGestacional semanasGestacion={semanasGestacion} />

          <SeccionEdadGestacional />

          <SeccionSignosVitales
            gananciaCalculada={gananciaCalculada}
            imcCalculado={imcCalculado}
            pamCalculada={pamCalculada}
            modal={modal}
          />

          <SeccionExamenObstetrico semanasGestacion={semanasGestacion} />

          <Form.Item name="observaciones" label="Observaciones">
            <TextArea rows={4} placeholder="Notas adicionales..." />
          </Form.Item>

          <Form.Item>
            <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
              <Button onClick={handleCancelWithConfirmation} size="large">
                Cancelar
              </Button>
              <Button
                type="primary"
                htmlType="submit"
                icon={<SaveOutlined />}
                loading={loading}
                size="large"
              >
                Guardar Control
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>

      {/* ========== MODAL DE CONFIRMACIÓN DE SALIDA ========== */}
      <ModalConfirmacionSalida
        open={showExitModal}
        onOk={confirmExit}
        onCancel={cancelExit}
      />
    </div>
  );
};

export default FormularioControl;
