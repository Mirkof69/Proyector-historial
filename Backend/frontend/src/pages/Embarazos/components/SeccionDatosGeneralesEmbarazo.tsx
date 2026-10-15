import React from 'react';
import { Divider, Row, Col, Form, InputNumber, DatePicker, Alert, Card, Typography, Tag } from 'antd';
import type { FormInstance } from 'antd';
import dayjs from 'dayjs';
import { PacienteSelect } from '../../../components/clinico/SelectoresClinicos';

const { Text } = Typography;

interface SeccionDatosGeneralesEmbarazoProps {
  form: FormInstance;
  fppCalculada: string;
  edadGestacional: string;
  trimestreActual: number;
}

const SeccionDatosGeneralesEmbarazo: React.FC<SeccionDatosGeneralesEmbarazoProps> = ({
  form, fppCalculada, edadGestacional, trimestreActual,
}) => (
  <>
    <Divider orientation="left">Informacion General</Divider>

    <Row gutter={16}>
      <Col xs={24} md={12}>
        <Form.Item
          name="paciente"
          label="Paciente"
          rules={[{ required: true, message: 'Seleccione un paciente' }]}
        >
          <PacienteSelect />
        </Form.Item>
      </Col>

      <Col xs={24} md={12}>
        <Form.Item
          name="numero_gesta"
          label="Numero de Gesta"
          tooltip="Se calcula solo: partos + abortos + 1 (este embarazo)"
          rules={[
            { required: true, message: 'Ingrese numero de gesta' },
            { type: 'number', min: 1, message: 'Debe ser numero positivo' },
            () => ({
              validator(_, value) {
                const numPara = form.getFieldValue('numero_para') || 0;
                const numAbortos = form.getFieldValue('numero_abortos') || 0;

                if (value && numPara > value) {
                  return Promise.reject(new Error(`El número de partos (${numPara}) no puede ser mayor que gestas (${value})`));
                }

                const minGesta = numPara + numAbortos;
                if (value && value < minGesta) {
                  return Promise.reject(new Error(`Gestas (${value}) debe ser al menos ${minGesta} (Partos ${numPara} + Abortos ${numAbortos})`));
                }

                return Promise.resolve();
              },
            }),
          ]}
        >
          {/* InputNumber (no Input type="number"): el HTML nativo emite STRING
              y la regla type:'number' rechazaba CUALQUIER valor tecleado —
              era imposible crear un embarazo desde este formulario. */}
          <InputNumber className="u-ancho" min={1} disabled aria-readonly />
        </Form.Item>
      </Col>
    </Row>

    <Divider orientation="left">Fechas y Calculos</Divider>

    <Row gutter={16}>
      <Col xs={24} md={12}>
        <Form.Item
          name="fecha_ultima_menstruacion"
          label="Fecha Ultima Menstruacion"
          rules={[
            { required: true, message: 'Seleccione la fecha' },
            ({ getFieldValue, isFieldTouched }) => ({
              validator(_, value) {
                if (!value) {
                  return Promise.resolve();
                }

                const hoy = dayjs();
                const fumDate = dayjs(value);

                if (fumDate.isAfter(hoy)) {
                  return Promise.reject(new Error('La Fecha de Última Menstruación no puede estar en el futuro'));
                }

                // Mismo criterio que el backend: solo un embarazo en curso con
                // la FUM recién escrita no puede pasar de 44 semanas. Los
                // embarazos terminados se pueden registrar y editar.
                const enCurso = (getFieldValue('estado') ?? 'activo') === 'activo';
                if (enCurso && isFieldTouched('fecha_ultima_menstruacion') && hoy.diff(fumDate, 'day') > 44 * 7) {
                  return Promise.reject(new Error('Un embarazo en curso no pasa de 44 semanas: revise la fecha o regístrelo como finalizado'));
                }

                return Promise.resolve();
              },
            }),
          ]}
          tooltip="Se calcularan automaticamente FPP y edad gestacional"
        >
          <DatePicker className="u-ancho" format="DD/MM/YYYY" placeholder="Seleccione fecha" />
        </Form.Item>
      </Col>

      <Col xs={24} md={12}>
        <Form.Item
          name="fecha_probable_parto"
          label="Fecha Probable de Parto"
          tooltip="Se calcula automaticamente (FUM + 280 dias)"
        >
          <DatePicker className="u-ancho" format="DD/MM/YYYY" placeholder="Se completa automaticamente" disabled />
        </Form.Item>
      </Col>
    </Row>

    {fppCalculada && (
      <Alert message={`FPP Calculada: ${fppCalculada}`} type="success" showIcon className="u-mb-4" />
    )}

    {edadGestacional && (
      <Row gutter={16} className="u-mb-4">
        <Col xs={24} md={12}>
          <Card>
            <Text strong>Edad Gestacional:</Text>
            <br />
            <Text>{edadGestacional}</Text>
          </Card>
        </Col>
        <Col xs={24} md={12}>
          <Card>
            <Text strong>Trimestre Actual:</Text>
            <br />
            {trimestreActual ? (
              <Tag color={trimestreActual === 1 ? 'processing' : trimestreActual === 2 ? 'success' : 'warning'} className="u-t-base u-p-etiqueta u-mt-1">
                Trimestre {trimestreActual}
              </Tag>
            ) : (
              <Text>-</Text>
            )}
          </Card>
        </Col>
      </Row>
    )}
  </>
);

export default SeccionDatosGeneralesEmbarazo;
