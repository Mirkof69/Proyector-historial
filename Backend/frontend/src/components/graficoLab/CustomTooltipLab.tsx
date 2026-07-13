import React from 'react';

interface CustomTooltipLabProps {
  active?: boolean;
  payload?: any[];
  unidad?: string;
  valorMinimo?: number;
  valorMaximo?: number;
}

const CustomTooltipLab = ({ active, payload, unidad, valorMinimo, valorMaximo }: CustomTooltipLabProps) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div
        style={{
          backgroundColor: 'white',
          padding: '10px',
          border: '1px solid #d9d9d9',
          borderRadius: '4px',
        }}
      >
        <p style={{ margin: 0, fontWeight: 'bold' }}>
          {data.fechaCompleta}
        </p>
        <p style={{ margin: '5px 0 0 0', color: '#1890ff' }}>
          Valor: <strong>{data.valor?.toFixed(2)} {unidad}</strong>
        </p>
        {valorMinimo && valorMaximo && (
          <p style={{ margin: '5px 0 0 0', fontSize: '12px', color: '#8c8c8c' }}>
            Rango: {valorMinimo} - {valorMaximo} {unidad}
          </p>
        )}
      </div>
    );
  }
  return null;
};

export default CustomTooltipLab;
