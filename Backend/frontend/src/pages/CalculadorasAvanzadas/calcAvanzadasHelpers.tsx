import React from 'react';
import {
  Card, Space, Divider, Alert, Statistic, Typography, Radio, Badge, Timeline,
  Table, Tooltip, Input,
} from 'antd';
import {
  CalculatorOutlined, CalendarOutlined, HeartOutlined, UserOutlined,
  MedicineBoxOutlined, WarningOutlined, CheckCircleOutlined, InfoCircleOutlined,
  LineChartOutlined, BulbOutlined, ExperimentOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import calculoHistorialService, { TipoCalculadora } from '../../services/calculoHistorialService';

const { Text, Paragraph } = Typography;

// Hoisted tab labels (static JSX - avoids recreation on every render)
export const tabEdadGestacional = (
  <Space>
    <CalendarOutlined />
    Edad Gestacional
  </Space>
);
export const tabBishop = (
  <Space>
    <MedicineBoxOutlined />
    Score de Bishop
  </Space>
);
export const tabIMC = (
  <Space>
    <UserOutlined />
    IMC
  </Space>
);
export const tabPreeclampsia = (
  <Space>
    <WarningOutlined />
    Riesgo Preeclampsia
  </Space>
);
export const tabDiabetesGestacional = (
  <Space>
    <LineChartOutlined />
    Diabetes Gestacional
  </Space>
);
export const tabILA = (
  <Space>
    <ExperimentOutlined />
    Índice Líquido Amniótico
  </Space>
);
export const tabPesoFetal = (
  <Space>
    <HeartOutlined />
    Peso Fetal
  </Space>
);
export const tabApgar = (
  <Space>
    <HeartOutlined />
    Score de Apgar
  </Space>
);

export interface ResultadoCalculo {
  valor: number | string;
  interpretacion: string;
  categoria: string;
  color: string;
  recomendaciones?: string[];
  alertas?: string[];
}

// ==========================================================================
// RESULTADO CARD COMPONENT (extracted from render-in-render)
// ==========================================================================
interface ResultadoCardProps {
  resultado: ResultadoCalculo;
}

export const guardarResultado = (tipo: TipoCalculadora, inputs: any, resultado: ResultadoCalculo) => {
  calculoHistorialService.crear({
    tipo_calculadora: tipo,
    inputs_json: inputs,
    resultado_json: resultado,
    resultado_resumen: typeof resultado.valor === 'string' ? resultado.valor : JSON.stringify(resultado.valor).slice(0, 250),
  });
};

export const ResultadoCard: React.FC<ResultadoCardProps> = ({ resultado }) => (
  <Card
    style={{
      marginTop: 24,
      borderColor: resultado.color,
      borderWidth: 2,
    }}
  >
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Statistic
        title="Resultado"
        value={resultado.valor}
        valueStyle={{ color: resultado.color, fontSize: 36 }}
        prefix={<CalculatorOutlined />}
      />

      <Alert
        message={resultado.categoria}
        description={resultado.interpretacion}
        type={
          resultado.color === 'green'
            ? 'success'
            : resultado.color === 'red'
              ? 'error'
              : 'warning'
        }
        showIcon
      />

      {resultado.alertas && resultado.alertas.length > 0 && (
        <Alert
          message="⚠️ ALERTAS IMPORTANTES"
          description={
            <ul style={{ marginBottom: 0, paddingLeft: 20 }}>
              {resultado.alertas.map((alerta) => (
                <li key={`alerta-${alerta}`}>
                  <strong>{alerta}</strong>
                </li>
              ))}
            </ul>
          }
          type="error"
          showIcon
          icon={<WarningOutlined />}
        />
      )}

      {resultado.recomendaciones && resultado.recomendaciones.length > 0 && (
        <Card
          type="inner"
          title={
            <Space>
              <BulbOutlined style={{ color: '#faad14' }} />
              Recomendaciones
              <Badge count={resultado.recomendaciones.length} showZero style={{ backgroundColor: '#52c41a' }} />
            </Space>
          }
        >
          <Timeline
            items={resultado.recomendaciones.map((rec) => ({
              key: `rec-${rec}`,
              color: resultado.color,
              dot: <CheckCircleOutlined />,
              children: (
                <Tooltip title="Recomendación basada en guías clínicas">
                  <Text>{rec}</Text>
                </Tooltip>
              )
            }))}
          />
        </Card>
      )}

      <Card type="inner">
        <Space direction="vertical" style={{ width: '100%' }}>
          <div>
            <InfoCircleOutlined style={{ marginRight: 8, color: '#1890ff' }} />
            <Text strong>Notas del Cálculo</Text>
          </div>
          <Paragraph type="secondary">
            Este resultado ha sido calculado usando fórmulas médicas estándar.
            Siempre consulte con un profesional de salud para interpretación clínica.
          </Paragraph>

          <Divider>Guardar Preferencias</Divider>
          <Radio.Group defaultValue="metric">
            <Radio value="metric">Sistema Métrico</Radio>
            <Radio value="imperial">Sistema Imperial</Radio>
          </Radio.Group>

          <Divider>Agregar Notas</Divider>
          <Input.TextArea
            rows={2}
            placeholder="Notas adicionales sobre este cálculo..."
          />
        </Space>
      </Card>

      <Card type="inner" title="Historial Reciente">
        <Table
          size="small"
          dataSource={[
            { key: '1', fecha: dayjs().format('DD/MM/YYYY HH:mm'), valor: resultado.valor, categoria: resultado.categoria },
          ]}
          columns={[
            { title: 'Fecha', dataIndex: 'fecha', key: 'fecha' },
            { title: 'Valor', dataIndex: 'valor', key: 'valor' },
            {
              title: 'Categoría',
              dataIndex: 'categoria',
              key: 'categoria',
              render: (cat: string) => <Badge status="processing" text={cat} />
            },
          ]}
          pagination={false}
        />
      </Card>
    </Space>
  </Card>
);
