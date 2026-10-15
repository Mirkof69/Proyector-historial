import React from 'react';
import { Button, Space, Typography } from 'antd';
import { BulbOutlined, LineChartOutlined, HeartOutlined, MedicineBoxOutlined } from '@ant-design/icons';

const { Text } = Typography;

interface IAAnalisisRapidosProps {
  analizarRapido: (tipo: string) => void;
}

const IAAnalisisRapidos: React.FC<IAAnalisisRapidosProps> = ({ analizarRapido }) => (
  <div className="ia-asistente-rapidos">
    <Text strong>Consultas rápidas</Text>
    <div>
      <Space wrap>
        <Button
          size="small"
          icon={<HeartOutlined />}
          onClick={() => analizarRapido('preeclampsia')}
        >
          Preeclampsia
        </Button>
        <Button
          size="small"
          icon={<MedicineBoxOutlined />}
          onClick={() => analizarRapido('diabetes')}
        >
          Diabetes
        </Button>
        <Button
          size="small"
          icon={<LineChartOutlined />}
          onClick={() => analizarRapido('rciu')}
        >
          RCIU
        </Button>
        <Button
          size="small"
          icon={<BulbOutlined />}
          onClick={() => analizarRapido('laboratorio')}
        >
          Laboratorios
        </Button>
      </Space>
    </div>
  </div>
);

export default IAAnalisisRapidos;
