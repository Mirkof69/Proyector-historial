import React from 'react';
import { Button, Space, Tag, Alert, Typography, Spin, Empty, List, Modal, Divider } from 'antd';
import { WarningOutlined, CheckCircleOutlined, SafetyOutlined } from '@ant-design/icons';

const { Text } = Typography;

interface RiesgoDetalladoModalProps {
  open: boolean;
  loadingRiesgo: boolean;
  riesgoDetallado: any;
  onClose: () => void;
}

const RiesgoDetalladoModal: React.FC<RiesgoDetalladoModalProps> = ({
  open, loadingRiesgo, riesgoDetallado, onClose,
}) => (
  <Modal
    title={
      <Space>
        <SafetyOutlined style={{ color: '#ff4d4f' }} />
        <span>Análisis de Riesgo Obstétrico Detallado</span>
      </Space>
    }
    open={open}
    onCancel={onClose}
    footer={[
      <Button
        key="close"
        onClick={onClose}
      >
        Cerrar
      </Button>,
    ]}
    width={900}
  >
    <Spin spinning={loadingRiesgo}>
      {riesgoDetallado ? (
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <Alert
            message={`Nivel de Riesgo: ${riesgoDetallado.nivel_riesgo?.toUpperCase()}`}
            description={`Puntaje total: ${riesgoDetallado.puntaje_total || 0} puntos`}
            type={
              riesgoDetallado.nivel_riesgo === 'alto'
                ? 'error'
                : riesgoDetallado.nivel_riesgo === 'medio'
                  ? 'warning'
                  : 'success'
            }
            showIcon
          />

          <Divider orientation="left">Factores de Riesgo Identificados</Divider>
          {riesgoDetallado.factores_riesgo && riesgoDetallado.factores_riesgo.length > 0 ? (
            <List
              dataSource={riesgoDetallado.factores_riesgo}
              renderItem={(factor: any) => (
                <List.Item key={`factor-${factor.nombre || factor.descripcion}`}>
                  <List.Item.Meta
                    avatar={<WarningOutlined style={{ color: '#ff4d4f', fontSize: 18 }} />}
                    title={<Text strong>{factor.nombre || factor.descripcion}</Text>}
                    description={
                      <Space direction="vertical" size={0}>
                        <Text type="secondary">{factor.detalle || factor.observaciones}</Text>
                        {factor.puntaje && (
                          <Tag color="red">Puntaje: {factor.puntaje} puntos</Tag>
                        )}
                      </Space>
                    }
                  />
                </List.Item>
              )}
            />
          ) : (
            <Alert
              message="Sin factores de riesgo"
              description="No se identificaron factores de riesgo significativos."
              type="success"
              showIcon
            />
          )}

          <Divider orientation="left">Recomendaciones Médicas</Divider>
          {riesgoDetallado.recomendaciones && riesgoDetallado.recomendaciones.length > 0 ? (
            <List
              dataSource={riesgoDetallado.recomendaciones}
               renderItem={(recomendacion: string, index: number) => (
                 <List.Item key={`rec-${recomendacion.substring(0, 30)}`}>
                  <List.Item.Meta
                    avatar={<CheckCircleOutlined style={{ color: '#52c41a', fontSize: 18 }} />}
                    title={`Recomendación ${index + 1}`}
                    description={recomendacion}
                  />
                </List.Item>
              )}
            />
          ) : (
            <Alert
              message="Continuar con controles regulares"
              description="Mantener el seguimiento prenatal según calendario establecido."
              type="info"
              showIcon
            />
          )}
        </Space>
      ) : (
        !loadingRiesgo && (
          <Empty description="No hay datos de riesgo disponibles" />
        )
      )}
    </Spin>
  </Modal>
);

export default RiesgoDetalladoModal;
