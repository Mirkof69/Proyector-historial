import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Tabs, Form, Button, Typography, Alert, Spin, Badge, Space, notification } from 'antd';
import { useAntdApp } from '../hooks/useMessage';
import { ShopOutlined, ClockCircleOutlined, CloudServerOutlined, DatabaseOutlined, SaveOutlined, ReloadOutlined, WarningOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import configService from '../services/configService';
import ConfiguracionIdentidad from './Configuracion/components/ConfiguracionIdentidad';
import ConfiguracionHorarios from './Configuracion/components/ConfiguracionHorarios';
import ConfiguracionSistema from './Configuracion/components/ConfiguracionSistema';
import './Configuracion/Configuracion.css';

const { Text } = Typography;

interface HorarioDia {
  dia: string;
  activo: boolean;
  hora_inicio: string;
  hora_fin: string;
  inicio?: any;
  fin?: any;
}

interface ConfigSistema {
  nombre_clinica?: string;
  direccion?: string;
  telefono?: string;
  email?: string;
  logo_url?: string;
  [key: string]: any;
}

interface Backup {
  id: string;
  fecha: string;
  size: string;
}

const tabIdentidadClinica = <span><ShopOutlined /> Identidad Clínica</span>;
const tabHorariosAtencion = <span><ClockCircleOutlined /> Horarios de Atención</span>;
const tabSistemaBackups = <span><DatabaseOutlined /> Backups del Sistema</span>;

const reloadIcon = <ReloadOutlined />;
const saveIcon = <SaveOutlined />;

const Configuracion: React.FC = () => {
  const { message } = useAntdApp();
  const [formGeneral] = Form.useForm();
  const [formSmtp] = Form.useForm();

  const [state, setState] = useState({
    loading: true,
    saving: false,
    horarios: [] as HorarioDia[],
    backups: [] as Backup[],
    configData: null as ConfigSistema | null,
    diasRetencion: 30,
    notasAdmin: ''
  });
  const { loading, saving, horarios, backups, configData, diasRetencion, notasAdmin } = state;
  const logoFileRef = useRef<any>(null);

  const setLoading = (loading: boolean) => setState(prev => ({ ...prev, loading }));
  const setSaving = (saving: boolean) => setState(prev => ({ ...prev, saving }));
  const setHorarios = (horarios: HorarioDia[]) => setState(prev => ({ ...prev, horarios }));
  const setBackups = (backups: Backup[]) => setState(prev => ({ ...prev, backups }));
  const setConfigData = (configData: ConfigSistema | null) => setState(prev => ({ ...prev, configData }));
  const setDiasRetencion = (diasRetencion: number) => setState(prev => ({ ...prev, diasRetencion }));
  const setNotasAdmin = (notasAdmin: string) => setState(prev => ({ ...prev, notasAdmin }));

  const cargarConfiguracion = useCallback(async () => {
    setLoading(true);
    try {
      const config = await configService.getConfiguracion();
      setConfigData(config);

      formGeneral.setFieldsValue({
        nombre_clinica: config.nombre_clinica,
        direccion: config.direccion,
        telefono_contacto: config.telefono_contacto,
        email_contacto: config.email_contacto,
        modo_mantenimiento: config.modo_mantenimiento,
        permitir_registro_publico: config.permitir_registro_publico
      });

      formSmtp.setFieldsValue({
        smtp_host: config.smtp_host,
        smtp_port: config.smtp_port,
        smtp_user: config.smtp_user,
        smtp_secure: config.smtp_secure
      });

      const horariosData = await configService.getHorarios();
      const horariosMapeados = horariosData.map(h => ({
        dia: h.dia_display,
        activo: h.activo,
        inicio: dayjs(h.hora_inicio, 'HH:mm'),
        fin: dayjs(h.hora_fin, 'HH:mm')
      }));
      setHorarios(horariosMapeados as any);

      const backupsData = await configService.listarBackups();
      const backupsMapeados = backupsData.map(b => ({
        id: b.filename,
        fecha: b.created_at,
        size: b.size_formatted
      }));
      setBackups(backupsMapeados);

      setLoading(false);
    } catch (error) {
      message.error('Error cargando configuración del sistema');
      setLoading(false);
    }
  }, [formGeneral, formSmtp, message]);

  useEffect(() => {
    cargarConfiguracion();
  }, [cargarConfiguracion]);

  const handleSaveGeneral = async (values: any) => {
    setSaving(true);
    try {
      const formData = new FormData();
      Object.keys(values).forEach(key => {
        if (values[key] !== undefined && values[key] !== null) {
          formData.append(key, values[key]);
        }
      });

      if (logoFileRef.current) {
        formData.append('logo', logoFileRef.current);
      }

      await configService.updateConfiguracion(formData);
      message.success('Configuración general actualizada correctamente');
      notification.info({
        message: 'Reinicio Requerido',
        description: 'Algunos cambios visuales pueden requerir recargar la página.',
      });

      await cargarConfiguracion();
    } catch (error: any) {
      message.error(error.response?.data?.message || 'Error al guardar cambios');
    } finally {
      setSaving(false);
    }
  };

  const handleSaveHorarios = async () => {
    setSaving(true);
    try {
      const diasMapping = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo'];
      const horariosPayload = horarios.map((h, index) => ({
        dia: diasMapping[index],
        activo: h.activo,
        hora_inicio: h.inicio ? dayjs(h.inicio).format('HH:mm') : '08:00',
        hora_fin: h.fin ? dayjs(h.fin).format('HH:mm') : '18:00',
      }));

      await configService.updateHorarios(horariosPayload);
      message.success('Horarios de atención actualizados');
    } catch (error: any) {
      message.error(error.response?.data?.message || 'Error al guardar horarios');
    } finally {
      setSaving(false);
    }
  };

  const handleCreateBackup = async () => {
    const hide = message.loading('Generando copia de seguridad...', 0);
    try {
      const result = await configService.crearBackup();
      hide();

      if (result.success) {
        message.success(`Backup creado exitosamente: ${result.filename}`);
        const backupsData = await configService.listarBackups();
        const backupsMapeados = backupsData.map(b => ({
          id: b.filename,
          fecha: b.created_at,
          size: b.size_formatted
        }));
        setBackups(backupsMapeados);
      } else {
        message.error(result.message || 'Error al generar backup');
      }
    } catch (error: any) {
      hide();
      message.error(error.response?.data?.message || 'Error al generar backup');
    }
  };

  const handleDescargarBackup = async (filename: string) => {
    try {
      await configService.descargarBackup(filename);
      message.success('Backup descargado correctamente');
    } catch (error: any) {
      message.error(error.response?.data?.message || 'Error al descargar backup');
    }
  };

  const handleEliminarBackup = async (filename: string) => {
    try {
      await configService.eliminarBackup(filename);
      message.success('Backup eliminado correctamente');
      const backupsData = await configService.listarBackups();
      const backupsMapeados = backupsData.map(b => ({
        id: b.filename,
        fecha: b.created_at,
        size: b.size_formatted
      }));
      setBackups(backupsMapeados);
    } catch (error: any) {
      message.error(error.response?.data?.message || 'Error al eliminar backup');
    }
  };

  if (loading) {
    return <div className="configuracion-page__cargando"><Spin size="large" tip="Cargando panel de control…"><div /></Spin></div>;
  }

  return (
    <section className="configuracion-page page-container">
          <header className="configuracion-page__cabecera">
            <Typography.Title level={2}>Configuración del Sistema</Typography.Title>
            <Text type="secondary">Administre los parámetros globales, horarios y mantenimiento de la plataforma.</Text>
          </header>

          {configData?.modo_mantenimiento && (
            <Alert
              message={<Space><WarningOutlined />Modo Mantenimiento Activado</Space>}
              description="El sistema está en modo mantenimiento. Solo los administradores pueden acceder."
              type="warning"
              showIcon
              closable
            />
          )}

          <div className="configuracion-page__estado">
            <span className="configuracion-page__en-linea"><CloudServerOutlined /> Sistema en línea</span>
            <Space>
              <Text type="secondary">Backups disponibles:</Text>
              <Badge className="configuracion-page__contador" count={backups.length} showZero overflowCount={999} />
              <Button size="small" icon={reloadIcon} onClick={cargarConfiguracion}>
                Refrescar
              </Button>
            </Space>
          </div>

          <Tabs
            defaultActiveKey="1"
            items={[
              {
                key: '1',
                label: tabIdentidadClinica,
                children: <ConfiguracionIdentidad
                  form={formGeneral}
                  saving={saving}
                  onSave={handleSaveGeneral}
                  logoFileRef={logoFileRef}
                  configData={configData}
                />,
              },
              {
                key: '2',
                label: tabHorariosAtencion,
                children: <ConfiguracionHorarios
                  horarios={horarios}
                  setHorarios={setHorarios}
                  saving={saving}
                  onSave={handleSaveHorarios}
                />,
              },
              {
                key: '3',
                label: tabSistemaBackups,
                children: <ConfiguracionSistema
                  formSmtp={formSmtp}
                  diasRetencion={diasRetencion}
                  setDiasRetencion={setDiasRetencion}
                  notasAdmin={notasAdmin}
                  setNotasAdmin={setNotasAdmin}
                  backups={backups}
                  onCreateBackup={handleCreateBackup}
                  onDescargarBackup={handleDescargarBackup}
                  onEliminarBackup={handleEliminarBackup}
                />,
              },
            ]}
          />
    </section>
  );
};

export default Configuracion;
