import React, { useState, useEffect, useCallback } from 'react';
import { Card, Table, Button, Space, Tag, Input, Select, Row, Col, Statistic } from 'antd';
import { useAntdApp } from '../../hooks/useMessage';
import { PlusOutlined, EyeOutlined, EditOutlined, DeleteOutlined, SearchOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import dayjs from 'dayjs';
import { notasEvolucionService, NotaEvolucion } from '../../services/notasEvolucionService';

const NotasEvolucionPage: React.FC = () => {
  const navigate = useNavigate();
  const { message } = useAntdApp();
  const [notas, setNotas] = useState<NotaEvolucion[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [filterTipo, setFilterTipo] = useState<string>('');

  // Asegurar que notas sea array
  const notasArray = Array.isArray(notas) ? notas : [];

  const stats = {
    total: notasArray.length,
    controles: notasArray.filter(n => n.tipo_consulta === 'control_prenatal').length,
    urgencias: notasArray.filter(n => n.tipo_consulta === 'urgencia').length,
    seguimientos: notasArray.filter(n => n.tipo_consulta === 'seguimiento').length,
  };



  const cargarNotas = useCallback(async () => {
    setLoading(true);
    try {
      const response = await notasEvolucionService.getNotas({ page_size: 1000 });

      // FIX: Manejar respuesta paginada correctamente
      // Siempre priorizar response.results si existe, sino usar array vacío
      const data = Array.isArray(response) ? response : (response.results || []);

      // Setear las notas (data ya es array garantizado)
      setNotas(data);
      if (data.length > 0) {
        message.success(`${data.length} Notas de evolución cargadas correctamente`);
      }
    } catch (error) {
      message.error('Error al cargar notas de evolución');
      setNotas([]); // Asegurar que notas sea array aunque haya error
    } finally {
      setLoading(false);
    }
  }, [message]);

  useEffect(() => {
    cargarNotas();
  }, [cargarNotas]);

  const handleDelete = async (id: number) => {
    try {
      await notasEvolucionService.eliminarNota(id);
      message.success('Nota eliminada correctamente');
      cargarNotas();
    } catch (error) {
      message.error('Error al eliminar nota');
    }
  };

  const filteredNotas = notasArray.filter(nota => {
    const matchSearch =
      nota.paciente_nombre?.toLowerCase().includes(searchText.toLowerCase()) ||
      nota.medico_nombre?.toLowerCase().includes(searchText.toLowerCase()) ||
      nota.motivo_consulta?.toLowerCase().includes(searchText.toLowerCase());
    const matchTipo = !filterTipo || nota.tipo_consulta === filterTipo;
    return matchSearch && matchTipo;
  });

  const columns = [
    {
      title: 'Fecha',
      dataIndex: 'fecha_consulta',
      key: 'fecha',
      render: (f: string) => dayjs(f).format('DD/MM/YYYY HH:mm'),
      sorter: (a: NotaEvolucion, b: NotaEvolucion) =>
        new Date(a.fecha_consulta).getTime() - new Date(b.fecha_consulta).getTime(),
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
            onClick={() => navigate(`/dashboard/notas-evolucion/${record.id}`)}
          />
          <Button
            size="small"
            icon={<EditOutlined />}
            onClick={() => navigate(`/dashboard/notas-evolucion/${record.id}/editar`)}
          />
          <Button
            size="small"
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleDelete(record.id)}
          />
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
              onChange={setFilterTipo}
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
        <Table
          columns={columns}
          dataSource={filteredNotas}
          loading={loading}
          rowKey="id"
          pagination={{ pageSize: 20 }}
          scroll={{ x: 1200 }}
        />
      </Card>
    </div>
  );
};

export default NotasEvolucionPage;
