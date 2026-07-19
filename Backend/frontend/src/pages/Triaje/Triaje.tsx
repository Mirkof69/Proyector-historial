import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { triajeService, TriajeEnfermeria } from '../../services/triajeService';
import { Empty, Table, Button, Card, Row, Col, Typography, Space } from 'antd';
import {
  PlusOutlined, PrinterOutlined, ExportOutlined, MedicineBoxOutlined,
} from '@ant-design/icons';
import { useAntdApp } from '../../hooks/useMessage';
import { exportarExcel } from '../../utils/excelExport';
import dayjs from 'dayjs';
import es from 'dayjs/locale/es';
import TriajeStats from './components/TriajeStats';
import TriajeFiltros from './components/TriajeFiltros';
import { buildTriajeColumns } from './components/triajeColumns';
import { incluyeTexto } from '../../utils/texto';

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

  const presionAlta = useMemo(
    () => triajesArray.filter(t => t.alerta_presion_alta).length,
    [triajesArray]
  );

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
        incluyeTexto(triaje.paciente_info?.nombre_completo, searchText) ||
        incluyeTexto(triaje.paciente_nombre, searchText) ||
        incluyeTexto(triaje.motivo_visita, searchText) ||
        incluyeTexto(triaje.motivo_consulta, searchText);
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

  const columns = useMemo(
    () => buildTriajeColumns(navigate, handleMarkComplete, handleDelete),
    [navigate, handleMarkComplete, handleDelete]
  );

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

      <TriajeStats
        total={stats.total}
        pendiente={stats.pendiente}
        completado={stats.completado}
        urgente={stats.urgente}
        presionAlta={presionAlta}
      />

      <TriajeFiltros
        searchText={searchText}
        filterState={filterState}
        filterPriority={filterPriority}
        filterDate={filterDate}
        onSearchChange={setSearchText}
        onStateChange={setFilterState}
        onPriorityChange={setFilterPriority}
        onDateChange={setFilterDate}
        onLimpiar={() => {
          setSearchText('');
          setFilterState('');
          setFilterPriority('');
          setFilterDate(null);
        }}
      />

      <Table
        columns={columns}
        dataSource={filteredTriajes}
        locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No hay registros de triaje" /> }}
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
