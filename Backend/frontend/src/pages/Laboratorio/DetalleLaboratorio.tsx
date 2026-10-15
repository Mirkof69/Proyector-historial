/**
 * =============================================================================
 * DETALLE DE EXAMEN DE LABORATORIO
 * =============================================================================
 * Vista completa de un examen de laboratorio con todos sus resultados
 * y evaluaciones médicas automáticas
 * =============================================================================
 */

import React, { useState, useRef, useEffect } from 'react';
import {
  Card,
  Descriptions,
  Button,
  Space,
  Tag,
  Alert,
  Row,
  Col,
  Spin,
  Typography,
  Tooltip,
} from 'antd';
import { useAntdApp } from '../../hooks/useMessage';
import {
  ArrowLeftOutlined,
  EditOutlined,
  PrinterOutlined,
  DeleteOutlined,
  ExperimentOutlined,
  ExclamationCircleOutlined,
  InfoCircleOutlined,
  WarningOutlined,
  UserOutlined,
  CalendarOutlined,
  FormOutlined,
} from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import dayjs from 'dayjs';
import { laboratorioService, ExamenLaboratorio } from '../../services/laboratorioService';
import { FRONTEND_ROUTES } from '../../config/routes';
import FormularioResultados from './FormularioResultados';
import ResumenResultadosLab from './components/ResumenResultadosLab';
import ResultadosLabTabs from './components/ResultadosLabTabs';
import InfoAdicionalLab from './components/InfoAdicionalLab';

import './Laboratorio.css';

const { Title, Text, Paragraph } = Typography;

