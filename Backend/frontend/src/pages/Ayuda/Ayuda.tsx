import React, { useState } from 'react';
import { Layout, Typography, Input, Tabs, Card, Breadcrumb, Form } from 'antd';
import { SearchOutlined, QuestionCircleOutlined, CustomerServiceOutlined, BookOutlined, BulbOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import AyudaGuiasRapidas from './components/AyudaGuiasRapidas';
import AyudaPreguntasFrecuentes from './components/AyudaPreguntasFrecuentes';
import AyudaDocumentacion from './components/AyudaDocumentacion';
import AyudaSoporteTecnico from './components/AyudaSoporteTecnico';

const { Title, Text } = Typography;
const { TabPane } = Tabs;

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
    <Layout className="animate-fade-in" style={{ minHeight: '100vh', background: '#f0f2f5' }}>
      <div style={{ padding: '16px 24px', background: '#fff', borderBottom: '1px solid #f0f0f0' }}>
        <Breadcrumb>
          <Breadcrumb.Item>
            <button
              type="button"
              onClick={() => navigate('/dashboard')}
              style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0, textAlign: 'left', width: '100%', color: '#1890ff' }}
              onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); navigate('/dashboard'); } }}
            >
              Inicio
            </button>
          </Breadcrumb.Item>
          <Breadcrumb.Item>Centro de Ayuda</Breadcrumb.Item>
        </Breadcrumb>
      </div>

      <div style={{
        background: 'linear-gradient(135deg, #001529 0%, #003a8c 100%)',
        padding: '60px 20px',
        textAlign: 'center',
        color: 'white'
      }}>
        <Title level={1} style={{ color: 'white', marginBottom: 16 }}>
          ¿En qué podemos ayudarte hoy?
        </Title>
        <Text style={{ color: 'rgba(255,255,255,0.8)', fontSize: 16 }}>
          Busca en la documentación, manuales y preguntas frecuentes del Sistema Clínico.
        </Text>

        <div style={{ maxWidth: 600, margin: '40px auto 0' }}>
          <Input
            size="large"
            placeholder="Ej: Registrar paciente, Error de impresión, FPP..."
            prefix={<SearchOutlined style={{ color: '#1890ff', fontSize: 20 }} />}
            onChange={handleSearch}
            style={{ borderRadius: 50, height: 60, fontSize: 18, boxShadow: '0 10px 25px rgba(0,0,0,0.2)' }}
            allowClear
          />
        </div>
      </div>

      <div style={{ padding: '0 24px 40px', marginTop: -40 }}>
        <Card variant="borderless" style={{ borderRadius: 16, boxShadow: '0 4px 12px rgba(0,0,0,0.05)', minHeight: 600 }}>
          <Tabs defaultActiveKey="1" size="large" centered>
            <TabPane tab={tabGuiasRapidas} key="1">
              <AyudaGuiasRapidas />
            </TabPane>

            <TabPane tab={tabPreguntasFrecuentes} key="2">
              <AyudaPreguntasFrecuentes searchQuery={searchQuery} />
            </TabPane>

            <TabPane tab={tabDocumentacion} key="3">
              <AyudaDocumentacion />
            </TabPane>

            <TabPane tab={tabSoporteTecnico} key="4">
              <AyudaSoporteTecnico form={form} />
            </TabPane>
          </Tabs>
        </Card>
      </div>

      <style>{`
        .guide-card {
          text-align: center;
          border-radius: 8px;
          transition: all 0.3s;
          height: 100%;
        }
        .guide-card:hover {
          transform: translateY(-5px);
          box-shadow: 0 10px 20px rgba(0,0,0,0.1);
          border-color: #1890ff;
        }
      `}</style>
    </Layout>
  );
};

export default Ayuda;
