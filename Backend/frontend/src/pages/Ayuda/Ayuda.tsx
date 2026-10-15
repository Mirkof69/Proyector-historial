import React, { useState } from 'react';
import { Typography, Input, Tabs, Card, Breadcrumb, Form } from 'antd';
import { SearchOutlined, QuestionCircleOutlined, CustomerServiceOutlined, BookOutlined, BulbOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import AyudaGuiasRapidas from './components/AyudaGuiasRapidas';
import AyudaPreguntasFrecuentes from './components/AyudaPreguntasFrecuentes';
import AyudaDocumentacion from './components/AyudaDocumentacion';
import AyudaSoporteTecnico from './components/AyudaSoporteTecnico';
import './Ayuda.css';

const { Title, Text } = Typography;

const tabGuiasRapidas = <span><BulbOutlined /> Guías Rápidas</span>;
const tabPreguntasFrecuentes = <span><QuestionCircleOutlined /> Preguntas Frecuentes</span>;
const tabDocumentacion = <span><BookOutlined /> Documentación</span>;
const tabSoporteTecnico = <span><CustomerServiceOutlined /> Soporte Técnico</span>;

const Ayuda: React.FC = () => {
  const navigate = useNavigate();
  const [form] = Form.useForm();
  const [searchQuery, setSearchQuery] = useState('');

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value.toLowerCase());
  };

  return (
    <div className="ayuda-page page-container">
      <Breadcrumb
        items={[
          {
            title: (
              <button
                type="button"
                className="ayuda-page__miga"
                onClick={() => navigate('/dashboard')}
                onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); navigate('/dashboard'); } }}
              >
                Inicio
              </button>
            ),
          },
          { title: 'Centro de Ayuda' },
        ]}
      />

      <header className="ayuda-page__cabecera">
        <div>
          <Title level={2}>¿En qué podemos ayudarte hoy?</Title>
          <Text type="secondary">
            Busca en la documentación, manuales y preguntas frecuentes del Sistema Clínico.
          </Text>
        </div>
        <Input
          className="ayuda-page__buscar"
          placeholder="Ej: Registrar paciente, Error de impresión, FPP..."
          prefix={<SearchOutlined />}
          onChange={handleSearch}
          allowClear
        />
      </header>

      <Card>
        <Tabs defaultActiveKey="1" items={[
          {
            key: "1",
            label: tabGuiasRapidas,
            children: <AyudaGuiasRapidas />
          },
          {
            key: "2",
            label: tabPreguntasFrecuentes,
            children: <AyudaPreguntasFrecuentes searchQuery={searchQuery} />
          },
          {
            key: "3",
            label: tabDocumentacion,
            children: <AyudaDocumentacion />
          },
          {
            key: "4",
            label: tabSoporteTecnico,
            children: <AyudaSoporteTecnico form={form} />
          }
        ]} />
      </Card>
    </div>
  );
};

export default Ayuda;
