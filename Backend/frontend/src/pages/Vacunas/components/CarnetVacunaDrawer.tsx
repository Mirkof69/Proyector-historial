import React from 'react';
import {
  Button, Space, Drawer, Timeline, Alert, Divider, Descriptions, Typography,
} from 'antd';
import {
  EditOutlined, ClockCircleOutlined, WarningOutlined, FilePdfOutlined,
  UserOutlined, ExportOutlined, PrinterOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { RegistroVacunaExtended } from '../vacunasUtils';

const { Title, Text } = Typography;

interface CarnetVacunaDrawerProps {
  isDrawerVisible: boolean;
  selectedVacuna: RegistroVacunaExtended | null;
  setIsDrawerVisible: (visible: boolean) => void;
  handleEditar: (id: number) => void;
}

const CarnetVacunaDrawer: React.FC<CarnetVacunaDrawerProps> = ({
  isDrawerVisible, selectedVacuna, setIsDrawerVisible, handleEditar,
}) => (
  <Drawer
    title={<Title level={4} style={{ margin: 0 }}><FilePdfOutlined /> Certificado Digital de Vacunación</Title>}
    placement="right"
    width={600}
    onClose={() => setIsDrawerVisible(false)}
    open={isDrawerVisible}
    className="carnet-drawer"
    extra={
      <Space>
        <Button icon={<PrinterOutlined />} onClick={() => window.print()}>Imprimir</Button>
        <Button type="primary" icon={<ExportOutlined />}>PDF</Button>
      </Space>
    }
  >
    {selectedVacuna && (
      <div className="carnet-content">
        <div className="carnet-header">
          <UserOutlined />
          <Title level={3}>{selectedVacuna.paciente_info?.nombre_completo || selectedVacuna.paciente_nombre}</Title>
          <Text type="secondary">Certificado de Inmunización Oficial</Text>
        </div>

        <Divider />

        <Descriptions title="Detalles del Paciente" column={1} bordered size="small">
          <Descriptions.Item label="ID Clínico">{selectedVacuna.paciente_info?.id_clinico}</Descriptions.Item>
          <Descriptions.Item label="Edad al momento">{selectedVacuna.paciente_info?.edad} años</Descriptions.Item>
        </Descriptions>

        <Divider />

        <Descriptions title="Información de la Vacuna" column={1} bordered size="small">
          <Descriptions.Item label="Vacuna">
            <Text strong color="blue">{selectedVacuna.tipo_vacuna_info?.nombre || selectedVacuna.tipo_vacuna_nombre}</Text>
          </Descriptions.Item>
          <Descriptions.Item label="Dosis Nº">{selectedVacuna.numero_dosis}</Descriptions.Item>
          <Descriptions.Item label="Fecha Aplicación">{dayjs(selectedVacuna.fecha_aplicacion).format('DD [de] MMMM, YYYY')}</Descriptions.Item>
          <Descriptions.Item label="Laboratorio">{selectedVacuna.laboratorio}</Descriptions.Item>
          <Descriptions.Item label="Número de Lote">{selectedVacuna.lote}</Descriptions.Item>
          <Descriptions.Item label="Vía de Adm.">{selectedVacuna.via_administracion}</Descriptions.Item>
        </Descriptions>

        <Divider />

        <Title level={5}><ClockCircleOutlined /> Línea de Tiempo</Title>
        <Timeline
          items={[
            {
              color: 'green',
              children: (
                <>
                  <Text strong>Vacuna aplicada</Text>
                  <br />
                  <Text type="secondary">
                    {dayjs(selectedVacuna.fecha_aplicacion).format('DD/MM/YYYY')}
                  </Text>
                </>
              ),
            },
            {
              color: selectedVacuna.proxima_dosis_fecha ? 'blue' : 'gray',
              children: selectedVacuna.proxima_dosis_fecha ? (
                <>
                  <Text strong>Próxima dosis programada</Text>
                  <br />
                  <Text type="secondary">
                    {dayjs(selectedVacuna.proxima_dosis_fecha).format('DD/MM/YYYY')}
                  </Text>
                </>
              ) : (
                <Text strong>Esquema de vacunación completo</Text>
              ),
            },
          ]}
        />

        {selectedVacuna.reacciones_adversas && (
          <>
            <Divider />
            <Alert
              message="Reacciones Adversas Reportadas"
              description={selectedVacuna.reacciones_adversas}
              type="warning"
              showIcon
              icon={<WarningOutlined />}
            />
          </>
        )}

        {selectedVacuna.observaciones && (
          <>
            <Divider />
            <Text strong>Observaciones:</Text>
            <p>{selectedVacuna.observaciones}</p>
          </>
        )}

        <Divider />
        <Space style={{ width: '100%', justifyContent: 'center' }}>
          <Button type="primary" icon={<FilePdfOutlined />} size="large">
            Descargar Certificado
          </Button>
          <Button icon={<EditOutlined />} size="large" onClick={() => handleEditar(selectedVacuna.id)}>
            Editar Registro
          </Button>
        </Space>
      </div>
    )}
  </Drawer>
);

export default CarnetVacunaDrawer;
