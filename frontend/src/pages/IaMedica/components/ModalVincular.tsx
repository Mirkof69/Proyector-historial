import React from 'react';
import { Tag, Modal, Alert, Descriptions } from 'antd';
import { LinkOutlined } from '@ant-design/icons';
import { ImagenEcografica } from '../../../services/iaMedicaService';

interface ModalVincularProps {
  vincularModalVisible: boolean;
  imagenAVincular: ImagenEcografica | null;
  vinculando: boolean;
  onCancel: () => void;
  onOk: () => void;
}

const ModalVincular: React.FC<ModalVincularProps> = ({
  vincularModalVisible, imagenAVincular, vinculando, onCancel, onOk,
}) => (
  <Modal
    title={<span><LinkOutlined /> Vincular Imagen a Ecografía</span>}
    open={vincularModalVisible}
    onCancel={onCancel}
    width={500}
    onOk={onOk}
    confirmLoading={vinculando}
    okText="Crear Ecografía"
    okButtonProps={{ icon: <LinkOutlined /> }}
  >
    {imagenAVincular && (
      <div>
        <Descriptions size="small" column={1} bordered style={{ marginBottom: 16 }}>
          <Descriptions.Item label="Imagen IA ID">{imagenAVincular.id}</Descriptions.Item>
          <Descriptions.Item label="Paciente">
            <Tag color="blue">{imagenAVincular.paciente_nombre}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Tipo">{imagenAVincular.tipo_imagen}</Descriptions.Item>
          <Descriptions.Item label="Fecha">
            {imagenAVincular.fecha_captura || imagenAVincular.fecha_subida.slice(0, 10)}
          </Descriptions.Item>
          <Descriptions.Item label="Tiene análisis CNN">
            {imagenAVincular.tiene_analisis ? (
              <Tag color="success">Sí</Tag>
            ) : (
              <Tag color="warning">No</Tag>
            )}
          </Descriptions.Item>
        </Descriptions>
        <Alert
          type="info"
          showIcon
          description={
            `Se creará una Ecografía en el módulo de ecografías para ${imagenAVincular.paciente_nombre}.
            ${imagenAVincular.tiene_analisis ? ' El análisis CNN se copiará a la nueva ecografía.' : ''}`
          }
        />
      </div>
    )}
  </Modal>
);

export default ModalVincular;
