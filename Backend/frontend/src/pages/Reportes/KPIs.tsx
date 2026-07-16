import React, { useState, useEffect, useCallback } from 'react';
import { Card, Row, Col, Statistic, Spin, Typography, Button, message } from 'antd';
import { RiseOutlined, UserOutlined, MedicineBoxOutlined, CalendarOutlined, WarningOutlined, ExperimentOutlined, DownloadOutlined } from '@ant-design/icons';
import { reportesService, DashboardKPIs } from '../../services/reportesService';
import { exportarExcel } from '../../utils/excelExport';

const { Title } = Typography;

const KPIs: React.FC = () => {
  const [kpis, setKpis] = useState<DashboardKPIs | null>(null);
  const [loading, setLoading] = useState(false);

  const cargarKPIs = useCallback(async () => {
    setLoading(true);
    try {
      const data = await reportesService.obtenerDashboardKPIs();
      setKpis(data);
    } catch {
      setKpis(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    cargarKPIs();
  }, [cargarKPIs]);

  const handleExportarExcel = () => {
    if (!kpis?.kpis) {
      message.warning('No hay indicadores cargados para exportar');
      return;
    }
    const filas = [
      { indicador: 'Pacientes Activos', valor: kpis.kpis.pacientes_activos?.valor || 0 },
      { indicador: 'Embarazos Activos', valor: kpis.kpis.embarazos_activos?.valor || 0 },
      { indicador: 'Citas del Día', valor: kpis.kpis.citas_dia?.valor || 0 },
      { indicador: 'Citas Completadas', valor: kpis.kpis.citas_dia?.completadas || 0 },
      { indicador: 'Alertas Alto Riesgo', valor: kpis.alertas?.embarazos_alto_riesgo || 0 },
    ];
    exportarExcel(filas, { indicador: 'Indicador', valor: 'Valor' }, {
      filename: `kpis_${new Date().toISOString().slice(0, 10)}.xlsx`,
      sheetName: 'KPIs',
      title: 'Indicadores Clave (KPIs)',
    });
    message.success('Indicadores exportados correctamente');
  };

  return (
    <Spin spinning={loading}>
      <Card
        title={<span><RiseOutlined style={{ marginRight: 8 }} />Indicadores Clave (KPIs)</span>}
        extra={<Button icon={<DownloadOutlined />} onClick={handleExportarExcel}>Exportar Excel</Button>}
      >
        {kpis?.kpis ? (
          <Row gutter={[16, 16]}>
            <Col xs={24} sm={12} md={6}>
              <Card>
                <Statistic
                  title="Pacientes Activos"
                  value={kpis.kpis.pacientes_activos?.valor || 0}
                  prefix={<UserOutlined />}
                  valueStyle={{ color: '#1890ff' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Card>
                <Statistic
                  title="Embarazos Activos"
                  value={kpis.kpis.embarazos_activos?.valor || 0}
                  prefix={<MedicineBoxOutlined />}
                  valueStyle={{ color: '#722ed1' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Card>
                <Statistic
                  title="Citas del Día"
                  value={kpis.kpis.citas_dia?.valor || 0}
                  prefix={<CalendarOutlined />}
                  valueStyle={{ color: '#52c41a' }}
                  suffix={`/ ${kpis.kpis.citas_dia?.completadas || 0} completadas`}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Card>
                <Statistic
                  title="Alertas Alto Riesgo"
                  value={kpis.alertas?.embarazos_alto_riesgo || 0}
                  prefix={<WarningOutlined />}
                  valueStyle={{ color: '#ff4d4f' }}
                />
              </Card>
            </Col>
          </Row>
        ) : (
          <Row gutter={[16, 16]}>
            {['Pacientes', 'Embarazos', 'Partos', 'Alertas'].map(label => (
              <Col xs={24} sm={12} md={6} key={label}>
                <Card>
                  <Statistic title={label} value={0} prefix={<ExperimentOutlined />} />
                </Card>
              </Col>
            ))}
          </Row>
        )}
      </Card>
    </Spin>
  );
};

export default KPIs;
