import React, { useState, useEffect } from 'react';
import { Table, Button, Space, Input, Card, message, Modal, Form, DatePicker, Row, Col, InputNumber, Select, Tag } from 'antd';
import { PlusOutlined, SearchOutlined, EyeOutlined, EditOutlined, DeleteOutlined, ExclamationCircleOutlined } from '@ant-design/icons';
import axios from 'axios';
import { authService } from '../services/authService';
import dayjs from 'dayjs';
import FormularioControl from './FormularioControl';
import DetalleControl from './DetalleControl';

interface Control {
  id: number;
  embarazo_id: number;
  paciente: number;
  paciente_nombre?: string;
  numero_control: number;
  fecha_control: string;
  semanas_gestacion: number;
  dias_gestacion?: number;
  edad_gestacional?: string;
  peso_actual: number;
  presion_arterial?: string;
  presion_arterial_sistolica?: number;
  presion_arterial_diastolica?: number;
  altura_uterina: number;
  frecuencia_cardiaca_fetal: number;
  imc_actual?: number;
  clasificacion_imc?: string;
  observaciones?: string;
  fecha_registro: string;
}

const Controles: React.FC = () => {
  const [controles, setControles] = useState<Control[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [showDetalle, setShowDetalle] = useState(false);
  const [selectedControlId, setSelectedControlId] = useState<number | null>(null);
  
  // Modal de eliminación
  const [isDeleteModalVisible, setIsDeleteModalVisible] = useState(false);
  const [controlToDelete, setControlToDelete] = useState<number | null>(null);
  
  // Modal de edición
  const [isEditModalVisible, setIsEditModalVisible] = useState(false);
  const [controlToEdit, setControlToEdit] = useState<number | null>(null);
  const [editForm] = Form.useForm();
  const [loadingEdit, setLoadingEdit] = useState(false);
  const [imcEditCalculado, setImcEditCalculado] = useState<string>('');
  const [pamEditCalculada, setPamEditCalculada] = useState<string>('');

  useEffect(() => {
    fetchControles();
  }, []);

  const fetchControles = async () => {
    setLoading(true);
    try {
      const token = authService.getToken();
      const response = await axios.get('http://127.0.0.1:8000/api/controles/', {
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

  const handleSuccess = () => {
    setShowForm(false);
    fetchControles();
  };

  const handleVerDetalle = (id: number) => {
    setSelectedControlId(id);
    setShowDetalle(true);
  };

  // ========== EDITAR ==========
  const calcularIMCEdit = () => {
    const peso = editForm.getFieldValue('peso_actual');
    const talla = editForm.getFieldValue('talla');
    
    if (peso && talla) {
      const tallaM = talla / 100;
      const imc = peso / (tallaM * tallaM);
      let clasificacion = '';
      
      if (imc < 18.5) clasificacion = 'Bajo peso';
      else if (imc < 25) clasificacion = 'Normal';
      else if (imc < 30) clasificacion = 'Sobrepeso';
      else clasificacion = 'Obesidad';
      
      setImcEditCalculado(`${imc.toFixed(2)} - ${clasificacion}`);
    }
  };

  const calcularPAMEdit = () => {
    const sistolica = editForm.getFieldValue('presion_arterial_sistolica');
    const diastolica = editForm.getFieldValue('presion_arterial_diastolica');
    
    if (sistolica && diastolica) {
      const pam = (sistolica + (2 * diastolica)) / 3;
      setPamEditCalculada(`PAM: ${pam.toFixed(2)} mmHg`);
    }
  };

  const handleEdit = async (id: number) => {
    console.log('🟡 Abriendo modal de edición para ID:', id);
    
    if (showDetalle) {
      setShowDetalle(false);
    }
    
    setControlToEdit(id);
    setIsEditModalVisible(true);
    
    try {
      const token = authService.getToken();
      const response = await axios.get(`http://127.0.0.1:8000/api/controles/${id}/`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      const control = response.data;
      editForm.setFieldsValue({
        numero_control: control.numero_control,
        fecha_control: dayjs(control.fecha_control),
        semanas_gestacion: control.semanas_gestacion,
        dias_gestacion: control.dias_gestacion || 0,
        peso_actual: control.peso_actual,
        talla: control.talla,
        presion_arterial_sistolica: control.presion_arterial_sistolica,
        presion_arterial_diastolica: control.presion_arterial_diastolica,
        frecuencia_cardiaca: control.frecuencia_cardiaca,
        temperatura: control.temperatura,
        altura_uterina: control.altura_uterina,
        frecuencia_cardiaca_fetal: control.frecuencia_cardiaca_fetal,
        presentacion_fetal: control.presentacion_fetal,
        movimientos_fetales: control.movimientos_fetales,
        edema: control.edema,
        proteinuria: control.proteinuria,
        observaciones: control.observaciones || ''
      });

      // Calcular IMC y PAM iniciales
      if (control.peso_actual && control.talla) {
        const tallaM = control.talla / 100;
        const imc = control.peso_actual / (tallaM * tallaM);
        let clasificacion = '';
        if (imc < 18.5) clasificacion = 'Bajo peso';
        else if (imc < 25) clasificacion = 'Normal';
        else if (imc < 30) clasificacion = 'Sobrepeso';
        else clasificacion = 'Obesidad';
        setImcEditCalculado(`${imc.toFixed(2)} - ${clasificacion}`);
      }

      if (control.presion_arterial_sistolica && control.presion_arterial_diastolica) {
        const pam = (control.presion_arterial_sistolica + (2 * control.presion_arterial_diastolica)) / 3;
        setPamEditCalculada(`PAM: ${pam.toFixed(2)} mmHg`);
      }
    } catch (error) {
      message.error('Error al cargar datos del control');
      console.error(error);
    }
  };

  const translateError = (msg: string): string => {
    const translations: any = {
      'This field is required.': 'Este campo es obligatorio',
      'This field may not be blank.': 'Este campo no puede estar en blanco',
      'Enter a valid date.': 'Ingrese una fecha válida',
      'Enter a valid number.': 'Ingrese un número válido'
    };
    return translations[msg] || msg;
  };

  const confirmarEdicion = async () => {
    try {
      const values = await editForm.validateFields();
      setLoadingEdit(true);
      
      const token = authService.getToken();
      await axios.put(
        `http://127.0.0.1:8000/api/controles/${controlToEdit}/`,
        {
          numero_control: values.numero_control,
          fecha_control: dayjs(values.fecha_control).format('YYYY-MM-DD'),
          semanas_gestacion: values.semanas_gestacion,
          dias_gestacion: values.dias_gestacion,
          peso_actual: values.peso_actual,
          talla: values.talla,
          presion_arterial_sistolica: values.presion_arterial_sistolica,
          presion_arterial_diastolica: values.presion_arterial_diastolica,
          frecuencia_cardiaca: values.frecuencia_cardiaca,
          temperatura: values.temperatura,
          altura_uterina: values.altura_uterina,
          frecuencia_cardiaca_fetal: values.frecuencia_cardiaca_fetal,
          presentacion_fetal: values.presentacion_fetal,
          movimientos_fetales: values.movimientos_fetales,
          edema: values.edema,
          proteinuria: values.proteinuria,
          observaciones: values.observaciones || ''
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      message.success('Control actualizado correctamente');
      setIsEditModalVisible(false);
      setControlToEdit(null);
      editForm.resetFields();
      setImcEditCalculado('');
      setPamEditCalculada('');
      fetchControles();
    } catch (error: any) {
      console.error('Error al actualizar:', error.response?.data);
      
      const errorData = error.response?.data;
      
      if (errorData?.errores) {
        const fieldErrors: any = {};
        
        Object.keys(errorData.errores).forEach(key => {
          const errorArray = errorData.errores[key];
          let errorMessage = Array.isArray(errorArray) ? errorArray[0] : errorArray;
          errorMessage = translateError(errorMessage);
          fieldErrors[key] = errorMessage;
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
        message.error('Error al actualizar control');
      }
    } finally {
      setLoadingEdit(false);
    }
  };

  const cancelarEdicion = () => {
    setIsEditModalVisible(false);
    setControlToEdit(null);
    editForm.resetFields();
    setImcEditCalculado('');
    setPamEditCalculada('');
  };

  // ========== ELIMINAR ==========
  const handleDelete = (id: number) => {
    console.log('🔴 Abriendo modal para eliminar ID:', id);
    setControlToDelete(id);
    setIsDeleteModalVisible(true);
  };

  const confirmarEliminacion = async () => {
    if (!controlToDelete) return;
    
    try {
      const token = authService.getToken();
      await axios.delete(`http://127.0.0.1:8000/api/controles/${controlToDelete}/`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      message.success('Control eliminado correctamente');
      setIsDeleteModalVisible(false);
      setControlToDelete(null);
      fetchControles();
    } catch (error: any) {
      console.error('Error al eliminar:', error);
      message.error('Error al eliminar control');
    }
  };

  const cancelarEliminacion = () => {
    setIsDeleteModalVisible(false);
    setControlToDelete(null);
  };

  // ========== TABLA ==========
  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 60,
      sorter: (a: Control, b: Control) => a.id - b.id,
    },
    {
      title: 'N° Control',
      dataIndex: 'numero_control',
      key: 'numero_control',
      width: 100,
    },
    {
      title: 'Paciente',
      dataIndex: 'paciente_nombre',
      key: 'paciente_nombre',
      width: 200,
      render: (text: string, record: Control) => text || `Paciente #${record.paciente}`,
    },
    {
      title: 'Embarazo',
      dataIndex: 'embarazo_id',
      key: 'embarazo_id',
      width: 100,
    },
    {
      title: 'Fecha Control',
      dataIndex: 'fecha_control',
      key: 'fecha_control',
      width: 120,
      render: (text: string) => dayjs(text).format('DD/MM/YYYY'),
    },
    {
      title: 'Edad Gestacional',
      key: 'edad_gestacional',
      width: 140,
      render: (record: Control) => (
        <span>
          {record.semanas_gestacion}+{record.dias_gestacion || 0} semanas
        </span>
      ),
    },
    {
      title: 'PA',
      key: 'presion_arterial',
      width: 100,
      render: (record: Control) => {
        if (!record.presion_arterial_sistolica || !record.presion_arterial_diastolica) return '-';
        const sistolica = record.presion_arterial_sistolica;
        const diastolica = record.presion_arterial_diastolica;
        
        let color = 'green';
        if (sistolica >= 140 || diastolica >= 90) color = 'red';
        else if (sistolica >= 120 || diastolica >= 80) color = 'orange';
        
        return (
          <Tag color={color}>
            {sistolica}/{diastolica}
          </Tag>
        );
      },
    },
    {
      title: 'FCF',
      dataIndex: 'frecuencia_cardiaca_fetal',
      key: 'frecuencia_cardiaca_fetal',
      width: 80,
      render: (fcf: number) => {
        if (!fcf) return '-';
        const color = (fcf < 110 || fcf > 160) ? 'red' : 'green';
        return <Tag color={color}>{fcf} lpm</Tag>;
      },
    },
    {
      title: 'Acciones',
      key: 'acciones',
      width: 250,
      fixed: 'right' as const,
      render: (record: Control) => (
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
          >
            Eliminar
          </Button>
        </Space>
      ),
    },
  ];

  const filteredControles = controles.filter(c => {
    if (!searchText) return true;
    return c.embarazo_id?.toString().includes(searchText) || 
           c.paciente_nombre?.toLowerCase().includes(searchText.toLowerCase()) ||
           c.id?.toString().includes(searchText);
  });

  if (showForm) {
    return <FormularioControl onCancel={() => setShowForm(false)} onSuccess={handleSuccess} />;
  }

  if (showDetalle && selectedControlId) {
    return (
      <DetalleControl 
        controlId={selectedControlId} 
        onBack={() => setShowDetalle(false)}
        onEdit={handleEdit}
      />
    );
  }

  return (
    <div style={{ padding: 24 }}>
      <Card>
        <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
          <h2>Controles Prenatales</h2>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setShowForm(true)}>
            Nuevo Control
          </Button>
        </div>

        <Input
          placeholder="Buscar por paciente, embarazo o ID..."
          prefix={<SearchOutlined />}
          onChange={(e) => setSearchText(e.target.value)}
          style={{ marginBottom: 16, width: 300 }}
        />

        <Table
          columns={columns}
          dataSource={filteredControles}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
          scroll={{ x: 1400 }}
        />
      </Card>

      {/* Modal de ELIMINAR */}
      <Modal
        title="Confirmar Eliminación"
        open={isDeleteModalVisible}
        onOk={confirmarEliminacion}
        onCancel={cancelarEliminacion}
        okText="Sí, eliminar"
        cancelText="Cancelar"
        okButtonProps={{ danger: true }}
      >
        <p>
          <ExclamationCircleOutlined style={{ color: '#ff4d4f', marginRight: 8 }} />
          ¿Está seguro de que desea eliminar este control prenatal?
        </p>
        <p>Esta acción no se puede deshacer.</p>
      </Modal>

      {/* Modal de EDITAR */}
      <Modal
        title="Editar Control Prenatal"
        open={isEditModalVisible}
        onOk={confirmarEdicion}
        onCancel={cancelarEdicion}
        okText="Guardar Cambios"
        cancelText="Cancelar"
        confirmLoading={loadingEdit}
        width={900}
      >
        <Form form={editForm} layout="vertical">
          <Row gutter={16}>
            <Col span={6}>
              <Form.Item 
                name="numero_control" 
                label="N° Control" 
                rules={[{ required: true, message: 'Obligatorio' }]}
              >
                <InputNumber style={{ width: '100%' }} min={1} />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item 
                name="fecha_control" 
                label="Fecha" 
                rules={[{ required: true, message: 'Obligatorio' }]}
              >
                <DatePicker style={{ width: '100%' }} format="DD/MM/YYYY" />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item 
                name="semanas_gestacion" 
                label="Semanas" 
                rules={[{ required: true, message: 'Obligatorio' }]}
              >
                <InputNumber style={{ width: '100%' }} min={0} max={42} />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="dias_gestacion" label="Días">
                <InputNumber style={{ width: '100%' }} min={0} max={6} />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item 
                name="peso_actual" 
                label="Peso (kg)"
                rules={[{ required: true, message: 'Obligatorio' }]}
              >
                <InputNumber 
                  style={{ width: '100%' }} 
                  min={30} 
                  max={200} 
                  step={0.1}
                  onChange={calcularIMCEdit}
                />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item 
                name="talla" 
                label="Talla (cm)"
                rules={[{ required: true, message: 'Obligatorio' }]}
              >
                <InputNumber 
                  style={{ width: '100%' }} 
                  min={130} 
                  max={200}
                  onChange={calcularIMCEdit}
                />
              </Form.Item>
              {imcEditCalculado && (
                <div style={{ color: '#52c41a', marginTop: -16, marginBottom: 16 }}>
                  ✓ IMC: {imcEditCalculado}
                </div>
              )}
            </Col>
            <Col span={8}>
              <Form.Item name="altura_uterina" label="AU (cm)">
                <InputNumber style={{ width: '100%' }} min={0} max={50} />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item 
                name="presion_arterial_sistolica" 
                label="PA Sistólica"
                rules={[{ required: true, message: 'Obligatorio' }]}
              >
                <InputNumber 
                  style={{ width: '100%' }} 
                  min={70} 
                  max={220}
                  onChange={calcularPAMEdit}
                />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item 
                name="presion_arterial_diastolica" 
                label="PA Diastólica"
                rules={[{ required: true, message: 'Obligatorio' }]}
              >
                <InputNumber 
                  style={{ width: '100%' }} 
                  min={40} 
                  max={130}
                  onChange={calcularPAMEdit}
                />
              </Form.Item>
              {pamEditCalculada && (
                <div style={{ color: '#52c41a', marginTop: -16, marginBottom: 16 }}>
                  ✓ {pamEditCalculada}
                </div>
              )}
            </Col>
            <Col span={8}>
              <Form.Item name="frecuencia_cardiaca" label="FC (lpm)">
                <InputNumber style={{ width: '100%' }} min={40} max={200} />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="temperatura" label="Temp (°C)">
                <InputNumber style={{ width: '100%' }} min={35} max={42} step={0.1} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item 
                name="frecuencia_cardiaca_fetal" 
                label="FCF (lpm)"
                rules={[{ required: true, message: 'Obligatorio' }]}
              >
                <InputNumber style={{ width: '100%' }} min={100} max={180} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="presentacion_fetal" label="Presentación">
                <Select>
                  <Select.Option value="cefalica">Cefálica</Select.Option>
                  <Select.Option value="podalica">Podálica</Select.Option>
                  <Select.Option value="transversa">Transversa</Select.Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="movimientos_fetales" label="Movimientos">
                <Select>
                  <Select.Option value="presentes">Presentes</Select.Option>
                  <Select.Option value="ausentes">Ausentes</Select.Option>
                  <Select.Option value="disminuidos">Disminuidos</Select.Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="edema" label="Edema">
                <Select>
                  <Select.Option value="no">No</Select.Option>
                  <Select.Option value="leve">Leve</Select.Option>
                  <Select.Option value="moderado">Moderado</Select.Option>
                  <Select.Option value="severo">Severo</Select.Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="proteinuria" label="Proteinuria">
                <Select>
                  <Select.Option value="negativa">Negativa</Select.Option>
                  <Select.Option value="trazas">Trazas</Select.Option>
                  <Select.Option value="positiva_1">+</Select.Option>
                  <Select.Option value="positiva_2">++</Select.Option>
                  <Select.Option value="positiva_3">+++</Select.Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={24}>
              <Form.Item name="observaciones" label="Observaciones">
                <Input.TextArea rows={3} placeholder="Observaciones del control..." />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>
    </div>
  );
};

export default Controles;