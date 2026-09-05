import React from 'react';
import { Card, Row, Col, Input, Select, Button, Space } from 'antd';
import { SearchOutlined, ReloadOutlined } from '@ant-design/icons';
import { ROLES, LISTA_ROLES } from '../../../config/roles';

const { Option } = Select;

interface UsuariosFilterBarProps {
  searchText: string;
  filtroRol?: string;
  filtroEstado?: boolean;
  onSearchChange: (value: string) => void;
  onFiltroRolChange: (value: string | undefined) => void;
  onFiltroEstadoChange: (value: boolean | undefined) => void;
  onBuscar: () => void;
  onLimpiar: () => void;
}

const UsuariosFilterBar: React.FC<UsuariosFilterBarProps> = ({
  searchText, filtroRol, filtroEstado,
  onSearchChange, onFiltroRolChange, onFiltroEstadoChange, onBuscar, onLimpiar,
}) => (
  <Card style={{ marginBottom: 16 }}>
    <Row gutter={[16, 16]}>
      <Col xs={24} sm={12} md={8}>
        <Input placeholder="Buscar por nombre o email..." prefix={<SearchOutlined />} value={searchText} onChange={(e) => onSearchChange(e.target.value)} onPressEnter={onBuscar} allowClear />
      </Col>
      <Col xs={24} sm={12} md={6}>
        <Select placeholder="Filtrar por rol" style={{ width: '100%' }} value={filtroRol} onChange={onFiltroRolChange} allowClear>
          {/* Los cinco roles del backend, no tres. El valor que se manda es la
              clave exacta de `Usuario.ROLES`: escribir 'enfermero' donde el
              backend guarda 'enfermera' devolvia cero resultados siempre. */}
          {LISTA_ROLES.map((rol) => (
            <Option key={rol} value={rol}>{ROLES[rol].nombre}</Option>
          ))}
        </Select>
      </Col>
      <Col xs={24} sm={12} md={6}>
        <Select placeholder="Filtrar por estado" style={{ width: '100%' }} value={filtroEstado} onChange={onFiltroEstadoChange} allowClear>
          <Option value={true}>Activos</Option>
          <Option value={false}>Inactivos</Option>
        </Select>
      </Col>
      <Col xs={24} sm={12} md={4}>
        <Space>
          <Button type="primary" icon={<SearchOutlined />} onClick={onBuscar}>Buscar</Button>
          <Button icon={<ReloadOutlined />} onClick={onLimpiar}>Limpiar</Button>
        </Space>
      </Col>
    </Row>
  </Card>
);

export default UsuariosFilterBar;
