import React from 'react';
import {
  Button, Space, Card, Row, Col, Tag, Typography, Alert, Modal, Divider,
  Descriptions, Statistic,
} from 'antd';
import {
  EditOutlined, MedicineBoxOutlined, EyeOutlined, CheckCircleOutlined,
  SearchOutlined, ExportOutlined, LinkOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { ControlPrenatal } from '../../../services/controlesService';
import { Embarazo } from '../../../services/embarazosService';

const { Text } = Typography;

interface VistaRapidaModalProps {
  modalVisible: boolean;
  editingControl: ControlPrenatal | null;
  controlVistaRapida: ControlPrenatal | null;
  selectedEmbarazo: Embarazo | null;
  alertasPreview: string[];
  handleCloseModal: () => void;
  handleEdit: (control: ControlPrenatal) => void;
  navigate: (path: string) => void;
  getNombrePaciente: (control: ControlPrenatal) => string;
  getIdClinicoPaciente: (control: ControlPrenatal) => string;
  getEdadGestacional: (control: ControlPrenatal) => string;
  getPresionArterial: (control: ControlPrenatal) => string;
  calcularIMC: (peso: number | null | undefined, talla: number | null | undefined) => number | null;
}

const VistaRapidaModal: React.FC<VistaRapidaModalProps> = ({
  modalVisible, editingControl, controlVistaRapida, selectedEmbarazo, alertasPreview,
  handleCloseModal, handleEdit, navigate, getNombrePaciente, getIdClinicoPaciente,
  getEdadGestacional, getPresionArterial, calcularIMC,
}) => (
  <Modal rootClassName="capa-clinica"
    title={
      <Space>
        <MedicineBoxOutlined />
        Vista Rápida del Control
        {controlVistaRapida && (
          <Tag color="processing">#{controlVistaRapida.numero_control}</Tag>
        )}
      </Space>
    }
    open={modalVisible}
    onCancel={handleCloseModal}
    width={800}
    footer={[
      <Button key="close" onClick={handleCloseModal}>
        Cerrar
      </Button>,
      <Button
        key="edit"
        type="primary"
        icon={<EditOutlined />}
        onClick={() => {
          if (editingControl) {
            handleEdit(editingControl);
            handleCloseModal();
          }
        }}
      >
        Editar Completo
      </Button>,
    ]}
  >
    {editingControl && (
      <>
        <Descriptions bordered column={2} size="small">
          <Descriptions.Item label="Paciente" span={2}>
            <Text strong>{getNombrePaciente(editingControl)}</Text>
          </Descriptions.Item>
          <Descriptions.Item label="ID Clínico">
            <Tag color="processing">{getIdClinicoPaciente(editingControl)}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Fecha Control">
            {dayjs(editingControl.fecha_control).format('DD/MM/YYYY')}
          </Descriptions.Item>
          <Descriptions.Item label="Edad Gestacional">
            <Tag>{getEdadGestacional(editingControl)}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="N° Control">
            {editingControl.numero_control}
          </Descriptions.Item>
        </Descriptions>

        <Divider>Signos Vitales</Divider>

        <Row gutter={[16, 16]}>
          <Col span={8}>
            <Statistic
              title="Presión Arterial"
              value={getPresionArterial(editingControl)}
              suffix="mmHg"
              valueStyle={{
                color:
                  (editingControl.presion_arterial_sistolica || 0) >= 140 ||
                    (editingControl.presion_arterial_diastolica || 0) >= 90
                    ? 'var(--color-peligro)'
                    : 'var(--color-exito)',
              }}
            />
          </Col>
          <Col span={8}>
            <Statistic
              title="FCF"
              value={editingControl.frecuencia_cardiaca_fetal || '-'}
              suffix="lpm"
              valueStyle={{
                color:
                  editingControl.frecuencia_cardiaca_fetal &&
                    (editingControl.frecuencia_cardiaca_fetal < 110 ||
                      editingControl.frecuencia_cardiaca_fetal > 160)
                    ? 'var(--color-peligro)'
                    : 'var(--color-exito)',
              }}
            />
          </Col>
          <Col span={8}>
            <Statistic
              title="Altura Uterina"
              value={editingControl.altura_uterina || '-'}
              suffix="cm"
            />
          </Col>
          <Col span={8}>
            <Statistic
              title="Peso Actual"
              value={editingControl.peso_actual || '-'}
              suffix="kg"
            />
          </Col>
          <Col span={8}>
            <Statistic
              title="IMC"
              value={
                calcularIMC(editingControl.peso_actual, editingControl.talla)?.toFixed(
                  1
                ) || '-'
              }
            />
          </Col>
          <Col span={8}>
            <Statistic
              title="Temperatura"
              value={editingControl.temperatura || '-'}
              suffix="°C"
            />
          </Col>
        </Row>

        {selectedEmbarazo && (
          <>
            <Divider>Datos del Embarazo</Divider>
            <Descriptions bordered column={2} size="small">
              <Descriptions.Item label="Estado">
                <Tag color={selectedEmbarazo.estado === 'activo' ? 'success' : 'default'}>
                  {selectedEmbarazo.estado}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="FUM">
                {selectedEmbarazo.fecha_ultima_menstruacion
                  ? dayjs(selectedEmbarazo.fecha_ultima_menstruacion).format(
                    'DD/MM/YYYY'
                  )
                  : '-'}
              </Descriptions.Item>
            </Descriptions>
          </>
        )}

        {alertasPreview && alertasPreview.length > 0 && (
          <>
            <Divider>Alertas Médicas</Divider>
            <Alert
              message={`${alertasPreview.length} Alerta(s) Detectada(s)`}
              description={
                <ul className="pc-lista">
                  {alertasPreview.map((alerta) => (
                    <li key={`alerta-${alerta}`}>{alerta}</li>
                  ))}
                </ul>
              }
              type="warning"
              showIcon
            />
          </>
        )}

        <Divider orientation="left"><LinkOutlined /> Acceso Rápido a Módulos</Divider>
        <Card size="small" className="u-mb-4">
          <Space direction="vertical" className="u-ancho" size="small">
            <Button
              type="link"
              icon={<EyeOutlined />}
              block
              className="u-izquierda"
              onClick={() => {
                handleCloseModal();
                navigate(`/dashboard/pacientes?id=${editingControl.paciente}`);
              }}
            >
              Ver Paciente: {getNombrePaciente(editingControl)}
            </Button>
            <Button
              type="link"
              icon={<MedicineBoxOutlined />}
              block
              className="u-izquierda"
              onClick={() => {
                handleCloseModal();
                navigate(`/dashboard/embarazos?id=${editingControl.embarazo}`);
              }}
            >
              Ver Datos del Embarazo
            </Button>
            <Button
              type="link"
              icon={<SearchOutlined />}
              block
              className="u-izquierda"
              onClick={() => {
                handleCloseModal();
                navigate(`/dashboard/ecografias?embarazo=${editingControl.embarazo}`);
              }}
            >
              Ver Ecografías del Embarazo
            </Button>
            <Button
              type="link"
              icon={<ExportOutlined />}
              block
              className="u-izquierda"
              onClick={() => {
                handleCloseModal();
                navigate(`/dashboard/laboratorio?embarazo=${editingControl.embarazo}`);
              }}
            >
              Ver Exámenes de Laboratorio
            </Button>
            <Button
              type="link"
              icon={<CheckCircleOutlined />}
              block
              className="u-izquierda"
              onClick={() => {
                handleCloseModal();
                navigate(`/dashboard/citas?embarazo=${editingControl.embarazo}`);
              }}
            >
              Ver Citas del Embarazo
            </Button>
            <Button
              type="link"
              icon={<MedicineBoxOutlined />}
              block
              className="u-izquierda"
              onClick={() => {
                handleCloseModal();
                navigate(`/dashboard/partos?embarazo=${editingControl.embarazo}`);
              }}
            >
              Ver Información de Parto
            </Button>
            <Divider className="u-mv-2" />
            <Button
              type="primary"
              icon={<ExportOutlined />}
              block
              onClick={() => {
                handleCloseModal();
                navigate(`/dashboard/pacientes/${editingControl.paciente}/historia`);
              }}
            >
              Ver Historia Clínica Completa
            </Button>
          </Space>
        </Card>
      </>
    )}
  </Modal>
);

export default VistaRapidaModal;
