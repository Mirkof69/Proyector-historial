/**
 * =============================================================================
 * MODAL DE GESTIÓN DE HORARIOS
 * =============================================================================
 * Modal para gestionar los horarios de atención de un usuario
 * =============================================================================
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Modal, Table, Button, Space, Form, Select, TimePicker, Switch, Tag, Alert, Spin, Card } from 'antd';
import { useAntdApp } from '../../hooks/useMessage';
import { PlusOutlined, EditOutlined, DeleteOutlined, ClockCircleOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { usuariosService, HorarioAtencion, horariosService } from '../../services/usuariosService';

interface GestionHorariosModalProps {
  open: boolean;
  onCancel: () => void;
  currentUser?: { id?: number; nombre?: string; rol?: string };
}

const DIAS_SEMANA = [
  { value: 'lunes', label: 'Lunes' },
  { value: 'martes', label: 'Martes' },
  { value: 'miercoles', label: 'Miércoles' },
  { value: 'jueves', label: 'Jueves' },
  { value: 'viernes', label: 'Viernes' },
  { value: 'sabado', label: 'Sábado' },
  { value: 'domingo', label: 'Domingo' },
];

export const GestionHorariosModal: React.FC<GestionHorariosModalProps> = ({
  open,
  onCancel,
  currentUser,
}) => {
  const { message } = useAntdApp();
  const [form] = Form.useForm();
  const [isLoading, setIsLoading] = useState(false);
  const [horarios, setHorarios] = useState<HorarioAtencion[]>([]);
  const [editingId, setEditingId] = useState<number | null>(null);

  // Ajuste de estado al cambiar de usuario, con estado previo en vez de ref
  // mutado en render (patrón oficial de React).
  const [prevUserId, setPrevUserId] = useState<number | undefined>(currentUser?.id);
  if (currentUser?.id !== prevUserId) {
    setPrevUserId(currentUser?.id);
    setHorarios([]);
  }

  const cargarHorarios = useCallback(async () => {
    if (!currentUser?.id) return;
    setIsLoading(true);
    try {
      const data = await horariosService.getAll({ usuario_id: currentUser.id });
      setHorarios(data || []);
    } catch (error) {
      message.error('Error al cargar los horarios');
    } finally {
      setIsLoading(false);
    }
  }, [currentUser?.id, message]);

  useEffect(() => {
    if (!currentUser?.id) return;
    cargarHorarios();
    return () => {};
  }, [currentUser?.id, cargarHorarios]);

  const handleGuardar = async (values: any) => {
    if (!currentUser?.id) return;
    setIsLoading(true);
    try {
      const horarioData = {
        usuario: currentUser.id,
        dia_semana: values.dia_semana,
        hora_inicio: values.hora_inicio.format('HH:mm:ss'),
        hora_fin: values.hora_fin.format('HH:mm:ss'),
        activo: values.activo ?? true,
      };

      if (editingId) {
        await horariosService.update(editingId, horarioData);
        message.success('Horario actualizado correctamente');
      } else {
        await horariosService.create(horarioData);
        message.success('Horario creado correctamente');
      }

      form.resetFields();
      setEditingId(null);
      await cargarHorarios();
    } catch (error) {
      message.error('Error al guardar el horario');
    } finally {
      setIsLoading(false);
    }
  };

  const handleEditar = (record: HorarioAtencion) => {
    setEditingId(record.id || null);
    form.setFieldsValue({
      dia_semana: record.dia_semana,
      hora_inicio: dayjs(record.hora_inicio, 'HH:mm:ss'),
      hora_fin: dayjs(record.hora_fin, 'HH:mm:ss'),
      activo: record.activo,
    });
  };

  const handleEliminar = async (id: number) => {
    try {
      await horariosService.delete(id);
      message.success('Horario eliminado');
      await cargarHorarios();
    } catch (error) {
      message.error('Error al eliminar el horario');
    }
  };

  const handleNuevo = () => {
    setEditingId(null);
    form.resetFields();
    form.setFieldsValue({ activo: true });
  };

  const columns = [
    {
      title: 'Día',
      dataIndex: 'dia_semana_display',
      key: 'dia',
    },
    {
      title: 'Hora Inicio',
      dataIndex: 'hora_inicio',
      key: 'hora_inicio',
      render: (text: string) => dayjs(text, 'HH:mm:ss').format('HH:mm'),
    },
    {
      title: 'Hora Fin',
      dataIndex: 'hora_fin',
      key: 'hora_fin',
      render: (text: string) => dayjs(text, 'HH:mm:ss').format('HH:mm'),
    },
    {
      title: 'Estado',
      dataIndex: 'activo',
      key: 'activo',
      render: (activo: boolean) => (
        <Tag color={activo ? 'green' : 'red'}>{activo ? 'Activo' : 'Inactivo'}</Tag>
      ),
    },
    {
      title: 'Acciones',
      key: 'acciones',
      render: (_: any, record: HorarioAtencion) => (
        <Space>
          <Button size="small" icon={<EditOutlined />} onClick={() => handleEditar(record)} />
          <Button size="small" danger icon={<DeleteOutlined />} onClick={() => handleEliminar(record.id!)} />
        </Space>
      ),
    },
  ];

  return (
    <Modal
      open={open}
      onCancel={onCancel}
      title={
        <Space>
          <ClockCircleOutlined />
          Gestión de Horarios
          {currentUser?.nombre && <Tag>{currentUser.nombre}</Tag>}
        </Space>
      }
      width={800}
      footer={null}
    >
      {!currentUser?.id ? (
        <Alert message="Seleccione un usuario para gestionar sus horarios" type="warning" showIcon />
      ) : (
        <>
          <Card title={editingId ? 'Editar Horario' : 'Nuevo Horario'} size="small" style={{ marginBottom: 16 }}>
            <Form form={form} layout="inline" onFinish={handleGuardar} initialValues={{ activo: true }}>
              <Form.Item name="dia_semana" label="Día" rules={[{ required: true, message: 'Seleccione un día' }]}>
                <Select style={{ width: 150 }} options={DIAS_SEMANA} />
              </Form.Item>
              <Form.Item name="hora_inicio" label="Inicio" rules={[{ required: true, message: 'Seleccione hora' }]}>
                <TimePicker format="HH:mm" />
              </Form.Item>
              <Form.Item name="hora_fin" label="Fin" rules={[{ required: true, message: 'Seleccione hora' }]}>
                <TimePicker format="HH:mm" />
              </Form.Item>
              <Form.Item name="activo" valuePropName="checked">
                <Switch checkedChildren="Activo" unCheckedChildren="Inactivo" />
              </Form.Item>
              <Form.Item>
                <Space>
                  <Button type="primary" htmlType="submit" loading={isLoading} icon={<PlusOutlined />}>
                    {editingId ? 'Actualizar' : 'Agregar'}
                  </Button>
                  {editingId && <Button onClick={handleNuevo}>Nuevo</Button>}
                </Space>
              </Form.Item>
            </Form>
          </Card>

          {isLoading ? (
            <div style={{ textAlign: 'center', padding: 20 }}>
              <Spin />
            </div>
          ) : (
            <Table
              columns={columns}
              dataSource={horarios}
              rowKey="id"
              pagination={false}
              size="small"
            />
          )}
        </>
      )}
    </Modal>
  );
};
