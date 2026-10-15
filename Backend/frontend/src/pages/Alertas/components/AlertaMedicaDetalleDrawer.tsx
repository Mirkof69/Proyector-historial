import React from 'react';
import { Tag, Badge, Button, Drawer, Descriptions, Timeline } from 'antd';
import { CheckOutlined, CloseOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { AlertaMedica } from '../../../services/reportesService';
import { AlertasState, getSeveridadColor } from '../alertasMedicasUtils';

interface AlertaMedicaDetalleDrawerProps {
  drawerVisible: boolean;
  selectedAlerta: AlertaMedica | null;
  setState: React.Dispatch<React.SetStateAction<AlertasState>>;
  marcarResuelta: (id: number) => void;
  navigate: (path: string) => void;
}

const AlertaMedicaDetalleDrawer: React.FC<AlertaMedicaDetalleDrawerProps> = ({
  drawerVisible, selectedAlerta, setState, marcarResuelta, navigate,
}) => (
  <Drawer
    title="Detalle de Alerta"
    placement="right"
    width={600}
    onClose={() => setState(prev => ({ ...prev, drawerVisible: false }))}
    open={drawerVisible}
  >
    {selectedAlerta && (
      <div>
        <Descriptions column={1} bordered>
          <Descriptions.Item label="ID Alerta">#{selectedAlerta.id}</Descriptions.Item>
          <Descriptions.Item label="Título">{selectedAlerta.titulo}</Descriptions.Item>
          <Descriptions.Item label="Paciente">
            {selectedAlerta.paciente_nombre || '—'}
          </Descriptions.Item>
          <Descriptions.Item label="Tipo de Alerta">{selectedAlerta.tipo_display || selectedAlerta.tipo}</Descriptions.Item>
          <Descriptions.Item label="Prioridad">
            <Tag color={getSeveridadColor(selectedAlerta.prioridad)}>
              {(selectedAlerta.prioridad_display || selectedAlerta.prioridad).toUpperCase()}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Módulo Origen">{selectedAlerta.modulo_origen_display || selectedAlerta.modulo_origen}</Descriptions.Item>
          <Descriptions.Item label="Descripción">{selectedAlerta.descripcion}</Descriptions.Item>
          <Descriptions.Item label="Acción Recomendada">{selectedAlerta.accion_recomendada || 'Sin acción registrada'}</Descriptions.Item>
          <Descriptions.Item label="Valor Actual / Umbral">
            {selectedAlerta.valor_actual || '—'} / {selectedAlerta.valor_umbral || '—'}
          </Descriptions.Item>
          <Descriptions.Item label="Estado">
            <Badge
              status={selectedAlerta.estado === 'resuelta' ? 'success' : selectedAlerta.estado === 'descartada' ? 'default' : 'error'}
              text={selectedAlerta.estado_display || selectedAlerta.estado}
            />
          </Descriptions.Item>
          <Descriptions.Item label="Fecha de Creación">
            {dayjs(selectedAlerta.fecha_creacion).format('DD/MM/YYYY HH:mm:ss')}
          </Descriptions.Item>
          {selectedAlerta.estado === 'resuelta' && (
            <>
              <Descriptions.Item label="Fecha de Resolución">
                {selectedAlerta.fecha_resolucion ? dayjs(selectedAlerta.fecha_resolucion).format('DD/MM/YYYY HH:mm:ss') : '—'}
              </Descriptions.Item>
              <Descriptions.Item label="Comentario de Resolución">
                {selectedAlerta.comentario_resolucion || '—'}
              </Descriptions.Item>
            </>
          )}
        </Descriptions>

        {selectedAlerta.estado !== 'resuelta' && selectedAlerta.estado !== 'descartada' && (
          <div className="alerta-detalle__acciones">
            <>
              <Button
                type="primary"
                icon={<CheckOutlined />}
                onClick={() => {
                  marcarResuelta(selectedAlerta.id);
                  setState(prev => ({ ...prev, drawerVisible: false }));
                }}
                block
              >
                Marcar como Resuelta
              </Button>
              <Button
                icon={<CloseOutlined />}
                onClick={() => setState(prev => ({ ...prev, drawerVisible: false }))}
                block
              >
                Cerrar sin Resolver
              </Button>
            </>
          </div>
        )}

        {/* Timeline de Historial */}
        <div className="alerta-detalle__bloque">
          <h4>Historial de Actividad</h4>
          <Timeline
            items={[
              {
                color: 'blue',
                children: (
                  <>
                    <p><strong>Alerta Creada</strong></p>
                    <p className="alerta-detalle__fecha">
                      {dayjs(selectedAlerta.fecha_creacion).format('DD/MM/YYYY HH:mm:ss')}
                    </p>
                    <p className="alerta-detalle__origen">Origen: {selectedAlerta.modulo_origen_display || selectedAlerta.modulo_origen}</p>
                  </>
                ),
              },
              ...(selectedAlerta.estado === 'resuelta'
                ? [
                    {
                      color: 'green',
                      children: (
                        <>
                          <p><strong>Alerta Resuelta</strong></p>
                          <p className="alerta-detalle__fecha">
                            {selectedAlerta.fecha_resolucion ? dayjs(selectedAlerta.fecha_resolucion).format('DD/MM/YYYY HH:mm:ss') : ''}
                          </p>
                        </>
                      ),
                    },
                  ]
                : []),
            ]}
          />
        </div>

        {/* Botón para ver paciente */}
        {selectedAlerta.paciente_id && (
          <div className="alerta-detalle__bloque">
            <Button
              type="dashed"
              block
              onClick={() => navigate(`/dashboard/pacientes/${selectedAlerta.paciente_id}`)}
            >
              Ver Expediente del Paciente
            </Button>
          </div>
        )}
      </div>
    )}
  </Drawer>
);

export default AlertaMedicaDetalleDrawer;
