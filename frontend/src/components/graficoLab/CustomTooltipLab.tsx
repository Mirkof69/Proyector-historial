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
          backgroundColor: 'var(--color-superficie)',
          padding: '10px',
          border: '1px solid var(--color-borde)',
          borderRadius: 'var(--radio)',
          boxShadow: 'var(--sombra-flotante)',
        }}
      >
        <p style={{ margin: 0, fontWeight: 'bold' }}>
          {data.fechaCompleta}
        </p>
        <p style={{ margin: '5px 0 0 0', color: 'var(--color-primario)' }}>
          Valor: <strong>{data.valor?.toFixed(2)} {unidad}</strong>
        </p>
        {valorMinimo && valorMaximo && (
          <p style={{ margin: '5px 0 0 0', fontSize: '12px', color: 'var(--color-texto-2)' }}>
            Rango: {valorMinimo} - {valorMaximo} {unidad}
          </p>
        )}
      </div>
    );
  }
  return null;
};

export default CustomTooltipLab;
