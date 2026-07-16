import React from 'react';
import {
  Drawer, Space, Tooltip, Button, Popconfirm, Alert, Table, Badge, Divider,
  Timeline, Empty, Typography,
} from 'antd';
import { DownloadOutlined, PrinterOutlined, DeleteOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { ResultadoCalculo } from '../calculadorasReducer';

const { Paragraph } = Typography;

interface HistorialDrawerProps {
  historialVisible: boolean;
  onClose: () => void;
  historial: ResultadoCalculo[];
  limpiarHistorial: () => void;
  message: { success: (m: string) => void; info: (m: string) => void };
  modal: { info: (config: any) => void };
}

const HistorialDrawer: React.FC<HistorialDrawerProps> = ({
  historialVisible, onClose, historial, limpiarHistorial, message, modal,
}) => (
  <Drawer
    title="Historial de Cálculos"
    placement="right"
    onClose={onClose}
    open={historialVisible}
    width={700}
    extra={
      <Space>
        <Tooltip title="Descargar historial">
          <Button icon={<DownloadOutlined />} onClick={() => {
            const dataStr = JSON.stringify(historial, null, 2);
            const dataBlob = new Blob([dataStr], { type: 'application/json' });
            const url = URL.createObjectURL(dataBlob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `historial-calculadoras-${dayjs().format('YYYY-MM-DD')}.json`;
            link.click();
            message.success('Historial descargado');
          }} />
        </Tooltip>
        <Tooltip title="Imprimir historial">
          <Button icon={<PrinterOutlined />} onClick={() => {
            window.print();
            message.info('Preparando impresión...');
          }} />
        </Tooltip>
        <Popconfirm
          title="Limpiar historial"
          description="¿Está seguro de que desea eliminar todo el historial?"
          onConfirm={limpiarHistorial}
        >
          <Tooltip title="Eliminar historial">
            <Button danger icon={<DeleteOutlined />} />
          </Tooltip>
        </Popconfirm>
      </Space>
    }
  >
    {historial.length > 0 ? (
      <>
        <Alert message="Vista de Tabla" type="info" showIcon style={{ marginBottom: 16 }} />
        <Table
          dataSource={historial}
          rowKey="id"
          size="small"
          pagination={{ pageSize: 5 }}
          columns={[
            {
              title: 'Tipo',
              dataIndex: 'tipo',
              key: 'tipo',
              render: (tipo) => <Badge status="processing" text={tipo} />
            },
            {
              title: 'Fecha',
              dataIndex: 'fecha',
              key: 'fecha',
            },
            {
              title: 'Acciones',
              key: 'actions',
              render: (_, record) => (
                <Button
                  size="small"
                  type="link"
                  onClick={() => {
                    modal.info({
                      title: record.tipo,
                      content: (
                        <div>
                          <Divider />
                          <Paragraph>
                            <strong>Fecha:</strong> {record.fecha}
                          </Paragraph>
                          <Divider>Datos Ingresados</Divider>
                          <pre>{JSON.stringify(record.datos, null, 2)}</pre>
                          <Divider>Resultados</Divider>
                          <pre>{JSON.stringify(record.resultado, null, 2)}</pre>
                        </div>
                      ),
                      width: 600,
                    });
                  }}
                >
                  Ver Detalle
                </Button>
              )
            }
          ]}
        />

        <Divider>Línea de Tiempo</Divider>
        <Timeline
          items={historial.slice(0, 10).map((item) => ({
            key: item.id,
            children: (
              <>
                <p><strong>{item.tipo}</strong></p>
                <p style={{ fontSize: 12, color: '#666' }}>{item.fecha}</p>
              </>
            ),
            color: 'blue'
          }))}
        />
      </>
    ) : (
      <Empty description="Sin historial de cálculos" />
    )}
  </Drawer>
);

export default HistorialDrawer;
