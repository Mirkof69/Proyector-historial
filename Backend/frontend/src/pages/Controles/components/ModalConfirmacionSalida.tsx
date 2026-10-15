import React from 'react';
import { Modal, Space } from 'antd';
import { WarningOutlined } from '@ant-design/icons';

interface ModalConfirmacionSalidaProps {
  open: boolean;
  onOk: () => void;
  onCancel: () => void;
}

const ModalConfirmacionSalida: React.FC<ModalConfirmacionSalidaProps> = ({ open, onOk, onCancel }) => (
  <Modal rootClassName="capa-clinica"
    title={
      <Space>
        <WarningOutlined className="u-c-aviso" />
        <span>¿Salir sin guardar?</span>
      </Space>
    }
    open={open}
    onOk={onOk}
    onCancel={onCancel}
    okText="Sí, salir"
    cancelText="Continuar editando"
    okButtonProps={{ danger: true }}
    centered
  >
    <p>Ha realizado cambios en el formulario que no se han guardado.</p>
    <p>¿Está seguro que desea salir? Los cambios se perderán.</p>
  </Modal>
);

export default ModalConfirmacionSalida;
