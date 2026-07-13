import React, { useState, useEffect, useCallback } from 'react';
import {Card,
  Row,
  Col,
  Button,
  Form,
  Input,
  Upload,
  Typography,
  Tabs,
  Descriptions,
  Tag,
  Divider,
  Avatar,
  Spin,
  Alert,
  Space,
  Empty,
  Progress} from "antd";
import {
  UserOutlined,
  UploadOutlined,
  LockOutlined,
  SaveOutlined,
  MailOutlined,
  PhoneOutlined,
  SafetyCertificateOutlined,
  IdcardOutlined,
  EditOutlined,
  KeyOutlined,
  LogoutOutlined,
  CheckOutlined,
} from '@ant-design/icons';
import type { UploadFile, UploadProps } from 'antd/es/upload/interface';
import { useMessage } from '../hooks/useMessage';
import { authService } from '../services/authService';
import { usuariosService } from '../services/usuariosService';
import dayjs from 'dayjs';

// ═════════════════════════════════════════════════════════════════════════
// TIPOS E INTERFACES
// ═════════════════════════════════════════════════════════════════════════

interface Usuario {
  id: number;
  username?: string;
  nombre: string;
  apellido_paterno: string;
  apellido_materno?: string;
  email: string;
  telefono?: string;
  rol: 'medico' | 'enfermero' | 'enfermera' | 'administrador' | 'paciente' | 'recepcion' | 'laboratorista';
  especialidad?: string;
  activo?: boolean;
  foto_url?: string | null;
  last_login?: string | null;
  fecha_creacion?: string;
}

const { Title, Text } = Typography;

const tabDatosPersonales = <span><UserOutlined /> Datos Personales</span>;
const tabSeguridad = <span><LockOutlined /> Seguridad</span>;

// ═════════════════════════════════════════════════════════════════════════
// COMPONENTE PRINCIPAL
// ═════════════════════════════════════════════════════════════════════════

