import React from 'react';
import { Card, Statistic } from 'antd';
import { MedicineBoxOutlined, WarningOutlined, WomanOutlined } from '@ant-design/icons';

interface PartosStatsProps {
  total: number;
  cesareas: number;
  vaginales: number;
}

const PartosStats: React.FC<PartosStatsProps> = ({ total, cesareas, vaginales }) => (
  <div className="partos-page__cifras">
    <Card size="small">
      <Statistic title={<><MedicineBoxOutlined />Total Partos Registrados</>} value={total} />
    </Card>
    <Card size="small">
      <Statistic title={<><WarningOutlined />Cesáreas</>} value={cesareas} suffix={`/ ${total}`} />
    </Card>
    <Card size="small">
      <Statistic title={<><WomanOutlined />Partos Vaginales</>} value={vaginales} suffix={`/ ${total}`} />
    </Card>
  </div>
);

export default PartosStats;
