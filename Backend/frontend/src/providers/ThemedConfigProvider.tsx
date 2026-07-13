import React from 'react';
import { ConfigProvider, Empty } from 'antd';
import esES from 'antd/locale/es_ES';
import useAntdTheme from '../hooks/useAntdTheme';

/**
 * Estado vacío consistente para TODAS las tablas, listas y selects del sistema.
 * Un solo lugar → toda la app distingue «no hay datos» de «cargando» o «se rompió».
 * Mensaje según el componente para que sea claro bajo presión clínica.
 */
const renderEmpty = (componentName?: string): React.ReactNode => {
  const descripciones: Record<string, string> = {
    Table: 'No hay registros para mostrar',
    List: 'No hay elementos en esta lista',
    Select: 'Sin opciones disponibles',
    TreeSelect: 'Sin opciones disponibles',
    Cascader: 'Sin opciones disponibles',
    Transfer: 'Sin datos',
  };
  const descripcion = descripciones[componentName ?? ''] ?? 'No hay datos disponibles';
  const compacto = componentName === 'Select' || componentName === 'TreeSelect' || componentName === 'Cascader';
  return (
    <Empty
      image={Empty.PRESENTED_IMAGE_SIMPLE}
      description={descripcion}
      style={compacto ? { margin: '8px 0' } : { padding: '20px 0' }}
    />
  );
};

/**
 * Aplica los tokens de Ant Design según el tema actual.
 * Debe estar dentro de ThemeProvider para acceder al contexto de tema.
 */
const ThemedConfigProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const themeConfig = useAntdTheme();

  return (
    <ConfigProvider locale={esES} theme={themeConfig} renderEmpty={renderEmpty}>
      {children}
    </ConfigProvider>
  );
};

export default ThemedConfigProvider;
