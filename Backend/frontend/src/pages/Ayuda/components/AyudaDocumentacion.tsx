import React from 'react';
import { List, Button, Avatar } from 'antd';
import { FilePdfOutlined, PrinterOutlined } from '@ant-design/icons';
import { MANUALES } from '../data/faqs';

const AyudaDocumentacion: React.FC = () => {
  return (
    <List
      itemLayout="horizontal"
      rowKey="title"
      dataSource={MANUALES}
      renderItem={item => (
        <List.Item
          actions={[
            <Button key="descargar" icon={<FilePdfOutlined />}>Descargar</Button>,
            <Button key="imprimir" icon={<PrinterOutlined />}>Imprimir</Button>
          ]}
        >
          <List.Item.Meta
            avatar={<Avatar shape="square" size="large" icon={<FilePdfOutlined />} className="ayuda-page__pdf" />}
            title={<span className="ayuda-page__titulo-enlace">{item.title}</span>}
            description={`Actualizado: ${item.date} • Tamaño: ${item.size} • Formato: PDF`}
          />
        </List.Item>
      )}
      className="ayuda-page__seccion"
    />
  );
};

export default AyudaDocumentacion;
