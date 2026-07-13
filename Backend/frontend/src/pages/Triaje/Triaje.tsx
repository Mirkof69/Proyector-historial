import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { triajeService, TriajeEnfermeria } from '../../services/triajeService';
import {
  Table, Button, Input, Select, DatePicker, Tag, Tooltip, Space,
  Card, Row, Col, Statistic, Typography
} from 'antd';
import {
  EditOutlined, DeleteOutlined, EyeOutlined, PlusOutlined,
  SearchOutlined, FilterOutlined, PrinterOutlined, ExportOutlined,
  CheckCircleOutlined, CloseCircleOutlined, ClockCircleOutlined,
  DashboardOutlined, MedicineBoxOutlined, HeartOutlined, AlertOutlined,
  WarningOutlined
} from '@ant-design/icons';
import { useAntdApp } from '../../hooks/useMessage';
import { exportarExcel } from '../../utils/excelExport';
import dayjs from 'dayjs';
import es from 'dayjs/locale/es';

dayjs.locale(es);
const { Title, Text } = Typography;

const Triaje: React.FC = () => {
  const navigate = useNavigate();
  const { message, modal } = useAntdApp();

  const [triajes, setTriajes] = useState<TriajeEnfermeria[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [filterState, setFilterState] = useState<string>('');
  const [filterPriority, setFilterPriority] = useState<string>('');
  const [filterDate, setFilterDate] = useState<any>(null);

  const triajesArray = useMemo(() => Array.isArray(triajes) ? triajes : [], [triajes]);

  const stats = useMemo(() => ({
    total: triajesArray.length,
    urgente: triajesArray.filter(t => t.prioridad === 'urgente').length,
    alto: triajesArray.filter(t => t.prioridad === 'alto').length,
    normal: triajesArray.filter(t => t.prioridad === 'normal').length,
    bajo: triajesArray.filter(t => t.prioridad === 'bajo').length,
    pendiente: triajesArray.filter(t => t.estado === 'pendiente').length,
    completado: triajesArray.filter(t => t.estado === 'completado').length,
  }), [triajesArray]);

  const loadTriajes = useCallback(async () => {
    setLoading(true);
    try {
      const data = await triajeService.listar();
      if (Array.isArray(data)) {
        setTriajes(data);
      } else {
        setTriajes([]);
      }
    } catch (error) {
      message.error('Error al cargar triajes');
      setTriajes([]);
    } finally {
      setLoading(false);
    }
  }, [message]);

  useEffect(() => {
    loadTriajes();
  }, [loadTriajes]);

  const handleDelete = useCallback(async (id: number) => {
    modal.confirm({
      title: '¿Eliminar triaje?',
      content: 'Esta acción no se puede deshacer y eliminará permanentemente el registro de triaje.',
      okText: 'Eliminar',
      okType: 'danger',
      cancelText: 'Cancelar',
      onOk: async () => {
        try {
          await triajeService.eliminar(id);
          message.success('Triaje eliminado correctamente');
          loadTriajes();
        } catch (error) {
          message.error('Error al eliminar triaje');
        }
      }
    });
  }, [loadTriajes, message, modal]);

  const handleMarkComplete = useCallback(async (id: number) => {
    try {
      await triajeService.actualizar(id, { estado: 'completado' });
      message.success('Triaje marcado como completado');
      loadTriajes();
    } catch (error) {
      message.error('Error al actualizar triaje');
    }
  }, [loadTriajes, message]);

  const filteredTriajes = useMemo(() => {
    return triajesArray.filter(triaje => {
      const matchSearch =
        triaje.paciente_info?.nombre_completo?.toLowerCase().includes(searchText.toLowerCase()) ||
        triaje.paciente_nombre?.toLowerCase().includes(searchText.toLowerCase()) ||
        triaje.motivo_visita?.toLowerCase().includes(searchText.toLowerCase()) ||
        triaje.motivo_consulta?.toLowerCase().includes(searchText.toLowerCase());
      const matchState = !filterState || triaje.estado === filterState;
      const matchPriority = !filterPriority || triaje.prioridad === filterPriority;
      const matchDate = !filterDate || dayjs(triaje.fecha_hora || triaje.fecha_registro).isSame(filterDate, 'day');
      return matchSearch && matchState && matchPriority && matchDate;
    });
  }, [triajesArray, searchText, filterState, filterPriority, filterDate]);

  const handleExportExcel = useCallback(() => {
    try {
      const datos = filteredTriajes.map(t => ({
        paciente: t.paciente_info?.nombre_completo || t.paciente_nombre || '-',
        fecha: dayjs(t.fecha_hora || t.fecha_registro).format('DD/MM/YYYY HH:mm'),
        prioridad: t.prioridad?.toUpperCase() || '-',
        estado: t.estado?.toUpperCase() || 'PENDIENTE',
        motivo: t.motivo_consulta || t.motivo_visita || '-',
        peso_kg: t.peso_kg ?? t.peso ?? '-',
        talla_cm: t.talla_cm ?? t.talla ?? '-',
        presion: t.presion_arterial || (t.presion_sistolica && t.presion_diastolica ? `${t.presion_sistolica}/${t.presion_diastolica}` : '-'),
        temperatura: t.temperatura ?? '-',
        frecuencia_cardiaca: t.frecuencia_cardiaca ?? '-',
      }));
      const columnas = {
        paciente: 'Paciente',
        fecha: 'Fecha/Hora',
        prioridad: 'Prioridad',
        estado: 'Estado',
        motivo: 'Motivo',
        peso_kg: 'Peso (kg)',
        talla_cm: 'Talla (cm)',
        presion: 'Presión Arterial',
        temperatura: 'Temperatura',
        frecuencia_cardiaca: 'FC',
      };
      exportarExcel(
        datos,
        columnas,
        {
          filename: `triaje_${dayjs().format('YYYYMMDD_HHmmss')}.xlsx`,
          sheetName: 'Triaje',
          title: `Registro de Triaje - ${dayjs().format('DD/MM/YYYY')}`,
        },
      );
      message.success('Archivo Excel generado exitosamente');
    } catch (error) {
      message.error('Error al generar el archivo Excel');
    }
  }, [filteredTriajes, message]);

  const columns = useMemo(() => [
    {
      title: 'Paciente',
      key: 'paciente',
      render: (_: any, record: TriajeEnfermeria) => (
        <Space direction="vertical" size={0}>
          <Text strong>{record.paciente_info?.nombre_completo || record.paciente_nombre || 'Sin nombre'}</Text>
          <Text type="secondary" style={{ fontSize: '12px' }}>{(record.paciente_info as any)?.id_clinico || '-'}</Text>
        </Space>
      ),
    },
    {
      title: 'Fecha/Hora',
      key: 'fecha_hora',
      width: 150,
      render: (_: any, record: TriajeEnfermeria) => (
        <Space direction="vertical" size={0}>
          <Text>{dayjs(record.fecha_hora || record.fecha_registro).format('DD/MM/YYYY')}</Text>
          <Text type="secondary">{dayjs(record.fecha_hora || record.fecha_registro).format('HH:mm')}</Text>
        </Space>
      ),
      sorter: (a: TriajeEnfermeria, b: TriajeEnfermeria) =>
        new Date(a.fecha_hora || a.fecha_registro || 0).getTime() -
        new Date(b.fecha_hora || b.fecha_registro || 0).getTime(),
    },
    {
      title: 'Prioridad',
      dataIndex: 'prioridad',
      key: 'prioridad',
      width: 120,
      render: (prioridad: string) => {
        if (!prioridad) return <Tag>Sin prioridad</Tag>;
        const config: { [key: string]: { color: string; icon: React.ReactNode } } = {
          urgente: { color: 'red', icon: <AlertOutlined /> },
          alto: { color: 'orange', icon: <WarningOutlined /> },
          normal: { color: 'blue', icon: <ClockCircleOutlined /> },
          bajo: { color: 'green', icon: <CheckCircleOutlined /> },
        };
        const { color, icon } = config[prioridad] || { color: 'default', icon: null };
        return <Tag color={color} icon={icon}>{prioridad.toUpperCase()}</Tag>;
      },
    },
    {
      title: 'Estado',
      dataIndex: 'estado',
      key: 'estado',
      width: 130,
      render: (estado: string) => {
        const config: { [key: string]: { color: string; icon: React.ReactNode } } = {
          pendiente: { color: 'warning', icon: <ClockCircleOutlined /> },
          completado: { color: 'success', icon: <CheckCircleOutlined /> },
          cancelado: { color: 'error', icon: <CloseCircleOutlined /> },
        };
        const { color, icon } = config[estado] || { color: 'default', icon: null };
        return <Tag color={color} icon={icon}>{estado?.toUpperCase() || 'PENDIENTE'}</Tag>;
      },
    },
    {
      title: 'Motivo',
      key: 'motivo',
      ellipsis: true,
      render: (_: any, record: TriajeEnfermeria) => (
        <Tooltip title={record.motivo_consulta || record.motivo_visita}>
          <Text ellipsis style={{ maxWidth: 200 }}>{record.motivo_consulta || record.motivo_visita}</Text>
        </Tooltip>
      ),
    },
    {
      title: 'Acciones',
      key: 'acciones',
      fixed: 'right' as const,
      width: 150,
      render: (_: any, record: TriajeEnfermeria) => (
        <Space>
          <Tooltip title="Ver detalles">
            <Button
              type="primary"
              ghost
              size="small"
              icon={<EyeOutlined />}
              onClick={() => navigate(`/dashboard/triaje/${record.id}`)}
            />
          </Tooltip>
          <Tooltip title="Editar">
            <Button
              size="small"
              icon={<EditOutlined />}
              onClick={() => navigate(`/dashboard/triaje/${record.id}/editar`)}
            />
          </Tooltip>
          {record.estado === 'pendiente' && (
            <Tooltip title="Completar">
              <Button
                size="small"
                type="primary"
                icon={<CheckCircleOutlined />}
                onClick={() => handleMarkComplete(record.id!)}
              />
            </Tooltip>
          )}
          <Tooltip title="Eliminar">
            <Button
              danger
              ghost
              size="small"
              icon={<DeleteOutlined />}
              onClick={() => handleDelete(record.id!)}
            />
          </Tooltip>
        </Space>
      ),
    },
  ], [navigate, handleDelete, handleMarkComplete]);

  return (
    <div className="animate-fade-in" style={{ padding: '24px' }}>
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col span={24}>
          <Card className="shadow-card">
            <Row justify="space-between" align="middle">
              <Col>
                <Title level={2} style={{ margin: 0 }}>
                  <MedicineBoxOutlined /> Gestión de Triaje
                </Title>
                <Text type="secondary">Evaluación inicial de pacientes y signos vitales</Text>
              </Col>
              <Col>
                <Space>
                  <Button icon={<PrinterOutlined />} onClick={() => window.print()}>
                    Imprimir
                  </Button>
                  <Button
                    icon={<ExportOutlined />}
                    onClick={handleExportExcel}
                  >
                    Exportar
                  </Button>
                  <Button
                    type="primary"
                    size="large"
                    icon={<PlusOutlined />}
                    onClick={() => navigate('/dashboard/triaje/nuevo')}
                    className="status-pulse"
                  >
                    Nuevo Triaje
                  </Button>
                </Space>
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={12} sm={8} md={4}>
          <Card className="blue-gradient stat-card">
            <Statistic title="Total" value={stats.total} valueStyle={{ color: '#fff' }} />
            <DashboardOutlined className="stat-icon-bg" />
          </Card>
        </Col>
        <Col xs={12} sm={8} md={4}>
          <Card className="orange-gradient stat-card">
            <Statistic title="Pendientes" value={stats.pendiente} valueStyle={{ color: '#fff' }} />
            <ClockCircleOutlined className="stat-icon-bg" />
          </Card>
        </Col>
        <Col xs={12} sm={8} md={4}>
          <Card className="green-gradient stat-card">
            <Statistic title="Completados" value={stats.completado} valueStyle={{ color: '#fff' }} />
            <CheckCircleOutlined className="stat-icon-bg" />
          </Card>
        </Col>
        <Col xs={12} sm={8} md={4}>
          <Card className="purple-gradient stat-card" style={{ background: 'linear-gradient(120deg, #ff4d4f 0%, #ff7a45 100%)' }}>
            <Statistic title="Urgentes" value={stats.urgente} valueStyle={{ color: '#fff' }} />
            <AlertOutlined className="stat-icon-bg" />
          </Card>
        </Col>
        <Col xs={12} sm={8} md={4}>
          <Card className="stat-card" style={{ background: 'linear-gradient(120deg, #13c2c2 0%, #1890ff 100%)' }}>
            <Statistic title="Presión Alta" value={triajesArray.filter(t => t.alerta_presion_alta).length} valueStyle={{ color: '#fff' }} />
            <HeartOutlined className="stat-icon-bg" />
          </Card>
        </Col>
      </Row>

      <Card className="shadow-card" style={{ marginBottom: '24px' }}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} md={8}>
            <Input
              placeholder="Buscar por paciente, motivo..."
              prefix={<SearchOutlined />}
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              size="large"
              allowClear
            />
          </Col>
          <Col xs={12} md={4}>
            <Select
              placeholder="Estado"
              value={filterState}
              onChange={setFilterState}
              style={{ width: '100%' }}
              allowClear
              size="large"
              options={[
                { label: 'Pendiente', value: 'pendiente' },
                { label: 'Completado', value: 'completado' },
              ]}
            />
          </Col>
          <Col xs={12} md={4}>
            <Select
              placeholder="Prioridad"
              value={filterPriority}
              onChange={setFilterPriority}
              style={{ width: '100%' }}
              allowClear
              size="large"
              options={[
                { label: 'Urgente', value: 'urgente' },
                { label: 'Alto', value: 'alto' },
                { label: 'Normal', value: 'normal' },
                { label: 'Bajo', value: 'bajo' },
              ]}
            />
          </Col>
          <Col xs={24} md={4}>
            <DatePicker
              value={filterDate}
              onChange={setFilterDate}
              placeholder="Fecha"
              style={{ width: '100%' }}
              format="DD/MM/YYYY"
              size="large"
            />
          </Col>
          <Col xs={24} md={4}>
            <Button
              icon={<FilterOutlined />}
              onClick={() => {
                setSearchText('');
                setFilterState('');
                setFilterPriority('');
                setFilterDate(null);
              }}
              block
              size="large"
            >
              Limpiar
            </Button>
          </Col>
        </Row>
      </Card>

      <Table
        columns={columns}
        dataSource={filteredTriajes}
        rowKey="id"
        loading={loading}
        className="shadow-card"
        pagination={{
          pageSize: 10,
          showSizeChanger: true,
          showTotal: (total) => `Total ${total} registros`
        }}
        scroll={{ x: 1000 }}
        onRow={(record) => ({
          onDoubleClick: () => navigate(`/dashboard/triaje/${record.id}`),
        })}
      />
    </div>
  );
};

export default Triaje;
