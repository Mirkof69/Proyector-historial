import React from 'react';
import { Card, Space, Tag, Alert, Row, Col, Image, Typography, Upload, Button } from 'antd';
import { FileImageOutlined, UploadOutlined, PlusOutlined } from '@ant-design/icons';
import { Ecografia } from '../../../services/ecografiasService';
import { API_URL } from '../../../services/api';

const { Text } = Typography;

interface DetalleEcoImagenesProps {
  ecografia: Ecografia;
  id?: string;
  getToken: () => string | null;
  handleImageUpload: (info: any) => void;
}

const DetalleEcoImagenes: React.FC<DetalleEcoImagenesProps> = ({ ecografia, id, getToken, handleImageUpload }) => (
  <Card
    title={
      <Space>
        <FileImageOutlined />
        Imágenes Ecográficas {ecografia.imagenes && ecografia.imagenes.length > 0 && `(${ecografia.imagenes.length})`}
      </Space>
    }
    style={{ marginBottom: 16 }}
  >
    {/* Sección de subida de imágenes */}
    <Upload
      name="imagen"
      action={`${API_URL}/ecografias/${id}/subir_imagen/`}
      headers={{
        'Authorization': `Bearer ${getToken()}`,
      }}
      onChange={handleImageUpload}
      listType="picture-card"
      showUploadList={false}
      accept="image/*"
    >
      <Button icon={<UploadOutlined />} type="dashed" block style={{ marginBottom: 16 }}>
        <PlusOutlined /> Subir Nueva Imagen
      </Button>
    </Upload>

    {/* Galería de imágenes */}
    {ecografia.imagenes && ecografia.imagenes.length > 0 ? (
      <Row gutter={[16, 16]}>
        {ecografia.imagenes.map((img, index) => (
          <Col xs={24} sm={12} md={8} lg={6} key={img.id || `img-${img.titulo}`}>
            <Card
              hoverable
              size="small"
              cover={
                <Image
                  src={img.url_imagen || (typeof img.imagen === 'string' ? img.imagen : '')}
                  alt={img.titulo || `Imagen ${index + 1}`}
                  style={{ height: 200, objectFit: 'cover', borderRadius: '8px 8px 0 0' }}
                  fallback="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+P+/HgAFcgJS9sIqAwAAAABJRU5ErkJggg=="
                />
              }
            >
              <Card.Meta
                title={
                  <Text ellipsis style={{ fontSize: 12 }}>
                    {img.titulo || `Imagen ${index + 1}`}
                  </Text>
                }
                description={
                  <Space direction="vertical" size={0} style={{ width: '100%' }}>
                    {img.tipo_imagen && (
                      <Tag color="blue" style={{ fontSize: '12px' }}>
                        {img.tipo_imagen.replace('_', ' ').toUpperCase()}
                      </Tag>
                    )}
                    {img.descripcion && (
                      <Text type="secondary" style={{ fontSize: '12px' }} ellipsis>
                        {img.descripcion}
                      </Text>
                    )}
                  </Space>
                }
              />
            </Card>
          </Col>
        ))}
      </Row>
    ) : (
      <Alert
        message="No hay imágenes"
        description="Aún no se han subido imágenes para esta ecografía. Use el botón superior para subir imágenes."
        type="info"
        showIcon
      />
    )}
  </Card>
);

export default DetalleEcoImagenes;
