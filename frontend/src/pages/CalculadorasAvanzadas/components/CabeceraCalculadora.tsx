import React from 'react';
import { Typography } from 'antd';

const { Title } = Typography;

interface CabeceraCalculadoraProps {
  icono: React.ReactNode;
  titulo: React.ReactNode;
  descripcion: React.ReactNode;
  acciones?: React.ReactNode;
}

/** Encabezado de página del contrato: título 22/600, una línea de descripción y acciones a la derecha. */
const CabeceraCalculadora: React.FC<CabeceraCalculadoraProps> = ({ icono, titulo, descripcion, acciones }) => (
  <div className="calc-cabecera">
    <div className="calc-cabecera__texto">
      <Title level={2} className="calc-cabecera__titulo">
        <span className="calc-cabecera__icono">{icono}</span>
        {titulo}
      </Title>
      <p className="calc-cabecera__descripcion">{descripcion}</p>
    </div>
    {acciones && <div className="calc-cabecera__acciones">{acciones}</div>}
  </div>
);

export default CabeceraCalculadora;
