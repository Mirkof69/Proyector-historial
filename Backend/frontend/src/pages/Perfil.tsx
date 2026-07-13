import React, { useState, useEffect, useCallback } from 'react';
import { Card, Row, Col, Tabs, Spin, Empty, Form, Upload } from "antd";
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import type { UploadFile, UploadProps } from 'antd/es/upload/interface';
import { useMessage } from '../hooks/useMessage';
import { authService } from '../services/authService';
import { usuariosService } from '../services/usuariosService';
import { Usuario } from './Perfil/perfilTypes';
import PerfilHeader from './Perfil/PerfilHeader';
import PerfilResumenAcceso from './Perfil/PerfilResumenAcceso';
import TabDatosPersonales from './Perfil/TabDatosPersonales';
import TabSeguridad from './Perfil/TabSeguridad';

const tabDatosPersonales = <span><UserOutlined /> Datos Personales</span>;
const tabSeguridad = <span><LockOutlined /> Seguridad</span>;

const Perfil: React.FC = () => {
  const message = useMessage();

  const [loading, setLoading] = useState(false);
  const [updating, setUpdating] = useState(false);
  const [user, setUser] = useState<Usuario | null>(null);
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [uploadProgress, setUploadProgress] = useState(0);

  const [formPerfil] = Form.useForm();
  const [formPassword] = Form.useForm();

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
        const progress = Math.round((info.file.percent || 0) * 100);
        setUploadProgress(progress);
      }
    },
    fileList,
  };

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
      <PerfilHeader user={user} />

      <Row gutter={24}>
        {/* COLUMNA IZQUIERDA: RESUMEN RÁPIDO */}
        <Col xs={24} lg={8}>
          <PerfilResumenAcceso user={user} />
        </Col>

        {/* COLUMNA DERECHA: FORMULARIOS DE EDICIÓN */}
        <Col xs={24} lg={16}>
          <Card className="shadow-sm">
            <Tabs defaultActiveKey="1" items={[
              {
                key: "1",
                label: tabDatosPersonales,
                children: (
                  <TabDatosPersonales
                    form={formPerfil}
                    user={user}
                    updating={updating}
                    uploadProps={uploadProps}
                    uploadProgress={uploadProgress}
                    onFinish={handleUpdateProfile}
                    onDescartar={() => fetchUserData()}
                    onLogout={() => {
                      authService.logout();
                      window.location.href = '/login';
                    }}
                  />
                )
              },
              {
                key: "2",
                label: tabSeguridad,
                children: (
                  <TabSeguridad
                    form={formPassword}
                    updating={updating}
                    onFinish={handleChangePassword}
                  />
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
