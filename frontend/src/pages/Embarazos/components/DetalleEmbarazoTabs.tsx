import React from 'react';
import { Card, Tag, Space, Typography, Tabs, Spin, Empty, Badge, List, Button, Alert } from 'antd';
import { MedicineBoxOutlined, WarningOutlined, PlusOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { ControlPrenatal } from '../../../services/controlesService';
import { tabEcografias, tabLaboratorio } from '../detalleEmbarazoUtils';

const { Text } = Typography;

interface DetalleEmbarazoTabsProps {
  controles: ControlPrenatal[];
  loadingControles: boolean;
  ultimoControl: ControlPrenatal | null;
  handleVerControl: (controlId: number) => void;
  handleNuevoControl: () => void;
}

const DetalleEmbarazoTabs: React.FC<DetalleEmbarazoTabsProps> = ({
  controles, loadingControles, ultimoControl, handleVerControl, handleNuevoControl,
}) => (
  <Card className="u-mt-4" title={<><MedicineBoxOutlined /> Seguimiento del Embarazo</>}>
    <Tabs defaultActiveKey="controles" items={[
      {
        key: 'controles',
        label: (
          <Badge count={controles.length} offset={[10, 0]}>
            <span>
              <MedicineBoxOutlined /> Controles Prenatales
            </span>
          </Badge>
        ),
        children: loadingControles ? (
          <div className="u-centro u-p-6">
            <Spin tip="Cargando controles…"><div /></Spin>
          </div>
        ) : controles.length > 0 ? (
          <>
            <Alert
              message={`${controles.length} control(es) prenatal(es) registrado(s)`}
              description={ultimoControl && `Último control: ${dayjs(ultimoControl.fecha_control).format('DD/MM/YYYY')}`}
              type="info"
              showIcon
              className="u-mb-4"
            />
            <List
              itemLayout="horizontal"
              dataSource={controles}
              renderItem={(control, idx) => (
                <List.Item
                  key={control.id}
                  actions={[
                    <Button
                      key="ver_detalle"
                      type="link"
                      onClick={() => handleVerControl(control.id!)}
                    >
                      Ver Detalle
                    </Button>,
                  ]}
                >
                  <List.Item.Meta
                    avatar={
                      // @ts-ignore
                      control.tiene_alertas ? (
                        <Badge dot>
                          <MedicineBoxOutlined className="u-t-xl u-c-peligro" />
                        </Badge>
                      ) : (
                        <MedicineBoxOutlined className="u-t-xl u-c-primario" />
                      )
                    }
                    title={
                      <Space>
                        <Text strong>Control #{control.numero_control}</Text>
                        <Tag color="processing">
                          {control.edad_gestacional_semanas}s + {control.edad_gestacional_dias || 0}d
                        </Tag>
                        {/* @ts-ignore */}
                        {control.tiene_alertas && (
                          <Tag color="error" icon={<WarningOutlined />}>
                            Con alertas
                          </Tag>
                        )}
                      </Space>
                    }
                    description={
                      <Space direction="vertical" size={0}>
                        <Text type="secondary">
                          Fecha: {dayjs(control.fecha_control).format('DD/MM/YYYY')}
                        </Text>
                        {control.presion_arterial_sistolica && control.presion_arterial_diastolica && (
                          <Text type="secondary">
                            PA: {control.presion_arterial_sistolica}/{control.presion_arterial_diastolica} mmHg
                          </Text>
                        )}
                        {control.frecuencia_cardiaca_fetal && (
                          <Text type="secondary">
                            FCF: {control.frecuencia_cardiaca_fetal} lpm
                          </Text>
                        )}
                      </Space>
                    }
                  />
                </List.Item>
              )}
            />
          </>
        ) : (
          <Empty
            description="No hay controles prenatales registrados"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          >
            <Button icon={<PlusOutlined />} onClick={handleNuevoControl}>
              Crear Primer Control
            </Button>
          </Empty>
        ),
      },
      {
        key: 'ecografias',
        label: tabEcografias,
        children: (
          <>
            <Alert
              message="Módulo en Desarrollo"
              description="El registro y visualización de ecografías estará disponible próximamente."
              type="info"
              showIcon
              className="u-mb-4"
            />
            <Empty description="No hay ecografías registradas" />
          </>
        ),
      },
      {
        key: 'laboratorio',
        label: tabLaboratorio,
        children: (
          <>
            <Alert
              message="Módulo en Desarrollo"
              description="Los resultados de laboratorio se mostrarán aquí próximamente."
              type="info"
              showIcon
              className="u-mb-4"
            />
            <Empty description="No hay estudios de laboratorio" />
          </>
        ),
      },
    ]} />
  </Card>
);

export default DetalleEmbarazoTabs;