const Perfil: React.FC = () => {
  const message = useMessage();

  // ─────────────────────────────────────────────────────────────────────────
  // ESTADOS
  // ─────────────────────────────────────────────────────────────────────────
  const [loading, setLoading] = useState(false);
  const [updating, setUpdating] = useState(false);
  const [user, setUser] = useState<Usuario | null>(null);
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [uploadProgress, setUploadProgress] = useState(0);

  const [formPerfil] = Form.useForm();
  const [formPassword] = Form.useForm();

  // ─────────────────────────────────────────────────────────────────────────
  // EFECTOS
  // ─────────────────────────────────────────────────────────────────────────

  // ─────────────────────────────────────────────────────────────────────────
  // FUNCIONES DE CARGA
  // ─────────────────────────────────────────────────────────────────────────

  const fetchUserData = useCallback(async () => {
    setLoading(true);
    try {
      // usuariosService.getMe() pide /usuarios/me/ al backend: datos reales y
      // actualizados (activo, last_login, foto_url). authService.getCurrentUser()
      // solo lee el objeto cacheado en localStorage desde el login, por lo que
      // mostraba "SUSPENDIDO"/"Nunca"/"N/A" aunque la base de datos tuviera
      // los valores correctos.
      const currentUser = await usuariosService.getMe();
      if (currentUser) {
        setUser(currentUser as unknown as Usuario);
        formPerfil.setFieldsValue(currentUser);

        if (currentUser.foto_url) {
          setFileList([
            {
              uid: '-1',
              name: 'avatar.png',
              status: 'done',
              url: currentUser.foto_url,
            },
          ]);
        } else {
          setFileList([]);
        }
      }
    } catch (error: any) {
      message.error('Error al cargar información del perfil.');
    } finally {
      setLoading(false);
    }
  }, [formPerfil, message]);

  useEffect(() => {
    fetchUserData();
  }, [fetchUserData]);

  // ─────────────────────────────────────────────────────────────────────────
  // HANDLERS (ACTUALIZAR DATOS)
  // ─────────────────────────────────────────────────────────────────────────

  const handleUpdateProfile = async (values: any) => {
    if (!user) return;
    setUpdating(true);
    try {
      const updatedUser: Usuario = {
        ...user,
        ...values,
        id: user.id,
        email: user.email,
        rol: user.rol,
        activo: user.activo,
      };

      // El archivo seleccionado en el Upload nunca se enviaba: solo se
      // guardaba en el estado local del componente "fileList", asi que
      // "Subir Foto" parecia funcionar pero nunca se persistia nada.
      // beforeUpload guarda el RcFile crudo (es un File real) en fileList,
      // no un originFileObj — solo aplica si es un archivo nuevo, no la
      // foto remota ya existente (que llega como {url: foto_url}).
      const candidato = fileList[0] as unknown as File | undefined;
      const nuevaFoto = candidato instanceof File ? candidato : undefined;
      const payload: any = { ...updatedUser };
      if (nuevaFoto) {
        payload.foto = nuevaFoto;
      }

      const guardado = await usuariosService.update(updatedUser.id, payload);

      message.success('Perfil actualizado correctamente');
      setUser({ ...updatedUser, foto_url: (guardado as any)?.foto_url ?? updatedUser.foto_url });
    } catch (error: any) {
      message.error(error.message || 'No se pudo actualizar el perfil');
    } finally {
      setUpdating(false);
    }
  };

  const handleChangePassword = async (values: any) => {
    if (!user) return;
    
    if (values.newPassword !== values.confirmPassword) {
      message.error('Las contraseñas no coinciden');
      return;
    }

    setUpdating(true);
    try {
      await usuariosService.cambiarPassword(user.id, {
        password_actual: values.currentPassword,
        password_nueva: values.newPassword,
        password_nueva_confirm: values.confirmPassword
      });
      message.success(
        'Contraseña modificada exitosamente. Por favor inicie sesión nuevamente.'
      );
      formPassword.resetFields();
      // Opcional: redirigir a login después de un tiempo
      setTimeout(() => {
        window.location.href = '/login';
      }, 2000);
    } catch (error: any) {
      message.error(
        error.response?.data?.detail ||
        'La contraseña actual es incorrecta o hubo un error.'
      );
    } finally {
      setUpdating(false);
    }
  };

  // ─────────────────────────────────────────────────────────────────────────
  // CONFIGURACIÓN DE UPLOAD (FOTO)
  // ─────────────────────────────────────────────────────────────────────────

  const uploadProps: UploadProps = {
    onRemove: (file) => {
      setFileList([]);
      setUploadProgress(0);
    },
    beforeUpload: (file) => {
      const isJpgOrPng =
        file.type === 'image/jpeg' || file.type === 'image/png';
      if (!isJpgOrPng) {
        message.error('Solo puedes subir archivos JPG/PNG');
        return Upload.LIST_IGNORE;
      }

      const isLt2M = file.size / 1024 / 1024 < 2;
      if (!isLt2M) {
        message.error('La imagen debe pesar menos de 2MB');
        return Upload.LIST_IGNORE;
      }

      setFileList([file]);
      return false;
    },
    onChange: (info) => {
      if (info.file.status === 'uploading') {
        const progress = Math.round(
          (info.file.percent || 0) * 100
        );
        setUploadProgress(progress);
      }
    },
    fileList,
  };

  // ─────────────────────────────────────────────────────────────────────────
  // RENDERIZADO
  // ─────────────────────────────────────────────────────────────────────────

  if (loading) {
    return (
      <div
        style={{
          height: '80vh',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
        }}
      >
        <Spin size="large" tip="Cargando perfil…"><div /></Spin>
      </div>
    );
  }

  if (!user) {
    return (
      <div style={{ padding: 24 }}>
        <Empty description="No se pudieron cargar los datos del usuario" />
      </div>
    );
  }

  return (
    <div
      className="perfil-container animate-fade-in"
      style={{ maxWidth: 1200, margin: '0 auto', padding: 24 }}
    >

      {/* CABECERA DEL PERFIL */}
      <Card
        variant="borderless"
        className="shadow-md"
        style={{
          marginBottom: 24,
          background: 'var(--bg-card)',
        }}
      >
        <Row align="middle" gutter={24}>
          <Col xs={24} sm={6} style={{ textAlign: 'center' }}>
            <Avatar
              size={100}
              src={user.foto_url || undefined}
              icon={<UserOutlined />}
              style={{
                border: '4px solid var(--border-color)',
                boxShadow: '0 4px 10px rgba(0,0,0,0.3)',
              }}
            />
          </Col>
          <Col xs={24} sm={18} md={20}>
            <Title level={2} style={{ marginBottom: 0 }}>
              {user.nombre} {user.apellido_paterno}
            </Title>
            <Text type="secondary" style={{ fontSize: 16 }}>
              {user.email}
            </Text>
            <div style={{ marginTop: 12 }}>
              <Tag color="blue" icon={<SafetyCertificateOutlined />}>
                {user.rol?.toUpperCase() || 'USUARIO'}
              </Tag>
              {user.especialidad && (
                <Tag color="cyan">{user.especialidad}</Tag>
              )}
              <Tag color={user.activo ? 'green' : 'red'}>
                {user.activo ? 'CUENTA ACTIVA' : 'SUSPENDIDO'}
              </Tag>
            </div>
          </Col>
        </Row>
      </Card>

      <Row gutter={24}>

        {/* COLUMNA IZQUIERDA: RESUMEN RÁPIDO */}
        <Col xs={24} lg={8}>
          <Card
            title="Información de Acceso"
            variant="borderless"
            className="shadow-sm"
            style={{ marginBottom: 24 }}
          >
            <Descriptions column={1} size="small" bordered>
              <Descriptions.Item
                label={
                  <>
                    <IdcardOutlined /> ID Usuario
                  </>
                }
              >
                {user.id}
              </Descriptions.Item>
              <Descriptions.Item
                label={
                  <>
                    <MailOutlined /> Email
                  </>
                }
              >
                {user.email}
              </Descriptions.Item>
              <Descriptions.Item label="Teléfono">
                {user.telefono || 'No registrado'}
              </Descriptions.Item>
              <Descriptions.Item label="Último Acceso">
                {user.last_login ? dayjs(user.last_login).format('DD/MM/YYYY HH:mm') : 'Nunca'}
              </Descriptions.Item>
              <Descriptions.Item label="Fecha Registro">
                {user.fecha_creacion ? dayjs(user.fecha_creacion).format('DD/MM/YYYY') : 'N/A'}
              </Descriptions.Item>
            </Descriptions>

            <Divider />
            <Alert
              message="Seguridad"
              description="Recuerde cambiar su contraseña cada 3 meses para mantener su cuenta segura."
              type="info"
              showIcon
            />
          </Card>
        </Col>

        {/* COLUMNA DERECHA: FORMULARIOS DE EDICIÓN */}
        <Col xs={24} lg={16}>
          <Card className="shadow-sm">
            <Tabs defaultActiveKey="1" items={[
              {
                key: "1",
                label: tabDatosPersonales,
                children: (
                  <Form
                    form={formPerfil}
                    layout="vertical"
                    onFinish={handleUpdateProfile}
                    initialValues={user}
                  >
                    <Row gutter={16}>
                      <Col span={12}>
                        <Form.Item
                          name="nombre"
                          label="Nombres"
                          rules={[
                            {
                              required: true,
                              message: 'Los nombres son obligatorios',
                            },
                          ]}
                        >
                          <Input prefix={<UserOutlined />} />
                        </Form.Item>
                      </Col>
                      <Col span={12}>
                        <Form.Item
                          name="apellido_paterno"
                          label="Apellido Paterno"
                          rules={[
                            {
                              required: true,
                              message: 'El apellido paterno es obligatorio',
                            },
                          ]}
                        >
                          <Input />
                        </Form.Item>
                      </Col>
                    </Row>
                    <Row gutter={16}>
                      <Col span={12}>
                        <Form.Item
                          name="apellido_materno"
                          label="Apellido Materno"
                        >
                          <Input />
                        </Form.Item>
                      </Col>
                      <Col span={12}>
                        <Form.Item name="telefono" label="Teléfono">
                          <Input prefix={<PhoneOutlined />} />
                        </Form.Item>
                      </Col>
                    </Row>

                    <Form.Item
                      name="email"
                      label="Correo Electrónico"
                      rules={[
                        {
                          required: true,
                          type: 'email',
                          message: 'Ingrese un email válido',
                        },
                      ]}
                    >
                      <Input
                        prefix={<MailOutlined />}
                        disabled
                        title="El email no puede ser modificado"
                      />
                    </Form.Item>

                    <Form.Item label="Foto de Perfil">
                      {uploadProgress > 0 && uploadProgress < 100 && (
                        <Progress
                          percent={uploadProgress}
                          style={{ marginBottom: 12 }}
                        />
                      )}
                      <Upload
                        {...uploadProps}
                        listType="picture-card"
                        maxCount={1}
                      >
                        <div>
                          <UploadOutlined style={{ fontSize: 24 }} />
                          <div style={{ marginTop: 8 }}>Subir Foto</div>
                        </div>
                      </Upload>
                      <Text type="secondary" style={{ fontSize: 12, display: 'block', marginTop: 4 }}>
                        JPG o PNG, máximo 2MB. Se guarda al hacer clic en "Guardar Cambios".
                      </Text>
                    </Form.Item>

                    <Form.Item>
                      <Space>
                        <Button
                          type="primary"
                          htmlType="submit"
                          icon={<SaveOutlined />}
                          loading={updating}
                        >
                          Guardar Cambios
                        </Button>
                        <Button
                          onClick={() => fetchUserData()}
                          icon={<EditOutlined />}
                        >
                          Descartar
                        </Button>
                        <Button
                          danger
                          icon={<LogoutOutlined />}
                          onClick={() => {
                            authService.logout();
                            window.location.href = '/login';
                          }}
                        >
                          Cerrar Sesión
                        </Button>
                      </Space>
                    </Form.Item>
                  </Form>
                )
              },
              {
                key: "2",
                label: tabSeguridad,
                children: (
                  <>
                    <Alert
                      message="Zona de Seguridad"
                      description="Asegúrese de usar una contraseña robusta con al menos 8 caracteres, letras, números y caracteres especiales."
                      type="warning"
                      showIcon
                      style={{ marginBottom: 20 }}
                    />

                    <Form
                      form={formPassword}
                      layout="vertical"
                      onFinish={handleChangePassword}
                      style={{ maxWidth: 500 }}
                    >
                      <Form.Item
                        name="currentPassword"
                        label="Contraseña Actual"
                        rules={[
                          {
                            required: true,
                            message: 'Requerida para confirmar su identidad',
                          },
                        ]}
                      >
                        <Input.Password prefix={<LockOutlined />} />
                      </Form.Item>

                      <Divider />

                      <Form.Item
                        name="newPassword"
                        label="Nueva Contraseña"
                        rules={[
                          {
                            required: true,
                            min: 8,
                            message: 'Mínimo 8 caracteres',
                          },
                        ]}
                      >
                        <Input.Password prefix={<KeyOutlined />} />
                      </Form.Item>

                      <Form.Item
                        name="confirmPassword"
                        label="Confirmar Nueva Contraseña"
                        dependencies={['newPassword']}
                        rules={[
                          { required: true, message: 'Confirme la contraseña' },
                          ({ getFieldValue }) => ({
                            validator(_, value) {
                              if (
                                !value ||
                                getFieldValue('newPassword') === value
                              ) {
                                return Promise.resolve();
                              }
                              return Promise.reject(
                                new Error('Las contraseñas no coinciden')
                              );
                            },
                          }),
                        ]}
                      >
                        <Input.Password prefix={<KeyOutlined />} />
                      </Form.Item>

                      <Form.Item>
                        <Space>
                          <Button
                            type="primary"
                            danger
                            htmlType="submit"
                            icon={<CheckOutlined />}
                            loading={updating}
                          >
                            Actualizar Contraseña
                          </Button>
                          <Button
                            onClick={() => formPassword.resetFields()}
                            icon={<EditOutlined />}
                          >
                            Limpiar
                          </Button>
                        </Space>
                      </Form.Item>
                    </Form>
                  </>
                )
              }
            ]} />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Perfil;
