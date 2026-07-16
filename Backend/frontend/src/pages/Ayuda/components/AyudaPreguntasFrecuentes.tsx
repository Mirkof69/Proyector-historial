import React from 'react';
import { Collapse, Tag, Typography, Button } from 'antd';
import { FAQS } from '../data/faqs';

const { Title, Paragraph, Text } = Typography;

interface AyudaPreguntasFrecuentesProps {
  searchQuery: string;
}

const handleContactarSoporte = () => {
  const soporteTab = document.querySelector<HTMLElement>('[data-tab-key="4"]');
  if (soporteTab) {
    soporteTab.click();
  }
};

const AyudaPreguntasFrecuentes: React.FC<AyudaPreguntasFrecuentesProps> = ({ searchQuery }) => {
  const filteredFaqs = searchQuery
    ? FAQS.reduce((acc, cat) => {
        const filteredItems = cat.items.filter(item =>
          item.pregunta.toLowerCase().includes(searchQuery) ||
          item.respuesta.toLowerCase().includes(searchQuery)
        );
        if (filteredItems.length > 0) {
          acc.push({ ...cat, items: filteredItems });
        }
        return acc;
      }, [] as typeof FAQS)
    : FAQS;


  return (
    <div style={{ maxWidth: 800, margin: '0 auto', padding: 20 }}>
      {searchQuery && (
        <div style={{ marginBottom: 20 }}>
          <Text strong>Resultados de búsqueda para: "{searchQuery}"</Text>
        </div>
      )}

      {filteredFaqs.length > 0 ? (
        filteredFaqs.map((categoria) => (
          <div key={categoria.categoria} style={{ marginBottom: 32 }}>
            <Title level={4} style={{ color: '#1890ff' }}>{categoria.categoria}</Title>
            <Collapse
              accordion
              ghost
              expandIconPosition="end"
              items={categoria.items.map((item) => ({
                key: item.pregunta,
                label: (
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <Text strong>{item.pregunta}</Text>
                    <Tag color={
                      item.dificultad === 'Básico' ? 'green' :
                      item.dificultad === 'Intermedio' ? 'orange' : 'red'
                    }>
                      {item.dificultad}
                    </Tag>
                  </div>
                ),
                children: <Paragraph style={{ color: '#666' }}>{item.respuesta}</Paragraph>
              }))}
            />
          </div>
        ))
      ) : (
        <div style={{ textAlign: 'center', padding: 50 }}>
          <Text type="secondary">No encontramos respuestas para tu búsqueda.</Text>
          <br />
          <Button type="primary" style={{ marginTop: 16 }} onClick={handleContactarSoporte}>
            Contactar Soporte
          </Button>
        </div>
      )}
    </div>
  );
};

export default AyudaPreguntasFrecuentes;
