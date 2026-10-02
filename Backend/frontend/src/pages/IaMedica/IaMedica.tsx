import React, { useReducer, useEffect } from 'react';
import { useAntdApp } from "../../hooks/useMessage";
import { Button, Tabs } from "antd";
import { useSearchParams } from 'react-router-dom';
import {
  RobotOutlined, DownloadOutlined, ReloadOutlined,
} from '@ant-design/icons';
import {
  iaMedicaService,
  ImagenEcografica,
} from '../../services/iaMedicaService';
import pacientesService from '../../services/pacientesService';
import { API_URL } from '../../services/api';
import './IaMedica.css';
import { initialState, reducer } from './iaMedicaReducer';
import IaMedicaStats from './components/IaMedicaStats';
import GaleriaEcografias from './components/GaleriaEcografias';
import InformeAnalisisModal from './components/InformeAnalisisModal';
import CardiotocografiaIA from './components/CardiotocografiaIA';
import EcografiaGinecologica from './components/EcografiaGinecologica';
import CatalogoModelos from './components/CatalogoModelos';
import ModalVincular from './components/ModalVincular';
import ModalCnnLegado from './components/ModalCnnLegado';
import RedesEcografiaReal from './components/RedesEcografiaReal';

const IaMedica: React.FC = () => {
  const { message } = useAntdApp();
  const [state, dispatch] = useReducer(reducer, initialState);
  const [selectedPacienteId, setSelectedPacienteId] = React.useState<number | null>(null);
  const [pacientesSearch, setPacientesSearch] = React.useState<{id: number; nombre: string}[]>([]);
  const [searchingPaciente, setSearchingPaciente] = React.useState(false);
  const [vincularModalVisible, setVincularModalVisible] = React.useState(false);
  const [imagenAVincular, setImagenAVincular] = React.useState<ImagenEcografica | null>(null);
  const [vinculando, setVinculando] = React.useState(false);
  const [ecografiasVinculadas, setEcografiasVinculadas] = React.useState<Record<number, number>>({});
  const [params, setParams] = useSearchParams();
  const pestana = ['ecografia', 'ginecologia', 'cardiotocografia', 'modelos'].includes(params.get('pestana') || '')
    ? (params.get('pestana') as string) : 'ecografia';

  const fetchData = async () => {
    dispatch({ type: 'SET_LOADING', payload: true });
    try {
      const [imgsData, statsData] = await Promise.all([
        iaMedicaService.getImagenes(),
        iaMedicaService.getEstadisticas()
      ]);
      dispatch({ type: 'SET_IMAGENES', payload: imgsData.results || imgsData });
      dispatch({ type: 'SET_ESTADISTICAS', payload: statsData });
    } catch (error) {
      message.error('Error al cargar datos del módulo IA');
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handlePatientSearch = async (query: string) => {
    if (!query || query.length < 2) return;
    setSearchingPaciente(true);
    try {
      const results = await pacientesService.listar();
      const q = query.toLowerCase();
      const filtered = results.filter((p: any) =>
        `${p.nombre} ${p.apellido_paterno} ${p.apellido_materno || ''}`.toLowerCase().includes(q)
      );
      setPacientesSearch(filtered.map((p: any) => ({
        id: p.id,
        nombre: p.nombre_completo || `${p.nombre} ${p.apellido_paterno}`.trim()
      })));
    } catch { /* silent */ }
    finally { setSearchingPaciente(false); }
  };

  const handleUpload = async (file: File) => {
    if (!selectedPacienteId) {
      message.warning('Seleccione un paciente antes de subir la imagen');
      return false;
    }
    dispatch({ type: 'SET_UPLOADING', payload: true });
    try {
      const formData = new FormData();
      formData.append('imagen', file);
      formData.append('paciente', String(selectedPacienteId));
      formData.append('tipo_imagen', 'eco_2d');

      await iaMedicaService.uploadImagen(formData);
      message.success('Imagen subida correctamente');
      fetchData();
    } catch (error: any) {
      message.error(`Error al subir la imagen: ${error?.response?.data ? JSON.stringify(error.response.data) : error.message}`);
    } finally {
      dispatch({ type: 'SET_UPLOADING', payload: false });
    }
    return false; // Prevenir upload default de antd
  };

  const handleAnalyze = async (id: number) => {
    dispatch({ type: 'SET_ANALYZING_ID', payload: id });
    try {
      const result = await iaMedicaService.analizarImagen(id, 'efficientnet');
      const imagenDetalle = await iaMedicaService.getImagenDetalle(id);
      message.success('Análisis completado');
      dispatch({ type: 'SET_SELECTED_ANALYSIS', payload: { analisis: result, imagen: imagenDetalle } });
      dispatch({ type: 'SET_IS_MODAL_VISIBLE', payload: true });
      fetchData();
    } catch (error) {
      message.error('Error durante el análisis CNN');
    } finally {
      dispatch({ type: 'SET_ANALYZING_ID', payload: null });
    }
  };

  const showAnalysis = async (id: number) => {
    try {
      const result = await iaMedicaService.getResultadoAnalisis(id);
      const imagenDetalle = await iaMedicaService.getImagenDetalle(id);
      dispatch({ type: 'SET_SELECTED_ANALYSIS', payload: { ...result, imagen: imagenDetalle } });
      dispatch({ type: 'SET_IS_MODAL_VISIBLE', payload: true });
    } catch (error) {
      message.error('No se pudo cargar el análisis');
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await iaMedicaService.deleteImagen(id);
      message.success('Imagen eliminada');
      fetchData();
    } catch (error) {
      message.error('Error al eliminar imagen');
    }
  };

  const handleExport = async () => {
    try {
      await iaMedicaService.exportarDataset();
      message.success('Dataset exportado correctamente');
    } catch (error) {
      message.error('Error al exportar dataset');
    }
  };

  const handleVincularClick = (img: ImagenEcografica) => {
    setImagenAVincular(img);
    setVincularModalVisible(true);
  };

  const handleVincularConfirm = async () => {
    if (!imagenAVincular) return;
    setVinculando(true);
    try {
      const result = await iaMedicaService.vincularAEcografia(
        imagenAVincular.id,
        imagenAVincular.paciente,
      );
      if (result.ecografia_id) {
        setEcografiasVinculadas(prev => ({
          ...prev,
          [imagenAVincular.id]: result.ecografia_id,
        }));
        message.success(`Ecografía #${result.ecografia_id} creada con análisis IA`);
      } else {
        message.success('Vinculado correctamente');
      }
      setVincularModalVisible(false);
      setImagenAVincular(null);
    } catch (error: any) {
      message.error(`Error al vincular: ${error?.response?.data?.error || error.message}`);
    } finally {
      setVinculando(false);
    }
  };


  // Análisis completo con las redes medidas (plano → segmentación → medidas)
  const handleAnalyzeCNN = async (img: ImagenEcografica) => {
    dispatch({ type: 'SET_ANALYZING_CNN_ID', payload: img.id });
    try {
      const imageUrl = `${API_URL.replace('/api', '')}${img.url_imagen}`;
      const response = await iaMedicaService.analyzeWithAI(undefined, String(img.id));
      dispatch({ type: 'SET_CNN_ANALYSIS', payload: response.ai_analysis });
      dispatch({ type: 'SET_CNN_IMAGE_URL', payload: imageUrl });
      dispatch({ type: 'SET_CNN_IMAGE_ID', payload: img.id });
      dispatch({ type: 'SET_NARRATIVE_REPORT', payload: null });
      dispatch({ type: 'SET_IS_CNN_MODAL_VISIBLE', payload: true });
      message.success('Análisis completado');
      fetchData();
    } catch (error: any) {
      message.error(error?.response?.data?.error || `No se pudo analizar la imagen: ${error?.message || 'error desconocido'}`);
    } finally {
      dispatch({ type: 'SET_ANALYZING_CNN_ID', payload: null });
    }
  };

  // Reporte narrativo de IA local (LLM con visión, Ollama) — siempre
  // grounded en el resultado real del CNN que ya se muestra arriba; nunca
  // se llama sin haber corrido antes el analisis CNN sobre esta imagen.
  const handleGenerarReporteNarrativo = async () => {
    if (!state.cnnImageId) {
      message.error('Primero analice la imagen.');
      return;
    }
    dispatch({ type: 'SET_LOADING_NARRATIVE', payload: true });
    try {
      const reporte = await iaMedicaService.generarReporteNarrativo(state.cnnImageId);
      dispatch({ type: 'SET_NARRATIVE_REPORT', payload: reporte });
      if (reporte._error_llm) {
        message.warning('El reporte narrativo se generó parcialmente: ' + reporte._error_llm);
      } else {
        message.success('Reporte narrativo generado');
      }
    } catch (error: any) {
      message.error(`Error generando el reporte narrativo: ${error?.message || 'Error desconocido'}`);
    } finally {
      dispatch({ type: 'SET_LOADING_NARRATIVE', payload: false });
    }
  };

  const cerrarInforme = () => {
    dispatch({ type: 'SET_IS_CNN_MODAL_VISIBLE', payload: false });
    dispatch({ type: 'SET_CNN_ANALYSIS', payload: null });
    dispatch({ type: 'SET_NARRATIVE_REPORT', payload: null });
    dispatch({ type: 'SET_CNN_IMAGE_ID', payload: null });
  };

  const galeria = (
    <>
      <RedesEcografiaReal />
      <GaleriaEcografias
        selectedPacienteId={selectedPacienteId}
        setSelectedPacienteId={setSelectedPacienteId}
        pacientesSearch={pacientesSearch}
        searchingPaciente={searchingPaciente}
        handlePatientSearch={handlePatientSearch}
        uploading={state.uploading}
        handleUpload={handleUpload}
        loading={state.loading}
        imagenes={state.imagenes}
        analyzingId={state.analyzingId}
        analyzingCnnId={state.analyzingCnnId}
        ecografiasVinculadas={ecografiasVinculadas}
        handleAnalyze={handleAnalyze}
        showAnalysis={showAnalysis}
        handleAnalyzeCNN={handleAnalyzeCNN}
        handleVincularClick={handleVincularClick}
        handleDelete={handleDelete}
      />
    </>
  );

  return (
    <div className="ia-medica-container page-container">
      <div className="ia-medica-header">
        <h1><RobotOutlined /> IA médica</h1>
        <div>
          <Button icon={<ReloadOutlined />} onClick={fetchData} style={{ marginRight: 8 }}>
            Actualizar
          </Button>
          <Button type="primary" icon={<DownloadOutlined />} onClick={handleExport}>
            Exportar dataset
          </Button>
        </div>
      </div>

      {state.estadisticas && (
        <IaMedicaStats estadisticas={state.estadisticas} />
      )}

      <Tabs
        activeKey={pestana}
        onChange={(clave) => { const n = new URLSearchParams(params); n.set('pestana', clave); setParams(n, { replace: true }); }}
        items={[
          { key: 'ecografia', label: 'Ecografía', children: galeria },
          { key: 'ginecologia', label: 'Ecografía ginecológica', children: <EcografiaGinecologica /> },
          { key: 'cardiotocografia', label: 'Cardiotocografía', children: <CardiotocografiaIA /> },
          {
            key: 'modelos', label: 'Modelos y métricas',
            children: <CatalogoModelos modelos={state.estadisticas?.modelos_disponibles ?? []} />,
          },
        ]}
      />

      <InformeAnalisisModal
        abierto={state.isCnnModalVisible}
        informe={state.cnnAnalysis}
        imagenUrl={state.cnnImageUrl}
        reporteNarrativo={state.narrativeReport}
        generandoNarrativa={state.loadingNarrative}
        onGenerarNarrativa={handleGenerarReporteNarrativo}
        onCerrar={cerrarInforme}
      />

      {/* Modal Vincular a Ecografía */}
      <ModalVincular
        vincularModalVisible={vincularModalVisible}
        imagenAVincular={imagenAVincular}
        vinculando={vinculando}
        onCancel={() => { setVincularModalVisible(false); setImagenAVincular(null); }}
        onOk={handleVincularConfirm}
      />

      {/* Modal de Análisis CNN (legado ia_medica app) */}
      <ModalCnnLegado
        isModalVisible={state.isModalVisible}
        selectedAnalysis={state.selectedAnalysis}
        dispatch={dispatch}
      />
    </div>
  );
};

export default IaMedica;
