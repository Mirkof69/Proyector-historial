import React from 'react';
import { Space, Input, InputNumber, Typography, Tag } from 'antd';
import { ValorReferencia, ResultadoLaboratorio } from '../../../services/laboratorioService';

const { Text } = Typography;

/**
 * Columnas de la tabla de resultados del examen de laboratorio.
 * Extraído de FormularioLaboratorio. Recibe los datos + el handler de cambio.
 */
export const buildColumnasResultados = (
  valoresReferencia: ValorReferencia[],
  resultados: Partial<ResultadoLaboratorio>[],
  onResultadoChange: (index: number, field: string, value: any) => void,
) => [
  {
    title: 'Parámetro',
    key: 'parametro',
    render: (_: any, __: any, index: number) => {
      const vr = valoresReferencia.find((v) => v.id === resultados[index]?.valor_referencia);
      return vr?.parametro || '-';
    },
  },
  {
    title: 'Valor',
    key: 'valor',
    render: (_: any, __: any, index: number) => {
      const vr = valoresReferencia.find((v) => v.id === resultados[index]?.valor_referencia);
      return (
        <Space>
          {vr?.unidad === 'cualitativo' ? (
            <Input
              placeholder="Ej: Negativo"
              value={resultados[index]?.valor_texto}
              onChange={(e) => onResultadoChange(index, 'valor_texto', e.target.value)}
            />
          ) : (
            <InputNumber
              style={{ width: 120 }}
              placeholder="Valor"
              value={resultados[index]?.valor_numerico}
              onChange={(value) => onResultadoChange(index, 'valor_numerico', value)}
            />
          )}
          {vr?.unidad !== 'cualitativo' && <Text type="secondary">{vr?.unidad}</Text>}
        </Space>
      );
    },
  },
  {
    title: 'Rango Normal',
    key: 'rango',
    render: (_: any, __: any, index: number) => {
      const vr = valoresReferencia.find((v) => v.id === resultados[index]?.valor_referencia);
      return vr?.rango_normal || '-';
    },
  },
  {
    title: 'Estado',
    key: 'estado',
    render: (_: any, __: any, index: number) => {
      const resultado = resultados[index];
      if (resultado?.es_critico) {
        return <Tag color="red">CRÍTICO</Tag>;
      }
      if (!resultado?.es_normal) {
        return <Tag color="orange">ANORMAL</Tag>;
      }
      return <Tag color="green">NORMAL</Tag>;
    },
  },
  {
    title: 'Observaciones',
    key: 'observaciones',
    render: (_: any, __: any, index: number) => (
      <Input
        placeholder="Observaciones"
        value={resultados[index]?.observaciones}
        onChange={(e) => onResultadoChange(index, 'observaciones', e.target.value)}
      />
    ),
  },
];
