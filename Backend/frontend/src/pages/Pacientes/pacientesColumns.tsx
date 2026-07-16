import React from 'react';
import { Button, Space, Tag, Typography, Tooltip, Badge, Avatar, Dropdown } from 'antd';
import {
  EditOutlined, DeleteOutlined, SearchOutlined, UserOutlined,
  FolderOpenOutlined, PhoneOutlined, IdcardOutlined, HomeOutlined,
  MoreOutlined, HistoryOutlined, PrinterOutlined, MedicineBoxOutlined,
  HeartOutlined, HeartFilled, WarningOutlined, FileTextOutlined,
  SafetyCertificateOutlined, SettingOutlined, QuestionCircleOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { Paciente } from './pacientesTypes';

const { Text } = Typography;

const USER_ICON = <UserOutlined />;
const FOLDER_OPEN_ICON = <FolderOpenOutlined />;
const SEARCH_ICON_2 = <SearchOutlined />;
const MORE_ICON = <MoreOutlined />;

export interface PacientesColumnsDeps {
  token: any;
  navigate: (path: string) => void;
  canChange: (perm: string) => boolean;
  canDelete: (perm: string) => boolean;
  modal: any;
  handleOpenEdit: (paciente: Paciente) => void;
  handleExportPacientePDF: (paciente: Paciente) => void;
  handleDelete: (id: number) => void;
  setSelectedPaciente: (paciente: Paciente) => void;
  setDrawerVisible: (visible: boolean) => void;
}

export const buildPacientesColumns = (deps: PacientesColumnsDeps) => {
  const {
    token, navigate, canChange, canDelete, modal, handleOpenEdit,
    handleExportPacientePDF, handleDelete, setSelectedPaciente, setDrawerVisible,
  } = deps;

  return [
    {
      title: 'ID / Registro',
      dataIndex: 'id_clinico',
      width: 120,
      render: (text: string, record: Paciente) => (
        <div>
          <Tag color="blue" style={{ marginRight: 0 }}>{text}</Tag>
          <div style={{ fontSize: '12px', color: token.colorTextTertiary, marginTop: 4 }}>
            {dayjs(record.fecha_registro).format('DD/MM/YYYY')}
          </div>
        </div>
      ),
    },
    {
      title: 'Paciente',
      key: 'paciente',
      width: 250,
      sorter: (a: Paciente, b: Paciente) => a.nombre.localeCompare(b.nombre),
      render: (_: any, record: Paciente) => (
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <Avatar
            shape="square"
            size="large"
            icon={USER_ICON}
            src={record.foto_perfil}
            style={{
              backgroundColor: record.genero === 'femenino' ? '#ffadd2' : token.colorPrimary,
              marginRight: 12
            }}
          />
          <div>
            <Text strong style={{ fontSize: 15 }}>{record.nombre_completo}</Text>
            <div style={{ fontSize: 12, color: token.colorTextSecondary }}>
              {record.edad} años • {record.genero === 'femenino' ? 'Mujer' : 'Hombre'}
            </div>
          </div>
        </div>
      ),
    },
    {
      title: 'Identificación',
      dataIndex: 'ci',
      width: 130,
      render: (ci: string) => (
        <Space>
          <IdcardOutlined style={{ color: token.colorPrimary }} />
          <Text copyable>{ci}</Text>
        </Space>
      )
    },
    {
      title: 'Estado Obstétrico',
      key: 'estado_obstetrico',
      width: 160,
      filters: [
        { text: 'Gestando', value: 'gestando' },
        { text: 'Sin Embarazo', value: 'sin_embarazo' },
        { text: 'Con Historial', value: 'con_historial' },
      ],
      onFilter: (value: any, record: Paciente) => {
        if (value === 'gestando') return !!record.embarazos_activos;
        if (value === 'sin_embarazo') return !record.embarazos_activos && !(record as any).numero_gesta;
        if (value === 'con_historial') return !record.embarazos_activos && !!(record as any).numero_gesta;
        return true;
      },
      render: (_: any, record: Paciente) => {
        const pacienteExtendido = record as any;
        const tieneEmbarazoActivo = record.embarazos_activos;
        const numeroGesta = pacienteExtendido.numero_gesta || 0;
        const numeroAbortos = pacienteExtendido.numero_abortos || 0;
        const numeroCesareas = pacienteExtendido.numero_cesareas || 0;
        const numeroPara = pacienteExtendido.numero_para || 0;
        const ultimoEstado = pacienteExtendido.ultimo_estado_obstetrico || '';
        const fechaUltimoEvento = pacienteExtendido.fecha_ultimo_evento || '';

        if (tieneEmbarazoActivo) {
          // Embarazo Activo - EN CONTROL
          return (
            <Space direction="vertical" size={3} style={{ width: '100%' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <Badge status="processing" />
                <Tag color="green" style={{ margin: 0, fontWeight: 'bold', fontSize: '12px' }}>
                  🤰 GESTANDO
                </Tag>
              </div>
              <div style={{ fontSize: '12px', color: token.colorSuccess }}>
                ✓ En Control Prenatal
              </div>
              {numeroGesta > 0 && (
                <Text style={{ fontSize: '12px', color: token.colorTextSecondary }}>
                  Gesta: {numeroGesta}
                </Text>
              )}
            </Space>
          );
        } else if (numeroGesta > 0 || numeroAbortos > 0 || numeroCesareas > 0 || numeroPara > 0) {
          // Tiene historial obstétrico - MOSTRAR ESTADO FINAL

          // Determinar el estado final más reciente
          let estadoFinal = '';
          let colorEstado = 'blue';
          let iconoEstado: React.ReactNode = <FileTextOutlined />;

          if (ultimoEstado) {
            estadoFinal = ultimoEstado;
            if (ultimoEstado.toLowerCase().includes('aborto')) {
              colorEstado = 'orange';
              iconoEstado = <WarningOutlined />;
            } else if (ultimoEstado.toLowerCase().includes('cesarea') || ultimoEstado.toLowerCase().includes('cesárea')) {
              colorEstado = 'purple';
              iconoEstado = <MedicineBoxOutlined />;
            } else if (ultimoEstado.toLowerCase().includes('parto')) {
              colorEstado = 'cyan';
              iconoEstado = <HeartOutlined />;
            }
          } else {
            if (numeroAbortos > 0 && numeroPara === 0 && numeroCesareas === 0) {
              estadoFinal = 'Último: Aborto';
              colorEstado = 'orange';
              iconoEstado = <WarningOutlined />;
            } else if (numeroCesareas > 0) {
              estadoFinal = 'Último: Cesárea';
              colorEstado = 'purple';
              iconoEstado = <MedicineBoxOutlined />;
            } else if (numeroPara > 0) {
              estadoFinal = 'Último: Parto Normal';
              colorEstado = 'cyan';
              iconoEstado = <HeartOutlined />;
            } else {
              estadoFinal = 'Con Historial';
              colorEstado = 'blue';
              iconoEstado = <FileTextOutlined />;
            }
          }

          return (
            <Space direction="vertical" size={2} style={{ width: '100%' }}>
              <Tag color={colorEstado} style={{ margin: 0, fontSize: '12px', fontWeight: 'bold' }}>
                {iconoEstado} {estadoFinal}
              </Tag>
              <Space direction="vertical" size={2} style={{ width: '100%' }}>
                {numeroGesta > 0 && <Tag color="blue" style={{ margin: 0, fontSize: '12px', fontWeight: 'bold' }}>Gestaciones: {numeroGesta}</Tag>}
                {numeroPara > 0 && <Tag color="green" style={{ margin: 0, fontSize: '12px', fontWeight: 'bold' }}>Partos: {numeroPara}</Tag>}
                {numeroCesareas > 0 && <Tag color="purple" style={{ margin: 0, fontSize: '12px', fontWeight: 'bold' }}>Cesáreas: {numeroCesareas}</Tag>}
                {numeroAbortos > 0 && <Tag color="orange" style={{ margin: 0, fontSize: '12px', fontWeight: 'bold' }}>Abortos: {numeroAbortos}</Tag>}
              </Space>
              {fechaUltimoEvento && (
                <Text type="secondary" style={{ fontSize: '12px' }}>
                  {dayjs(fechaUltimoEvento).format('DD/MM/YYYY')}
                </Text>
              )}
            </Space>
          );
        } else {
          // Sin embarazo y sin historial
          return (
            <Space direction="vertical" size={2}>
              <Tag color="default" style={{ margin: 0, fontSize: '12px' }}>
                ✓ Sin Embarazo
              </Tag>
              <Text type="secondary" style={{ fontSize: '12px' }}>
                Sin historial
              </Text>
            </Space>
          );
        }
      },
    },
    {
      title: 'Datos Médicos',
      key: 'datos_medicos',
      width: 200,
      render: (_: any, record: Paciente) => {
        // Calcular IMC si tenemos peso y altura
        let imc = record.imc;
        if (!imc && record.peso_kg && record.altura_cm) {
          const alturaMetros = record.altura_cm / 100;
          imc = record.peso_kg / (alturaMetros * alturaMetros);
        }

        const tieneDatos = record.tipo_sangre || imc || record.peso_kg || record.altura_cm;

        return (
          <Space direction="vertical" size={4} style={{ width: '100%' }}>
            {/* Tipo de Sangre */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <HeartFilled style={{ color: token.colorError, fontSize: 12 }} />
              {record.tipo_sangre ? (
                <Tag color="red" style={{ fontWeight: 'bold', margin: 0, fontSize: '12px' }}>
                  {record.tipo_sangre}
                  {record.factor_rh && ` ${record.factor_rh === 'positivo' ? '+' : '-'}`}
                </Tag>
              ) : (
                <Text type="secondary" style={{ fontSize: '12px' }}>Sin registro</Text>
              )}
            </div>

            {/* Peso y Altura */}
            {(record.peso_kg || record.altura_cm) && (
              <div style={{ fontSize: '12px', color: token.colorTextSecondary }}>
                {record.peso_kg && <span>{record.peso_kg}kg</span>}
                {record.peso_kg && record.altura_cm && <span> • </span>}
                {record.altura_cm && <span>{record.altura_cm}cm</span>}
              </div>
            )}

            {/* IMC */}
            {imc && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                <Text strong style={{ fontSize: '12px', color: token.colorTextSecondary }}>IMC:</Text>
                <Tag
                  color={
                    imc < 18.5 ? 'orange' :
                      imc < 25 ? 'green' :
                        imc < 30 ? 'gold' : 'red'
                  }
                  style={{ fontSize: '12px', margin: 0 }}
                >
                  {imc.toFixed(1)} - {
                    imc < 18.5 ? 'Bajo' :
                      imc < 25 ? 'Normal' :
                        imc < 30 ? 'Sobrepeso' : 'Obesidad'
                  }
                </Tag>
              </div>
            )}

            {!tieneDatos && <Text type="secondary" style={{ fontSize: '12px' }}>Sin datos médicos</Text>}
          </Space>
        );
      },
    },
    {
      title: 'Contacto',
      key: 'contacto',
      width: 150,
      render: (_: any, record: Paciente) => (
        <Space direction="vertical" size={0} style={{ fontSize: 12 }}>
          {record.telefono && <span><PhoneOutlined /> {record.telefono}</span>}
          {record.ciudad && <span><HomeOutlined /> {record.ciudad}</span>}
        </Space>
      ),
    },
    {
      title: 'Acciones',
      key: 'acciones',
      fixed: 'right' as 'right',
      width: 140,
      render: (_: any, record: Paciente) => (
        <Space>
          <Tooltip title="Historia Clínica">
            <Button
              type="primary"
              shape="circle"
              icon={FOLDER_OPEN_ICON}
              onClick={() => navigate(`/dashboard/pacientes/${record.id}/historia`)}
            />
          </Tooltip>
          <Tooltip title="Ver Detalles">
            <Button
              shape="circle"
              icon={SEARCH_ICON_2}
              onClick={() => { setSelectedPaciente(record); setDrawerVisible(true); }}
            />
          </Tooltip>
          <Dropdown menu={{
            items: [
              // Editar - solo si tiene permiso
              ...(canChange('paciente') ? [{
                key: 'edit',
                icon: <EditOutlined />,
                label: 'Editar Información',
                onClick: () => handleOpenEdit(record)
              }] : []),
              {
                key: 'history',
                icon: <HistoryOutlined />,
                label: 'Ver Historial',
                onClick: () => navigate(`/dashboard/pacientes/${record.id}/historia`)
              },
              {
                key: 'export-pdf',
                icon: <SafetyCertificateOutlined />,
                label: 'Exportar a PDF',
                onClick: () => handleExportPacientePDF(record)
              },
              {
                key: 'print',
                icon: <PrinterOutlined />,
                label: 'Imprimir Ficha'
              },
              {
                key: 'settings',
                icon: <SettingOutlined />,
                label: 'Configuración Paciente'
              },
              {
                key: 'help',
                icon: <QuestionCircleOutlined />,
                label: 'Ayuda'
              },
              // Separador solo si tiene permiso de eliminar
              ...(canDelete('paciente') ? [{
                type: 'divider' as const
              }] : []),
              // Eliminar - solo si tiene permiso
              ...(canDelete('paciente') ? [{
                key: 'delete',
                danger: true,
                icon: <DeleteOutlined />,
                label: 'Eliminar Paciente',
                onClick: () => {
                  modal.confirm({
                    title: '⚠️ ¿Confirmar eliminación permanente del paciente?',
                    content: (
                      <div>
                        <p><strong>Se eliminará el paciente:</strong></p>
                        <ul style={{ marginLeft: 20 }}>
                          <li>Nombre: {record.nombre_completo}</li>
                          <li>ID Clínico: {record.id_clinico}</li>
                          <li>CI: {record.ci}</li>
                        </ul>
                        <p style={{ color: token.colorError, fontWeight: 'bold', marginTop: 16 }}>
                          ⚠️ ADVERTENCIA: Esta acción eliminará PERMANENTEMENTE:
                        </p>
                        <ul style={{ marginLeft: 20, color: token.colorError }}>
                          <li>Toda la historia clínica del paciente</li>
                          <li>Todos los embarazos registrados</li>
                          <li>Todos los controles prenatales</li>
                          <li>Todos los partos y recién nacidos</li>
                          <li>Documentos, citas y seguimientos</li>
                        </ul>
                        <p style={{ marginTop: 16 }}>
                          <strong>Esta acción NO se puede deshacer. ¿Está completamente seguro?</strong>
                        </p>
                      </div>
                    ),
                    okText: 'Sí, eliminar permanentemente',
                    cancelText: 'Cancelar',
                    okButtonProps: { danger: true },
                    width: 650,
                    onOk: () => handleDelete(record.id)
                  });
                }
              }] : [])
            ]
          }} trigger={['click']}>
            <Button type="text" icon={MORE_ICON} />
          </Dropdown>
        </Space>
      ),
    },
  ];
};
