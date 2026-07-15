import React from 'react';
import { Typography, Alert, Collapse } from 'antd';
import dayjs from 'dayjs';

const { Text } = Typography;

interface IAErroresCollapseProps {
  systemErrors: any[];
  collapseErrorLabel: React.ReactNode;
}

const IAErroresCollapse: React.FC<IAErroresCollapseProps> = ({ systemErrors, collapseErrorLabel }) => (
  <Collapse
    items={[{
      key: '1',
      label: collapseErrorLabel,
      children: systemErrors.slice(-3).map((err) => (
        <Alert
          key={err.message || err.timestamp}
          message={`${err.details.status || 'Error'}: ${err.message}`}
          description={
            <div>
              <Text type="secondary" style={{ fontSize: '12px' }}>
                {dayjs(err.timestamp).format('HH:mm:ss')} - {err.details.url}
              </Text>
            </div>
          }
          type={err.severity === 'critical' ? 'error' : 'warning'}
          showIcon
          style={{ marginBottom: 8 }}
        />
      ))
    }]}
    style={{ marginBottom: 16 }}
  />
);

export default IAErroresCollapse;
