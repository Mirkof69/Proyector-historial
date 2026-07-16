import React from 'react';
import { Card, Spin, Table, Tabs } from 'antd';
import {
  ExperimentOutlined,
  LineChartOutlined,
} from '@ant-design/icons';
import GraficoTendenciaLaboratorio from '../../../components/GraficoTendenciaLaboratorio';
import { buildColumnsResultados } from './columnsResultadosLab';

const tabResultadosDetallados = (
  <span>
    <ExperimentOutlined />
    Resultados Detallados
  </span>
);

const TabEstadisticasLabel = React.memo(({ count }: { count: number }) => (
  <span>
    <LineChartOutlined />
    Análisis Estadístico ({count} exámenes previos)
  </span>
));

interface ResultadosLabTabsProps {
  examen: any;
  estadisticas: any | null;
  loadingEstadisticas: boolean;
}

const ResultadosLabTabs: React.FC<ResultadosLabTabsProps> = ({ examen, estadisticas, loadingEstadisticas }) => {
  const columnsResultados = buildColumnsResultados();

  return (
    <Card style={{ marginBottom: 16 }}>
      <Tabs defaultActiveKey="resultados" items={[
        {
          key: "resultados",
          label: tabResultadosDetallados,
          children: (
            <Table
              columns={columnsResultados}
              dataSource={examen.resultados}
              rowKey="id"
              pagination={false}
              bordered
            />
          )
        },
        ...(estadisticas && estadisticas.examenes_historicos && estadisticas.examenes_historicos.length > 0 ? [{
          key: "estadisticas",
          label: <TabEstadisticasLabel count={estadisticas?.total_historicos ?? 0} />,
          children: loadingEstadisticas ? (
            <div style={{ textAlign: 'center', padding: '50px 0' }}>
              <Spin tip="Cargando estadísticas…"><div /></Spin>
            </div>
          ) : (
            <Tabs tabPosition="left" items={
              examen.resultados.reduce((items: any[], resultado: any) => {
                const historicoParametro = estadisticas.examenes_historicos.reduce((acc: any[], exHist: any) => {
                  const resultadoHist = exHist.resultados.find(
                    (r: any) => r.parametro === resultado.parametro_nombre
                  );
                  if (resultadoHist && resultadoHist.valor_numerico !== null) {
                    acc.push({
                      fecha: exHist.fecha_resultado,
                      valor: resultadoHist.valor_numerico,
                    });
                  }
                  return acc;
                }, []);

                if (historicoParametro.length === 0) return items;

                const match = resultado.rango_referencia?.match(/(\\d+\\.?\\d*)\\s*-\\s*(\\d+\\.?\\d*)/);
                const valorMin = match ? parseFloat(match[1]) : undefined;
                const valorMax = match ? parseFloat(match[2]) : undefined;

                items.push({
                  key: resultado.parametro_nombre,
                  label: resultado.parametro_nombre,
                  children: (
                    <GraficoTendenciaLaboratorio
                      parametro={resultado.parametro_nombre || ''}
                      historico={historicoParametro}
                      valorMinimo={valorMin}
                      valorMaximo={valorMax}
                      unidad={resultado.unidad}
                    />
                  )
                });
                return items;
              }, [])
            } />
          )
        }] : [])
      ]} />
    </Card>
  );
};

export default ResultadosLabTabs;
