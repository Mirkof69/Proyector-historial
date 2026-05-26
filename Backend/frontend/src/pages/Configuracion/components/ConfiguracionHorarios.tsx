import React from 'react';
import { Card, Alert, List, Space, TimePicker, Tag, Typography, Button } from 'antd';
import { SaveOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';

const { Text } = Typography;

const DIAS_SEMANA = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];

interface HorarioDia {
  dia: string;
  activo: boolean;
  hora_inicio: string;
  hora_fin: string;
  inicio?: any;
  fin?: any;
}

interface ConfiguracionHorariosProps {
  horarios: HorarioDia[];
  setHorarios: (horarios: HorarioDia[]) => void;
  saving: boolean;
  onSave: () => void;
}

const ConfiguracionHorarios: React.FC<ConfiguracionHorariosProps> = ({ horarios, setHorarios, saving, onSave }) => {
  const saveIcon = <SaveOutlined />;

  return (
    <Card className="shadow-sm">
      <Alert
        message="Control de Agenda"
        description={
          <div>
            Estos horarios definen los límites para la creación de citas médicas automáticas.
            <br />
            <Text type="secondary">
              Días de la semana configurables: {DIAS_SEMANA.join(', ')}
            </Text>
          </div>
        }
        type="info"
        showIcon
        style={{ marginBottom: 24 }}
      />

      <List
        itemLayout="horizontal"
        dataSource={horarios}
        renderItem={(item, index) => (
          <List.Item>
            <List.Item.Meta
              title={<Text strong>{item.dia.toUpperCase()}</Text>}
              description={
                item.activo ? (
                  <Space>
                    <TimePicker
                      format="HH:mm"
                      value={item.inicio}
                      onChange={(val) => {
                        const nh = [...horarios];
                        nh[index].inicio = val;
                        setHorarios(nh);
                      }}
                      placeholder="Apertura"
                    />
                    <Text>a</Text>
                    <TimePicker
                      format="HH:mm"
                      value={item.fin}
                      onChange={(val) => {
                        const nh = [...horarios];
                        nh[index].fin = val;
                        setHorarios(nh);
                      }}
                      placeholder="Cierre"
                    />
                  </Space>
                ) : <Tag color="red">CERRADO</Tag>
              }
            />
          </List.Item>
        )}
      />

      <div style={{ marginTop: 24, textAlign: 'right' }}>
        <Button type="primary" icon={saveIcon} onClick={onSave} loading={saving}>
          Actualizar Horarios
        </Button>
      </div>
    </Card>
  );
};

export default ConfiguracionHorarios;
