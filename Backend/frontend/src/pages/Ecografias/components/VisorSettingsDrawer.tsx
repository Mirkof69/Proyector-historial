import React from 'react';
import { Space, Typography, Divider, Radio, InputNumber, Select, Drawer, Statistic, Progress } from 'antd';
import { SettingOutlined, ExperimentOutlined } from '@ant-design/icons';
import { ViewerAction } from '../visorDicomReducer';

const { Title, Text } = Typography;

interface VisorSettingsDrawerProps {
  settingsVisible: boolean;
  brightness: number;
  contrast: number;
  showMeasurements: boolean;
  showAnnotations: boolean;
  nitidezDetectada: number;
  calidadImagen: number;
  dispatch: React.Dispatch<ViewerAction>;
}

const VisorSettingsDrawer: React.FC<VisorSettingsDrawerProps> = ({
  settingsVisible, brightness, contrast, showMeasurements, showAnnotations,
  nitidezDetectada, calidadImagen, dispatch,
}) => (
  <Drawer
    title={<><SettingOutlined /> Configuración del Visor</>}
    placement="right"
    onClose={() => dispatch({ type: 'SET_SETTINGS_VISIBLE', payload: false })}
    open={settingsVisible}
    width={400}
  >
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <div>
        <Title level={5}>Calidad de Imagen</Title>
        <Divider style={{ margin: '8px 0' }} />

        <Space direction="vertical" style={{ width: '100%' }}>
          <div>
            <Text>Interpolación:</Text>
            <Select
              style={{ width: '100%', marginTop: 8 }}
              defaultValue="bilinear"
              options={[
                { value: 'nearest', label: 'Nearest Neighbor' },
                { value: 'bilinear', label: 'Bilineal' },
                { value: 'bicubic', label: 'Bicúbica' }
              ]}
            />
          </div>

          <div>
            <Text>Resolución de Renderizado:</Text>
            <Radio.Group defaultValue="high" style={{ marginTop: 8, width: '100%' }}>
              <Radio.Button value="low">Baja</Radio.Button>
              <Radio.Button value="medium">Media</Radio.Button>
              <Radio.Button value="high">Alta</Radio.Button>
            </Radio.Group>
          </div>
        </Space>
      </div>

      <div>
        <Title level={5}>Herramientas</Title>
        <Divider style={{ margin: '8px 0' }} />

        <Space direction="vertical" style={{ width: '100%' }}>
          <div>
            <Text>Grosor de línea (mediciones):</Text>
            <InputNumber
              min={1}
              max={10}
              defaultValue={2}
              style={{ width: '100%', marginTop: 8 }}
              suffix="px"
            />
          </div>

          <div>
            <Text>Tamaño de fuente (anotaciones):</Text>
            <InputNumber
              min={10}
              max={30}
              defaultValue={14}
              style={{ width: '100%', marginTop: 8 }}
              suffix="px"
            />
          </div>

          <div style={{ marginTop: 16 }}>
            <Radio.Group value={[showMeasurements, showAnnotations]}>
              <Space direction="vertical">
                <Radio
                  checked={showMeasurements}
                  onChange={(e) => dispatch({ type: 'SET_SHOW_MEASUREMENTS', payload: e.target.checked })}
                >
                  Mostrar mediciones
                </Radio>
                <Radio
                  checked={showAnnotations}
                  onChange={(e) => dispatch({ type: 'SET_SHOW_ANNOTATIONS', payload: e.target.checked })}
                >
                  Mostrar anotaciones
                </Radio>
              </Space>
            </Radio.Group>
          </div>
        </Space>
      </div>

      <div>
        <Title level={5}><ExperimentOutlined /> Análisis de Imagen</Title>
        <Divider style={{ margin: '8px 0' }} />

        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          <Statistic
            title="Brillo Promedio"
            value={brightness}
            suffix="%"
            valueStyle={{ fontSize: 20 }}
          />
          <Progress
            percent={brightness}
            status="active"
            strokeColor={{ from: '#108ee9', to: '#87d068' }}
          />

          <Statistic
            title="Contraste"
            value={contrast}
            suffix="%"
            valueStyle={{ fontSize: 20 }}
          />
          <Progress
            percent={contrast}
            status="active"
            strokeColor={{ from: '#ffd666', to: '#ff4d4f' }}
          />

          <Statistic
            title="Nitidez Detectada"
            value={nitidezDetectada}

            suffix="%"
            valueStyle={{ fontSize: 20 }}
          />
          <Progress
            percent={calidadImagen}

            status="active"
          />
        </Space>
      </div>
    </Space>
  </Drawer>
);

export default VisorSettingsDrawer;
