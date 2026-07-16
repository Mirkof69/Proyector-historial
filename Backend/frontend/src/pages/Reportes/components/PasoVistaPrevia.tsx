import React from 'react';
import { Card, Alert, Spin, Typography, Tag, Descriptions } from 'antd';
import dayjs from 'dayjs';

const { Title, Text, Paragraph } = Typography;

interface PasoVistaPreviaProps {
  loading: boolean;
  vistaPrevia: any;
}

const PasoVistaPrevia: React.FC<PasoVistaPreviaProps> = ({ loading, vistaPrevia }) => (
  <div>
    <Title level={4}>Vista Previa</Title>
    <Paragraph type="secondary">
      Revise la configuración antes de generar el reporte
    </Paragraph>

    {loading ? (
      <div style={{ textAlign: 'center', padding: '50px 0' }}>
        <Spin size="large" />
        <div style={{ marginTop: 16 }}>Generando vista previa…</div>
      </div>
    ) : vistaPrevia ? (
      <Card>
        <Descriptions column={{ xs: 1, sm: 2 }} bordered>
          <Descriptions.Item label="Tipo de Reporte">
            {vistaPrevia.tipo_nombre}
          </Descriptions.Item>
          <Descriptions.Item label="Formato">
            <Tag color={vistaPrevia.formato === 'pdf' ? 'red' : 'green'}>
              {vistaPrevia.formato?.toUpperCase()}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Rango de Fechas">
            {vistaPrevia.fecha_inicio && vistaPrevia.fecha_fin
              ? `${dayjs(vistaPrevia.fecha_inicio).format('DD/MM/YYYY')} - ${dayjs(vistaPrevia.fecha_fin).format('DD/MM/YYYY')}`
              : 'Sin restricción de fechas'}
          </Descriptions.Item>
          <Descriptions.Item label="Registros a Incluir">
            <Text strong>{vistaPrevia.total_registros}</Text>
          </Descriptions.Item>
          <Descriptions.Item label="Tamaño Estimado">
            {vistaPrevia.tamanio_estimado_kb >= 1024
              ? `${(vistaPrevia.tamanio_estimado_kb / 1024).toFixed(1)} MB`
              : `${vistaPrevia.tamanio_estimado_kb} KB`}
          </Descriptions.Item>
        </Descriptions>

        <Alert
          message="Información"
          description={`El reporte incluirá ${vistaPrevia.total_registros} registros del período seleccionado.`}
          type="info"
          showIcon
          style={{ marginTop: 16 }}
        />
      </Card>
    ) : (
      <Alert
        message="No se pudo generar la vista previa"
        type="warning"
        showIcon
      />
    )}
  </div>
);

export default PasoVistaPrevia;
