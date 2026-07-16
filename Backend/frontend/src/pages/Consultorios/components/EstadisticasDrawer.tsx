import React from 'react';
import { Drawer, Space, Card, Row, Col, Statistic, Descriptions } from 'antd';
import { BarChartOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { Consultorio } from '../../../services/consultoriosService';

interface EstadisticasDrawerProps {
  drawerEstadisticasVisible: boolean;
  consultorioEstadisticas: Consultorio | null;
  loadingEstadisticas: boolean;
  estadisticas: any;
  onClose: () => void;
}

const EstadisticasDrawer: React.FC<EstadisticasDrawerProps> = ({
  drawerEstadisticasVisible, consultorioEstadisticas, loadingEstadisticas, estadisticas, onClose,
}) => (
  <Drawer
    title={
      <Space>
        <BarChartOutlined />
        Estadísticas - {consultorioEstadisticas?.nombre}
      </Space>
    }
    placement="right"
    onClose={onClose}
    open={drawerEstadisticasVisible}
    width={700}
  >
    {loadingEstadisticas ? (
      <div style={{ textAlign: 'center', padding: '50px' }}>Cargando estadísticas…</div>
    ) : estadisticas ? (
      <Space direction="vertical" style={{ width: '100%' }} size="large">
        <Card>
          <Statistic
            title="Período"
            value={`${dayjs(estadisticas.periodo?.inicio).format('DD/MM/YYYY')} - ${dayjs(
              estadisticas.periodo?.fin
            ).format('DD/MM/YYYY')}`}
            valueStyle={{ fontSize: 14 }}
          />
        </Card>

        <Row gutter={16}>
          <Col span={12}>
            <Card>
              <Statistic
                title="Tasa de Ocupación"
                value={estadisticas.tasa_ocupacion || 0}
                suffix="%"
                valueStyle={{
                  color:
                    (estadisticas.tasa_ocupacion || 0) >= 80
                      ? '#cf1322'
                      : (estadisticas.tasa_ocupacion || 0) >= 60
                      ? '#faad14'
                      : '#3f8600',
                }}
              />
            </Card>
          </Col>
          <Col span={12}>
            <Card>
              <Statistic
                title="Horas Ocupadas"
                value={estadisticas.horas_ocupadas || 0}
                suffix={`/ ${estadisticas.horas_totales_disponibles || 0}h`}
              />
            </Card>
          </Col>
        </Row>

        <Row gutter={16}>
          <Col span={8}>
            <Card>
              <Statistic
                title="Consultas"
                value={estadisticas.total_consultas || 0}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col span={8}>
            <Card>
              <Statistic
                title="Procedimientos"
                value={estadisticas.total_procedimientos || 0}
                valueStyle={{ color: '#722ed1' }}
              />
            </Card>
          </Col>
          <Col span={8}>
            <Card>
              <Statistic
                title="Emergencias"
                value={estadisticas.total_emergencias || 0}
                valueStyle={{ color: '#cf1322' }}
              />
            </Card>
          </Col>
        </Row>

        <Card title="Uso y Mantenimiento">
          <Descriptions column={2} bordered size="small">
            <Descriptions.Item label="Médicos Usuarios">
              {estadisticas.medicos_usuarios || 0}
            </Descriptions.Item>
            <Descriptions.Item label="Promedio Ocupación/Día">
              {estadisticas.promedio_ocupacion_dia || 0}h
            </Descriptions.Item>
            <Descriptions.Item label="Total Mantenimientos">
              {estadisticas.total_mantenimientos || 0}
            </Descriptions.Item>
            <Descriptions.Item label="Horas Mantenimiento">
              {estadisticas.horas_mantenimiento || 0}h
            </Descriptions.Item>
            {estadisticas.dia_mas_ocupado && (
              <Descriptions.Item label="Día Más Ocupado" span={2}>
                {estadisticas.dia_mas_ocupado}
              </Descriptions.Item>
            )}
            {estadisticas.hora_pico && (
              <Descriptions.Item label="Hora Pico" span={2}>
                {estadisticas.hora_pico}
              </Descriptions.Item>
            )}
            {estadisticas.medico_mas_frecuente && (
              <Descriptions.Item label="Médico Más Frecuente" span={2}>
                {estadisticas.medico_mas_frecuente}
              </Descriptions.Item>
            )}
          </Descriptions>
        </Card>
      </Space>
    ) : (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        No hay estadísticas disponibles
      </div>
    )}
  </Drawer>
);

export default EstadisticasDrawer;
