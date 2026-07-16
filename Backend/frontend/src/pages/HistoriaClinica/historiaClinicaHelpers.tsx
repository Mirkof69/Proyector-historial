import React from 'react';
import { List, Typography, Tag, Progress, Alert, Button, Divider } from 'antd';
import { CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';

const { Text } = Typography;

export const verticalDivider = <Divider type="vertical" />;

export const formatAntecedente = (valor: any): string => {
    if (!valor) return 'No registra';
    if (typeof valor === 'string') return valor;
    if (typeof valor === 'object') {
      if (valor.resumen_enfermedades) return valor.resumen_enfermedades;
      if (valor.otras_enfermedades) return valor.otras_enfermedades;
      return 'Ver sección de antecedentes detallados';
    }
    return String(valor);
};

export const formatRiesgoTick = (v: number) => v === 1 ? 'BAJO' : v === 2 ? 'ALTO' : 'MUY ALTO';

// Constantes de ejes para gráficos recharts
export const FCF_DOMAIN = [100, 180];
export const FCF_LABEL = { value: 'LPM', angle: -90, position: 'insideLeft' };
export const HGB_DOMAIN = [8, 16];
export const HGB_LABEL = { value: 'g/dL', angle: -90, position: 'insideLeft' };
export const HCT_DOMAIN = [25, 50];
export const HCT_LABEL = { value: '%', angle: -90, position: 'insideLeft' };
export const RIESGO_DOMAIN = [0, 4];
export const RIESGO_TICKS = [1, 2, 3];

interface ProtocoloEmbarazoItemProps {
  protocolo: any;
}
export const ProtocoloEmbarazoItem: React.FC<ProtocoloEmbarazoItemProps> = ({ protocolo }) => (
  <List.Item>
    <List.Item.Meta
      avatar={
        protocolo.cumplido ? (
          <CheckCircleOutlined style={{ fontSize: 24, color: '#52c41a' }} />
        ) : (
          <CloseCircleOutlined style={{ fontSize: 24, color: '#ff4d4f' }} />
        )
      }
      title={protocolo.nombre}
      description={
        <>
          <Text type="secondary">{protocolo.descripcion}</Text>
          <br />
          <Tag color="blue">
            {protocolo.semanas_inicio}-{protocolo.semanas_fin} semanas
          </Tag>
          {protocolo.examenes_requeridos.map((examen: string) => (
            <Tag key={examen}>{examen}</Tag>
          ))}
        </>
      }
    />
    <div>
      <Progress
        type="circle"
        percent={protocolo.cumplido ? 100 : 0}
        width={50}
        status={protocolo.cumplido ? 'success' : 'exception'}
      />
    </div>
  </List.Item>
);

interface TendenciaLaboratorioItemProps {
  tendencia: any;
}
export const TendenciaLaboratorioItem: React.FC<TendenciaLaboratorioItemProps> = ({ tendencia }) => (
  <List.Item>
    <Text strong>{tendencia.examen}: </Text>
    <Tag color={tendencia.tendencia === 'MEJORANDO' ? 'green' : tendencia.tendencia === 'EMPEORANDO' ? 'red' : 'blue'}>
      {tendencia.tendencia}
    </Tag>
  </List.Item>
);

interface AlertaClinicaItemProps {
  alerta: any;
  onResuelta: (id: string) => void;
}
export const AlertaClinicaItem: React.FC<AlertaClinicaItemProps> = ({ alerta, onResuelta }) => (
  <List.Item>
    <Alert
      message={`${alerta.categoria} - Prioridad: ${alerta.prioridad}`}
      description={
        <>
          {alerta.mensaje}
          <br />
          <Text type="secondary">{dayjs(alerta.fecha_generacion).format('DD/MM/YYYY')}</Text>
          {alerta.acciones_recomendadas && alerta.acciones_recomendadas.length > 0 && (
            <>
              <br />
              <Text strong>Acciones recomendadas:</Text>
              <ul style={{ marginTop: 4, marginBottom: 0 }}>
                {alerta.acciones_recomendadas.map((accion: string) => (
                  <li key={accion}><Text type="secondary">{accion}</Text></li>
                ))}
              </ul>
            </>
          )}
        </>
      }
      type={alerta.tipo === 'ERROR' ? 'error' : 'warning'}
      showIcon
      style={{ width: '100%' }}
      action={
        <Button
          size="small"
          type="text"
          onClick={() => onResuelta(alerta.id)}
        >
          Marcar como resuelta
        </Button>
      }
    />
  </List.Item>
);

interface RiesgoPreeclampsiaItemProps {
  item: string;
}
export const RiesgoPreeclampsiaItem: React.FC<RiesgoPreeclampsiaItemProps> = ({ item }) => (
  <List.Item>
    <CheckCircleOutlined style={{ color: '#1890ff', marginRight: 8 }} />
    {item}
  </List.Item>
);

interface RiskFactorItemProps {
  item: string;
}
export const RiskFactorItem: React.FC<RiskFactorItemProps> = React.memo(({ item }) => (
  <List.Item>
    <Text>{item}</Text>
  </List.Item>
));
