import React from 'react';
import { Card, Button, Space, Typography, Progress, Timeline, Tag, Descriptions } from 'antd';
import {
  CheckCircleOutlined, LoadingOutlined, DownloadOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';

const { Title, Text, Paragraph } = Typography;

interface PasoGeneracionProps {
  generando: boolean;
  progresoGeneracion: number;
  reporteGenerado: any;
  handleDescargarReporte: () => void;
  handleGenerarOtro: () => void;
  handleVolver: () => void;
}

const PasoGeneracion: React.FC<PasoGeneracionProps> = ({
  generando, progresoGeneracion, reporteGenerado,
  handleDescargarReporte, handleGenerarOtro, handleVolver,
}) => (
  <div>
    {generando ? (
      <div style={{ textAlign: 'center', padding: '50px 0' }}>
        <LoadingOutlined style={{ fontSize: 64, color: '#1890ff' }} />
        <Title level={3} style={{ marginTop: 24 }}>
          Generando Reporte…
        </Title>
        <Paragraph type="secondary">
          Por favor espere mientras se genera el reporte
        </Paragraph>
        <Progress
          percent={progresoGeneracion}
          status="active"
          strokeColor={{ from: '#108ee9', to: '#87d068' }}
          style={{ marginBottom: 32 }}
        />

        <Timeline
          mode="alternate"
          style={{ textAlign: 'left', marginTop: 24 }}
          items={[
            {
              color: progresoGeneracion > 0 ? 'green' : 'gray',
              children: (
                <>
                  <Text strong>Validando datos</Text>
                  <br />
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    {progresoGeneracion > 0 ? '✓ Completado' : 'En espera...'}
                  </Text>
                </>
              )
            },
            {
              color: progresoGeneracion > 30 ? 'green' : progresoGeneracion > 0 ? 'blue' : 'gray',
              children: (
                <>
                  <Text strong>Consultando base de datos</Text>
                  <br />
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    {progresoGeneracion > 30 ? '✓ Completado' : progresoGeneracion > 0 ? '⟳ En proceso...' : 'En espera...'}
                  </Text>
                </>
              )
            },
            {
              color: progresoGeneracion > 60 ? 'green' : progresoGeneracion > 30 ? 'blue' : 'gray',
              children: (
                <>
                  <Text strong>Procesando información</Text>
                  <br />
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    {progresoGeneracion > 60 ? '✓ Completado' : progresoGeneracion > 30 ? '⟳ En proceso...' : 'En espera...'}
                  </Text>
                </>
              )
            },
            {
              color: progresoGeneracion > 90 ? 'green' : progresoGeneracion > 60 ? 'blue' : 'gray',
              children: (
                <>
                  <Text strong>Generando archivo</Text>
                  <br />
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    {progresoGeneracion > 90 ? '✓ Completado' : progresoGeneracion > 60 ? '⟳ En proceso...' : 'En espera...'}
                  </Text>
                </>
              )
            },
            {
              color: progresoGeneracion === 100 ? 'green' : 'gray',
              children: (
                <>
                  <Text strong>Finalizado</Text>
                  <br />
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    {progresoGeneracion === 100 ? '✓ Listo para descargar' : 'En espera...'}
                  </Text>
                </>
              )
            }
          ]}
        />
      </div>
    ) : reporteGenerado ? (
      <div style={{ textAlign: 'center', padding: '50px 0' }}>
        <CheckCircleOutlined
          style={{ fontSize: 64, color: reporteGenerado.estado === 'completado' ? '#52c41a' : '#1890ff', marginBottom: 24 }}
        />
        <Title level={3}>
          {reporteGenerado.estado === 'completado' ? '¡Reporte Listo!' : 'Solicitud de Reporte Creada'}
        </Title>
        <Paragraph type="secondary">
          {reporteGenerado.estado === 'completado'
            ? 'El reporte se generó correctamente y está listo para descargar.'
            : 'La solicitud se registró correctamente y se está procesando. Podrá descargarlo cuando el estado cambie a "Completado".'}
        </Paragraph>

        <Card style={{ marginTop: 24, textAlign: 'left' }}>
          <Descriptions column={1} bordered>
            <Descriptions.Item label="Tipo de Reporte">
              {reporteGenerado.tipo_reporte_nombre}
            </Descriptions.Item>
            <Descriptions.Item label="Formato">
              <Tag color={reporteGenerado.formato === 'pdf' ? 'red' : 'green'}>
                {reporteGenerado.formato?.toUpperCase()}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="Estado">
              <Tag color={reporteGenerado.estado === 'completado' ? 'success' : reporteGenerado.estado === 'error' ? 'error' : 'processing'}>
                {reporteGenerado.estado_display || reporteGenerado.estado}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="Fecha de Solicitud">
              {dayjs(reporteGenerado.fecha_solicitud).format('DD/MM/YYYY HH:mm')}
            </Descriptions.Item>
          </Descriptions>
        </Card>

        <Space size="large" style={{ marginTop: 32 }}>
          <Button
            type="primary"
            size="large"
            icon={<DownloadOutlined />}
            disabled={reporteGenerado.estado !== 'completado'}
            onClick={handleDescargarReporte}
          >
            Descargar Reporte
          </Button>
          <Button size="large" onClick={handleGenerarOtro}>
            Generar Otro Reporte
          </Button>
          <Button size="large" onClick={handleVolver}>
            Volver al Listado
          </Button>
        </Space>
      </div>
    ) : null}
  </div>
);

export default PasoGeneracion;
