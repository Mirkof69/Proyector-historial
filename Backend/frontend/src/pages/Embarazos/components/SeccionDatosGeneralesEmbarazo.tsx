import React from 'react';
import { Divider, Row, Col, Form, Select, Input, DatePicker, Alert, Card, Typography, Tag } from 'antd';
import type { FormInstance } from 'antd';
import dayjs from 'dayjs';
import { Paciente } from '../../../services/pacientesService';

const { Option } = Select;
const { Text } = Typography;

interface SeccionDatosGeneralesEmbarazoProps {
  form: FormInstance;
  pacientes: Paciente[];
  fppCalculada: string;
  edadGestacional: string;
  trimestreActual: number;
}

const SeccionDatosGeneralesEmbarazo: React.FC<SeccionDatosGeneralesEmbarazoProps> = ({
  form, pacientes, fppCalculada, edadGestacional, trimestreActual,
}) => (
  <>
    <Divider orientation="left">Informacion General</Divider>

    <Row gutter={16}>
      <Col span={12}>
        <Form.Item
          name="paciente"
          label="Paciente"
          rules={[{ required: true, message: 'Seleccione un paciente' }]}
        >
          <Select
            placeholder="Seleccione paciente"
            optionLabelProp="label"
            showSearch
            filterOption={(input, option) =>
              (option?.label as string ?? '').toLowerCase().includes(input.toLowerCase())
            }
          >
            {pacientes.map((p) => (
              <Option key={p.id} value={p.id} label={`${p.nombre} ${p.apellido_paterno}`}>
                {p.nombre} {p.apellido_paterno} - {p.id_clinico}
              </Option>
            ))}
          </Select>
        </Form.Item>
      </Col>

      <Col span={12}>
        <Form.Item
          name="numero_gesta"
          label="Numero de Gesta"
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
          <Input type="number" placeholder="1" min={1} />
        </Form.Item>
      </Col>
    </Row>

    <Divider orientation="left">Fechas y Calculos</Divider>

    <Row gutter={16}>
      <Col span={12}>
        <Form.Item
          name="fecha_ultima_menstruacion"
          label="Fecha Ultima Menstruacion"
          rules={[
            { required: true, message: 'Seleccione la fecha' },
            () => ({
              validator(_, value) {
                if (!value) {
                  return Promise.resolve();
                }

                const hoy = dayjs();
                const fumDate = dayjs(value);

                if (fumDate.isAfter(hoy)) {
                  return Promise.reject(new Error('La Fecha de Última Menstruación no puede estar en el futuro'));
                }

                const unAnioAtras = hoy.subtract(1, 'year');
                if (fumDate.isBefore(unAnioAtras)) {
                  return Promise.reject(new Error('La Fecha de Última Menstruación no puede ser mayor a 1 año atrás'));
                }

                return Promise.resolve();
              },
            }),
          ]}
          tooltip="Se calcularan automaticamente FPP y edad gestacional"
        >
          <DatePicker style={{ width: '100%' }} format="DD/MM/YYYY" placeholder="Seleccione fecha" />
        </Form.Item>
      </Col>

      <Col span={12}>
        <Form.Item
          name="fecha_probable_parto"
          label="Fecha Probable de Parto"
          tooltip="Se calcula automaticamente (FUM + 280 dias)"
        >
          <DatePicker style={{ width: '100%' }} format="DD/MM/YYYY" placeholder="Se completa automaticamente" disabled />
        </Form.Item>
      </Col>
    </Row>

    {fppCalculada && (
      <Alert message={`FPP Calculada: ${fppCalculada}`} type="success" showIcon style={{ marginBottom: 16 }} />
    )}

    {edadGestacional && (
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={12}>
          <Card>
            <Text strong>Edad Gestacional:</Text>
            <br />
            <Text>{edadGestacional}</Text>
          </Card>
        </Col>
        <Col span={12}>
          <Card>
            <Text strong>Trimestre Actual:</Text>
            <br />
            {trimestreActual ? (
              <Tag color={trimestreActual === 1 ? 'blue' : trimestreActual === 2 ? 'green' : 'orange'} style={{ fontSize: 14, padding: '4px 12px', marginTop: 4 }}>
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
