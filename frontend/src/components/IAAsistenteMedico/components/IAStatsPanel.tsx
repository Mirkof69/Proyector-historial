import React from 'react';
import { Alert, Statistic } from 'antd';
import { MessageOutlined } from '@ant-design/icons';

interface IAStatsPanelProps {
  /** Consultas respondidas en esta sesión. */
  consultas: number;
}

/**
 * Antes mostraba «Precisión 94,5 %» (un número fijo en el código) y contaba
 * «alertas» y «recomendaciones» buscando emojis en el texto. El asistente es una
 * base de conocimiento por palabras clave: no tiene una precisión medida.
 */
const IAStatsPanel: React.FC<IAStatsPanelProps> = ({ consultas }) => (
  <div className="ia-asistente-resumen">
    <Statistic title="Consultas en esta sesión" value={consultas} prefix={<MessageOutlined />} />
    <Alert
      type="info"
      showIcon
      message="Base de conocimiento por palabras clave, no un modelo entrenado: no tiene una exactitud medida."
    />
  </div>
);

export default IAStatsPanel;
