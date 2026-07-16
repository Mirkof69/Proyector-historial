import React from 'react';
import { Button, Tag, Modal } from 'antd';
import {
  RobotOutlined, WarningOutlined, CheckCircleOutlined,
  DownloadOutlined, FundProjectionScreenOutlined, InfoCircleOutlined,
} from '@ant-design/icons';
import { ImagenEcografica, AnalisisCNN } from '../../../services/iaMedicaService';
import { API_URL } from '../../../services/api';
import { IaMedicaAction } from '../iaMedicaReducer';
import { getResultIcon, getResultClass } from '../iaMedicaHelpers';

interface ModalCnnLegadoProps {
  isModalVisible: boolean;
  selectedAnalysis: {imagen?: ImagenEcografica, analisis: AnalisisCNN} | null;
  dispatch: React.Dispatch<IaMedicaAction>;
}

const ModalCnnLegado: React.FC<ModalCnnLegadoProps> = ({
  isModalVisible, selectedAnalysis, dispatch,
}) => (
  <Modal
    title="Resultado del Análisis CNN"
    open={isModalVisible}
    onCancel={() => dispatch({ type: 'SET_IS_MODAL_VISIBLE', payload: false })}
    width={1000}
    footer={[
      <Button key="close" onClick={() => dispatch({ type: 'SET_IS_MODAL_VISIBLE', payload: false })}>Cerrar</Button>,
      <Button key="export" type="primary" icon={<DownloadOutlined />}>Exportar Reporte</Button>
    ]}
    className="cnn-analysis-modal"
  >
    {selectedAnalysis && (
      <div className="analysis-container">
        {selectedAnalysis.imagen && (
          <div className="image-preview-section">
            <img src={`${API_URL.replace('/api', '')}${selectedAnalysis.imagen.url_imagen}`} alt="Ecografía" />
          </div>
        )}

        <div className="results-section">
          {selectedAnalysis.analisis.sugerencia_diagnostica_data && (
            <div className="diagnosis-suggestion" style={{ background: 'var(--ia-info-bg)', padding: 12, borderRadius: 8, marginBottom: 12, border: '1px solid var(--ia-info)' }}>
              <h4 style={{ margin: 0, color: 'var(--ia-info)' }}><RobotOutlined /> Diagnóstico Sugerido</h4>
              <p style={{ margin: '4px 0', fontSize: 16, fontWeight: 600, color: 'var(--ia-text)' }}>
                {selectedAnalysis.analisis.sugerencia_diagnostica_data.patologia.replace(/_/g, ' ').toUpperCase()}
                <Tag color="blue" style={{ marginLeft: 8 }}>
                  {Math.round(selectedAnalysis.analisis.sugerencia_diagnostica_data.confianza * 100)}%
                </Tag>
              </p>
              <p style={{ margin: 0, fontSize: 12, color: 'var(--ia-text-secondary)' }}>
                ICD-10: {selectedAnalysis.analisis.sugerencia_diagnostica_data.icd10}
                {selectedAnalysis.analisis.sugerencia_diagnostica_data.descripcion && ` — ${selectedAnalysis.analisis.sugerencia_diagnostica_data.descripcion}`}
              </p>
              {selectedAnalysis.analisis.sugerencia_diagnostica_data.recomendacion && (
                <div style={{ marginTop: 8, fontSize: 12, padding: '8px 12px', background: 'var(--ia-bg-alt)', color: 'var(--ia-text)', borderRadius: 6 }}>
                  <InfoCircleOutlined style={{ marginRight: 6 }} />
                  {selectedAnalysis.analisis.sugerencia_diagnostica_data.recomendacion}
                </div>
              )}
            </div>
          )}
          <div className={`result-header ${getResultClass(selectedAnalysis.analisis.resultado)}`}>
            {getResultIcon(selectedAnalysis.analisis.resultado)}
            <div className="result-info">
              <h3>Diagnóstico IA: {selectedAnalysis.analisis.resultado.replace('_', ' ').toUpperCase()}</h3>
              <p>Modelo: {selectedAnalysis.analisis.modelo_usado.toUpperCase()} • Confianza: {selectedAnalysis.analisis.confianza_porcentaje}%</p>
            </div>
          </div>

          <div className="findings-list">
            <h4><FundProjectionScreenOutlined /> Estructuras Detectadas</h4>
            {Object.entries(selectedAnalysis.analisis.estructuras_detectadas).map(([key, val]: any) => (
              <div className="finding-item" key={key}>
                <span className="finding-name">{key.replace('_', ' ')}</span>
                <span className="finding-conf">{(val.confianza * 100).toFixed(1)}% {val.normal ? 'Normal' : 'Anomalo'}</span>
              </div>
            ))}
          </div>

          {selectedAnalysis.analisis.anomalias_detectadas.length > 0 && (
            <div className="findings-list" style={{ borderColor: '#fecaca' }}>
              <h4 style={{ color: '#dc2626' }}><WarningOutlined /> Anomalías Detectadas</h4>
              {selectedAnalysis.analisis.anomalias_detectadas.map((anom: any) => (
                <div className="finding-item" key={anom.tipo}>
                  <span className="finding-name">{anom.tipo.replace('_', ' ')}</span>
                  <span className="finding-conf">{(anom.confianza * 100).toFixed(1)}% • {anom.severidad}</span>
                </div>
              ))}
            </div>
          )}

          {selectedAnalysis.analisis.recomendaciones.length > 0 && (
            <div className="recommendations-box">
              <h4><CheckCircleOutlined /> Recomendaciones Médicas</h4>
              <ul>
                {selectedAnalysis.analisis.recomendaciones.map((rec: string) => (
                  <li key={rec}>{rec}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    )}
  </Modal>
);

export default ModalCnnLegado;
