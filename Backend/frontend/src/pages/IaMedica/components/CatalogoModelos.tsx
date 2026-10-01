import React from 'react';
import { Alert, Table, Tag, Typography } from 'antd';
import { ModeloCatalogo } from '../../../services/iaMedicaService';

const { Text } = Typography;

/**
 * Los modelos de IA del sistema con la métrica que se midió DE VERDAD en datos
 * que no vieron (ia_medica/services/catalogo_modelos.py). Si una red no está
 * disponible no se muestra ningún número: antes esta lista traía exactitudes
 * fijas inventadas para redes que no existían.
 */
const CatalogoModelos: React.FC<{ modelos: ModeloCatalogo[] }> = ({ modelos }) => (
  <>
    <Alert type="info" showIcon style={{ marginBottom: 12 }}
      message="Cada métrica se midió en pacientes o registros que el modelo no vio al entrenar. Son herramientas de apoyo: el diagnóstico lo hace el médico." />
    <Table
      rowKey="codigo"
      size="small"
      pagination={false}
      dataSource={modelos}
      scroll={{ x: 760 }}
      columns={[
        { title: 'Modelo', dataIndex: 'nombre', render: (n: string, m: ModeloCatalogo) => (
          <><Text strong>{n}</Text><br /><Text type="secondary">{m.tipo}{m.version ? ` · v${m.version}` : ''}</Text></>) },
        { title: 'Estado', dataIndex: 'disponible', width: 120,
          render: (d: boolean) => (d ? <Tag color="green">Disponible</Tag> : <Tag>No disponible</Tag>) },
        { title: 'Métrica medida', dataIndex: 'metrica_principal', render: (t: string | null) => t ?? <Text type="secondary">—</Text> },
        { title: 'Datos', dataIndex: 'datos_reales', width: 120,
          render: (r: boolean) => (r ? <Tag color="blue">Reales</Tag> : <Tag color="orange">Simulados</Tag>) },
      ]}
    />
  </>
);

export default CatalogoModelos;
