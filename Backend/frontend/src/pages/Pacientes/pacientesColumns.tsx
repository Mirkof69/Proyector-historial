import React from 'react';
import { Button, Space, Tag, Typography, Badge, Avatar, Dropdown } from 'antd';
import {
  EditOutlined, DeleteOutlined, SearchOutlined, UserOutlined,
  FolderOpenOutlined, PhoneOutlined, IdcardOutlined, HomeOutlined,
  MoreOutlined, HistoryOutlined, PrinterOutlined, MedicineBoxOutlined,
  HeartOutlined, HeartFilled, WarningOutlined, FileTextOutlined,
  SafetyCertificateOutlined, SettingOutlined, QuestionCircleOutlined, CheckOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { Paciente } from './pacientesTypes';
import { imcRedondeado } from '../../utils/imc';

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
      // Orden en el SERVIDOR (`?ordering=id_clinico`), sobre todas las pacientes.
      sorter: true,
      width: 120,
      render: (text: string, record: Paciente) => (
        <div>
          <Tag className="pacientes-tabla__codigo">{text}</Tag>
          <div className="pacientes-tabla__nota texto-ayuda">
            {dayjs(record.fecha_registro).format('DD/MM/YYYY')}
          </div>
        </div>
      ),
    },
    {
      title: 'Paciente',
      key: 'paciente',
      width: 250,
      // Sin orden por nombre: está cifrado en la base y ordenar una sola
      // página en el navegador daría un orden falso entre páginas.
      render: (_: any, record: Paciente) => (
        <div className="pacientes-tabla__persona">
          <Avatar
            shape="square"
            size="large"
            icon={USER_ICON}
            src={record.foto_perfil}
            className="pacientes-tabla__avatar"
          />
          <div>
            <Text strong>{record.nombre_completo}</Text>
            <div className="pacientes-tabla__nota texto-secundario">
              {record.edad} años
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
      // Filtro resuelto en el SERVIDOR (`?estado_obstetrico=`): con `onFilter`
      // solo filtraba la página visible. Pacientes.tsx lee el valor en onChange.
      filters: [
        { text: 'Gestando', value: 'gestando' },
        { text: 'Sin Embarazo', value: 'sin_embarazo' },
        { text: 'Con Historial', value: 'con_historial' },
      ],
      filterMultiple: false,
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
            <Space direction="vertical" size={3} className="pacientes-tabla__ancho">
              <div className="pacientes-tabla__fila">
                <Badge status="processing" />
                <Tag color="success" icon={<HeartOutlined />} className="pacientes-tabla__tag">
                  GESTANDO
                </Tag>
              </div>
              <div className="pacientes-tabla__nota pacientes-tabla__nota--exito">
                <CheckOutlined /> En Control Prenatal
              </div>
              {numeroGesta > 0 && (
                <Text type="secondary" className="pacientes-tabla__nota">
                  Gesta: {numeroGesta}
                </Text>
              )}
            </Space>
          );
        } else if (numeroGesta > 0 || numeroAbortos > 0 || numeroCesareas > 0 || numeroPara > 0) {
          // Tiene historial obstétrico - MOSTRAR ESTADO FINAL

          // Determinar el estado final más reciente
          let estadoFinal = '';
          let colorEstado = 'default';
          let iconoEstado: React.ReactNode = <FileTextOutlined />;

          if (ultimoEstado) {
            estadoFinal = ultimoEstado;
            if (ultimoEstado.toLowerCase().includes('aborto')) {
              colorEstado = 'warning';
              iconoEstado = <WarningOutlined />;
            } else if (ultimoEstado.toLowerCase().includes('cesarea') || ultimoEstado.toLowerCase().includes('cesárea')) {
              colorEstado = 'default';
              iconoEstado = <MedicineBoxOutlined />;
            } else if (ultimoEstado.toLowerCase().includes('parto')) {
              colorEstado = 'default';
              iconoEstado = <HeartOutlined />;
            }
          } else {
            if (numeroAbortos > 0 && numeroPara === 0 && numeroCesareas === 0) {
              estadoFinal = 'Último: Aborto';
              colorEstado = 'warning';
              iconoEstado = <WarningOutlined />;
            } else if (numeroCesareas > 0) {
              estadoFinal = 'Último: Cesárea';
              colorEstado = 'default';
              iconoEstado = <MedicineBoxOutlined />;
            } else if (numeroPara > 0) {
              estadoFinal = 'Último: Parto Normal';
              colorEstado = 'default';
              iconoEstado = <HeartOutlined />;
            } else {
              estadoFinal = 'Con Historial';
              colorEstado = 'default';
              iconoEstado = <FileTextOutlined />;
            }
          }

          return (
            <Space direction="vertical" size={2} className="pacientes-tabla__ancho">
              <Tag color={colorEstado} className="pacientes-tabla__tag">
                {iconoEstado} {estadoFinal}
              </Tag>
              <Space direction="vertical" size={2} className="pacientes-tabla__ancho">
                {numeroGesta > 0 && <Tag className="pacientes-tabla__tag">Gestaciones: {numeroGesta}</Tag>}
                {numeroPara > 0 && <Tag className="pacientes-tabla__tag">Partos: {numeroPara}</Tag>}
                {numeroCesareas > 0 && <Tag className="pacientes-tabla__tag">Cesáreas: {numeroCesareas}</Tag>}
                {numeroAbortos > 0 && <Tag className="pacientes-tabla__tag">Abortos: {numeroAbortos}</Tag>}
              </Space>
              {fechaUltimoEvento && (
                <Text type="secondary" className="pacientes-tabla__nota">
                  {dayjs(fechaUltimoEvento).format('DD/MM/YYYY')}
                </Text>
              )}
            </Space>
          );
        } else {
          // Sin embarazo y sin historial
          return (
            <Space direction="vertical" size={2}>
              <Tag className="pacientes-tabla__tag">
                Sin Embarazo
              </Tag>
              <Text type="secondary" className="pacientes-tabla__nota">
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
          imc = imcRedondeado(record.peso_kg, alturaMetros);
        }

        const tieneDatos = record.tipo_sangre || imc || record.peso_kg || record.altura_cm;

        return (
          <Space direction="vertical" size={4} className="pacientes-tabla__ancho">
            {/* Tipo de Sangre */}
            <div className="pacientes-tabla__fila">
              <HeartFilled className="pacientes-tabla__icono-sangre" />
              {record.tipo_sangre ? (
                <Tag className="pacientes-tabla__tag">
                  {record.tipo_sangre}
                  {record.factor_rh && ` ${record.factor_rh === 'positivo' ? '+' : '-'}`}
                </Tag>
              ) : (
                <Text type="secondary" className="pacientes-tabla__nota">Sin registro</Text>
              )}
            </div>

            {/* Peso y Altura */}
            {(record.peso_kg || record.altura_cm) && (
              <div className="pacientes-tabla__nota texto-secundario">
                {record.peso_kg && <span>{record.peso_kg}kg</span>}
                {record.peso_kg && record.altura_cm && <span> • </span>}
                {record.altura_cm && <span>{record.altura_cm}cm</span>}
              </div>
            )}

            {/* IMC */}
            {imc && (
              <div className="pacientes-tabla__fila">
                <Text strong type="secondary" className="pacientes-tabla__nota">IMC:</Text>
                <Tag
                  color={
                    imc < 18.5 ? 'warning' :
                      imc < 25 ? 'success' :
                        imc < 30 ? 'warning' : 'error'
                  }
                  className="pacientes-tabla__tag"
                >
                  {imc.toFixed(1)} - {
                    imc < 18.5 ? 'Bajo' :
                      imc < 25 ? 'Normal' :
                        imc < 30 ? 'Sobrepeso' : 'Obesidad'
                  }
                </Tag>
              </div>
            )}

            {!tieneDatos && <Text type="secondary" className="pacientes-tabla__nota">Sin datos médicos</Text>}
          </Space>
        );
      },
    },
    {
      title: 'Contacto',
      key: 'contacto',
      width: 150,
      render: (_: any, record: Paciente) => (
        <Space direction="vertical" size={0} className="pacientes-tabla__nota">
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
          <Button
            shape="circle"
            icon={FOLDER_OPEN_ICON}
            aria-label={`Historia clínica de ${record.nombre_completo || 'la paciente'}`}
            title="Historia clínica"
            onClick={() => navigate(`/dashboard/pacientes/${record.id}/historia`)}
          />
          <Button
            shape="circle"
            icon={SEARCH_ICON_2}
            aria-label={`Ver detalles de ${record.nombre_completo || 'la paciente'}`}
            title="Ver detalles"
            onClick={() => { setSelectedPaciente(record); setDrawerVisible(true); }}
          />
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
                    // El backend hace BAJA LÓGICA (DS 1793/2013: la historia
                    // clínica se conserva 10 años). Antes este diálogo
                    // anunciaba un borrado permanente de toda la historia.
                    title: '¿Dar de baja a la paciente?',
                    content: (
                      <div>
                        <p><strong>Se dará de baja a la paciente:</strong></p>
                        <ul style={{ marginLeft: 20 }}>
                          <li>Nombre: {record.nombre_completo}</li>
                          <li>ID Clínico: {record.id_clinico}</li>
                          <li>CI: {record.ci}</li>
                        </ul>
                        <p style={{ color: token.colorError, fontWeight: 'bold', marginTop: 16 }}>
                          Dejará de figurar como activa en el sistema.
                        </p>
                        <p style={{ marginTop: 16 }}>
                          Su historia clínica (embarazos, controles, partos y documentos) se conserva
                          y un administrador puede reactivarla.
                        </p>
                      </div>
                    ),
                    okText: 'Sí, dar de baja',
                    cancelText: 'Cancelar',
                    okButtonProps: { danger: true },
                    width: 650,
                    onOk: () => handleDelete(record.id)
                  });
                }
              }] : [])
            ]
          }} trigger={['click']}>
            <Button type="text" icon={MORE_ICON} aria-label="Más acciones de la paciente" title="Más acciones" />
          </Dropdown>
        </Space>
      ),
    },
  ];
};
