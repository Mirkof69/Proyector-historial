/**
 * =============================================================================
 * DETALLE DE PARTO - VISTA COMPLETA
 * =============================================================================
 * Muestra información completa de un parto específico
 * - Datos del parto y trabajo de parto
 * - Información del recién nacido
 * - Apgar scores y estado neonatal
 * - Complicaciones maternas y neonatales
 * - Procedimientos realizados
 * - Conexión: GET /partos/{id}/
 * =============================================================================
 */

import React, { useState, useEffect, useRef } from 'react';
import { useAntdApp } from "../../hooks/useMessage";
import { useNavigate, useParams } from 'react-router-dom';
import {Card,
  Button,
  Space,
  Tag,
  Alert,
  Row,
  Col,
  Divider,
  Spin,
  Typography} from "antd";
import {
  ArrowLeftOutlined,
  EditOutlined,
  PrinterOutlined,
  FilePdfOutlined,
  FileExcelOutlined,
  DeleteOutlined,
  MedicineBoxOutlined,
  UserOutlined,
  ExclamationCircleOutlined,
  WarningOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import duration from 'dayjs/plugin/duration';
import { partosService, Parto } from '../../services/partosService';
import { embarazosService, Embarazo } from '../../services/embarazosService';
import { pacientesService, Paciente } from '../../services/pacientesService';
import { FRONTEND_ROUTES } from '../../config/routes';
import './DetalleParto.css';
import { handleImprimir, getApgarInterpretacion, getClasificacionPeso } from './detallePartoUtils';
import { descargarArchivo } from '../../utils/descargarArchivo';
import DetallePartoAbortoView from './components/DetallePartoAbortoView';
import DetallePartoView from './components/DetallePartoView';

dayjs.extend(duration);

const { Title, Text } = Typography;

const ARROW_LEFT_ICON_3 = <ArrowLeftOutlined />;
const PRINTER_ICON_2 = <PrinterOutlined />;
const EDIT_ICON_3 = <EditOutlined />;
const DELETE_ICON_4 = <DeleteOutlined />;

const DetalleParto: React.FC = () => {
  const navigate = useNavigate();
  const { message, modal } = useAntdApp();
  const { id } = useParams<{ id: string }>();
  const [loading, setLoading] = useState(true);
  const [parto, setParto] = useState<Parto | null>(null);
  const [paciente, setPaciente] = useState<Paciente | null>(null);
  const embarazoRef = useRef<Embarazo | null>(null);
  const isMounted = useRef(true);

  useEffect(() => {
    isMounted.current = true;
    return () => { isMounted.current = false; };
  }, []);

  // ✅ DETECTAR SI ES ABORTO O PARTO SEGÚN LOS CAMPOS REGISTRADOS
  const esAborto = () => {
    // Si tiene tipo_aborto registrado, ES UN ABORTO
    if ((parto as any)?.tipo_aborto) {
      return true;
    }
    // Si tiene tipo_parto registrado, ES UN PARTO
    if (parto?.tipo_parto) {
      return false;
    }
    // Solo si no tiene ninguno, usar edad gestacional para determinar
    if (!parto?.edad_gestacional_parto) return false;
    try {
      const semanas = parseInt(parto.edad_gestacional_parto.split('+')[0]);
      return semanas < 20;
    } catch {
      return false;
    }
  };

  // ==========================================================================
  // CARGAR DATOS
  // ==========================================================================
  const cargarDatos = React.useCallback(async () => {
    setLoading(true);
    try {
      // Cargar parto
      const partoData = await partosService.getById(Number(id));
      setParto(partoData);

      // Si el parto ya incluye paciente_info (serializer expandido), usarlo directamente
      if (partoData.paciente_info) {
        // Crear objeto Paciente completo desde paciente_info
        const pacienteCompleto: Paciente = {
          id: partoData.paciente_info.id || partoData.paciente || 0,
          id_clinico: partoData.paciente_info.id_clinico || '',
          nombre: partoData.paciente_info.nombre || '',
          apellido_paterno: partoData.paciente_info.apellido_paterno || '',
          apellido_materno: partoData.paciente_info.apellido_materno || '',
          fecha_nacimiento: '', // No siempre viene en info parcial
          genero: 'femenino',
          ci: partoData.paciente_info.cedula_identidad || '',
        };
        setPaciente(pacienteCompleto);
      }

      // Cargar embarazo relacionado si existe
      if (partoData.embarazo) {
        try {
          const embarazoData = await embarazosService.getById(partoData.embarazo);
          embarazoRef.current = embarazoData;

          // Solo cargar paciente si no fue cargado desde paciente_info
          if (!partoData.paciente_info && embarazoData.paciente) {
            const pacienteId = typeof embarazoData.paciente === 'number'
              ? embarazoData.paciente
              : (embarazoData.paciente as any).id;

            const pacienteData = await pacientesService.getById(pacienteId);
            setPaciente(pacienteData);
          }
        } catch (embarazoError) {
          // Continuar aunque falle la carga del embarazo
        }
      }

      if (isMounted.current) {
        message.success('Datos cargados correctamente');
      }
    } catch (error) {
      if (isMounted.current) {
        message.error('Error al cargar los datos del parto');
      }
    } finally {
      if (isMounted.current) setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    if (id) cargarDatos();
  }, [id, cargarDatos]);



  // ==========================================================================
  // HANDLERS
  // ==========================================================================
  const handleVolver = () => {
    navigate(FRONTEND_ROUTES.DASHBOARD.PARTOS);
  };

  const handleEditar = () => {
    navigate(FRONTEND_ROUTES.DASHBOARD.PARTOS_EDITAR(Number(id)));
  };

  const handleEliminar = () => {
    modal.confirm({
      title: '¿Eliminar este registro de parto?',
      icon: <ExclamationCircleOutlined />,
      content: 'Esta acción no se puede deshacer.',
      okText: 'Eliminar',
      okType: 'danger',
      cancelText: 'Cancelar',
      onOk: async () => {
        try {
          await partosService.delete(Number(id));
          message.success('Parto eliminado correctamente');
          navigate(FRONTEND_ROUTES.DASHBOARD.PARTOS);
        } catch (error) {
          message.error('Error al eliminar el parto');
        }
      },
    });
  };

  // ==========================================================================
  // FUNCIONES AUXILIARES
  // ==========================================================================
  const calcularDuracionTrabajoParto = () => {
    if (!parto?.fecha_inicio_trabajo_parto || !parto?.fecha_parto) return null;

    const inicio = dayjs(parto.fecha_inicio_trabajo_parto);
    const fin = dayjs(parto.fecha_parto);
    const duracion = dayjs.duration(fin.diff(inicio));

    const horas = Math.floor(duracion.asHours());
    const minutos = duracion.minutes();

    return `${horas}h ${minutos}min`;
  };

  const getEdadGestacionalCategoria = () => {
    if (!parto?.edad_gestacional_parto) return null;

    // Parse "39+2"
    const parts = parto.edad_gestacional_parto.split('+');
    const semanas = parseInt(parts[0]);

    if (semanas < 37) {
      return { text: 'Pretérmino', color: 'orange' };
    } else if (semanas >= 37 && semanas <= 42) {
      return { text: 'A término', color: 'green' };
    } else {
      return { text: 'Postérmino', color: 'red' };
    }
  };

  // ==========================================================================
  // RENDER
  // ==========================================================================
  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px 0' }}>
        <Spin size="large" />
        <div style={{ marginTop: 16, fontSize: 16 }}>Cargando datos del parto…</div>
      </div>
    );
  }

  if (!parto) {
    return (
      <Card>
        <Alert
          message="Parto no encontrado"
          description="No se encontró el registro de parto solicitado."
          type="error"
          showIcon
        />
        <Button onClick={handleVolver} style={{ marginTop: 16 }}>
          Volver al listado
        </Button>
      </Card>
    );
  }

  const rn = parto.recien_nacidos && parto.recien_nacidos.length > 0 ? parto.recien_nacidos[0] : null;
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const apgar1Interpretacion = getApgarInterpretacion(rn?.apgar_1_minuto || parto.apgar_1min || 0);
  const apgar5Interpretacion = getApgarInterpretacion(rn?.apgar_5_minutos || parto.apgar_5min || 0);
  const duracionTP = calcularDuracionTrabajoParto();
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const clasificacionPeso = rn?.peso_nacimiento ? getClasificacionPeso(rn.peso_nacimiento) : (parto.peso_bebe ? getClasificacionPeso(parto.peso_bebe) : null);
  const categoriaEG = getEdadGestacionalCategoria();

  return (
    <div className="detalle-parto-container">
      {/* HEADER */}
      <Card className="header-card">
        <Row justify="space-between" align="middle">
          <Col>
            <Space>
              <Button icon={ARROW_LEFT_ICON_3} onClick={handleVolver}>
                Volver
              </Button>
              <Divider type="vertical" />
              {esAborto() ? (
                <WarningOutlined style={{ fontSize: 24, color: '#ff4d4f' }} />
              ) : (
                <MedicineBoxOutlined style={{ fontSize: 24, color: '#722ed1' }} />
              )}
              <div>
                <Title level={4} style={{ margin: 0 }}>
                  {esAborto() ? 'Registro de Aborto' : 'Registro de Parto'} {paciente && `- ${paciente.nombre} ${paciente.apellido_paterno} ${paciente.apellido_materno || ''}`}
                </Title>
                <Space>
                  <Text type="secondary">
                    {dayjs(parto.fecha_parto).format('DD/MM/YYYY HH:mm')}
                  </Text>
                  {paciente?.id_clinico && (
                    <>
                      <Divider type="vertical" />
                      <Tag color="blue">ID: {paciente.id_clinico}</Tag>
                    </>
                  )}
                </Space>
              </div>
            </Space>
          </Col>
          <Col>
            <Space>
              <Button icon={PRINTER_ICON_2} onClick={handleImprimir}>
                Imprimir
              </Button>
              <Button
                icon={<FilePdfOutlined />}
                onClick={() => descargarArchivo(`/partos/${id}/generar-pdf/`, `parto_${id}.pdf`)
                  .then(() => message.success('PDF descargado'))
                  .catch(() => message.error('No se pudo generar el PDF'))}
              >
                PDF
              </Button>
              <Button
                icon={<FileExcelOutlined />}
                onClick={() => descargarArchivo(`/partos/${id}/exportar-excel/`, `parto_${id}.xlsx`)
                  .then(() => message.success('Excel descargado'))
                  .catch(() => message.error('No se pudo generar el Excel'))}
              >
                Excel
              </Button>
              <Button type="primary" icon={EDIT_ICON_3} onClick={handleEditar}>
                Editar
              </Button>
              <Button danger icon={DELETE_ICON_4} onClick={handleEliminar}>
                Eliminar
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* ALERTAS DE COMPLICACIONES */}
      {(parto.complicaciones_maternas || (rn?.complicaciones_neonatales)) && (
        <Alert
          message="⚠️ Atención: Complicaciones Registradas"
          description={
            <Space direction="vertical">
              {parto.complicaciones_maternas && (
                <Text>• Complicaciones maternas presentes</Text>
              )}
              {rn?.complicaciones_neonatales && (
                <Text>• Complicaciones neonatales presentes</Text>
              )}
            </Space>
          }
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      {/* ═════════════════════════════════════════════════════════════════════════ */}
      {esAborto() ? (
        <DetallePartoAbortoView parto={parto} paciente={paciente} />
      ) : (
        <DetallePartoView
          parto={parto}
          paciente={paciente}
          rn={rn}
          duracionTP={duracionTP}
          categoriaEG={categoriaEG}
          apgar5Interpretacion={apgar5Interpretacion}
        />
      )}
      {/* ═════════════════════════════════════════════════════════════════════════ */}
    </div>
  );
};

export default DetalleParto;
