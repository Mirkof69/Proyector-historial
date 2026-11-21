import React from 'react';
import { Drawer, Space, Button, List, Tag } from 'antd';
import { ToolOutlined, PlusOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { Consultorio, MantenimientoConsultorio } from '../../../services/consultoriosService';

const plusIcon = <PlusOutlined />;

interface MantenimientoDrawerProps {
  drawerMantenimientoVisible: boolean;
  consultorioMantenimiento: Consultorio | null;
  mantenimientos: MantenimientoConsultorio[];
  loadingMantenimientos: boolean;
  onClose: () => void;
  handleAbrirModalMantenimiento: () => void;
  handleCompletarMantenimiento: (mantenimientoId: number) => void;
}

const MantenimientoDrawer: React.FC<MantenimientoDrawerProps> = ({
  drawerMantenimientoVisible, consultorioMantenimiento, mantenimientos, loadingMantenimientos,
  onClose, handleAbrirModalMantenimiento, handleCompletarMantenimiento,
}) => (
  <Drawer
    title={
      <Space>
        <ToolOutlined />
        Mantenimiento - {consultorioMantenimiento?.nombre}
      </Space>
    }
    placement="right"
    onClose={onClose}
    open={drawerMantenimientoVisible}
    width={600}
  >
    <Space direction="vertical" style={{ width: '100%' }} size="middle">
      <Button
        type="primary"
        icon={plusIcon}
        onClick={handleAbrirModalMantenimiento}
        block
      >
        Programar Mantenimiento
      </Button>

      <List
        loading={loadingMantenimientos}
        dataSource={mantenimientos}
        renderItem={(mantenimiento) => (
          <List.Item
            actions={[
              mantenimiento.estado === 'programado' && (
                <Button
                  key="completar"
                  type="link"
                  size="small"
                  onClick={() => handleCompletarMantenimiento(mantenimiento.id!)}
                >
                  Completar
                </Button>
              ),
            ]}
          >
            <List.Item.Meta
              title={
                <Space>
                  <span>{mantenimiento.tipo_mantenimiento}</span>
                  <Tag
                    color={
                      mantenimiento.estado === 'completado'
                        ? 'success'
                        : mantenimiento.estado === 'en_proceso'
                        ? 'processing'
                        : 'default'
                    }
                  >
                    {mantenimiento.estado}
                  </Tag>
                </Space>
              }
              description={
                <Space direction="vertical" size="small">
                  <div>
                    Programado: {dayjs(mantenimiento.fecha_programada).format('DD/MM/YYYY')}
                  </div>
                  {mantenimiento.fecha_realizada && (
                    <div>
                      Realizado: {dayjs(mantenimiento.fecha_realizada).format('DD/MM/YYYY')}
                    </div>
                  )}
                  <div>{mantenimiento.descripcion}</div>
                  {mantenimiento.costo && <div>Costo: ${mantenimiento.costo}</div>}
                </Space>
              }
            />
          </List.Item>
        )}
      />
    </Space>
  </Drawer>
);

export default MantenimientoDrawer;
