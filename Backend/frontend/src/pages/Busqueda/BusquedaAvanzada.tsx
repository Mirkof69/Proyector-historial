/**
 * Búsqueda Avanzada de Pacientes
 */
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, Form, Input, Select, DatePicker, InputNumber, Button, Table, Space, Tag, Row, Col, Checkbox, Empty } from 'antd';
import { useAntdApp } from '../../hooks/useMessage';
import { SearchOutlined, ClearOutlined, UserOutlined } from '@ant-design/icons';
import { api } from '../../services/api';
import { FRONTEND_ROUTES } from '../../config/routes';

const { RangePicker } = DatePicker;
const { Option } = Select;

const BusquedaAvanzada: React.FC = () => {
    const [form] = Form.useForm();
    const navigate = useNavigate();
    const { message } = useAntdApp();
    const [loading, setLoading] = useState(false);
    const [resultados, setResultados] = useState<any[]>([]);
    const [total, setTotal] = useState(0);

    const handleBuscar = async (values: any) => {
        setLoading(true);
        try {
            const payload: any = {};

            if (values.nombre) payload.nombre = values.nombre;
            if (values.id_clinico) payload.id_clinico = values.id_clinico;
            if (values.ci) payload.ci = values.ci;
            if (values.fecha_rango) {
                payload.fecha_desde = values.fecha_rango[0].format('YYYY-MM-DD');
                payload.fecha_hasta = values.fecha_rango[1].format('YYYY-MM-DD');
            }
            if (values.edad_min) payload.edad_min = values.edad_min;
            if (values.edad_max) payload.edad_max = values.edad_max;
            if (values.estado_civil) payload.estado_civil = values.estado_civil;
            if (values.embarazo_activo !== undefined) payload.embarazo_activo = values.embarazo_activo;
            if (values.riesgo_alto !== undefined) payload.riesgo_alto = values.riesgo_alto;

            const response = await api.post('/pacientes/busqueda-avanzada/', payload);
            setResultados(response.results);
            setTotal(response.count);
            message.success(`${response.count} pacientes encontrados`);
        } catch (error) {
            message.error('Error en la búsqueda');
        } finally {
            setLoading(false);
        }
    };

    const handleLimpiar = () => {
        form.resetFields();
        setResultados([]);
        setTotal(0);
    };

    const columns = [
        { title: 'ID Clínico', dataIndex: 'id_clinico', key: 'id_clinico', width: 120 },
        { title: 'Nombre Completo', key: 'nombre', render: (r: any) => `${r.nombre} ${r.apellido_paterno} ${r.apellido_materno || ''}` },
        { title: 'CI', dataIndex: 'ci', key: 'ci', width: 120 },
        { title: 'Edad', key: 'edad', render: (r: any) => `${r.edad || 'N/A'} años`, width: 80 },
        { title: 'Teléfono', dataIndex: 'telefono', key: 'telefono', width: 120 },
        {
            title: 'Acciones', key: 'acciones', width: 100, render: (r: any) => (
                <Button size="small" type="link" icon={<UserOutlined />} onClick={() => navigate(FRONTEND_ROUTES.DASHBOARD.PACIENTES_DETALLE(r.id))}>Ver</Button>
            )
        },
    ];

    return (
        <div className="page-container" style={{ padding: 24 }}>
            <Card title={<Space><SearchOutlined /> Búsqueda Avanzada de Pacientes</Space>}>
                <Form form={form} layout="vertical" onFinish={handleBuscar}>
                    <Row gutter={16}>
                        <Col span={8}><Form.Item label="Nombre/Apellido" name="nombre"><Input placeholder="Búsqueda fuzzy" /></Form.Item></Col>
                        <Col span={8}><Form.Item label="ID Clínico" name="id_clinico"><Input placeholder="HC-XXX" /></Form.Item></Col>
                        <Col span={8}><Form.Item label="CI" name="ci"><Input placeholder="Cédula" /></Form.Item></Col>
                    </Row>

                    <Row gutter={16}>
                        <Col span={12}><Form.Item label="Rango de Registro" name="fecha_rango"><RangePicker style={{ width: '100%' }} /></Form.Item></Col>
                        <Col span={6}><Form.Item label="Edad Mínima" name="edad_min"><InputNumber min={0} max={100} style={{ width: '100%' }} /></Form.Item></Col>
                        <Col span={6}><Form.Item label="Edad Máxima" name="edad_max"><InputNumber min={0} max={100} style={{ width: '100%' }} /></Form.Item></Col>
                    </Row>

                    {/* Sin filtro de género: todas las pacientes son femeninas. */}
                    <Row gutter={16}>
                        <Col span={8}>
                            <Form.Item label="Estado Civil" name="estado_civil">
                                <Select placeholder="Seleccionar" allowClear>
                                    <Option value="soltera">Soltera</Option>
                                    <Option value="casada">Casada</Option>
                                    <Option value="union_libre">Unión Libre</Option>
                                    <Option value="divorciada">Divorciada</Option>
                                    <Option value="viuda">Viuda</Option>
                                </Select>
                            </Form.Item>
                        </Col>
                        <Col span={8}>
                            <Form.Item label="Filtros Especiales" style={{ marginBottom: 0 }}>
                                <Form.Item name="embarazo_activo" valuePropName="checked"><Checkbox>Embarazo Activo</Checkbox></Form.Item>
                                <Form.Item name="riesgo_alto" valuePropName="checked"><Checkbox>Alto Riesgo</Checkbox></Form.Item>
                            </Form.Item>
                        </Col>
                    </Row>

                    <Space>
                        <Button type="primary" htmlType="submit" icon={<SearchOutlined />} loading={loading}>Buscar</Button>
                        <Button icon={<ClearOutlined />} onClick={handleLimpiar}>Limpiar</Button>
                    </Space>
                </Form>
            </Card>

            {total > 0 && (
                <Card title={`Resultados (${total})`} style={{ marginTop: 24 }}>
                    <Table columns={columns} dataSource={resultados} rowKey="id" pagination={{ pageSize: 20 }} locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="Sin resultados — ajuste los filtros de búsqueda" /> }} />
                </Card>
            )}
        </div>
    );
};

export default BusquedaAvanzada;
