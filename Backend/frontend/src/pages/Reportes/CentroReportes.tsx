import React, { Suspense } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Card, Space, Tabs, Typography } from 'antd';
import { BarChartOutlined } from '@ant-design/icons';
import { useAuth } from '../../hooks/useAuth';
import { GlobalLoader } from '../../components/common/GlobalLoader';
import {
  AuditoriaReportes, GenerarReporte, Indicadores, KPIs, Reportes, Statistics,
} from '../../routes/lazyPages';

const { Title, Text } = Typography;

/**
 * Centro de reportes: UNA página con pestañas.
 *
 * Antes eran seis páginas sueltas (y cuatro solo se alcanzaban escribiendo la
 * URL). Cada pestaña reutiliza la pantalla existente, se muestra solo si el
 * rol tiene el permiso y queda en la URL (`?pestana=kpis`) para poder
 * compartir el enlace; las rutas viejas redirigen aquí.
 */
export const PESTANAS = [
  { key: 'tiempo-real', label: 'Panel en tiempo real', permiso: 'view_reportegenerado', Componente: Reportes },
  { key: 'estadisticas', label: 'Estadísticas por fecha', permiso: null, Componente: Statistics },
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
    <div className="page-container" style={{ padding: 24 }}>
      <Card style={{ marginBottom: 16 }}>
        <Space align="center">
          <BarChartOutlined style={{ fontSize: 28 }} />
          <div>
            <Title level={3} style={{ margin: 0 }}>Centro de reportes</Title>
            <Text type="secondary">Indicadores en tiempo real, estadísticas por fecha, KPIs, reportes PDF y auditoría.</Text>
          </div>
        </Space>
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
  );
};

export default CentroReportes;
