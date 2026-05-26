import React, { useState, useEffect, useCallback } from 'react';
import { antecedentesService } from '../../services/antecedentesService';
import { pacientesService } from '../../services/pacientesService';
import {
  Table, Button, Modal, Tag, Tooltip, Space,
  Spin, Empty, Popconfirm, Form
} from 'antd';
import { useAntdApp } from '../../hooks/useMessage';
import {
  EditOutlined, DeleteOutlined, EyeOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import es from 'dayjs/locale/es';
import StatsCards from './components/StatsCards';
import SearchBar from './components/SearchBar';
import AntecedentesFormFields from './components/AntecedentesFormFields';

dayjs.locale(es);

const Antecedentes: React.FC = () => {
  const [antecedentes, setAntecedentes] = useState<any[]>([]);
  const [pacientes, setPacientes] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const { message, modal } = useAntdApp();
  const [form] = Form.useForm();

  const antecedentesArray = Array.isArray(antecedentes) ? antecedentes : [];
  const stats = {
    total: antecedentesArray.length,
    conGestas: antecedentesArray.filter((a: any) => (a.gestas || 0) > 0).length,
    conPartos: antecedentesArray.filter((a: any) => (a.partos || 0) > 0).length,
    conAbortos: antecedentesArray.filter((a: any) => (a.abortos || 0) > 0).length,
  };

  const loadAntecedentes = useCallback(async () => {
    setLoading(true);
    try {
      const data = await antecedentesService.listar();
      setAntecedentes(Array.isArray(data) ? data : []);
    } catch (error) {
      message.error('Error al cargar antecedentes');
      setAntecedentes([]);
    } finally {
      setLoading(false);
    }
  }, [message]);

  const loadPacientes = useCallback(async () => {
    try {
      const data = await pacientesService.listar();
      setPacientes(data);
    } catch (error) { /* silencioso */ }
  }, []);

  useEffect(() => {
    loadAntecedentes();
    loadPacientes();
  }, [loadAntecedentes, loadPacientes]);

  const handleDelete = async (id: number) => {
    try {
      await antecedentesService.eliminar(id);
      message.success('Antecedente eliminado');
      loadAntecedentes();
    } catch (error) {
      message.error('Error al eliminar');
    }
  };

  const handleSave = async (values: any) => {
    try {
      const payload = { ...values, paciente: values.paciente };
      if (editingId) {
        await antecedentesService.actualizar(editingId, payload);
        message.success('Antecedente actualizado');
      } else {
        await antecedentesService.crear(payload);
        message.success('Antecedente creado');
      }
      setIsModalVisible(false);
      setEditingId(null);
      form.resetFields();
      loadAntecedentes();
    } catch (error) {
      message.error('Error al guardar');
    }
  };

  const handleEdit = (record: any) => {
    setEditingId(record.id);
    form.setFieldsValue({
      paciente: record.paciente_id || record.paciente,
      menarquia_edad: record.menarquia_edad,
      ciclos_menstruales: record.ciclos_menstruales,
      duracion_ciclo_dias: record.duracion_ciclo_dias,
      duracion_menstruacion_dias: record.duracion_menstruacion_dias,
      gestas: record.gestas,
      partos: record.partos,
      abortos: record.abortos,
      cesareas: record.cesareas,
      hijos_vivos: record.hijos_vivos,
      metodo_anticonceptivo_actual: record.metodo_anticonceptivo_actual,
      inicio_vida_sexual_edad: record.inicio_vida_sexual_edad,
      numero_parejas_sexuales: record.numero_parejas_sexuales,
    });
    setIsModalVisible(true);
  };

  const getNombrePaciente = (record: any) => {
    if (record.paciente_info?.nombre_completo) return record.paciente_info.nombre_completo;
    const pacienteId = record.paciente_id || record.paciente;
    const paciente = pacientes.find(p => p.id === pacienteId);
    return paciente
      ? `${paciente.nombre} ${paciente.apellido_paterno || paciente.apellido || ''}`.trim()
      : record.paciente_nombre || '-';
  };

  const filteredAntecedentes = antecedentesArray.filter((ant: any) => {
    if (!searchText) return true;
    return getNombrePaciente(ant).toLowerCase().includes(searchText.toLowerCase());
  });

  const columns = [
    { title: 'Paciente', key: 'paciente_nombre', render: (_: any, record: any) => getNombrePaciente(record) },
    {
      title: 'Fórmula Obstétrica', key: 'formula',
      render: (_: any, record: any) => {
        const formula = record.formula_obstetrica ||
          `G${record.gestas ?? 0}P${record.partos ?? 0}A${record.abortos ?? 0}C${record.cesareas ?? 0}`;
        return <Tag color="blue">{formula}</Tag>;
      },
    },
    { title: 'Gestas', dataIndex: 'gestas', render: (val: number) => val ?? '-' },
    { title: 'Partos', dataIndex: 'partos', render: (val: number) => val ?? '-' },
    { title: 'Abortos', dataIndex: 'abortos', render: (val: number) => val ?? '-' },
    { title: 'Cesáreas', dataIndex: 'cesareas', render: (val: number) => val ?? '-' },
    {
      title: 'Ciclos', dataIndex: 'ciclos_menstruales',
      render: (val: string) => {
        const colors: Record<string, string> = { regular: 'green', irregular: 'orange', amenorrea: 'red' };
        return val ? <Tag color={colors[val] || 'default'}>{val}</Tag> : '-';
      },
    },
    {
      title: 'Acciones', key: 'acciones',
      render: (_: any, record: any) => (
        <Space>
          <Tooltip title="Ver detalles">
            <Button size="small" icon={<EyeOutlined />} onClick={() => {
              modal.info({
                title: 'Antecedente Gineco-Obstétrico', width: 600,
                content: (
                  <div style={{ marginTop: 16 }}>
                    <p><strong>Paciente:</strong> {getNombrePaciente(record)}</p>
                    <p><strong>Fórmula:</strong> {record.formula_obstetrica || `G${record.gestas ?? 0}P${record.partos ?? 0}A${record.abortos ?? 0}C${record.cesareas ?? 0}`}</p>
                    <p><strong>Menarquia:</strong> {record.menarquia_edad ? `${record.menarquia_edad} años` : 'No registrada'}</p>
                    <p><strong>Ciclos:</strong> {record.ciclos_menstruales || 'No registrado'}</p>
                    <p><strong>Duración ciclo:</strong> {record.duracion_ciclo_dias ? `${record.duracion_ciclo_dias} días` : '-'}</p>
                    <p><strong>Hijos vivos:</strong> {record.hijos_vivos ?? '-'}</p>
                    <p><strong>Método anticonceptivo:</strong> {record.metodo_anticonceptivo_actual || 'Ninguno'}</p>
                    <p><strong>Inicio vida sexual:</strong> {record.inicio_vida_sexual_edad ? `${record.inicio_vida_sexual_edad} años` : '-'}</p>
                    <p><strong>FUM:</strong> {record.fecha_ultima_menstruacion ? dayjs(record.fecha_ultima_menstruacion).format('DD/MM/YYYY') : '-'}</p>
                  </div>
                ),
              });
            }} />
          </Tooltip>
          <Tooltip title="Editar">
            <Button size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)} />
          </Tooltip>
          <Popconfirm title="¿Eliminar este antecedente?" onConfirm={() => handleDelete(record.id)} okText="Sí" cancelText="No">
            <Button danger size="small" icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div className="page-container" style={{ padding: '24px' }}>
      <StatsCards stats={stats} />
      <SearchBar
        searchText={searchText}
        onSearchChange={setSearchText}
        onNew={() => { setEditingId(null); form.resetFields(); setIsModalVisible(true); }}
      />
      <Spin spinning={loading}>
        <Table
          columns={columns}
          dataSource={filteredAntecedentes}
          rowKey="id"
          pagination={{ pageSize: 20 }}
          locale={{ emptyText: <Empty description="Sin antecedentes gineco-obstétricos" /> }}
        />
      </Spin>
      <Modal
        title={editingId ? 'Editar Antecedente Gineco-Obstétrico' : 'Nuevo Antecedente Gineco-Obstétrico'}
        open={isModalVisible}
        onCancel={() => { setIsModalVisible(false); setEditingId(null); form.resetFields(); }}
        footer={[
          <Button key="cancel" onClick={() => { setIsModalVisible(false); setEditingId(null); form.resetFields(); }}>Cancelar</Button>,
          <Button key="submit" type="primary" onClick={() => form.submit()}>
            {editingId ? 'Actualizar' : 'Crear'}
          </Button>,
        ]}
        width={700}
      >
        <Form form={form} layout="vertical" onFinish={handleSave}>
          <AntecedentesFormFields pacientes={pacientes} />
        </Form>
      </Modal>
    </div>
  );
};

export default Antecedentes;
