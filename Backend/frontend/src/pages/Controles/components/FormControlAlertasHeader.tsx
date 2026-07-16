import React from 'react';
import { Alert, Space, Typography } from 'antd';
import { InfoCircleOutlined, WarningOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { Embarazo } from '../../../services/embarazosService';

const { Text } = Typography;

interface FormControlAlertasHeaderProps {
  selectedEmbarazo: Embarazo | null;
  nombrePacienteSel: string;
  edadGestacionalInfo: string;
  alertasPreliminares: string[];
}

const FormControlAlertasHeader: React.FC<FormControlAlertasHeaderProps> = ({
  selectedEmbarazo, nombrePacienteSel, edadGestacionalInfo, alertasPreliminares,
}) => (
  <>
    {/* ========== INFORMACIÓN DEL EMBARAZO ========== */}
    {selectedEmbarazo && (
      <Alert
        message="Información del Embarazo Seleccionado"
        description={
          <Space direction="vertical" size={0}>
            <Text>
              <strong>Paciente:</strong> {nombrePacienteSel}
            </Text>
            <Text>
              <strong>Gesta:</strong> G{selectedEmbarazo.numero_gesta}
            </Text>
            <Text>
              <strong>FPP:</strong>{' '}
              {dayjs(selectedEmbarazo.fecha_probable_parto).format('DD/MM/YYYY')}
            </Text>
            {edadGestacionalInfo && (
              <Text>
                <strong>Edad Gestacional:</strong> {edadGestacionalInfo}
              </Text>
            )}
          </Space>
        }
        type="info"
        showIcon
        icon={<InfoCircleOutlined />}
        style={{ marginBottom: 16 }}
      />
    )}

    {/* ========== ALERTAS ========== */}
    {alertasPreliminares.length > 0 && (
      <Alert
        message={`⚠️ ${alertasPreliminares.length} Alerta(s) Clínica(s) Detectada(s)`}
        description={
          <ul style={{ marginBottom: 0, paddingLeft: 20 }}>
            {alertasPreliminares.map((alerta) => (
              <li key={alerta} style={{ marginBottom: 4 }}>
                {alerta}
              </li>
            ))}
          </ul>
        }
        type="error"
        showIcon
        icon={<WarningOutlined />}
        style={{ marginBottom: 16 }}
      />
    )}
  </>
);

export default FormControlAlertasHeader;
