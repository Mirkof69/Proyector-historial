import React from 'react';
import { Card, Row, Col, Input, Button } from 'antd';
import { SearchOutlined, PlusOutlined } from '@ant-design/icons';

interface SearchBarProps {
  searchText: string;
  onSearchChange: (value: string) => void;
  onNew: () => void;
}

const SearchBar: React.FC<SearchBarProps> = ({ searchText, onSearchChange, onNew }) => (
  <Card style={{ marginBottom: '24px' }}>
    <Row gutter={16} align="middle">
      <Col flex="auto">
        <Input
          placeholder="Buscar por nombre de paciente..."
          value={searchText}
          onChange={(e) => onSearchChange(e.target.value)}
          size="large"
          prefix={<SearchOutlined style={{ color: '#bfbfbf' }} />}
          allowClear
        />
      </Col>
      <Col>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={onNew}
          size="large"
        >
          Nuevo Antecedente
        </Button>
      </Col>
    </Row>
  </Card>
);

export default SearchBar;
