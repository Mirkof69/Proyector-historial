/**
 * =============================================================================
 * DETALLE DE ECOGRAFÍA - VISTA COMPLETA
 * =============================================================================
 * Muestra información completa de una ecografía específica con todos los datos
 * relacionados: Biometría, Anatomía, Anexos e Imágenes.
 * =============================================================================
 */

import React, { useState, useEffect } from 'react';
import { useAntdApp } from "../../hooks/useMessage";
import {Card,
  Descriptions,
  Button,
  Space,
  Tag,
  Alert,
  Row,
  Col,
  Divider,
  Image,
  Timeline,
  Statistic,
  Collapse,
  Spin,
  Typography,
  Badge,
  Modal,
  Checkbox,
  Tabs,
  Upload,
  Empty} from "antd";
import {
  ArrowLeftOutlined,
  EditOutlined,
  PrinterOutlined,
  DeleteOutlined,
  FileImageOutlined,
  CalendarOutlined,
  UserOutlined,
  HeartOutlined,
  ExclamationCircleOutlined,
  CheckCircleOutlined,
  InfoCircleOutlined,
  LineChartOutlined,
  MedicineBoxOutlined,
  ScanOutlined,
  UploadOutlined,
  PlusOutlined,
} from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import dayjs from 'dayjs';
import { ecografiasService, Ecografia } from '../../services/ecografiasService';
import { FRONTEND_ROUTES } from '../../config/routes';
import { useAuth } from '../../hooks/useAuth';
import { API_URL } from '../../services/api';

const { Title, Text, Paragraph } = Typography;

const handleImprimir = () => {
  window.print();
};

