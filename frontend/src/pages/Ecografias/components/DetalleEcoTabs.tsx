import React from 'react';
import { Card, Descriptions, Tag, Alert, Row, Col, Statistic, Collapse, Typography, Tabs, Empty } from 'antd';
import {
  FileImageOutlined, HeartOutlined, InfoCircleOutlined, LineChartOutlined, MedicineBoxOutlined,
} from '@ant-design/icons';
import { Ecografia } from '../../../services/ecografiasService';
import { useAuth } from '../../../hooks/useAuth';
import PrediccionPesoNacer from './PrediccionPesoNacer';
import RedesEcografiaReal, { ImagenGuardada } from '../../IaMedica/components/RedesEcografiaReal';

const { Text, Paragraph } = Typography;

interface DetalleEcoTabsProps {
  ecografia: Ecografia;
}

const DetalleEcoTabs: React.FC<DetalleEcoTabsProps> = ({ ecografia }) => {
  const { user } = useAuth();
  // El endpoint solo atiende a médicos y administradores.
  const puedePredecir = user?.rol === 'medico' || user?.rol === 'administrador';
  const imagenesGuardadas: ImagenGuardada[] = (ecografia.imagenes ?? [])
    .map((img, i) => ({
      url: typeof img.imagen === 'string' ? img.imagen : (img.url_imagen ?? ''),
      nombre: img.titulo || img.descripcion || `Imagen ${i + 1}`,
    }))
    .filter((img) => img.url);
  return (
  <Card className="u-mb-4">
    <Tabs
      defaultActiveKey="biometria"
      items={[
        {
          key: 'biometria',
          label: (
            <span>
              <LineChartOutlined />
              Biometría Fetal
            </span>
          ),
          children: ecografia.biometria ? (
            <>
              <Row gutter={[16, 16]}>
                {ecografia.biometria.diametro_biparietal && (
                  <Col xs={24} sm={12} md={8}>
                    <Statistic
                      title="DBP"
                      value={ecografia.biometria.diametro_biparietal}
                      suffix="mm"
                    />
                  </Col>
                )}
                {ecografia.biometria.circunferencia_cefalica && (
                  <Col xs={24} sm={12} md={8}>
                    <Statistic
                      title="CC"
                      value={ecografia.biometria.circunferencia_cefalica}
                      suffix="mm"
                    />
                  </Col>
                )}
                {ecografia.biometria.circunferencia_abdominal && (
                  <Col xs={24} sm={12} md={8}>
                    <Statistic
                      title="CA"
                      value={ecografia.biometria.circunferencia_abdominal}
                      suffix="mm"
                    />
                  </Col>
                )}
                {ecografia.biometria.longitud_femur && (
                  <Col xs={24} sm={12} md={8}>
                    <Statistic
                      title="LF"
                      value={ecografia.biometria.longitud_femur}
                      suffix="mm"
                    />
                  </Col>
                )}
                {ecografia.biometria.peso_fetal_estimado && (
                  <Col xs={24} sm={12} md={8}>
                    <Statistic
                      title="Peso Fetal Estimado"
                      value={ecografia.biometria.peso_fetal_estimado}
                      suffix="g"
                                            prefix={<HeartOutlined />}
                    />
                  </Col>
                )}
                {ecografia.biometria.percentil_peso && (
                  <Col xs={24} sm={12} md={8}>
                    <Statistic
                      title="Percentil de Peso"
                      value={ecografia.biometria.percentil_peso}
                      suffix="%"
                    />
                  </Col>
                )}
              </Row>
              {ecografia.biometria.evaluacion_crecimiento && (
                <Alert
                  message={ecografia.biometria.evaluacion_crecimiento}
                  type={ecografia.biometria.evaluacion_crecimiento?.includes('Normal') ? 'success' : 'warning'}
                  showIcon
                  className="u-mt-4"
                />
              )}
              {puedePredecir && ecografia.id && <PrediccionPesoNacer ecografiaId={ecografia.id} />}
            </>
          ) : (
            <Empty description="No hay datos de biometría" />
          ),
        },
        {
          key: 'anatomia',
          label: (
            <span>
              <MedicineBoxOutlined />
              Anatomía Fetal
            </span>
          ),
          children: ecografia.anatomia ? (
            <>
              <Collapse
                defaultActiveKey={['organos']}
                items={[
                  {
                    key: 'organos',
                    label: 'Evaluación de Órganos',
                    children: (
                      <Descriptions column={{ xs: 1, sm: 2 }} bordered size="small">
                        <Descriptions.Item label="Cráneo">
                          <Tag color={ecografia.anatomia.craneo_normal ? 'success' : 'error'}>{ecografia.anatomia.craneo_normal ? 'Normal' : 'Anormal'}</Tag>
                        </Descriptions.Item>
                        <Descriptions.Item label="Cerebro">
                          <Tag color={ecografia.anatomia.cerebro_normal ? 'success' : 'error'}>{ecografia.anatomia.cerebro_normal ? 'Normal' : 'Anormal'}</Tag>
                        </Descriptions.Item>
                        <Descriptions.Item label="Corazón">
                          <Tag color={ecografia.anatomia.corazon_normal ? 'success' : 'error'}>{ecografia.anatomia.corazon_normal ? 'Normal' : 'Anormal'}</Tag>
                        </Descriptions.Item>
                        <Descriptions.Item label="Columna">
                          <Tag color={ecografia.anatomia.columna_normal ? 'success' : 'error'}>{ecografia.anatomia.columna_normal ? 'Normal' : 'Anormal'}</Tag>
                        </Descriptions.Item>
                        <Descriptions.Item label="Extremidades Superiores">
                          <Tag color={ecografia.anatomia.extremidades_superiores_normales ? 'success' : 'error'}>{ecografia.anatomia.extremidades_superiores_normales ? 'Normal' : 'Anormal'}</Tag>
                        </Descriptions.Item>
                        <Descriptions.Item label="Extremidades Inferiores">
                          <Tag color={ecografia.anatomia.extremidades_inferiores_normales ? 'success' : 'error'}>{ecografia.anatomia.extremidades_inferiores_normales ? 'Normal' : 'Anormal'}</Tag>
                        </Descriptions.Item>
                        {ecografia.anatomia.sexo_fetal && (
                          <Descriptions.Item label="Sexo Fetal" span={2}>
                            <Tag>
                              {ecografia.anatomia.sexo_fetal.toUpperCase()}
                            </Tag>
                          </Descriptions.Item>
                        )}
                      </Descriptions>
                    ),
                  },
                ]}
              />
              {ecografia.anatomia.evaluacion_anatomica && (
                <Collapse
                  className="u-mt-4"
                  items={[
                    {
                      key: '1',
                      label: 'Evaluación Anatómica Completa',
                      children: (
                        <Alert
                          message={ecografia.anatomia.evaluacion_anatomica}
                          type={ecografia.anatomia.evaluacion_anatomica?.includes('normal') ? 'success' : 'warning'}
                          showIcon
                        />
                      ),
                    },
                  ]}
                />
              )}
            </>
          ) : (
            <Empty description="No hay datos de anatomía" />
          ),
        },
        {
          key: 'anexos',
          label: (
            <span>
              <InfoCircleOutlined />
              Anexos Fetales
            </span>
          ),
          children: ecografia.anexos ? (
            <>
              <Descriptions column={2} bordered>
                {ecografia.anexos.placenta_localizacion && (
                  <Descriptions.Item label="Placenta - Localización">
                    {ecografia.anexos.placenta_localizacion}
                  </Descriptions.Item>
                )}
                {ecografia.anexos.numero_vasos_cordon && (
                  <Descriptions.Item label="Vasos del Cordón">
                    {ecografia.anexos.numero_vasos_cordon} vasos
                  </Descriptions.Item>
                )}
                {ecografia.indice_liquido_amniotico && (
                  <Descriptions.Item label="ILA">
                    {ecografia.indice_liquido_amniotico} cm
                  </Descriptions.Item>
                )}
                {ecografia.estado_liquido_amniotico && (
                  <Descriptions.Item label="Estado Líquido">
                    <Tag>{ecografia.estado_liquido_amniotico}</Tag>
                  </Descriptions.Item>
                )}
              </Descriptions>
              {ecografia.anexos.evaluacion_cordon && (
                <Alert
                  message={ecografia.anexos.evaluacion_cordon}
                  type={ecografia.anexos.evaluacion_cordon?.includes('Normal') ? 'success' : 'warning'}
                  showIcon
                  className="u-mt-4"
                />
              )}
              {puedePredecir && ecografia.id && <PrediccionPesoNacer ecografiaId={ecografia.id} />}
            </>
          ) : (
            <Empty description="No hay datos de anexos" />
          ),
        },
        {
          key: 'ia-medida',
          label: (
            <span>
              <MedicineBoxOutlined />
              IA medida
            </span>
          ),
          children: imagenesGuardadas.length > 0 ? (
            <RedesEcografiaReal imagenes={imagenesGuardadas} />
          ) : (
            <Empty description="Esta ecografía no tiene imágenes guardadas" />
          ),
        },
        {
          key: 'diagnostico',
          label: (
            <span>
              <FileImageOutlined />
              Diagnóstico
            </span>
          ),
          children: (
            <Descriptions column={1} bordered>
              <Descriptions.Item label="Diagnóstico Ecográfico">
                {ecografia.diagnostico && ecografia.diagnostico.trim() !== '' ? (
                  <Paragraph>{ecografia.diagnostico}</Paragraph>
                ) : (
                  <Text type="secondary" italic>
                    No se registró diagnóstico para esta ecografía
                  </Text>
                )}
              </Descriptions.Item>
              {ecografia.observaciones && ecografia.observaciones.trim() !== '' && (
                <Descriptions.Item label="Observaciones">
                  <Paragraph>{ecografia.observaciones}</Paragraph>
                </Descriptions.Item>
              )}
              {ecografia.requiere_seguimiento && (
                <Descriptions.Item label="Seguimiento">
                  <Alert
                    message="Requiere seguimiento especial"
                    type="warning"
                    showIcon
                  />
                </Descriptions.Item>
              )}
            </Descriptions>
          ),
        },
      ]}
    />
  </Card>
);
};

export default DetalleEcoTabs;
