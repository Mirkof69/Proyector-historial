import React from 'react';
import { Card, Space, Tag, Alert, Row, Col, Image, Typography, Upload, Button } from 'antd';
import { FileImageOutlined, UploadOutlined, PlusOutlined } from '@ant-design/icons';
import { Ecografia } from '../../../services/ecografiasService';
import { API_URL, getCsrfToken } from '../../../services/api';

const { Text } = Typography;

interface DetalleEcoImagenesProps {
  ecografia: Ecografia;
  id?: string;
  handleImageUpload: (info: any) => void;
}

const DetalleEcoImagenes: React.FC<DetalleEcoImagenesProps> = ({ ecografia, id, handleImageUpload }) => (
  <Card
    title={
      <Space>
        <FileImageOutlined />
        Imágenes Ecográficas {ecografia.imagenes && ecografia.imagenes.length > 0 && `(${ecografia.imagenes.length})`}
      </Space>
    }
    className="u-mb-4"
  >
    {/* Sección de subida de imágenes */}
    <Upload
      name="imagen"
      action={`${API_URL}/ecografias/${id}/subir_imagen/`}
      withCredentials
      headers={{
        // Auth por cookie httpOnly; CSRF via double-submit cookie
        'X-CSRFToken': getCsrfToken() ?? '',
      }}
      onChange={handleImageUpload}
      listType="picture-card"
      showUploadList={false}
      accept="image/*"
    >
      <Button icon={<UploadOutlined />} type="dashed" block className="u-mb-4">
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
                  className="eco-miniatura"
                  fallback="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+P+/HgAFcgJS9sIqAwAAAABJRU5ErkJggg=="
                />
              }
            >
              <Card.Meta
                title={
                  <Text ellipsis className="u-t-xs">
                    {img.titulo || `Imagen ${index + 1}`}
                  </Text>
                }
                description={
                  <Space direction="vertical" size={0} className="u-ancho">
                    {img.tipo_imagen && (
                      <Tag color="processing" className="u-t-xs">
                        {img.tipo_imagen.replace('_', ' ').toUpperCase()}
                      </Tag>
                    )}
                    {img.descripcion && (
                      <Text type="secondary" className="u-t-xs" ellipsis>
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
