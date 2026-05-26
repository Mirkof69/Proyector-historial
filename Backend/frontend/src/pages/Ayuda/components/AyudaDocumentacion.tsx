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
            <Button key="descargar" type="primary" ghost icon={<FilePdfOutlined />}>Descargar</Button>,
            <Button key="imprimir" icon={<PrinterOutlined />}>Imprimir</Button>
          ]}
        >
          <List.Item.Meta
            avatar={<Avatar shape="square" size="large" icon={<FilePdfOutlined />} style={{ backgroundColor: '#ff4d4f' }} />}
            title={<span style={{ color: '#1890ff', cursor: 'pointer' }}>{item.title}</span>}
            description={`Actualizado: ${item.date} • Tamaño: ${item.size} • Formato: PDF`}
          />
        </List.Item>
      )}
      style={{ padding: 20 }}
    />
  );
};

export default AyudaDocumentacion;
