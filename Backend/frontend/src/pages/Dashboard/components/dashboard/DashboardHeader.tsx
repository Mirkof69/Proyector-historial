import React from 'react';
import { Typography, Input } from 'antd';
import { UserOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { Search } = Input;

interface DashboardHeaderProps {
  user: any;
  onSearch: (value: string) => void;
}

const DashboardHeader: React.FC<DashboardHeaderProps> = ({ user, onSearch }) => (
  <header className="dashboard-header-wrapper">
    <div className="dashboard-header__texto">
      <Title level={2}>
        Hola, {user?.nombre || 'Doctor(a)'}
      </Title>
      <Text className="dashboard-header__descripcion">
        {dayjs().format('dddd, D [de] MMMM [de] YYYY')} • Panel de Control General
      </Text>
    </div>
    <div className="dashboard-header__busqueda">
      <Search
        placeholder="Buscar paciente por nombre o CI..."
        enterButton="Buscar"
        size="large"
        onSearch={onSearch}
        prefix={<UserOutlined className="texto-ayuda" />}
      />
    </div>
  </header>
);

export default DashboardHeader;
