import React, { useState, useEffect } from 'react';
import { Table, Button, Space, Tag, Input, Card, Select, message, Modal, Form, DatePicker, Row, Col } from 'antd';
import { PlusOutlined, SearchOutlined, EyeOutlined, EditOutlined, DeleteOutlined, ExclamationCircleOutlined } from '@ant-design/icons';
import axios from 'axios';
import { authService } from '../services/authService';
import dayjs from 'dayjs';
import FormularioEmbarazo from './FormularioEmbarazo';
import DetalleEmbarazo from './DetalleEmbarazo';

interface Embarazo {
  id: number;
  paciente: number;
  paciente_nombre?: string;
  numero_gesta: number;
  fecha_ultima_menstruacion: string;
  fecha_probable_parto: string;
  tipo_embarazo: string;
  riesgo_embarazo: string;
  estado: string;
  notas?: string;
  semanas_gestacion?: string;
  fecha_registro: string;
}

const Embarazos: React.FC = () => {
  const [embarazos, setEmbarazos] = useState<Embarazo[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [estadoFiltro, setEstadoFiltro] = useState<string>('todos');
  const [showForm, setShowForm] = useState(false);
  const [showDetalle, setShowDetalle] = useState(false);
  const [selectedEmbarazoId, setSelectedEmbarazoId] = useState<number | null>(null);
  
  // Modal de eliminación
  const [isDeleteModalVisible, setIsDeleteModalVisible] = useState(false);
  const [embarazoToDelete, setEmbarazoToDelete] = useState<number | null>(null);
  
  // Modal de edición
  const [isEditModalVisible, setIsEditModalVisible] = useState(false);
  const [embarazoToEdit, setEmbarazoToEdit] = useState<number | null>(null);
  const [editForm] = Form.useForm();
  const [loadingEdit, setLoadingEdit] = useState(false);
  const [fppCalculada, setFppCalculada] = useState<string>('');

  useEffect(() => {
    fetchEmbarazos();
  }, [estadoFiltro]);

  const fetchEmbarazos = async () => {
    setLoading(true);
    try {
      const token = authService.getToken();
      let url = 'http://127.0.0.1:8000/api/embarazos/';
      if (estadoFiltro !== 'todos') {
        url += `?estado=${estadoFiltro}`;
      }
      const response = await axios.get(url, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setEmbarazos(response.data);
    } catch (error) {
      console.error('Error al cargar embarazos:', error);
      message.error('Error al cargar embarazos');
    } finally {
      setLoading(false);
    }
  };

  const handleSuccess = () => {
    setShowForm(false);
    fetchEmbarazos();
  };

  const handleVerDetalle = (id: number) => {
    setSelectedEmbarazoId(id);
    setShowDetalle(true);
  };

  // ========== EDITAR ==========
  const calcularFPPEnEdicion = (fum: any) => {
    if (fum) {
      const fechaFPP = dayjs(fum).add(280, 'day');
      setFppCalculada(fechaFPP.format('DD/MM/YYYY'));
      editForm.setFieldsValue({ fecha_probable_parto: fechaFPP });
    }
  };

  const handleEdit = async (id: number) => {
    console.log('🟡 Abriendo modal de edición para ID:', id);
    
    if (showDetalle) {
      setShowDetalle(false);
    }
    
    setEmbarazoToEdit(id);
    setIsEditModalVisible(true);
    setFppCalculada('');
    
    try {
      const token = authService.getToken();
      const response = await axios.get(`http://127.0.0.1:8000/api/embarazos/${id}/`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      const embarazo = response.data;
      editForm.setFieldsValue({
        numero_gesta: embarazo.numero_gesta,
        fecha_ultima_menstruacion: dayjs(embarazo.fecha_ultima_menstruacion),
        fecha_probable_parto: embarazo.fecha_probable_parto ? dayjs(embarazo.fecha_probable_parto) : null,
        tipo_embarazo: embarazo.tipo_embarazo || 'simple',
        riesgo_embarazo: embarazo.riesgo_embarazo || 'bajo',
        estado: embarazo.estado || 'activo',
        notas: embarazo.notas || ''
      });
      
      // Mostrar FPP actual
      if (embarazo.fecha_probable_parto) {
        setFppCalculada(dayjs(embarazo.fecha_probable_parto).format('DD/MM/YYYY'));
      }
    } catch (error) {
      message.error('Error al cargar datos del embarazo');
      console.error(error);
    }
  };

  // Función para traducir mensajes de error
  const translateError = (msg: string): string => {
    const translations: any = {
      'This field is required.': 'Este campo es obligatorio',
      'This field may not be blank.': 'Este campo no puede estar en blanco',
      'Enter a valid date.': 'Ingrese una fecha válida',
      'Date has wrong format. Use one of these formats instead: YYYY-MM-DD.': 'Formato de fecha incorrecto'
    };
    return translations[msg] || msg;
  };

  const confirmarEdicion = async () => {
    try {
      const values = await editForm.validateFields();
      setLoadingEdit(true);
      
      const token = authService.getToken();
      await axios.put(
        `http://127.0.0.1:8000/api/embarazos/${embarazoToEdit}/`,
        {
          numero_gesta: values.numero_gesta,
          fecha_ultima_menstruacion: dayjs(values.fecha_ultima_menstruacion).format('YYYY-MM-DD'),
          fecha_probable_parto: values.fecha_probable_parto ? dayjs(values.fecha_probable_parto).format('YYYY-MM-DD') : null,
          tipo_embarazo: values.tipo_embarazo,
          riesgo_embarazo: values.riesgo_embarazo,
          estado: values.estado,
          notas: values.notas || ''
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      message.success('Embarazo actualizado correctamente');
      setIsEditModalVisible(false);
      setEmbarazoToEdit(null);
      editForm.resetFields();
      setFppCalculada('');
      fetchEmbarazos();
    } catch (error: any) {
      console.error('Error al actualizar:', error.response?.data);
      
      const errorData = error.response?.data;
      
      if (errorData?.errores) {
        const fieldErrors: any = {};
        
        Object.keys(errorData.errores).forEach(key => {
          const errorArray = errorData.errores[key];
          let errorMessage = Array.isArray(errorArray) ? errorArray[0] : errorArray;
          errorMessage = translateError(errorMessage);
          
          const fieldMap: any = {
            'numero_gesta': 'numero_gesta',
            'fecha_ultima_menstruacion': 'fecha_ultima_menstruacion',
            'fecha_probable_parto': 'fecha_probable_parto',
            'tipo_embarazo': 'tipo_embarazo',
            'riesgo_embarazo': 'riesgo_embarazo',
            'estado': 'estado',
            'notas': 'notas'
          };
          
          const frontendField = fieldMap[key] || key;
          fieldErrors[frontendField] = errorMessage;
        });
        
        editForm.setFields(
          Object.keys(fieldErrors).map(field => ({
            name: field,
            errors: [fieldErrors[field]]
          }))
        );
        
        message.error('Por favor corrija los errores en el formulario');
      } else if (error.errorFields) {
        message.error('Por favor complete todos los campos requeridos');
      } else {
        message.error('Error al actualizar embarazo');
      }
    } finally {
      setLoadingEdit(false);
    }
  };

  const cancelarEdicion = () => {
    setIsEditModalVisible(false);
    setEmbarazoToEdit(null);
    editForm.resetFields();
    setFppCalculada('');
  };

  // ========== ELIMINAR (Finalizar) ==========
  const handleDelete = (id: number) => {
    console.log('🔴 Abriendo modal para finalizar ID:', id);
    setEmbarazoToDelete(id);
    setIsDeleteModalVisible(true);
  };

  const confirmarEliminacion = async () => {
    if (!embarazoToDelete) return;
    
    try {
      const token = authService.getToken();
      await axios.delete(`http://127.0.0.1:8000/api/embarazos/${embarazoToDelete}/`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      message.success('Embarazo finalizado correctamente');
      setIsDeleteModalVisible(false);
      setEmbarazoToDelete(null);
      fetchEmbarazos();
    } catch (error: any) {
      console.error('❌ Error:', error);
      message.error('Error al finalizar embarazo');
    }
  };

  const cancelarEliminacion = () => {
    setIsDeleteModalVisible(false);
    setEmbarazoToDelete(null);
  };

  const calcularSemanasGestacion = (fum: string) => {
    const hoy = dayjs();
    const fechaFum = dayjs(fum);
    const diasDiferencia = hoy.diff(fechaFum, 'day');
    const semanas = Math.floor(diasDiferencia / 7);
    const dias = diasDiferencia % 7;
    return `${semanas}+${dias}`;
  };

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: 'Paciente',
      dataIndex: 'paciente_nombre',
      key: 'paciente_nombre',
      render: (nombre: string) => nombre || 'Sin información',
    },
    {
      title: 'Gesta',
      dataIndex: 'numero_gesta',
      key: 'numero_gesta',
      width: 80,
    },
    {
      title: 'FUM',
      dataIndex: 'fecha_ultima_menstruacion',
      key: 'fecha_ultima_menstruacion',
      render: (fecha: string) => dayjs(fecha).format('DD/MM/YYYY'),
    },
    {
      title: 'FPP',
      dataIndex: 'fecha_probable_parto',
      key: 'fecha_probable_parto',
      render: (fecha: string) => fecha ? dayjs(fecha).format('DD/MM/YYYY') : 'No calculada',
    },
    {
      title: 'EG',
      key: 'semanas',
      render: (record: Embarazo) => (
        <Tag color="blue">{calcularSemanasGestacion(record.fecha_ultima_menstruacion)} sem</Tag>
      ),
    },
    {
      title: 'Tipo',
      dataIndex: 'tipo_embarazo',
      key: 'tipo_embarazo',
      render: (tipo: string) => tipo?.charAt(0).toUpperCase() + tipo?.slice(1),
    },
    {
      title: 'Riesgo',
      dataIndex: 'riesgo_embarazo',
      key: 'riesgo_embarazo',
      render: (riesgo: string) => {
        let color = 'green';
        if (riesgo === 'medio') color = 'orange';
        if (riesgo === 'alto') color = 'red';
        return <Tag color={color}>{riesgo?.toUpperCase()}</Tag>;
      },
    },
    {
      title: 'Estado',
      dataIndex: 'estado',
      key: 'estado',
      render: (estado: string) => {
        let color = 'blue';
        if (estado === 'finalizado') color = 'green';
        if (estado === 'perdida') color = 'red';
        return <Tag color={color}>{estado?.toUpperCase()}</Tag>;
      },
    },
    {
      title: 'Acciones',
      key: 'acciones',
      fixed: 'right' as 'right',
      width: 250,
      render: (record: Embarazo) => (
        <Space>
          <Button 
            icon={<EyeOutlined />} 
            size="small"
            onClick={() => handleVerDetalle(record.id)}
          >
            Ver
          </Button>
          <Button 
            icon={<EditOutlined />} 
            size="small" 
            type="primary"
            onClick={() => handleEdit(record.id)}
          >
            Editar
          </Button>
          <Button 
            icon={<DeleteOutlined />} 
            size="small" 
            danger
            onClick={() => handleDelete(record.id)}
            disabled={record.estado === 'finalizado'}
          >
            Finalizar
          </Button>
        </Space>
      ),
    },
  ];

  const filteredEmbarazos = embarazos.filter(e =>
    e.paciente_nombre?.toLowerCase().includes(searchText.toLowerCase()) ||
    e.id.toString().includes(searchText)
  );

  if (showForm) {
    return <FormularioEmbarazo onCancel={() => setShowForm(false)} onSuccess={handleSuccess} />;
  }

  if (showDetalle && selectedEmbarazoId) {
    return (
      <DetalleEmbarazo 
        embarazoId={selectedEmbarazoId} 
        onBack={() => setShowDetalle(false)}
        onEdit={handleEdit}
      />
    );
  }

  return (
    <div style={{ padding: 24 }}>
      <Card>
        <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
          <h2>Lista de Embarazos</h2>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setShowForm(true)}>
            Nuevo Embarazo
          </Button>
        </div>

        <Space style={{ marginBottom: 16 }}>
          <Input
            placeholder="Buscar por paciente o ID..."
            prefix={<SearchOutlined />}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 300 }}
          />
          <Select 
            value={estadoFiltro} 
            onChange={setEstadoFiltro}
            style={{ width: 150 }}
          >
            <Select.Option value="todos">Todos</Select.Option>
            <Select.Option value="activo">Activos</Select.Option>
            <Select.Option value="finalizado">Finalizados</Select.Option>
            <Select.Option value="perdida">Pérdida</Select.Option>
          </Select>
        </Space>

        <Table
          columns={columns}
          dataSource={filteredEmbarazos}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
          scroll={{ x: 1400 }}
        />
      </Card>

      {/* Modal de FINALIZAR */}
      <Modal
        title="Confirmar Finalización"
        open={isDeleteModalVisible}
        onOk={confirmarEliminacion}
        onCancel={cancelarEliminacion}
        okText="Sí, finalizar"
        cancelText="Cancelar"
        okButtonProps={{ danger: true }}
      >
        <p>
          <ExclamationCircleOutlined style={{ color: '#ff4d4f', marginRight: 8 }} />
          ¿Está seguro de que desea finalizar este embarazo?
        </p>
        <p>El embarazo cambiará a estado "finalizado".</p>
      </Modal>

      {/* Modal de EDITAR */}
      <Modal
        title="Editar Embarazo"
        open={isEditModalVisible}
        onOk={confirmarEdicion}
        onCancel={cancelarEdicion}
        okText="Guardar Cambios"
        cancelText="Cancelar"
        confirmLoading={loadingEdit}
        width={800}
      >
        <Form form={editForm} layout="vertical">
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item 
                name="numero_gesta" 
                label="Número de Gesta" 
                rules={[
                  { required: true, message: 'Este campo es obligatorio' },
                  { type: 'number', min: 1, max: 20, message: 'Debe ser entre 1 y 20' }
                ]}
              >
                <Input type="number" min={1} max={20} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item 
                name="tipo_embarazo" 
                label="Tipo" 
                rules={[{ required: true, message: 'Este campo es obligatorio' }]}
              >
                <Select>
                  <Select.Option value="simple">Simple</Select.Option>
                  <Select.Option value="gemelar">Gemelar</Select.Option>
                  <Select.Option value="multiple">Múltiple</Select.Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item 
                name="riesgo_embarazo" 
                label="Riesgo" 
                rules={[{ required: true, message: 'Este campo es obligatorio' }]}
              >
                <Select>
                  <Select.Option value="bajo">Bajo</Select.Option>
                  <Select.Option value="medio">Medio</Select.Option>
                  <Select.Option value="alto">Alto</Select.Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item 
                name="fecha_ultima_menstruacion" 
                label="FUM" 
                rules={[{ required: true, message: 'Este campo es obligatorio' }]}
              >
                <DatePicker 
                  style={{ width: '100%' }} 
                  format="DD/MM/YYYY"
                  onChange={calcularFPPEnEdicion}
                  placeholder="Seleccionar cualquier fecha"
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item 
                name="fecha_probable_parto" 
                label="FPP (editable manualmente)"
              >
                <DatePicker 
                  style={{ width: '100%' }} 
                  format="DD/MM/YYYY"
                  placeholder="Editable manualmente"
                />
              </Form.Item>
              {fppCalculada && (
                <div style={{ color: '#52c41a', marginTop: -16, marginBottom: 16 }}>
                  ✓ FPP calculada: {fppCalculada}
                </div>
              )}
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={24}>
              <Form.Item 
                name="estado" 
                label="Estado" 
                rules={[{ required: true, message: 'Este campo es obligatorio' }]}
              >
                <Select>
                  <Select.Option value="activo">Activo</Select.Option>
                  <Select.Option value="finalizado">Finalizado</Select.Option>
                  <Select.Option value="perdida">Pérdida</Select.Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={24}>
              <Form.Item name="notas" label="Notas / Observaciones">
                <Input.TextArea rows={3} placeholder="Observaciones del embarazo..." />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>
    </div>
  );
};

export default Embarazos;