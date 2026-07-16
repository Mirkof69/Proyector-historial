import React from 'react';
import { Descriptions, Tag, Space, Badge, Typography, Divider, Alert } from 'antd';
import { InfoCircleOutlined } from '@ant-design/icons';
import { Reporte } from '../reporteTypes';
import { EstadoTagReporte } from './DetalleReporteHelpers';

const { Text, Paragraph } = Typography;

interface TabInfoGeneralReporteProps {
  reporte: Reporte;
}

const TabInfoGeneralReporte: React.FC<TabInfoGeneralReporteProps> = ({ reporte }) => (
  <>
    <Descriptions
      bordered
      column={{ xxl: 3, xl: 3, lg: 2, md: 2, sm: 1, xs: 1 }}
      layout="vertical"
    >
      <Descriptions.Item label="Estado Actual">
        <EstadoTagReporte estado={reporte.estado} />
      </Descriptions.Item>

      <Descriptions.Item label="Tipo de Reporte">
        <Tag color="blue">{reporte.tipo_reporte}</Tag>
      </Descriptions.Item>

      <Descriptions.Item label="Formato">
        <Tag color="geekblue">{reporte.formato}</Tag>
      </Descriptions.Item>

      <Descriptions.Item label="Generado Por">
        <Space>
          <Badge status="processing" />
          <Text strong>{reporte.creado_por.nombre_completo}</Text>
          <Text type="secondary">({reporte.creado_por.rol})</Text>
        </Space>
      </Descriptions.Item>

      <Descriptions.Item label="Fecha de Finalización">
        {reporte.fecha_actualizacion ? new Date(reporte.fecha_actualizacion).toISOString().slice(0, 16).replace('T', ' ') : '-'}
      </Descriptions.Item>

      <Descriptions.Item label="Metadatos del Archivo">
        {reporte.resumen_data ? (
          <Space direction="vertical" size={0}>
            <Text>Registros: {reporte.resumen_data.total_registros}</Text>
            {reporte.resumen_data.tiempo_procesamiento_seg && (
              <Text type="secondary">Tiempo: {reporte.resumen_data.tiempo_procesamiento_seg}s</Text>
            )}
          </Space>
        ) : (
          <Text type="secondary">No disponible</Text>
        )}
      </Descriptions.Item>
    </Descriptions>

    <Divider />

    <Paragraph>
      <InfoCircleOutlined style={{ color: '#1890ff', marginRight: 8 }} />
      Este reporte fue generado automáticamente por el sistema Fetal Medical.
      Los datos reflejan el estado de la base de datos al momento de la creación.
    </Paragraph>

    {reporte.estado === 'FALLIDO' && (
      <Alert
        style={{ marginTop: 20 }}
        message="Causa del Error"
        description={reporte.mensaje_error || "Error desconocido durante la generación del reporte."}
        type="error"
        showIcon
        icon={<InfoCircleOutlined />}
      />
    )}
  </>
);

export default TabInfoGeneralReporte;