const DetalleEcografia: React.FC = () => {
  const { modal, message } = useAntdApp();
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const { getToken } = useAuth();
  const [loading, setLoading] = useState(true);
  const [ecografia, setEcografia] = useState<Ecografia | null>(null);

  // ==========================================================================
  // CARGAR DATOS
  // ==========================================================================
  const cargarDatos = React.useCallback(async () => {
    setLoading(true);
    try {
      const ecoData = await ecografiasService.getById(Number(id));
      setEcografia(ecoData);
      message.success('Datos cargados correctamente');
    } catch (error) {
      message.error('Error al cargar los datos de la ecografía');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    if (id) cargarDatos();
  }, [id, cargarDatos]);

  // ==========================================================================
  // HANDLERS
  // ==========================================================================
  const handleVolver = () => {
    navigate(FRONTEND_ROUTES.DASHBOARD.ECOGRAFIAS);
  };

  const handleEditar = () => {
    navigate(FRONTEND_ROUTES.DASHBOARD.ECOGRAFIAS_EDITAR(Number(id)));
  };

  const handleEliminar = () => {
    modal.confirm({
      title: '¿Eliminar esta ecografía?',
      icon: <ExclamationCircleOutlined />,
      content: 'Esta acción no se puede deshacer.',
      okText: 'Eliminar',
      okType: 'danger',
      cancelText: 'Cancelar',
      onOk: async () => {
        try {
          await ecografiasService.delete(Number(id));
          message.success('Ecografía eliminada correctamente');
          navigate(FRONTEND_ROUTES.DASHBOARD.ECOGRAFIAS);
        } catch (error) {
          message.error('Error al eliminar la ecografía');
        }
      },
    });
  };

  const handleImageUpload = (info: any) => {
    if (info.file.status === 'uploading') {
      message.loading({ content: 'Subiendo imagen...', key: 'upload' });
    }
    if (info.file.status === 'done') {
      message.success({ content: 'Imagen subida correctamente', key: 'upload' });
      cargarDatos(); // Recargar para mostrar las nuevas imágenes
    } else if (info.file.status === 'error') {
      message.error({ content: 'Error al subir la imagen', key: 'upload' });
    }
  };

  // ==========================================================================
  // RENDER
  // ==========================================================================
  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px 0' }}>
        <Spin size="large" />
        <div style={{ marginTop: 16 }}>Cargando datos de la ecografía…</div>
      </div>
    );
  }

  if (!ecografia) {
    return (
      <Card>
        <Alert
          message="Ecografía no encontrada"
          description="No se encontró la ecografía solicitada."
          type="error"
          showIcon
        />
        <Button onClick={handleVolver} style={{ marginTop: 16 }}>
          Volver al listado
        </Button>
      </Card>
    );
  }

  return (
    <div className="detalle-ecografia-container">
      {/* HEADER */}
      <Card className="header-card">
        <Row justify="space-between" align="middle">
          <Col>
            <Space>
              <Button icon={<ArrowLeftOutlined />} onClick={handleVolver}>
                Volver
              </Button>
              <Divider type="vertical" />
              <FileImageOutlined style={{ fontSize: 24, color: '#1890ff' }} />
              <div>
                <Title level={4} style={{ margin: 0 }}>
                  Detalle de Ecografía
                </Title>
                <Text type="secondary">
                  {dayjs(ecografia.fecha_ecografia).format('DD/MM/YYYY')}
                </Text>
              </div>
            </Space>
          </Col>
          <Col>
            <Space>
              <Button icon={<PrinterOutlined />} onClick={handleImprimir}>
                Imprimir
              </Button>
              <Button type="primary" icon={<EditOutlined />} onClick={handleEditar}>
                Editar
              </Button>
              <Button danger icon={<DeleteOutlined />} onClick={handleEliminar}>
                Eliminar
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={16}>
          {/* INFORMACIÓN GENERAL */}
          <Card
            title={
              <Space>
                <ScanOutlined />
                Datos Generales
              </Space>
            }
            style={{ marginBottom: 16 }}
          >
            <Descriptions column={{ xs: 1, sm: 2 }} bordered>
              <Descriptions.Item label="Paciente">
                {ecografia.paciente_nombre || `ID: ${ecografia.paciente}`}
              </Descriptions.Item>
              <Descriptions.Item label="Médico">
                <Space>
                  <UserOutlined style={{ color: '#1890ff' }} />
                  {ecografia.medico_nombre || '-'}
                  {ecografia.medico_nombre && <CheckCircleOutlined style={{ color: '#52c41a' }} />}
                </Space>
              </Descriptions.Item>
              <Descriptions.Item label="Fecha del Estudio">
                <Space>
                  <CalendarOutlined />
                  {dayjs(ecografia.fecha_ecografia).format('DD/MM/YYYY')}
                </Space>
              </Descriptions.Item>
              <Descriptions.Item label="Tipo de Ecografía">
                <Tag color="blue">
                  {ecografia.tipo_ecografia?.replace('_', ' ').toUpperCase()}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Edad Gestacional">
                <Text strong>{ecografia.edad_gestacional_texto}</Text>
              </Descriptions.Item>
              <Descriptions.Item label="Número de Fetos">
                {ecografia.numero_fetos || 1}
              </Descriptions.Item>
              <Descriptions.Item label="Vitalidad Fetal">
                {ecografia.vitalidad_fetal ? (
                  <Badge status="success" text="Presente" />
                ) : (
                  <Badge status="error" text="Ausente" />
                )}
              </Descriptions.Item>
              {ecografia.frecuencia_cardiaca_fetal && (
                <Descriptions.Item label="FCF">
                  <Space>
                    <HeartOutlined style={{ color: '#ff4d4f' }} />
                    {ecografia.frecuencia_cardiaca_fetal} lpm
                  </Space>
                </Descriptions.Item>
              )}
            </Descriptions>
          </Card>

          {/* TIMELINE DEL ESTUDIO */}
          <Card
            title={
              <Space>
                <InfoCircleOutlined />
                Línea de Tiempo del Estudio
              </Space>
            }
            style={{ marginBottom: 16 }}
          >
            <Timeline
              items={[
                {
                  color: 'green',
                  children: (
                    <>
                      <Text strong>Estudio Solicitado</Text>
                      <br />
                      <Text type="secondary">{dayjs(ecografia.fecha_ecografia).subtract(1, 'day').format('DD/MM/YYYY')}</Text>
                    </>
                  ),
                },
                {
                  color: 'blue',
                  children: (
                    <>
                      <Text strong>Ecografía Realizada</Text>
                      <br />
                      <Text type="secondary">{dayjs(ecografia.fecha_ecografia).format('DD/MM/YYYY HH:mm')}</Text>
                      <br />
                      <Space style={{ marginTop: 4 }}>
                        <Checkbox checked disabled>Biometría completa</Checkbox>
                        <Checkbox checked={!!ecografia.anatomia} disabled>Evaluación anatómica</Checkbox>
                        <Checkbox checked={!!ecografia.anexos} disabled>Anexos evaluados</Checkbox>
                      </Space>
                    </>
                  ),
                },
                {
                  color: ecografia.diagnostico ? 'green' : 'gray',
                  children: (
                    <>
                      <Text strong>Diagnóstico Emitido</Text>
                      <br />
                      <Text type="secondary">
                        {ecografia.diagnostico ? dayjs(ecografia.fecha_ecografia).format('DD/MM/YYYY') : 'Pendiente'}
                      </Text>
                    </>
                  ),
                },
                {
                  color: ecografia.requiere_seguimiento ? 'orange' : 'green',
                  children: (
                    <>
                      <Text strong>{ecografia.requiere_seguimiento ? 'Requiere Seguimiento' : 'Estudio Completo'}</Text>
                      <br />
                      <Text type="secondary">
                        {ecografia.requiere_seguimiento ? 'Se programará control adicional' : 'No requiere seguimiento especial'}
                      </Text>
                    </>
                  ),
                },
              ]}
            />
          </Card>

          {/* SECCIONES ORGANIZADAS EN TABS */}
          <Card style={{ marginBottom: 16 }}>
            <Tabs
              defaultActiveKey="biometria"
              items={[
                {
                  key: 'biometria',
                  label: (
                    <span>
                      <LineChartOutlined />
                      Biometría Fetal
                    </span>
                  ),
                  children: ecografia.biometria ? (
                    <>
                      <Row gutter={[16, 16]}>
                        {ecografia.biometria.diametro_biparietal && (
                          <Col xs={24} sm={12} md={8}>
                            <Statistic
                              title="DBP"
                              value={ecografia.biometria.diametro_biparietal}
                              suffix="mm"
                              valueStyle={{ color: '#1890ff' }}
                            />
                          </Col>
                        )}
                        {ecografia.biometria.circunferencia_cefalica && (
                          <Col xs={24} sm={12} md={8}>
                            <Statistic
                              title="CC"
                              value={ecografia.biometria.circunferencia_cefalica}
                              suffix="mm"
                              valueStyle={{ color: '#52c41a' }}
                            />
                          </Col>
                        )}
                        {ecografia.biometria.circunferencia_abdominal && (
                          <Col xs={24} sm={12} md={8}>
                            <Statistic
                              title="CA"
                              value={ecografia.biometria.circunferencia_abdominal}
                              suffix="mm"
                              valueStyle={{ color: '#722ed1' }}
                            />
                          </Col>
                        )}
                        {ecografia.biometria.longitud_femur && (
                          <Col xs={24} sm={12} md={8}>
                            <Statistic
                              title="LF"
                              value={ecografia.biometria.longitud_femur}
                              suffix="mm"
                              valueStyle={{ color: '#fa8c16' }}
                            />
                          </Col>
                        )}
                        {ecografia.biometria.peso_fetal_estimado && (
                          <Col xs={24} sm={12} md={8}>
                            <Statistic
                              title="Peso Fetal Estimado"
                              value={ecografia.biometria.peso_fetal_estimado}
                              suffix="g"
                              valueStyle={{ color: '#13c2c2', fontSize: 24 }}
                              prefix={<HeartOutlined />}
                            />
                          </Col>
                        )}
                        {ecografia.biometria.percentil_peso && (
                          <Col xs={24} sm={12} md={8}>
                            <Statistic
                              title="Percentil de Peso"
                              value={ecografia.biometria.percentil_peso}
                              suffix="%"
                              valueStyle={{ color: '#eb2f96' }}
                            />
                          </Col>
                        )}
                      </Row>
                      {ecografia.biometria.evaluacion_crecimiento && (
                        <Alert
                          message={ecografia.biometria.evaluacion_crecimiento}
                          type={ecografia.biometria.evaluacion_crecimiento?.includes('Normal') ? 'success' : 'warning'}
                          showIcon
                          style={{ marginTop: 16 }}
                        />
                      )}
                    </>
                  ) : (
                    <Empty description="No hay datos de biometría" />
                  ),
                },
                {
                  key: 'anatomia',
                  label: (
                    <span>
                      <MedicineBoxOutlined />
                      Anatomía Fetal
                    </span>
                  ),
                  children: ecografia.anatomia ? (
                    <>
                      <Collapse
                        defaultActiveKey={['organos']}
                        items={[
                          {
                            key: 'organos',
                            label: 'Evaluación de Órganos',
                            children: (
                              <Descriptions column={2} bordered size="small">
                                <Descriptions.Item label="Cráneo">
                                  {ecografia.anatomia.craneo_normal ? '✅ Normal' : '❌ Anormal'}
                                </Descriptions.Item>
                                <Descriptions.Item label="Cerebro">
                                  {ecografia.anatomia.cerebro_normal ? '✅ Normal' : '❌ Anormal'}
                                </Descriptions.Item>
                                <Descriptions.Item label="Corazón">
                                  {ecografia.anatomia.corazon_normal ? '✅ Normal' : '❌ Anormal'}
                                </Descriptions.Item>
                                <Descriptions.Item label="Columna">
                                  {ecografia.anatomia.columna_normal ? '✅ Normal' : '❌ Anormal'}
                                </Descriptions.Item>
                                <Descriptions.Item label="Extremidades Superiores">
                                  {ecografia.anatomia.extremidades_superiores_normales ? '✅ Normal' : '❌ Anormal'}
                                </Descriptions.Item>
                                <Descriptions.Item label="Extremidades Inferiores">
                                  {ecografia.anatomia.extremidades_inferiores_normales ? '✅ Normal' : '❌ Anormal'}
                                </Descriptions.Item>
                                {ecografia.anatomia.sexo_fetal && (
                                  <Descriptions.Item label="Sexo Fetal" span={2}>
                                    <Tag color={ecografia.anatomia.sexo_fetal === 'masculino' ? 'blue' : 'magenta'}>
                                      {ecografia.anatomia.sexo_fetal.toUpperCase()}
                                    </Tag>
                                  </Descriptions.Item>
                                )}
                              </Descriptions>
                            ),
                          },
                        ]}
                      />
                      {ecografia.anatomia.evaluacion_anatomica && (
                        <Collapse
                          style={{ marginTop: 16 }}
                          items={[
                            {
                              key: '1',
                              label: 'Evaluación Anatómica Completa',
                              children: (
                                <Alert
                                  message={ecografia.anatomia.evaluacion_anatomica}
                                  type={ecografia.anatomia.evaluacion_anatomica?.includes('normal') ? 'success' : 'warning'}
                                  showIcon
                                />
                              ),
                            },
                          ]}
                        />
                      )}
                    </>
                  ) : (
                    <Empty description="No hay datos de anatomía" />
                  ),
                },
                {
                  key: 'anexos',
                  label: (
                    <span>
                      <InfoCircleOutlined />
                      Anexos Fetales
                    </span>
                  ),
                  children: ecografia.anexos ? (
                    <>
                      <Descriptions column={2} bordered>
                        {ecografia.anexos.placenta_localizacion && (
                          <Descriptions.Item label="Placenta - Localización">
                            {ecografia.anexos.placenta_localizacion}
                          </Descriptions.Item>
                        )}
                        {ecografia.anexos.numero_vasos_cordon && (
                          <Descriptions.Item label="Vasos del Cordón">
                            {ecografia.anexos.numero_vasos_cordon} vasos
                          </Descriptions.Item>
                        )}
                        {ecografia.indice_liquido_amniotico && (
                          <Descriptions.Item label="ILA">
                            {ecografia.indice_liquido_amniotico} cm
                          </Descriptions.Item>
                        )}
                        {ecografia.estado_liquido_amniotico && (
                          <Descriptions.Item label="Estado Líquido">
                            <Tag>{ecografia.estado_liquido_amniotico}</Tag>
                          </Descriptions.Item>
                        )}
                      </Descriptions>
                      {ecografia.anexos.evaluacion_cordon && (
                        <Alert
                          message={ecografia.anexos.evaluacion_cordon}
                          type={ecografia.anexos.evaluacion_cordon?.includes('Normal') ? 'success' : 'warning'}
                          showIcon
                          style={{ marginTop: 16 }}
                        />
                      )}
                    </>
                  ) : (
                    <Empty description="No hay datos de anexos" />
                  ),
                },
                {
                  key: 'diagnostico',
                  label: (
                    <span>
                      <FileImageOutlined />
                      Diagnóstico
                    </span>
                  ),
                  children: (
                    <Descriptions column={1} bordered>
                      <Descriptions.Item label="Diagnóstico Ecográfico">
                        {ecografia.diagnostico && ecografia.diagnostico.trim() !== '' ? (
                          <Paragraph>{ecografia.diagnostico}</Paragraph>
                        ) : (
                          <Text type="secondary" italic>
                            No se registró diagnóstico para esta ecografía
                          </Text>
                        )}
                      </Descriptions.Item>
                      {ecografia.observaciones && ecografia.observaciones.trim() !== '' && (
                        <Descriptions.Item label="Observaciones">
                          <Paragraph>{ecografia.observaciones}</Paragraph>
                        </Descriptions.Item>
                      )}
                      {ecografia.requiere_seguimiento && (
                        <Descriptions.Item label="Seguimiento">
                          <Alert
                            message="Requiere seguimiento especial"
                            type="warning"
                            showIcon
                          />
                        </Descriptions.Item>
                      )}
                    </Descriptions>
                  ),
                },
              ]}
            />
          </Card>

          {/* Las secciones de Biometría, Anatomía, Anexos y Diagnóstico ahora están organizadas en Tabs arriba */}

          {/* ANATOMÍA FETAL (código antiguo, ahora en Tabs) */}
          {false && ecografia && (
            <>
              {/* ANATOMÍA FETAL */}
              {ecografia?.anatomia && (
                <Card
                  title={
                    <Space>
                      <MedicineBoxOutlined />
                      Anatomía Fetal
                    </Space>
                  }
                  style={{ marginBottom: 16 }}
                >
                  <Descriptions column={2} bordered size="small">
                    <Descriptions.Item label="Cráneo">
                      {ecografia?.anatomia?.craneo_normal ? '✅ Normal' : '❌ Anormal'}
                    </Descriptions.Item>
                    <Descriptions.Item label="Cerebro">
                      {ecografia?.anatomia?.cerebro_normal ? '✅ Normal' : '❌ Anormal'}
                    </Descriptions.Item>
                    <Descriptions.Item label="Corazón">
                      {ecografia?.anatomia?.corazon_normal ? '✅ Normal' : '❌ Anormal'}
                    </Descriptions.Item>
                    <Descriptions.Item label="Columna">
                      {ecografia?.anatomia?.columna_normal ? '✅ Normal' : '❌ Anormal'}
                    </Descriptions.Item>
                    <Descriptions.Item label="Extremidades Superiores">
                      {ecografia?.anatomia?.extremidades_superiores_normales ? '✅ Normal' : '❌ Anormal'}
                    </Descriptions.Item>
                    <Descriptions.Item label="Extremidades Inferiores">
                      {ecografia?.anatomia?.extremidades_inferiores_normales ? '✅ Normal' : '❌ Anormal'}
                    </Descriptions.Item>
                    {ecografia?.anatomia?.sexo_fetal && (
                      <Descriptions.Item label="Sexo Fetal" span={2}>
                        <Tag color={ecografia?.anatomia?.sexo_fetal === 'masculino' ? 'blue' : 'magenta'}>
                          {ecografia?.anatomia?.sexo_fetal?.toUpperCase()}
                        </Tag>
                      </Descriptions.Item>
                    )}
                  </Descriptions>
                  {ecografia?.anatomia?.evaluacion_anatomica && (
                    <Alert
                      message={ecografia?.anatomia?.evaluacion_anatomica}
                      type={ecografia?.anatomia?.evaluacion_anatomica?.includes('normal') ? 'success' : 'warning'}
                      showIcon
                      style={{ marginTop: 16 }}
                    />
                  )}
                </Card>
              )}

              {/* ANEXOS FETALES */}
              {ecografia?.anexos && (
                <Card
                  title={
                    <Space>
                      <InfoCircleOutlined />
                      Anexos Fetales
                    </Space>
                  }
                  style={{ marginBottom: 16 }}
                >
                  <Descriptions column={2} bordered>
                    {ecografia?.anexos?.placenta_localizacion && (
                      <Descriptions.Item label="Placenta - Localización">
                        {ecografia?.anexos?.placenta_localizacion}
                      </Descriptions.Item>
                    )}
                    {ecografia?.anexos?.numero_vasos_cordon && (
                      <Descriptions.Item label="Vasos del Cordón">
                        {ecografia?.anexos?.numero_vasos_cordon} vasos
                      </Descriptions.Item>
                    )}
                    {ecografia?.indice_liquido_amniotico && (
                      <Descriptions.Item label="ILA">
                        {ecografia?.indice_liquido_amniotico} cm
                      </Descriptions.Item>
                    )}
                    {ecografia?.estado_liquido_amniotico && (
                      <Descriptions.Item label="Estado Líquido">
                        <Tag>{ecografia?.estado_liquido_amniotico}</Tag>
                      </Descriptions.Item>
                    )}
                  </Descriptions>
                  {ecografia?.anexos?.evaluacion_cordon && (
                    <Alert
                      message={ecografia?.anexos?.evaluacion_cordon}
                      type={ecografia?.anexos?.evaluacion_cordon?.includes('Normal') ? 'success' : 'warning'}
                      showIcon
                      style={{ marginTop: 16 }}
                    />
                  )}
                </Card>
              )}

              {/* DIAGNÓSTICO Y OBSERVACIONES */}
              <Card
                title={
                  <Space>
                    <FileImageOutlined />
                    Diagnóstico y Conclusiones
                  </Space>
                }
                style={{ marginBottom: 16 }}
              >
                <Descriptions column={1} bordered>
                  <Descriptions.Item label="Diagnóstico Ecográfico">
                    {ecografia?.diagnostico && ecografia?.diagnostico?.trim() !== '' ? (
                      <Paragraph>{ecografia?.diagnostico}</Paragraph>
                    ) : (
                      <Text type="secondary" italic>
                        No se registró diagnóstico para esta ecografía
                      </Text>
                    )}
                  </Descriptions.Item>
                  {ecografia?.observaciones && ecografia?.observaciones?.trim() !== '' && (
                    <Descriptions.Item label="Observaciones">
                      <Paragraph>{ecografia?.observaciones}</Paragraph>
                    </Descriptions.Item>
                  )}
                  {ecografia?.requiere_seguimiento && (
                    <Descriptions.Item label="Seguimiento">
                      <Alert
                        message="Requiere seguimiento especial"
                        type="warning"
                        showIcon
                      />
                    </Descriptions.Item>
                  )}
                </Descriptions>
              </Card>
            </>
          )}

          {/* IMÁGENES ECOGRÁFICAS */}
          <Card
            title={
              <Space>
                <FileImageOutlined />
                Imágenes Ecográficas {ecografia.imagenes && ecografia.imagenes.length > 0 && `(${ecografia.imagenes.length})`}
              </Space>
            }
            style={{ marginBottom: 16 }}
          >
            {/* Sección de subida de imágenes */}
            <Upload
              name="imagen"
              action={`${API_URL}/ecografias/${id}/subir_imagen/`}
              headers={{
                'Authorization': `Bearer ${getToken()}`,
              }}
              onChange={handleImageUpload}
              listType="picture-card"
              showUploadList={false}
              accept="image/*"
            >
              <Button icon={<UploadOutlined />} type="dashed" block style={{ marginBottom: 16 }}>
                <PlusOutlined /> Subir Nueva Imagen
              </Button>
            </Upload>

            {/* Galería de imágenes */}
            {ecografia.imagenes && ecografia.imagenes.length > 0 ? (
              <Row gutter={[16, 16]}>
                {ecografia.imagenes.map((img, index) => (
                  <Col xs={24} sm={12} md={8} lg={6} key={img.id || `img-${img.titulo}`}>
                    <Card
                      hoverable
                      size="small"
                      cover={
                        <Image
                          src={img.url_imagen || (typeof img.imagen === 'string' ? img.imagen : '')}
                          alt={img.titulo || `Imagen ${index + 1}`}
                          style={{ height: 200, objectFit: 'cover', borderRadius: '8px 8px 0 0' }}
                          fallback="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+P+/HgAFcgJS9sIqAwAAAABJRU5ErkJggg=="
                        />
                      }
                    >
                      <Card.Meta
                        title={
                          <Text ellipsis style={{ fontSize: 12 }}>
                            {img.titulo || `Imagen ${index + 1}`}
                          </Text>
                        }
                        description={
                          <Space direction="vertical" size={0} style={{ width: '100%' }}>
                            {img.tipo_imagen && (
                              <Tag color="blue" style={{ fontSize: '12px' }}>
                                {img.tipo_imagen.replace('_', ' ').toUpperCase()}
                              </Tag>
                            )}
                            {img.descripcion && (
                              <Text type="secondary" style={{ fontSize: '12px' }} ellipsis>
                                {img.descripcion}
                              </Text>
                            )}
                          </Space>
                        }
                      />
                    </Card>
                  </Col>
                ))}
              </Row>
            ) : (
              <Alert
                message="No hay imágenes"
                description="Aún no se han subido imágenes para esta ecografía. Use el botón superior para subir imágenes."
                type="info"
                showIcon
              />
            )}
          </Card>
        </Col>

        {/* COLUMNA DERECHA */}
        <Col xs={24} lg={8}>
          {/* INFORMACIÓN ADICIONAL */}
          <Card
            title={
              <Space>
                <InfoCircleOutlined />
                Información Adicional
              </Space>
            }
          >
            <Descriptions column={1} bordered size="small">
              <Descriptions.Item label="Calidad del Estudio">
                <Tag>{ecografia.calidad_estudio || 'No especificada'}</Tag>
              </Descriptions.Item>
              {ecografia.limitaciones_tecnicas && (
                <Descriptions.Item label="Limitaciones">
                  {ecografia.limitaciones_tecnicas}
                </Descriptions.Item>
              )}
              <Descriptions.Item label="Fecha de Registro">
                {ecografia.fecha_registro
                  ? dayjs(ecografia.fecha_registro).format('DD/MM/YYYY HH:mm')
                  : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="Registrado por">
                {ecografia.created_by_nombre || <Text type="secondary">No registrado</Text>}
              </Descriptions.Item>
              <Descriptions.Item label="Última Modificación">
                {ecografia.fecha_modificacion
                  ? dayjs(ecografia.fecha_modificacion).format('DD/MM/YYYY HH:mm')
                  : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="Modificado por">
                {ecografia.updated_by_nombre || <Text type="secondary">No registrado</Text>}
              </Descriptions.Item>
            </Descriptions>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default DetalleEcografia;
