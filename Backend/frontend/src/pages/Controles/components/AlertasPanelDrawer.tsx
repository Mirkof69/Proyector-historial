import React from 'react';
import { Button, Space, Card, Typography, Alert, Drawer, Divider, Badge } from 'antd';
import { WarningOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { ControlPrenatal } from '../../../services/controlesService';

const { Text } = Typography;

/**
 * Panel de alertas. Las cifras y los 10 controles con alerta más recientes
 * llegan del servidor (GET /controles/resumen/) con los filtros actuales.
 * Antes se calculaban en el navegador sobre la lista ENTERA de controles,
 * que la pantalla descargaba página por página solo para esto.
 */
interface AlertasPanelDrawerProps {
  showAlertasPanel: boolean;
  onClose: () => void;
  /** Controles que cumplen los filtros actuales. */
  total: number;
  /** Cuántos de ellos tienen alertas críticas. */
  totalConAlertas: number;
  /** Los más recientes con alerta (el servidor manda como mucho 10). */
  controlesConAlertas: ControlPrenatal[];
  detectarAlertas: (values: any) => string[];
  getNombrePaciente: (control: ControlPrenatal) => string;
  handleQuickView: (control: ControlPrenatal) => void;
}

const AlertasPanelDrawer: React.FC<AlertasPanelDrawerProps> = ({
  showAlertasPanel, onClose, total, totalConAlertas, controlesConAlertas,
  detectarAlertas, getNombrePaciente, handleQuickView,
}) => (
  <Drawer
    title={
      <Space>
        <WarningOutlined />
        Panel de Alertas
        <Badge
          count={totalConAlertas}
          style={{ backgroundColor: '#ff4d4f' }}
        />
      </Space>
    }
    placement="right"
    onClose={onClose}
    open={showAlertasPanel}
    width={400}
  >
    <Space direction="vertical" style={{ width: '100%' }} size="middle">
      <Alert
        message="Resumen de Alertas"
        description={`Se encontraron ${totalConAlertas} controles con alertas médicas de un total de ${total} controles (con los filtros aplicados).`}
        type="info"
        showIcon
      />

      <Divider>Controles con Alertas</Divider>

      {controlesConAlertas.map((control) => {
        const alertas = detectarAlertas(control);
        return (
          <Card
            key={control.id}
            size="small"
            title={
              <Space>
                <Badge count={alertas.length} />
                <Text strong>{getNombrePaciente(control)}</Text>
              </Space>
            }
            extra={
              <Button
                size="small"
                type="link"
                onClick={() => {
                  handleQuickView(control);
                  onClose();
                }}
              >
                Ver
              </Button>
            }
          >
            <Space direction="vertical" style={{ width: '100%' }} size="small">
              <Text type="secondary">
                Control #{control.numero_control} -{' '}
                {dayjs(control.fecha_control).format('DD/MM/YYYY')}
              </Text>
              {alertas.slice(0, 2).map((alerta) => (
                <Alert
                  key={`alerta-${alerta}`}
                  message={alerta}
                  type="warning"
                  showIcon
                  style={{ fontSize: 12 }}
                />
              ))}
              {alertas.length > 2 && (
                <Text type="secondary" style={{ fontSize: 12 }}>
                  +{alertas.length - 2} alertas más…
                </Text>
              )}
            </Space>
          </Card>
        );
      })}

      {totalConAlertas > controlesConAlertas.length && (
        <Alert
          message={`Mostrando ${controlesConAlertas.length} de ${totalConAlertas} controles con alertas. Use el filtro «Con Alertas» para verlos todos en la tabla.`}
          type="info"
        />
      )}
    </Space>
  </Drawer>
);

export default AlertasPanelDrawer;
