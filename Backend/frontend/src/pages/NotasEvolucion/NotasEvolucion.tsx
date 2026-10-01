import React, { useState, useEffect, useCallback } from 'react';
import { Alert, Empty, Card, Table, Button, Space, Tag, Input, Select, Row, Col, Statistic, Popconfirm } from 'antd';
import { useAntdApp } from '../../hooks/useMessage';
import { PlusOutlined, EyeOutlined, EditOutlined, DeleteOutlined, SearchOutlined, ExportOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import dayjs from 'dayjs';
import { notasEvolucionService, NotaEvolucion } from '../../services/notasEvolucionService';
import { aQuery, contarEnServidor, useListadoServidor } from '../../hooks/useListadoServidor';
import { descargarArchivo } from '../../utils/descargarArchivo';

const URL_NOTAS = '/notas-evolucion/';

const NotasEvolucionPage: React.FC = () => {
  const navigate = useNavigate();
  const { message } = useAntdApp();
  const [searchText, setSearchText] = useState('');
  const [filterTipo, setFilterTipo] = useState<string>('');

  // Búsqueda y tipo los filtra el SERVIDOR. Antes se pedían 1.000 notas, el
  // servidor cortaba en 200 y las demás no aparecían.
  const listado = useListadoServidor<NotaEvolucion>(URL_NOTAS, {
    filtros: { tipo_consulta: filterTipo || undefined }, busqueda: searchText, ordenInicial: '-fecha_consulta',
  });
  const { parametros, recargar } = listado;

  const [stats, setStats] = useState({ total: 0, controles: 0, urgencias: 0, seguimientos: 0 });
  const cargarStats = useCallback(async () => {
    try {
      const [total, controles, urgencias, seguimientos] = await Promise.all([
        contarEnServidor(URL_NOTAS),
        contarEnServidor(URL_NOTAS, { tipo_consulta: 'control_prenatal' }),
        contarEnServidor(URL_NOTAS, { tipo_consulta: 'urgencia' }),
        contarEnServidor(URL_NOTAS, { tipo_consulta: 'seguimiento' }),
      ]);
      setStats({ total, controles, urgencias, seguimientos });
    } catch {
      // Las cifras de cabecera no deben impedir usar el listado.
    }
  }, []);
  useEffect(() => { cargarStats(); }, [cargarStats]);

  const handleDelete = async (id: number) => {
    try {
      await notasEvolucionService.eliminarNota(id);
      message.success('Nota eliminada');
      recargar();
      cargarStats();
    } catch (error: any) {
      // 409: la historia clínica está protegida; el servidor dice por qué.
      message.error(error?.response?.data?.error || error?.response?.data?.detail || 'No se pudo eliminar la nota');
    }
  };

  const handleExportExcel = async () => {
    try {
      await descargarArchivo(`${URL_NOTAS}exportar-excel/${aQuery(parametros())}`,
        `notas_evolucion_${dayjs().format('YYYYMMDD_HHmm')}.xlsx`);
    } catch {
      message.error('No se pudo generar el Excel de notas');
    }
  };

  const columns = [
    {
      title: 'Fecha',
      dataIndex: 'fecha_consulta',
      key: 'fecha_consulta',
      render: (f: string) => dayjs(f).format('DD/MM/YYYY HH:mm'),
      sorter: true,
    },
    {
      title: 'Paciente',
      dataIndex: 'paciente_nombre',
      key: 'paciente',
      render: (text: string) => text || '-',
    },
    {
      title: 'Tipo',
      dataIndex: 'tipo_consulta',
      key: 'tipo',
      render: (tipo: string) => {
        const colors: { [key: string]: string } = {
          control_prenatal: 'blue',
          urgencia: 'red',
          seguimiento: 'green',
          interconsulta: 'orange',
          puerperio: 'purple',
          otro: 'default',
        };
        const labels: { [key: string]: string } = {
          control_prenatal: 'Control Prenatal',
          urgencia: 'Urgencia',
          seguimiento: 'Seguimiento',
          interconsulta: 'Interconsulta',
          puerperio: 'Puerperio',
          otro: 'Otro',
        };
        return <Tag color={colors[tipo] || 'default'}>{labels[tipo] || tipo}</Tag>;
      },
    },
    {
      title: 'Motivo',
      dataIndex: 'motivo_consulta',
      key: 'motivo',
      render: (text: string) => text?.substring(0, 50) + (text?.length > 50 ? '...' : ''),
    },
    {
      title: 'Médico',
      dataIndex: 'medico_nombre',
      key: 'medico',
      render: (text: string) => text || '-',
    },
    {
      title: 'Acciones',
      key: 'acciones',
      fixed: 'right' as const,
      width: 150,
      render: (_: any, record: NotaEvolucion) => (
        <Space>
          <Button
            size="small"
            type="primary"
            icon={<EyeOutlined />}
            aria-label="Ver nota"
            title="Ver nota"
            onClick={() => navigate(`/dashboard/notas-evolucion/${record.id}`)}
          />
          <Button
            size="small"
            icon={<EditOutlined />}
            aria-label="Editar nota"
            title="Editar nota"
            onClick={() => navigate(`/dashboard/notas-evolucion/${record.id}/editar`)}
          />
          <Popconfirm
            title="¿Eliminar esta nota de evolución?"
            description="Es parte de la historia clínica de la paciente."
            okText="Eliminar"
            okButtonProps={{ danger: true }}
            cancelText="Cancelar"
            onConfirm={() => handleDelete(record.id)}
          >
            <Button size="small" danger icon={<DeleteOutlined />} aria-label="Eliminar nota" title="Eliminar nota" />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div className="page-container" style={{ padding: 24 }}>
      {/* Estadísticas */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Statistic
            title="Total Notas"
            value={stats.total}
            valueStyle={{ color: '#1890ff' }}
          />
        </Col>
        <Col span={6}>
          <Statistic
            title="Controles Prenatales"
            value={stats.controles}
            valueStyle={{ color: '#52c41a' }}
          />
        </Col>
        <Col span={6}>
          <Statistic
            title="Urgencias"
            value={stats.urgencias}
            valueStyle={{ color: '#ff4d4f' }}
          />
        </Col>
        <Col span={6}>
          <Statistic
            title="Seguimientos"
            value={stats.seguimientos}
            valueStyle={{ color: '#faad14' }}
          />
        </Col>
      </Row>

      {/* Barra de búsqueda y filtros */}
      <Card style={{ marginBottom: 24 }}>
        <Row gutter={16} align="middle">
          <Col flex="auto">
            <Input
              placeholder="Buscar por paciente, médico o motivo..."
              prefix={<SearchOutlined />}
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              size="large"
            />
          </Col>
          <Col>
            <Select
              placeholder="Tipo de consulta"
              value={filterTipo}
              onChange={(v) => setFilterTipo(v ?? '')}
              style={{ width: 200 }}
              size="large"
              allowClear
              options={[
                { label: 'Control Prenatal', value: 'control_prenatal' },
                { label: 'Urgencia', value: 'urgencia' },
                { label: 'Seguimiento', value: 'seguimiento' },
                { label: 'Interconsulta', value: 'interconsulta' },
                { label: 'Puerperio', value: 'puerperio' },
                { label: 'Otro', value: 'otro' },
              ]}
            />
          </Col>
          <Col>
            <Button
              icon={<ExportOutlined />}
              onClick={handleExportExcel}
              size="large"
            >
              Exportar
            </Button>
          </Col>
          <Col>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => navigate('/dashboard/notas-evolucion/nuevo')}
              size="large"
            >
              Nueva Nota
            </Button>
          </Col>
        </Row>
      </Card>

      {/* Tabla de notas */}
      <Card>
        {listado.error && <Alert type="error" showIcon message={listado.error} style={{ marginBottom: 12 }} />}
        <Table
          columns={columns}
          dataSource={listado.datos}
          locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No hay notas de evolución registradas" /> }}
          loading={listado.cargando}
          rowKey="id"
          pagination={listado.paginacion}
          onChange={listado.onChange}
          scroll={{ x: 1200 }}
        />
      </Card>
    </div>
  );
};

export default NotasEvolucionPage;
