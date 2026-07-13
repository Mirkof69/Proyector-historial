import React, { useState, useEffect, useCallback } from 'react';
import { Card, Table, Tag, Button, Space, Typography, Spin } from 'antd';
import { ReloadOutlined, WomanOutlined } from '@ant-design/icons';
import { antecedentesService, AntecedenteGinecoObstetrico } from '../../services/antecedentesService';

const { Text } = Typography;

const AntecedentesGinecoObstetricos: React.FC = () => {
  const [antecedentes, setAntecedentes] = useState<AntecedenteGinecoObstetrico[]>([]);
  const [loading, setLoading] = useState(false);

  const cargarAntecedentes = useCallback(async () => {
    setLoading(true);
    try {
      const data = await antecedentesService.getGinecoObstetricos();
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
    { title: 'Paciente', key: 'paciente', render: (_: unknown, r: AntecedenteGinecoObstetrico) => r.paciente_info?.nombre_completo || `ID: ${r.paciente}` },
    {
      title: 'Fórmula Obstétrica', key: 'formula',
      render: (_: unknown, r: AntecedenteGinecoObstetrico) => (
        <Tag color="blue">{r.formula_obstetrica || `G${r.gestas ?? 0}P${r.partos ?? 0}A${r.abortos ?? 0}C${r.cesareas ?? 0}`}</Tag>
      ),
    },
    { title: 'Gestas', dataIndex: 'gestas', key: 'gestas', render: (v: number) => v ?? '-' },
    { title: 'Partos', dataIndex: 'partos', key: 'partos', render: (v: number) => v ?? '-' },
    { title: 'Abortos', dataIndex: 'abortos', key: 'abortos', render: (v: number) => v ?? '-' },
    { title: 'Cesáreas', dataIndex: 'cesareas', key: 'cesareas', render: (v: number) => v ?? '-' },
    { title: 'Hijos Vivos', dataIndex: 'hijos_vivos', key: 'hijos_vivos', render: (v: number) => v ?? '-' },
    {
      title: 'Ciclos', dataIndex: 'ciclos_menstruales', key: 'ciclos',
      render: (v: string) => {
        const colors: Record<string, string> = { regular: 'green', irregular: 'orange', amenorrea: 'red' };
        return v ? <Tag color={colors[v] || 'default'}>{v}</Tag> : '-';
      },
    },
  ];

  return (
    <Card
      title={<span><WomanOutlined style={{ color: '#eb2f96', marginRight: 8 }} />Antecedentes Gineco-Obstétricos</span>}
      extra={<Button icon={<ReloadOutlined />} onClick={cargarAntecedentes} loading={loading}>Recargar</Button>}
    >
      <Spin spinning={loading}>
        <Table
          columns={columns}
          dataSource={antecedentes}
          rowKey="id"
          pagination={{ pageSize: 20 }}
          locale={{ emptyText: 'No hay antecedentes gineco-obstétricos registrados' }}
        />
      </Spin>
    </Card>
  );
};

export default AntecedentesGinecoObstetricos;
