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
    <div className="ayuda-page__faq ayuda-page__seccion">
      {searchQuery && (
        <div>
          <Text strong>Resultados de búsqueda para: "{searchQuery}"</Text>
        </div>
      )}

      {filteredFaqs.length > 0 ? (
        filteredFaqs.map((categoria) => (
          <div key={categoria.categoria}>
            <Title level={4}>{categoria.categoria}</Title>
            <Collapse
              accordion
              ghost
              expandIconPosition="end"
              items={categoria.items.map((item) => ({
                key: item.pregunta,
                label: (
                  <div className="ayuda-page__pregunta">
                    <Text strong>{item.pregunta}</Text>
                    <Tag>
                      {item.dificultad}
                    </Tag>
                  </div>
                ),
                children: <Paragraph type="secondary">{item.respuesta}</Paragraph>
              }))}
            />
          </div>
        ))
      ) : (
        <div className="ayuda-page__sin-resultados">
          <Text type="secondary">No encontramos respuestas para tu búsqueda.</Text>
          <Button type="primary" onClick={handleContactarSoporte}>
            Contactar Soporte
          </Button>
        </div>
      )}
    </div>
  );
};

export default AyudaPreguntasFrecuentes;
