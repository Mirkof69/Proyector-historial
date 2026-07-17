import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Button,
  Spin,
  Tag,
  Space,
  Alert,
  Typography,
  Row,
  Col,
} from 'antd';
import { useAntdApp } from '../../hooks/useMessage';
import {
  ArrowLeftOutlined,
  UserOutlined,
  EditOutlined,
  PrinterOutlined,
} from '@ant-design/icons';
import { pacientesService, Paciente } from '../../services/pacientesService';
import { triajeService } from '../../services/triajeService';
import { antecedentesService } from '../../services/antecedentesService';
import { notasEvolucionService } from '../../services/notasEvolucionService';
import { vacunasService } from '../../services/vacunasService';
import { ecografiasService } from '../../services/ecografiasService';
import { Embarazo } from '../../services/embarazosService';
import { FRONTEND_ROUTES } from '../../config/routes';
import DetallePacienteStats from './components/DetallePacienteStats';
import DetallePacienteGraficas from './components/DetallePacienteGraficas';
import DetallePacienteInfo from './components/DetallePacienteInfo';
import DetallePacienteTabs from './components/DetallePacienteTabs';

const { Title } = Typography;

const DetallePaciente: React.FC = () => {
  const { message } = useAntdApp();
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  // Estados principales
  const [paciente, setPaciente] = useState<Paciente | null>(null);
  const loadingRef = useRef(true);
  const [loadingHistory, setLoadingHistory] = useState(false);

  // Estados de datos médicos
  const [embarazos, setEmbarazos] = useState<Embarazo[]>([]);
  const [triajes, setTriajes] = useState<any[]>([]);
  const [antecedentes, setAntecedentes] = useState<any[]>([]);
  const [notasEvolucion, setNotasEvolucion] = useState<any[]>([]);
  const [vacunas, setVacunas] = useState<any[]>([]);
  const [ecografias, setEcografias] = useState<any[]>([]);
  const isMounted = useRef(true);

  useEffect(() => {
    isMounted.current = true;
    return () => {
      isMounted.current = false;
    };
  }, []);

  // ✅ Función para mostrar estado civil según género
  const fetchData = async (pacienteId: number) => {
    loadingRef.current = true;
    try {
      // Cargar todos los datos en paralelo
      const [
        pacienteData,
        embarazosData,
        triajesData,
        antecedentesData,
        notasData,
        vacunasData,
        ecografiasData,
      ] = await Promise.all([
        pacientesService.getById(pacienteId),
        pacientesService.getEmbarazos(pacienteId),
        triajeService.listar().then(data => Array.isArray(data) ? data.filter((t: any) => t.paciente === pacienteId) : []),
        antecedentesService.listar().then(data => Array.isArray(data) ? data.filter((a: any) => (a.paciente_id || a.paciente) === pacienteId) : []),
        notasEvolucionService.getNotas({ page_size: 1000 }).then(res => {
          const data = res.results || res;
          return Array.isArray(data) ? data.filter((n: any) => n.paciente === pacienteId) : [];
        }),
        vacunasService.getRegistros({ page_size: 1000 }).then(res => {
          const data = res.results || res;
          return Array.isArray(data) ? data.filter((v: any) => v.paciente === pacienteId) : [];
        }),
        ecografiasService.obtenerPorPaciente(pacienteId),
      ]);

      if (isMounted.current) {
        setPaciente(pacienteData);
        setEmbarazos(Array.isArray(embarazosData) ? embarazosData : []);
        setTriajes(triajesData);
        setAntecedentes(antecedentesData);
        setNotasEvolucion(notasData);
        setVacunas(vacunasData);
        setEcografias(Array.isArray(ecografiasData) ? ecografiasData : (ecografiasData?.results || []));
        message.success('Datos cargados correctamente');
      }
    } catch (error) {
      if (isMounted.current) {
        message.error('Error al cargar los datos del paciente');
      }
    } finally {
      if (isMounted.current) {
        loadingRef.current = false;
      }
    }
  };

  useEffect(() => {
    if (id) fetchData(parseInt(id));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const handleEdit = () => {
    if (paciente) {
      navigate(FRONTEND_ROUTES.DASHBOARD.PACIENTES_EDITAR(paciente.id));
    }
  };

  const handlePrintHistory = async () => {
    if (!paciente) return;
    setLoadingHistory(true);
    try {
      const blob = await pacientesService.getHistoriaClinica(paciente.id);
      if (isMounted.current) {
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `Historia_Clinica_${paciente.id_clinico}.pdf`);
        document.body.appendChild(link);
        link.click();
        link.parentNode?.removeChild(link);
        message.success('Historia clínica descargada');
      }
    } catch (error) {
      if (isMounted.current) {
        message.error('Error al generar la historia clínica');
      }
    } finally {
      if (isMounted.current) {
        setLoadingHistory(false);
      }
    }
  };

  // Calcular estadísticas
  const stats = {
    totalEmbarazos: embarazos.length,
    embarazosActivos: embarazos.filter(e => e.estado === 'activo').length,
    totalTriajes: triajes.length,
    totalNotas: notasEvolucion.length,
    totalVacunas: vacunas.length,
    vacunasCompletas: vacunas.filter(v => !v.proxima_dosis_fecha).length,
  };

  if (loadingRef.current) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" tip="Cargando historial clínico completo del paciente…"><div /></Spin>
      </div>
    );
  }

  if (!paciente) {
    return <Alert message="Paciente no encontrado" type="error" showIcon />;
  }

  return (
    <div style={{ padding: '24px', backgroundColor: 'var(--bg-secondary)' }}>
      {/* Header */}
      <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Space>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate(FRONTEND_ROUTES.DASHBOARD.PACIENTES)}>
            Volver
          </Button>
          <Title level={2} style={{ margin: 0 }}>
            <UserOutlined /> {paciente.nombre_completo}
          </Title>
          <Tag color={paciente.activo ? 'green' : 'red'}>
            {paciente.activo ? 'ACTIVO' : 'INACTIVO'}
          </Tag>
        </Space>
        <Space>
          <Button icon={<EditOutlined />} onClick={handleEdit}>
            Editar
          </Button>
          <Button
            icon={<PrinterOutlined />}
            type="primary"
            onClick={handlePrintHistory}
            loading={loadingHistory}
          >
            Historia Clínica PDF
          </Button>
        </Space>
      </div>

      {/* Estadísticas Generales */}
      <DetallePacienteStats stats={stats} />

      {/* Gráficas de Análisis */}
      <DetallePacienteGraficas triajes={triajes} vacunas={vacunas} notasEvolucion={notasEvolucion} />

      {/* Información del Paciente + Historial en Tabs */}
      <Row gutter={[16, 16]}>
        <DetallePacienteInfo paciente={paciente} />

        {/* Historial Médico Completo en Tabs */}
        <Col span={24}>
          <DetallePacienteTabs
            embarazos={embarazos}
            triajes={triajes}
            notasEvolucion={notasEvolucion}
            vacunas={vacunas}
            antecedentes={antecedentes}
            ecografias={ecografias}
            navigate={navigate}
          />
        </Col>
      </Row>
    </div>
  );
};

export default DetallePaciente;
