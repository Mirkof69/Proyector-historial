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
  dispatch: React.Dispatch<ViewerAction>;
}

const VisorSettingsDrawer: React.FC<VisorSettingsDrawerProps> = ({
  settingsVisible, brightness, contrast, showMeasurements, showAnnotations,
  dispatch,
}) => (
  <Drawer rootClassName="capa-clinica"
    title={<><SettingOutlined /> Configuración del Visor</>}
    placement="right"
    onClose={() => dispatch({ type: 'SET_SETTINGS_VISIBLE', payload: false })}
    open={settingsVisible}
    width={400}
  >
    <Space direction="vertical" size="large" className="u-ancho">
      <div>
        <Title level={5}>Calidad de Imagen</Title>
        <Divider className="u-mv-2" />

        <Space direction="vertical" className="u-ancho">
          <div>
            <Text>Interpolación:</Text>
            <Select
              className="u-ancho u-mt-2"
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
            <Radio.Group defaultValue="high" className="u-mt-2 u-ancho">
              <Radio.Button value="low">Baja</Radio.Button>
              <Radio.Button value="medium">Media</Radio.Button>
              <Radio.Button value="high">Alta</Radio.Button>
            </Radio.Group>
          </div>
        </Space>
      </div>

      <div>
        <Title level={5}>Herramientas</Title>
        <Divider className="u-mv-2" />

        <Space direction="vertical" className="u-ancho">
          <div>
            <Text>Grosor de línea (mediciones):</Text>
            <InputNumber
              min={1}
              max={10}
              defaultValue={2}
              className="u-ancho u-mt-2"
              suffix="px"
            />
          </div>

          <div>
            <Text>Tamaño de fuente (anotaciones):</Text>
            <InputNumber
              min={10}
              max={30}
              defaultValue={14}
              className="u-ancho u-mt-2"
              suffix="px"
            />
          </div>

          <div className="u-mt-4">
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
        <Divider className="u-mv-2" />

        <Space direction="vertical" size="middle" className="u-ancho">
          <Statistic
            title="Brillo Promedio"
            value={brightness}
            suffix="%"
            className="u-cifra-media"
          />
          <Progress
            percent={brightness}
            status="active"
            strokeColor="var(--color-primario)"
          />

          <Statistic
            title="Contraste"
            value={contrast}
            suffix="%"
            className="u-cifra-media"
          />
          <Progress
            percent={contrast}
            status="active"
            strokeColor="var(--color-primario)"
          />

        </Space>
      </div>
    </Space>
  </Drawer>
);

export default VisorSettingsDrawer;
