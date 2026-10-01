import React, { Suspense, lazy } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Button, Card, Col, Row, Space, Tabs, Typography } from 'antd';
import { BarChartOutlined, PrinterOutlined } from '@ant-design/icons';
import { useAuth } from '../../hooks/useAuth';
import { GlobalLoader } from '../../components/common/GlobalLoader';
import {
  AuditoriaReportes, GenerarReporte, Indicadores, KPIs, Reportes, Statistics,
} from '../../routes/lazyPages';
import { FiltroFechasReportes, ProveedorRangoReportes } from './rangoReportes';

const NatalidadMorbilidad = lazy(() => import('./NatalidadMorbilidad'));
const ReporteIA = lazy(() => import('./ReporteIA'));

const { Title, Text } = Typography;

/**
 * Centro de reportes: UNA página con pestañas.
 *
 * Antes eran seis páginas sueltas (y cuatro solo se alcanzaban escribiendo la
 * URL). Cada pestaña reutiliza la pantalla existente, se muestra solo si el
 * rol tiene el permiso y queda en la URL (`?pestana=kpis`) para poder
 * compartir el enlace; las rutas viejas redirigen aquí.
 *
 * El período (hoy, 7 días, mes, año o un rango) se elige UNA vez arriba y lo
 * usan todas las pestañas que dependen de fechas; «Imprimir» imprime la
 * pestaña abierta sin el menú ni los botones.
 */
export const PESTANAS = [
  { key: 'tiempo-real', label: 'Panel en tiempo real', permiso: 'view_reportegenerado', Componente: Reportes },
  { key: 'estadisticas', label: 'Estadísticas por fecha', permiso: null, Componente: Statistics },
  { key: 'natalidad', label: 'Natalidad y morbilidad', permiso: 'view_parto', Componente: NatalidadMorbilidad },
  { key: 'ia', label: 'Inteligencia artificial', permiso: 'view_analisiscnn', Componente: ReporteIA },
  { key: 'kpis', label: 'KPIs', permiso: 'view_dashboardkpi', Componente: KPIs },
  { key: 'indicadores', label: 'Indicadores y metas', permiso: 'view_dashboardkpi', Componente: Indicadores },
  { key: 'generar', label: 'Generar reporte PDF', permiso: 'add_reportegenerado', Componente: GenerarReporte },
  { key: 'auditoria', label: 'Auditoría', permiso: 'view_auditoriareporte', Componente: AuditoriaReportes },
] as const;

const CentroReportes: React.FC = () => {
  const { hasPermission } = useAuth();
  const [params, setParams] = useSearchParams();
  const visibles = PESTANAS.filter((p) => !p.permiso || hasPermission(p.permiso));
  const pedida = params.get('pestana');
  const activa = visibles.some((p) => p.key === pedida) ? (pedida as string) : visibles[0]?.key;

  return (
    <ProveedorRangoReportes>
    <div className="page-container" style={{ padding: 24 }}>
      <Card style={{ marginBottom: 16 }}>
        <Row justify="space-between" align="middle" gutter={[16, 12]}>
          <Col>
            <Space align="center">
              <BarChartOutlined style={{ fontSize: 28 }} />
              <div>
                <Title level={3} style={{ margin: 0 }}>Centro de reportes</Title>
                <Text type="secondary">Natalidad, morbilidad, IA, KPIs, estadísticas por fecha, PDF y auditoría.</Text>
              </div>
            </Space>
          </Col>
          <Col className="no-print">
            <Space wrap>
              <FiltroFechasReportes />
              <Button icon={<PrinterOutlined />} onClick={() => window.print()}>Imprimir</Button>
            </Space>
          </Col>
        </Row>
      </Card>
      {visibles.length === 0 ? (
        <Card><Text>Su rol no tiene acceso a ningún reporte.</Text></Card>
      ) : (
        <Tabs
          activeKey={activa}
          onChange={(key) => setParams({ pestana: key }, { replace: true })}
          destroyInactiveTabPane
          items={visibles.map(({ key, label, Componente }) => ({
            key,
            label,
            children: (
              <Suspense fallback={<GlobalLoader tip="Cargando…" />}>
                <Componente />
              </Suspense>
            ),
          }))}
        />
      )}
    </div>
    </ProveedorRangoReportes>
  );
};

export default CentroReportes;
