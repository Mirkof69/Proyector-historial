import React from 'react';
import { Button, Space, Card, Tag, Typography, Alert, Drawer, Divider, Badge } from 'antd';
import { WarningOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { ControlPrenatal } from '../../../services/controlesService';

const { Text } = Typography;

interface AlertasPanelDrawerProps {
  showAlertasPanel: boolean;
  onClose: () => void;
  controles: ControlPrenatal[];
  detectarAlertas: (values: any) => string[];
  getNombrePaciente: (control: ControlPrenatal) => string;
  handleQuickView: (control: ControlPrenatal) => void;
}

const AlertasPanelDrawer: React.FC<AlertasPanelDrawerProps> = ({
  showAlertasPanel, onClose, controles, detectarAlertas, getNombrePaciente, handleQuickView,
}) => (
  <Drawer
    title={
      <Space>
        <WarningOutlined />
        Panel de Alertas
        <Badge
          count={
            controles.filter((c) => c.tiene_alertas).length
          }
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
        description={`Se encontraron ${controles.filter((c) => c.tiene_alertas).length
          } controles con alertas médicas de un total de ${controles.length} controles.`}
        type="info"
        showIcon
      />

      <Divider>Controles con Alertas</Divider>

      {controles
        .filter((c) => c.tiene_alertas)
        .slice(0, 10)
        .map((control) => {
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

      {controles.filter((c) => c.tiene_alertas).length > 10 && (
        <Alert
          message={`Mostrando 10 de ${controles.filter((c) => c.tiene_alertas).length
            } controles con alertas`}
          type="info"
        />
      )}
    </Space>
  </Drawer>
);

export default AlertasPanelDrawer;
