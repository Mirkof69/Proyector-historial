import React from 'react';
import { InfoCircleOutlined, LineChartOutlined, EditOutlined } from '@ant-design/icons';

// Hoisted tab label (static JSX)
export const tabResumen = (
  <span>
    <InfoCircleOutlined /> Resumen
  </span>
);

export const TabMediciones = React.memo(({ count }: { count: number }) => (
  <span>
    <LineChartOutlined /> Mediciones ({count})
  </span>
));

export const TabAnotaciones = React.memo(({ count }: { count: number }) => (
  <span>
    <EditOutlined /> Anotaciones ({count})
  </span>
));
