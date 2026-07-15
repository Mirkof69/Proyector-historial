import React, { useState } from 'react';
import { Form } from 'antd';
import './HemorragiaObstetrica.css';
import {
  DatosHemorragia, ResultadoHemorragia, RegistroHemorragia,
  calcularHemorragia, getCausaTexto,
} from './hemorragiaObstetricaUtils';
import HemorragiaForm from './components/HemorragiaForm';
import HemorragiaResultado from './components/HemorragiaResultado';
import HemorragiaGraficas from './components/HemorragiaGraficas';

const HemorragiaObstetrica: React.FC = () => {
  const [form] = Form.useForm();
  const [resultado, setResultado] = useState<ResultadoHemorragia | null>(null);
  const [historial, setHistorial] = useState<RegistroHemorragia[]>([]);
  const [loading, setLoading] = useState(false);

  const onFinish = (valores: any) => {
    setLoading(true);

    const datos: DatosHemorragia = {
      frecuencia_cardiaca: valores.frecuencia_cardiaca,
      presion_sistolica: valores.presion_sistolica,
      presion_diastolica: valores.presion_diastolica,
      frecuencia_respiratoria: valores.frecuencia_respiratoria,
      temperatura: valores.temperatura,
      saturacion_o2: valores.saturacion_o2,
      perdida_estimada_ml: valores.perdida_estimada_ml,
      tiempo_minutos: valores.tiempo_minutos,
      causa_principal: valores.causa_principal,
      tono_uterino: valores.tono_uterino,
      placenta_completa: valores.placenta_completa ?? false,
      laceraciones: valores.laceraciones ?? false,
      coagulopatia: valores.coagulopatia ?? false,
      hemoglobina_inicial: valores.hemoglobina_inicial,
      hemoglobina_actual: valores.hemoglobina_actual,
      plaquetas: valores.plaquetas,
      fibrinogeno: valores.fibrinogeno
    };

    const res = calcularHemorragia(datos);
    setResultado(res);

    // Agregar al historial
    const nuevoRegistro: RegistroHemorragia = {
      fecha: new Date().toLocaleString('es-ES'),
      shock_index: res.shock_index,
      perdida_ml: valores.perdida_estimada_ml,
      gravedad: res.gravedad,
      causa: getCausaTexto(valores.causa_principal)
    };
    setHistorial(prev => [nuevoRegistro, ...prev]);

    setLoading(false);
  };

  return (
    <div className="hemorragia-obstetrica-page">
      <HemorragiaForm form={form} onFinish={onFinish} loading={loading} />

      {resultado && (
        <>
          <HemorragiaResultado resultado={resultado} />
          <HemorragiaGraficas resultado={resultado} form={form} historial={historial} />
        </>
      )}
    </div>
  );
};

export default HemorragiaObstetrica;
