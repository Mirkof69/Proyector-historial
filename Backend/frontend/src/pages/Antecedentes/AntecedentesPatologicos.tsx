import React, { useState, useEffect, useCallback } from 'react';
import { Card, Table, Tag, Button, Space, Typography, Spin } from 'antd';
import { ReloadOutlined, WarningOutlined } from '@ant-design/icons';
import { antecedentesService, AntecedentePatologico } from '../../services/antecedentesService';

const { Text } = Typography;

const AntecedentesPatologicos: React.FC = () => {
  const [antecedentes, setAntecedentes] = useState<AntecedentePatologico[]>([]);
  const [loading, setLoading] = useState(false);

  const cargarAntecedentes = useCallback(async () => {
    setLoading(true);
    try {
      const data = await antecedentesService.getPatologicos();
      setAntecedentes(Array.isArray(data) ? data : []);
    } catch {
      setAntecedentes([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    cargarAntecedentes();
  }, [cargarAntecedentes]);

  const columns = [
    { title: 'Paciente', key: 'paciente', render: (_: unknown, r: AntecedentePatologico) => r.paciente_info?.nombre_completo || `ID: ${r.paciente}` },
    {
      title: 'Tipo', dataIndex: 'tipo', key: 'tipo',
      render: (v: string) => <Tag color={v === 'personal' ? 'blue' : 'purple'}>{v === 'personal' ? 'Personal' : 'Heredofamiliar'}</Tag>,
    },
    { title: 'Diabetes', dataIndex: 'diabetes', key: 'diabetes', render: (v: boolean) => v ? <Tag color="orange">Sí</Tag> : 'No' },
    { title: 'Hipertensión', dataIndex: 'hipertension', key: 'hipertension', render: (v: boolean) => v ? <Tag color="red">Sí</Tag> : 'No' },
    { title: 'Alergias', dataIndex: 'tiene_alergias', key: 'alergias', render: (v: boolean) => v ? <Tag color="magenta">Sí</Tag> : 'No' },
    { title: 'Asma', dataIndex: 'asma', key: 'asma', render: (v: boolean) => v ? <Tag color="cyan">Sí</Tag> : 'No' },
    {
      title: 'Riesgo', key: 'riesgo',
      render: (_: unknown, r: AntecedentePatologico) => r.tiene_factores_riesgo_calculado
        ? <Tag color="red" icon={<WarningOutlined />}>Alto</Tag>
        : <Tag color="green">Bajo</Tag>,
    },
  ];

  return (
    <Card
      title={<span><WarningOutlined style={{ color: '#faad14', marginRight: 8 }} />Antecedentes Patológicos</span>}
      extra={<Button icon={<ReloadOutlined />} onClick={cargarAntecedentes} loading={loading}>Recargar</Button>}
    >
      <Spin spinning={loading}>
        <Table
          columns={columns}
          dataSource={antecedentes}
          rowKey="id"
          pagination={{ pageSize: 20 }}
          locale={{ emptyText: 'No hay antecedentes patológicos registrados' }}
        />
      </Spin>
    </Card>
  );
};

export default AntecedentesPatologicos;
