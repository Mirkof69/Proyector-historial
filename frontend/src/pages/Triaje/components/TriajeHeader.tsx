import React from 'react';
import { Row, Col, Space, Button, Typography } from 'antd';
import { ArrowLeftOutlined, PrinterOutlined, EditOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { TriajeEnfermeria } from '../../../services/triajeService';

const { Title, Text } = Typography;

interface TriajeHeaderProps {
  triaje: TriajeEnfermeria;
  onVolver: () => void;
  onEditar: () => void;
}

const TriajeHeader: React.FC<TriajeHeaderProps> = ({ triaje, onVolver, onEditar }) => (
  <div className="triaje-cabecera">
    <Row justify="space-between" align="middle" gutter={[16, 16]}>
      <Col>
        <Space size="large">
          <Button
            icon={<ArrowLeftOutlined />}
            onClick={onVolver}
            aria-label="Volver"
          />
          <div>
            <Title level={2} className="pagina-encabezado__titulo">
              Detalle de Evaluación de Triaje
            </Title>
            <Text className="pagina-encabezado__descripcion">
              ID Registro: #{triaje.id} | Fecha: {dayjs(triaje.fecha_registro).format('DD/MM/YYYY HH:mm')}
            </Text>
          </div>
        </Space>
      </Col>
      <Col>
        <Space wrap>
          <Button icon={<PrinterOutlined />} onClick={() => window.print()}>
            Imprimir Informe
          </Button>
          <Button
            type="primary"
            icon={<EditOutlined />}
            onClick={onEditar}
          >
            Editar Registro
          </Button>
        </Space>
      </Col>
    </Row>
  </div>
);

export default TriajeHeader;