const DetalleLaboratorio: React.FC = () => {
  const {modal,  message } = useAntdApp();
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const loadingRef = useRef(true);
  const [examen, setExamen] = useState<ExamenLaboratorio | null>(null);
  const [estadisticas, setEstadisticas] = useState<any | null>(null);
  const [loadingEstadisticas, setLoadingEstadisticas] = useState(false);


  // ==========================================================================
  // CARGAR DATOS
  // ==========================================================================
  const cargarDatos = React.useCallback(async () => {
    loadingRef.current = true;
    try {
      const data = await laboratorioService.getById(Number(id));
      setExamen(data);
      message.success('Datos cargados correctamente');
    } catch (error) {
      message.error('Error al cargar el examen de laboratorio');
    } finally {
      loadingRef.current = false;
    }
  }, [id, message]);

  // Cargar estadísticas del paciente
  const cargarEstadisticas = async () => {
    if (!id) return;

    setLoadingEstadisticas(true);
    try {
      const data = await laboratorioService.getEstadisticasPaciente(Number(id), 10);
      setEstadisticas(data);
    } catch (error) {
    } finally {
      setLoadingEstadisticas(false);
    }
  };

  useEffect(() => {
    if (id) cargarDatos();
  }, [id, cargarDatos]);

  // Estadísticas: cargar recién cuando el examen ya está completado. Antes se
  // evaluaba examen?.estado en el render de carga (aún null) → nunca cargaba.
  useEffect(() => {
    if (examen?.estado === 'completado') cargarEstadisticas();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [examen?.estado]);

  // ==========================================================================
  // HANDLERS
  // ==========================================================================
  const handleVolver = () => {
    navigate(FRONTEND_ROUTES.DASHBOARD.LABORATORIO);
  };

  const handleEditar = () => {
    navigate(FRONTEND_ROUTES.DASHBOARD.LABORATORIO_EDITAR(Number(id)));
  };

  const handleEliminar = () => {
    modal.confirm({
      title: '¿Eliminar este examen?',
      icon: <ExclamationCircleOutlined />,
      content: 'Esta acción no se puede deshacer.',
      okText: 'Eliminar',
      okType: 'danger',
      cancelText: 'Cancelar',
      onOk: async () => {
        try {
          await laboratorioService.delete(Number(id));
          message.success('Examen eliminado correctamente');
          navigate(FRONTEND_ROUTES.DASHBOARD.LABORATORIO);
        } catch (error) {
          message.error('Error al eliminar el examen');
        }
      },
    });
  };

  // ==========================================================================
  // RENDER
  // ==========================================================================
  if (loadingRef.current) {
    return (
      <div className="laboratorio-page__cargando">
        <Spin size="large" />
        <div className="laboratorio-arriba">Cargando datos del examen…</div>
      </div>
    );
  }

  if (!examen) {
    return (
      <Card>
        <Alert
          message="Examen no encontrado"
          description="No se encontró el examen solicitado."
          type="error"
          showIcon
        />
        <Button onClick={handleVolver} className="laboratorio-arriba">
          Volver al listado
        </Button>
      </Card>
    );
  }

  return (
    <div className="laboratorio-page page-container">
      {/* ENCABEZADO */}
      <header className="laboratorio-page__cabecera">
        <div>
          <Title level={2}>
            Detalle de Examen de Laboratorio
          </Title>
          <Text type="secondary">
            {examen.tipo_examen_info?.nombre || `Examen #${examen.id}`}
          </Text>
        </div>
            <Space wrap className="no-print">
              <Button icon={<ArrowLeftOutlined />} onClick={handleVolver}>
                Volver
              </Button>
              <Tooltip title="Imprimir el reporte del examen de laboratorio">
                <Button icon={<PrinterOutlined />} onClick={() => window.print()}>
                  Imprimir
                </Button>
              </Tooltip>
              <Tooltip title="Editar los datos del examen">
                <Button type="primary" icon={<EditOutlined />} onClick={handleEditar}>
                  Editar
                </Button>
              </Tooltip>
              <Tooltip title="Eliminar permanentemente este examen">
                <Button danger icon={<DeleteOutlined />} onClick={handleEliminar}>
                  Eliminar
                </Button>
              </Tooltip>
            </Space>
      </header>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={16}>
          {/* ALERTAS CRÍTICAS */}
          {examen.resumen && examen.resumen.criticos > 0 && (
            <Alert
              message={`${examen.resumen.criticos} RESULTADO(S) CRÍTICO(S) DETECTADO(S)`}
              description="Requiere atención médica inmediata. Consulte con el médico tratante."
              type="error"
              showIcon
              icon={<WarningOutlined />}
              className="laboratorio-separado"
            />
          )}

          {/* INFORMACIÓN DEL PACIENTE */}
          <Card
            title={
              <Space>
                <UserOutlined />
                Información del Paciente
              </Space>
            }
            className="laboratorio-separado"
          >
            {examen.paciente_info && (
              <Descriptions column={{ xs: 1, sm: 2 }} bordered>
                <Descriptions.Item label="Nombre Completo">
                  {examen.paciente_info.nombre_completo}
                </Descriptions.Item>
                <Descriptions.Item label="ID Clínico">
                  {examen.paciente_info.id_clinico}
                </Descriptions.Item>
                <Descriptions.Item label="Edad">
                  {examen.paciente_info.edad} años
                </Descriptions.Item>
              </Descriptions>
            )}
          </Card>

          {/* DATOS DEL EXAMEN */}
          <Card
            title={
              <Space>
                <ExperimentOutlined />
                Datos del Examen
              </Space>
            }
            className="laboratorio-separado"
          >
            <Descriptions column={{ xs: 1, sm: 2 }} bordered>
              <Descriptions.Item label="Tipo de Examen">
                {examen.tipo_examen_info?.nombre || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="Código">
                {examen.tipo_examen_info?.codigo || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="Categoría">
                <Tag>{examen.categoria || examen.tipo_examen_info?.categoria}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Estado">
                <Tag color={examen.estado === 'completado' ? 'success' : examen.estado === 'en_proceso' ? 'default' : 'warning'}>
                  {examen.estado?.toUpperCase()}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Prioridad">
                <Tag color={examen.prioridad === 'stat' ? 'error' : examen.prioridad === 'urgente' ? 'warning' : 'default'}>
                  {examen.prioridad?.toUpperCase()}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Fecha de Solicitud">
                <Space>
                  <CalendarOutlined />
                  {dayjs(examen.fecha_solicitud).format('DD/MM/YYYY HH:mm')}
                </Space>
              </Descriptions.Item>
              {examen.fecha_muestra && (
                <Descriptions.Item label="Fecha de Muestra">
                  {dayjs(examen.fecha_muestra).format('DD/MM/YYYY HH:mm')}
                </Descriptions.Item>
              )}
              {examen.fecha_resultado && (
                <Descriptions.Item label="Fecha de Resultado">
                  {dayjs(examen.fecha_resultado).format('DD/MM/YYYY HH:mm')}
                </Descriptions.Item>
              )}
              {examen.medico_info && (
                <Descriptions.Item label="Médico Solicitante">
                  {examen.medico_info.nombre} - {examen.medico_info.especialidad}
                </Descriptions.Item>
              )}
              {examen.indicaciones && (
                <Descriptions.Item label="Indicaciones Clínicas" span={2}>
                  <Paragraph>{examen.indicaciones}</Paragraph>
                </Descriptions.Item>
              )}
            </Descriptions>
          </Card>

          {/* RESUMEN DE RESULTADOS */}
          {examen.resumen && <ResumenResultadosLab resumen={examen.resumen} />}

          {/* RESULTADOS DETALLADOS O FORMULARIO DE INGRESO */}
          {examen.resultados && examen.resultados.length > 0 ? (
            <ResultadosLabTabs
              examen={examen}
              estadisticas={estadisticas}
              loadingEstadisticas={loadingEstadisticas}
            />
          ) : examen.estado !== 'completado' ? (
            /* FORMULARIO PARA INGRESAR RESULTADOS */
            <Card
              title={
                <Space>
                  <FormOutlined />
                  Ingresar Resultados del Examen
                </Space>
              }
              className="laboratorio-separado"
            >
              <Alert
                message="Este examen aún no tiene resultados"
                description="Complete el formulario a continuació n para ingresar los resultados de laboratorio."
                type="info"
                showIcon
                className="laboratorio-separado"
              />
              <FormularioResultados
                examenId={examen.id!}
                tipoExamenId={examen.tipo_examen}
                tipoExamenNombre={examen.tipo_examen_info?.nombre || 'Examen'}
                onResultadosGuardados={cargarDatos}
              />
            </Card>
          ) : (
            <Card className="laboratorio-separado">
              <Alert
                message="Sin Resultados"
                description="Este examen fue marcado como completado pero no tiene resultados registrados."
                type="warning"
                showIcon
              />
            </Card>
          )}

          {/* OBSERVACIONES */}
          {examen.observaciones && (
            <Card
              title={
                <Space>
                  <InfoCircleOutlined />
                  Observaciones
                </Space>
              }
              className="laboratorio-separado"
            >
              <Paragraph>{examen.observaciones}</Paragraph>
            </Card>
          )}
        </Col>

        {/* COLUMNA DERECHA */}
        <Col xs={24} lg={8}>
          {/* INFORMACIÓN ADICIONAL */}
          <InfoAdicionalLab examen={examen} />
        </Col>
      </Row>
    </div>
  );
};

export default DetalleLaboratorio;
