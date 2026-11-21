import React, { useState, useCallback } from 'react';
import { Form, Row, Col } from 'antd';
import { MedicineBoxOutlined } from '@ant-design/icons';
import {
  calcularDosis, DatosPaciente, ResultadoDosis, RegistroDosis,
} from './dosisMedicamentos/dosisMedicamentosUtils';
import FormDosis from './dosisMedicamentos/FormDosis';
import ResultadoDosisPanel from './dosisMedicamentos/ResultadoDosisPanel';
import AnalisisDosis from './dosisMedicamentos/AnalisisDosis';
import './calculadoraAvanzada.css';
import CabeceraCalculadora from './components/CabeceraCalculadora';

const DosisMedicamentos: React.FC = () => {
  const [form] = Form.useForm();
  const [resultado, setResultado] = useState<ResultadoDosis | null>(null);
  const [historial, setHistorial] = useState<RegistroDosis[]>([]);

  const tooltipFormatter = useCallback((value: any) => value ? `${value} ${resultado?.unidad ?? ''}` : '', [resultado?.unidad]);

  const onFinish = (valores: DatosPaciente) => {
    const res = calcularDosis(valores);
    setResultado(res);

    const nuevoRegistro: RegistroDosis = {
      ...res,
      fecha: new Date().toLocaleString('es-ES'),
      peso: valores.peso
    };
    setHistorial(prev => [nuevoRegistro, ...prev]);
  };

  return (
    <div className="calc-pagina dosis-medicamentos-page">
      <CabeceraCalculadora
        icono={<MedicineBoxOutlined />}
        titulo="Calculadora de Dosis Obstétricas"
        descripcion="Cálculo de dosis de 16 medicamentos obstétricos con ajuste por peso, función renal y alertas de seguridad"
      />

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={10}>
          <FormDosis form={form} onFinish={onFinish} />
        </Col>

        <Col xs={24} lg={14}>
          {resultado && <ResultadoDosisPanel resultado={resultado} />}
        </Col>
      </Row>

      {resultado && (
        <AnalisisDosis
          resultado={resultado}
          historial={historial}
          tooltipFormatter={tooltipFormatter}
        />
      )}
    </div>
  );
};

export default DosisMedicamentos;
