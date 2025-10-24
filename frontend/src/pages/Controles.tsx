import React, { useState, useEffect } from 'react';
import { 
  Table, Button, Space, message, Popconfirm, Card, Tag, Badge, 
  Input, Select, DatePicker, Row, Col, Statistic, Modal, Form,
  Tooltip, Alert, Divider
} from 'antd';
import { 
  PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined, 
  SearchOutlined, FilterOutlined, WarningOutlined, 
  CheckCircleOutlined, ReloadOutlined, LineChartOutlined,
  ExportOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import axios from 'axios';
import { authService } from '../services/authService';
import FormularioControl from './FormularioControl';
import DetalleControl from './DetalleControl';
import dayjs from 'dayjs';
import 'dayjs/locale/es';

dayjs.locale('es');

const { RangePicker } = DatePicker;
const { Option } = Select;

interface Control {
  id: number;
  embarazo_id: number;
  paciente_nombre: string;
  numero_control: number;
  fecha_control: string;
  edad_gestacional: string;
  presion_arterial: string;
  frecuencia_cardiaca_fetal: number;
  tiene_alertas: boolean;
  semanas_gestacion: number;
  imc_actual: number;
  clasificacion_imc: string;
}

interface Estadisticas {
  total_controles: number;
  controles_con_alertas: number;
  distribucion_trimestres: {
    primer_trimestre: number;
    segundo_trimestre: number;
    tercer_trimestre: number;
  };
  promedios: {
    peso_promedio: number;
    pa_sistolica_promedio: number;
    pa_diastolica_promedio: number;
    fcf_promedio: number;
  };
}

const Controles: React.FC = () => {
  const [controles, setControles] = useState<Control[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [detalleVisible, setDetalleVisible] = useState(false);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [controlSeleccionado, setControlSeleccionado] = useState<number | null>(null);
  const [estadisticas, setEstadisticas] = useState<Estadisticas | null>(null);
  
  // Filtros
  const [busqueda, setBusqueda] = useState('');
  const [filtroEmbarazo, setFiltroEmbarazo] = useState<number | null>(null);
  const [filtroTrimestre, setFiltroTrimestre] = useState<string | null>(null);
  const [filtroAlertas, setFiltroAlertas] = useState<boolean | null>(null);
  const [filtroFechas, setFiltroFechas] = useState<[dayjs.Dayjs | null, dayjs.Dayjs | null] | null>(null);

  useEffect(() => {
    fetchControles();
    fetchEstadisticas();
  }, [filtroEmbarazo, filtroTrimestre, filtroAlertas, filtroFechas]);

  const fetchControles = async () => {
    setLoading(true);
    try {
      const token = authService.getToken();
      let url = 'http://127.0.0.1:8000/api/controles/';
      
      const params = new URLSearchParams();
      if (filtroEmbarazo) params.append('embarazo', filtroEmbarazo.toString());
      if (filtroTrimestre) params.append('trimestre', filtroTrimestre);
      if (filtroAlertas) params.append('con_alertas', 'true');
      if (filtroFechas && filtroFechas[0] && filtroFechas[1]) {
        params.append('fecha_desde', filtroFechas[0].format('YYYY-MM-DD'));
        params.append('fecha_hasta', filtroFechas[1].format('YYYY-MM-DD'));
      }
      
      if (params.toString()) {
        url += `?${params.toString()}`;
      }

      const response = await axios.get(url, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setControles(response.data);
    } catch (error) {
      console.error('Error al cargar controles:', error);
      message.error('Error al cargar controles prenatales');
    } finally {
      setLoading(false);
    }
  };

  const fetchEstadisticas = async () => {
    try {
      const token = authService.getToken();
      const response = await axios.get('http://127.0.0.1:8000/api/controles/estadisticas/', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setEstadisticas(response.data);
    } catch (error) {
      console.error('Error al cargar estadísticas:', error);
    }
  };

  const handleEliminar = async (id: number) => {
    try {
      const token = authService.getToken();
      await axios.delete(`http://127.0.0.1:8000/api/controles/${id}/`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      message.success('Control eliminado correctamente');
      fetchControles();
      fetchEstadisticas();
    } catch (error) {
      message.error('Error al eliminar el control');
      console.error(error);
    }
  };

  const handleVerDetalle = (id: number) => {
    setControlSeleccionado(id);
    setDetalleVisible(true);
  };

  const handleEditar = (id: number) => {
    setControlSeleccionado(id);
    setEditModalVisible(true);
  };

  const handleExportar = () => {
    // Preparar datos para exportar
    const dataExport = controles.map(c => ({
      'N° Control': c.numero_control,
      'Paciente': c.paciente_nombre,
      'Fecha': dayjs(c.fecha_control).format('DD/MM/YYYY'),
      'EG': c.edad_gestacional,
      'PA': c.presion_arterial,
      'FCF': c.frecuencia_cardiaca_fetal,
      'Alertas': c.tiene_alertas ? 'Sí' : 'No'
    }));

    // Convertir a CSV
    const headers = Object.keys(dataExport[0]).join(',');
    const rows = dataExport.map(row => Object.values(row).join(','));
    const csv = [headers, ...rows].join('\n');

    // Descargar
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `controles_${dayjs().format('YYYY-MM-DD')}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    message.success('Datos exportados correctamente');
  };

  const limpiarFiltros = () => {
    setBusqueda('');
    setFiltroEmbarazo(null);
    setFiltroTrimestre(null);
    setFiltroAlertas(null);
    setFiltroFechas(null);
  };

  const columns: ColumnsType<Control> = [
    {
      title: 'N° Control',
      dataIndex: 'numero_control',
      key: 'numero_control',
      width: 100,
      sorter: (a, b) => a.numero_control - b.numero_control,
      render: (numero: number, record: Control) => (
        <Space>
          <Badge 
            count={numero} 
            style={{ backgroundColor: record.tiene_alertas ? '#ff4d4f' : '#52c41a' }}
          />
          {record.tiene_alertas && (
            <Tooltip title="Tiene alertas">
              <WarningOutlined style={{ color: '#ff4d4f' }} />
            </Tooltip>
          )}
        </Space>
      )
    },
    {
      title: 'Paciente',
      dataIndex: 'paciente_nombre',
      key: 'paciente_nombre',
      width: 200,
      ellipsis: true,
      filteredValue: busqueda ? [busqueda] : null,
      onFilter: (value, record) => 
        record.paciente_nombre.toLowerCase().includes(value.toString().toLowerCase()),
      render: (nombre: string) => (
        <Tooltip title={nombre}>
          <strong>{nombre}</strong>
        </Tooltip>
      )
    },
    {
      title: 'Fecha Control',
      dataIndex: 'fecha_control',
      key: 'fecha_control',
      width: 130,
      sorter: (a, b) => dayjs(a.fecha_control).unix() - dayjs(b.fecha_control).unix(),
      render: (fecha: string) => dayjs(fecha).format('DD/MM/YYYY')
    },
    {
      title: 'Edad Gestacional',
      dataIndex: 'edad_gestacional',
      key: 'edad_gestacional',
      width: 140,
      render: (eg: string, record: Control) => {
        let color = 'blue';
        if (record.semanas_gestacion < 13) color = 'cyan';
        else if (record.semanas_gestacion >= 27) color = 'purple';
        
        return <Tag color={color}>{eg} semanas</Tag>;
      }
    },
    {
      title: 'Trimestre',
      key: 'trimestre',
      width: 100,
      render: (_, record: Control) => {
        let trimestre = 1;
        let color = 'cyan';
        if (record.semanas_gestacion >= 27) {
          trimestre = 3;
          color = 'purple';
        } else if (record.semanas_gestacion >= 13) {
          trimestre = 2;
          color = 'blue';
        }
        return <Tag color={color}>{trimestre}° Trim.</Tag>;
      }
    },
    {
      title: 'Presión Arterial',
      dataIndex: 'presion_arterial',
      key: 'presion_arterial',
      width: 140,
      render: (pa: string) => {
        const [sistolica, diastolica] = pa.split('/').map(Number);
        let color = 'green';
        if (sistolica >= 140 || diastolica >= 90) color = 'red';
        else if (sistolica >= 120 || diastolica >= 80) color = 'orange';
        
        return <Tag color={color}>{pa} mmHg</Tag>;
      }
    },
    {
      title: 'FCF',
      dataIndex: 'frecuencia_cardiaca_fetal',
      key: 'frecuencia_cardiaca_fetal',
      width: 100,
      render: (fcf: number) => {
        let color = 'green';
        if (fcf < 110 || fcf > 160) color = 'red';
        else if (fcf < 120 || fcf > 150) color = 'orange';
        
        return <Tag color={color}>{fcf} lpm</Tag>;
      }
    },
    {
      title: 'IMC',
      key: 'imc',
      width: 120,
      render: (_, record: Control) => {
        if (!record.imc_actual) return '-';
        
        let color = 'green';
        if (record.imc_actual < 18.5 || record.imc_actual >= 30) color = 'red';
        else if (record.imc_actual >= 25) color = 'orange';
        
        return (
          <Tooltip title={record.clasificacion_imc}>
            <Tag color={color}>{record.imc_actual.toFixed(1)}</Tag>
          </Tooltip>
        );
      }
    },
    {
      title: 'Estado',
      key: 'estado',
      width: 100,
      render: (_, record: Control) => (
        record.tiene_alertas ? (
          <Tag icon={<WarningOutlined />} color="error">Con Alertas</Tag>
        ) : (
          <Tag icon={<CheckCircleOutlined />} color="success">Normal</Tag>
        )
      )
    },
    {
      title: 'Acciones',
      key: 'acciones',
      fixed: 'right',
      width: 180,
      render: (_, record: Control) => (
        <Space size="small">
          <Tooltip title="Ver Detalle">
            <Button 
              type="primary" 
              icon={<EyeOutlined />} 
              size="small"
              onClick={() => handleVerDetalle(record.id)}
            />
          </Tooltip>
          <Tooltip title="Editar">
            <Button 
              type="default" 
              icon={<EditOutlined />} 
              size="small"
              onClick={() => handleEditar(record.id)}
            />
          </Tooltip>
          <Popconfirm
            title="¿Eliminar control?"
            description="Esta acción no se puede deshacer"
            onConfirm={() => handleEliminar(record.id)}
            okText="Eliminar"
            cancelText="Cancelar"
            okButtonProps={{ danger: true }}
          >
            <Tooltip title="Eliminar">
              <Button 
                danger 
                icon={<DeleteOutlined />} 
                size="small"
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      )
    }
  ];

  return (
    <div>
      {/* ESTADÍSTICAS */}
      {estadisticas && (
        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col span={6}>
            <Card>
              <Statistic 
                title="Total Controles" 
                value={estadisticas.total_controles} 
                prefix={<LineChartOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic 
                title="Con Alertas" 
                value={estadisticas.controles_con_alertas || 0}
                prefix={<WarningOutlined />}
                valueStyle={{ color: '#ff4d4f' }}
                suffix={`/ ${estadisticas.total_controles}`}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic 
                title="PA Sistólica Promedio" 
                value={estadisticas.promedios.pa_sistolica_promedio?.toFixed(0) || 0}
                suffix="mmHg"
                valueStyle={{ 
                  color: estadisticas.promedios.pa_sistolica_promedio >= 120 ? '#ff4d4f' : '#52c41a' 
                }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic 
                title="FCF Promedio" 
                value={estadisticas.promedios.fcf_promedio?.toFixed(0) || 0}
                suffix="lpm"
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* DISTRIBUCIÓN POR TRIMESTRES */}
      {estadisticas && (
        <Card style={{ marginBottom: 16 }}>
          <Row gutter={16}>
            <Col span={8}>
              <Statistic 
                title="1er Trimestre" 
                value={estadisticas.distribucion_trimestres.primer_trimestre}
                valueStyle={{ color: '#1890ff' }}
              />
            </Col>
            <Col span={8}>
              <Statistic 
                title="2do Trimestre" 
                value={estadisticas.distribucion_trimestres.segundo_trimestre}
                valueStyle={{ color: '#52c41a' }}
              />
            </Col>
            <Col span={8}>
              <Statistic 
                title="3er Trimestre" 
                value={estadisticas.distribucion_trimestres.tercer_trimestre}
                valueStyle={{ color: '#722ed1' }}
              />
            </Col>
          </Row>
        </Card>
      )}

      {/* FILTROS Y BÚSQUEDA */}
      <Card 
        title="Controles Prenatales" 
        extra={
          <Space>
            <Button 
              type="primary" 
              icon={<PlusOutlined />}
              onClick={() => setModalVisible(true)}
            >
              Nuevo Control
            </Button>
            <Button 
              icon={<ExportOutlined />}
              onClick={handleExportar}
              disabled={controles.length === 0}
            >
              Exportar CSV
            </Button>
          </Space>
        }
        style={{ marginBottom: 0 }}
      >
        <Space direction="vertical" style={{ width: '100%', marginBottom: 16 }}>
          <Row gutter={16}>
            <Col span={8}>
              <Input
                placeholder="Buscar por paciente..."
                prefix={<SearchOutlined />}
                value={busqueda}
                onChange={(e) => setBusqueda(e.target.value)}
                allowClear
              />
            </Col>
            <Col span={4}>
              <Select
                placeholder="Trimestre"
                style={{ width: '100%' }}
                value={filtroTrimestre}
                onChange={setFiltroTrimestre}
                allowClear
              >
                <Option value="1">1er Trimestre</Option>
                <Option value="2">2do Trimestre</Option>
                <Option value="3">3er Trimestre</Option>
              </Select>
            </Col>
            <Col span={4}>
              <Select
                placeholder="Alertas"
                style={{ width: '100%' }}
                value={filtroAlertas === null ? undefined : filtroAlertas}
                onChange={(value) => setFiltroAlertas(value === undefined ? null : value)}
                allowClear
              >
                <Option value={true}>Con Alertas</Option>
                <Option value={false}>Sin Alertas</Option>
              </Select>
            </Col>
            <Col span={6}>
              <RangePicker
                style={{ width: '100%' }}
                format="DD/MM/YYYY"
                placeholder={['Fecha desde', 'Fecha hasta']}
                value={filtroFechas}
                onChange={(dates) => setFiltroFechas(dates as [dayjs.Dayjs | null, dayjs.Dayjs | null] | null)}
              />
            </Col>
            <Col span={2}>
              <Button 
                icon={<ReloadOutlined />} 
                onClick={limpiarFiltros}
                block
              >
                Limpiar
              </Button>
            </Col>
          </Row>
        </Space>

        {/* ALERTA DE FILTROS ACTIVOS */}
        {(filtroEmbarazo || filtroTrimestre || filtroAlertas !== null || filtroFechas) && (
          <Alert
            message="Filtros activos"
            description={
              <Space direction="vertical" size="small">
                {filtroTrimestre && <span>• Trimestre: {filtroTrimestre}</span>}
                {filtroAlertas !== null && <span>• {filtroAlertas ? 'Con alertas' : 'Sin alertas'}</span>}
                {filtroFechas && <span>• Rango de fechas aplicado</span>}
              </Space>
            }
            type="info"
            closable
            onClose={limpiarFiltros}
            style={{ marginBottom: 16 }}
          />
        )}

        {/* TABLA */}
        <Table
          columns={columns}
          dataSource={controles}
          rowKey="id"
          loading={loading}
          scroll={{ x: 1400 }}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showTotal: (total) => `Total: ${total} controles`,
            pageSizeOptions: ['10', '20', '50', '100']
          }}
          rowClassName={(record) => record.tiene_alertas ? 'row-with-alert' : ''}
        />
      </Card>

      {/* MODAL NUEVO CONTROL */}
      <Modal
        title="Nuevo Control Prenatal"
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={1200}
        destroyOnClose
      >
        <FormularioControl
          onCancel={() => setModalVisible(false)}
          onSuccess={() => {
            setModalVisible(false);
            fetchControles();
            fetchEstadisticas();
          }}
        />
      </Modal>

      {/* MODAL EDITAR CONTROL */}
      <Modal
        title="Editar Control Prenatal"
        open={editModalVisible}
        onCancel={() => {
          setEditModalVisible(false);
          setControlSeleccionado(null);
        }}
        footer={null}
        width={1200}
        destroyOnClose
      >
        <FormularioControl
          controlId={controlSeleccionado}
          onCancel={() => {
            setEditModalVisible(false);
            setControlSeleccionado(null);
          }}
          onSuccess={() => {
            setEditModalVisible(false);
            setControlSeleccionado(null);
            fetchControles();
            fetchEstadisticas();
          }}
        />
      </Modal>

      {/* MODAL DETALLE CONTROL */}
      <Modal
        title="Detalle del Control Prenatal"
        open={detalleVisible}
        onCancel={() => {
          setDetalleVisible(false);
          setControlSeleccionado(null);
        }}
        footer={null}
        width={1000}
        destroyOnClose
      >
        {controlSeleccionado && (
          <DetalleControl 
            controlId={controlSeleccionado}
            onClose={() => {
              setDetalleVisible(false);
              setControlSeleccionado(null);
            }}
          />
        )}
      </Modal>

      {/* CSS PERSONALIZADO PARA FILAS CON ALERTA */}
      <style>{`
        .row-with-alert {
          background-color: #fff1f0;
        }
        .row-with-alert:hover {
          background-color: #ffe7e5 !important;
        }
      `}</style>
    </div>
  );
};

export default Controles;