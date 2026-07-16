import React from 'react';
import { Card, List, Tag, Space, Tabs, Avatar } from 'antd';
import {
  WarningOutlined, MedicineBoxOutlined, BellOutlined, InfoCircleOutlined, CalendarOutlined,
} from '@ant-design/icons';
import { AlertaMedica, getTipoConfig, getEstadoConfig } from '../sistemaAlertasUtils';

interface AlertasCategoriasProps {
  alertas: AlertaMedica[];
}

const AlertasCategorias: React.FC<AlertasCategoriasProps> = ({ alertas }) => (
  <Card
    title={
      <Space>
        <InfoCircleOutlined />
        <span>Análisis Detallado por Categoría</span>
      </Space>
    }
    style={{ marginTop: 24 }}
  >
    <Tabs
      defaultActiveKey="signos_vitales"
      type="card"
      items={[
        {
          key: 'signos_vitales',
          label: (
            <span>
              <MedicineBoxOutlined /> Signos Vitales ({alertas.filter(a => a.categoria === 'Signos Vitales').length})
            </span>
          ),
          children: (
            <List
              dataSource={alertas.filter(a => a.categoria === 'Signos Vitales')}
              renderItem={alerta => (
                <List.Item key={alerta.id}>
                  <List.Item.Meta
                    avatar={<Avatar style={{ backgroundColor: getTipoConfig(alerta.tipo).color }} icon={getTipoConfig(alerta.tipo).icon} />}
                    title={alerta.titulo}
                    description={`${alerta.paciente_nombre || 'Sin paciente'} - ${alerta.descripcion}`}
                  />
                  <Tag color={getEstadoConfig(alerta.estado).color}>{alerta.estado}</Tag>
                </List.Item>
              )}
            />
          )
        },
        {
          key: 'controles',
          label: (
            <span>
              <CalendarOutlined /> Controles ({alertas.filter(a => a.categoria === 'Control Prenatal').length})
            </span>
          ),
          children: (
            <List
              dataSource={alertas.filter(a => a.categoria === 'Control Prenatal')}
              renderItem={alerta => (
                <List.Item key={alerta.id}>
                  <List.Item.Meta
                    avatar={<Avatar style={{ backgroundColor: getTipoConfig(alerta.tipo).color }} icon={getTipoConfig(alerta.tipo).icon} />}
                    title={alerta.titulo}
                    description={`${alerta.paciente_nombre || 'Sin paciente'} - ${alerta.descripcion}`}
                  />
                  <Tag color={getEstadoConfig(alerta.estado).color}>{alerta.estado}</Tag>
                </List.Item>
              )}
            />
          )
        },
        {
          key: 'riesgos',
          label: (
            <span>
              <WarningOutlined /> Riesgos ({alertas.filter(a => a.categoria === 'Riesgo Obstétrico').length})
            </span>
          ),
          children: (
            <List
              dataSource={alertas.filter(a => a.categoria === 'Riesgo Obstétrico')}
              renderItem={alerta => (
                <List.Item key={alerta.id}>
                  <List.Item.Meta
                    avatar={<Avatar style={{ backgroundColor: getTipoConfig(alerta.tipo).color }} icon={getTipoConfig(alerta.tipo).icon} />}
                    title={alerta.titulo}
                    description={`${alerta.paciente_nombre || 'Sin paciente'} - ${alerta.descripcion}`}
                  />
                  <Tag color={getEstadoConfig(alerta.estado).color}>{alerta.estado}</Tag>
                </List.Item>
              )}
            />
          )
        },
        {
          key: 'otras',
          label: (
            <span>
              <BellOutlined /> Otras ({alertas.filter(a => !['Signos Vitales', 'Control Prenatal', 'Riesgo Obstétrico'].includes(a.categoria)).length})
            </span>
          ),
          children: (
            <List
              dataSource={alertas.filter(a => !['Signos Vitales', 'Control Prenatal', 'Riesgo Obstétrico'].includes(a.categoria))}
              renderItem={alerta => (
                <List.Item key={alerta.id}>
                  <List.Item.Meta
                    avatar={<Avatar style={{ backgroundColor: getTipoConfig(alerta.tipo).color }} icon={getTipoConfig(alerta.tipo).icon} />}
                    title={alerta.titulo}
                    description={`${alerta.paciente_nombre || 'Sin paciente'} - ${alerta.descripcion}`}
                  />
                  <Tag color={getEstadoConfig(alerta.estado).color}>{alerta.estado}</Tag>
                </List.Item>
              )}
            />
          )
        }
      ]}
    />
  </Card>
);

export default AlertasCategorias;
