import React, { useEffect, useState } from 'react';
import { useAntdApp } from "../../hooks/useMessage";
import { Button, Tabs } from "antd";
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  RobotOutlined, DownloadOutlined, ReloadOutlined, ReadOutlined,
} from '@ant-design/icons';
import { iaMedicaService, EstadisticasIA } from '../../services/iaMedicaService';
import './IaMedica.css';
import IaMedicaStats from './components/IaMedicaStats';
import HistorialAnalisisIA from './components/HistorialAnalisisIA';
import CardiotocografiaIA from './components/CardiotocografiaIA';
import HistorialCardiotocografias from './components/HistorialCardiotocografias';
import EcografiaGinecologica from './components/EcografiaGinecologica';
import CatalogoModelos from './components/CatalogoModelos';
import RedesEcografiaReal from './components/RedesEcografiaReal';

const IaMedica: React.FC = () => {
  const { message } = useAntdApp();
  const [estadisticas, setEstadisticas] = useState<EstadisticasIA | null>(null);
  // Sube al guardar un análisis para que el historial vuelva a pedir su lista.
  const [claveHistorial, setClaveHistorial] = useState(0);
  const [params, setParams] = useSearchParams();
  const navigate = useNavigate();
  const pestana = ['ecografia', 'ginecologia', 'cardiotocografia', 'modelos'].includes(params.get('pestana') || '')
    ? (params.get('pestana') as string) : 'ecografia';

  const cargarEstadisticas = async () => {
    try {
      setEstadisticas(await iaMedicaService.getEstadisticas());
    } catch {
      message.error('Error al cargar datos del módulo IA');
    }
  };

  useEffect(() => {
    cargarEstadisticas();
    // eslint-disable-next-line react-doctor/exhaustive-deps
  }, []);

  const actualizar = () => {
    cargarEstadisticas();
    setClaveHistorial((c) => c + 1);
  };

  const handleExport = async () => {
    try {
      await iaMedicaService.exportarDataset();
      message.success('Dataset exportado correctamente');
    } catch (error) {
      message.error('Error al exportar dataset');
    }
  };

  return (
    <div className="ia-medica-container page-container">
      <div className="ia-medica-header">
        <div>
          <h1><RobotOutlined /> IA médica</h1>
          <p>Redes entrenadas con datos reales y medidas en pacientes que no vieron. Son apoyo a la decisión: el diagnóstico lo hace el médico.</p>
        </div>
        <div className="ia-medica-acciones">
          <Button icon={<ReadOutlined />} onClick={() => navigate('/dashboard/ia-guia')}>
            Guía de IA
          </Button>
          <Button icon={<ReloadOutlined />} onClick={actualizar}>
            Actualizar
          </Button>
          <Button icon={<DownloadOutlined />} onClick={handleExport}>
            Exportar dataset
          </Button>
        </div>
      </div>

      {estadisticas && (
        <IaMedicaStats estadisticas={estadisticas} />
      )}

      <Tabs
        activeKey={pestana}
        onChange={(clave) => { const n = new URLSearchParams(params); n.set('pestana', clave); setParams(n, { replace: true }); }}
        items={[
          { key: 'ecografia', label: 'Ecografía', children: <RedesEcografiaReal onGuardado={actualizar} /> },
          { key: 'ginecologia', label: 'Ecografía ginecológica', children: <EcografiaGinecologica onGuardado={actualizar} /> },
          { key: 'cardiotocografia', label: 'Cardiotocografía', children: <CardiotocografiaIA onGuardado={actualizar} /> },
          {
            key: 'modelos', label: 'Modelos y métricas',
            children: <CatalogoModelos modelos={estadisticas?.modelos_disponibles ?? []} />,
          },
        ]}
      />

      {/* Cada pestaña muestra lo que guarda: imágenes o cardiotocografías; el catálogo, nada. */}
      {['ecografia', 'ginecologia'].includes(pestana) && (
        <HistorialAnalisisIA claveRecarga={claveHistorial} onCambio={cargarEstadisticas} />
      )}
      {pestana === 'cardiotocografia' && <HistorialCardiotocografias claveRecarga={claveHistorial} />}
    </div>
  );
};

export default IaMedica;
