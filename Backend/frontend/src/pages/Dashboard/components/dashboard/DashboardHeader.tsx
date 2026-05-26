import React from 'react';
import { Row, Col, Typography, Input } from 'antd';
import { UserOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { Search } = Input;

interface DashboardHeaderProps {
  user: any;
  onSearch: (value: string) => void;
}

const DashboardHeader: React.FC<DashboardHeaderProps> = ({ user, onSearch }) => (
  <div className="dashboard-header-wrapper">
    <Row justify="space-between" align="middle" gutter={[16, 16]}>
      <Col xs={24} md={14}>
        <Title level={2} style={{ marginBottom: 0, color: '#001529' }}>
          Hola, {user?.nombre || 'Doctor(a)'} 👋
        </Title>
        <Text type="secondary">
          {dayjs().format('dddd, D [de] MMMM [de] YYYY')} • Panel de Control General
        </Text>
      </Col>
      <Col xs={24} md={10}>
        <Search
          placeholder="Buscar paciente por nombre o CI..."
          enterButton="Buscar"
          size="large"
          onSearch={onSearch}
          prefix={<UserOutlined style={{ color: '#bfbfbf' }} />}
        />
      </Col>
    </Row>
  </div>
);

export default DashboardHeader;
