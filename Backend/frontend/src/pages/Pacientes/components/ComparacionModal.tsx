import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Modal, Alert, Row, Col, Card, Select, Divider, Descriptions, Empty, Table, Button } from 'antd';
import { FilePdfOutlined } from '@ant-design/icons';
// Cliente axios: la respuesta trae los datos en `.data`.
import apiClient from '../../../services/api';
import { Paciente, getEstadoCivilConGenero } from '../pacientesTypes';

const FILE_PDF_ICON_4 = <FilePdfOutlined />;

/**
 * Selector de paciente que busca EN EL SERVIDOR (`?search=`, que entiende los
 * nombres cifrados). Antes listaba las pacientes que la pantalla había bajado
 * en bucle; ahora la pantalla solo tiene la página visible.
 */
const SelectorPaciente: React.FC<{
  valor: Paciente | null;
  onElegir: (paciente: Paciente | null) => void;
}> = ({ valor, onElegir }) => {
  const [opciones, setOpciones] = useState<Paciente[]>([]);
  const [cargando, setCargando] = useState(false);
  const ultima = useRef(0);
  const espera = useRef<ReturnType<typeof setTimeout>>();

  const buscar = useCallback(async (termino: string) => {
    const id = ++ultima.current;
    setCargando(true);
    try {
      const r = await apiClient.get('/pacientes/', {
        params: { search: termino.trim() || undefined, page_size: 20 },
      });
      if (id === ultima.current) setOpciones(r.data?.results ?? []);
    } catch {
      if (id === ultima.current) setOpciones([]);
    } finally {
      if (id === ultima.current) setCargando(false);
    }
  }, []);

  useEffect(() => {
    buscar('');
    return () => clearTimeout(espera.current);
  }, [buscar]);

  // Espera a que se deje de escribir: cada búsqueda descifra nombres en el servidor.
  const alEscribir = (termino: string) => {
    clearTimeout(espera.current);
    espera.current = setTimeout(() => buscar(termino), 350);
  };

  const lista = valor && !opciones.some(o => o.id === valor.id) ? [valor, ...opciones] : opciones;

  return (
    <Select
      placeholder="Buscar paciente por nombre, CI o ID..."
      style={{ width: '100%' }}
      showSearch
      allowClear
      filterOption={false}
      onSearch={alEscribir}
      loading={cargando}
      notFoundContent={cargando ? 'Buscando…' : 'Sin resultados'}
      value={valor?.id}
      onChange={(id) => onElegir(lista.find(p => p.id === id) ?? null)}
      options={lista.map(p => ({ value: p.id, label: p.nombre_completo }))}
    />
  );
};

interface ComparacionState {
  a: Paciente | null;
  b: Paciente | null;
  c: Paciente | null;
}

interface ComparacionModalProps {
  visible: boolean;
  onClose: () => void;
  pacientesComparacion: ComparacionState;
  setPacientesComparacion: React.Dispatch<React.SetStateAction<ComparacionState>>;
}

const ComparacionModal: React.FC<ComparacionModalProps> = ({
  visible, onClose, pacientesComparacion, setPacientesComparacion,
}) => (
  <Modal
    title="Comparación de Pacientes"
    open={visible}
    onCancel={onClose}
    width={1000}
    footer={null}
  >
    <Alert
      message="Herramienta de Comparación Clínica"
      description="Seleccione hasta 3 pacientes para comparar perfiles médicos, evolución y resultados"
      type="info"
      showIcon
      style={{ marginBottom: 16 }}
    />

    <Row gutter={16}>
      <Col span={8}>
        <Card title="Paciente A" size="small">
          <SelectorPaciente
            valor={pacientesComparacion.a}
            onElegir={(pac) => setPacientesComparacion(prev => ({ ...prev, a: pac }))}
          />
          <Divider />
          {pacientesComparacion.a ? (
            <Descriptions size="small" column={1} bordered>
              <Descriptions.Item label="Edad">{pacientesComparacion.a.edad} años</Descriptions.Item>
              <Descriptions.Item label="Grupo">{pacientesComparacion.a.tipo_sangre || 'N/A'}</Descriptions.Item>
              <Descriptions.Item label="CI">{pacientesComparacion.a.ci}</Descriptions.Item>
            </Descriptions>
          ) : (
            <Empty description="Seleccione un paciente" />
          )}
        </Card>
      </Col>
      <Col span={8}>
        <Card title="Paciente B" size="small">
          <SelectorPaciente
            valor={pacientesComparacion.b}
            onElegir={(pac) => setPacientesComparacion(prev => ({ ...prev, b: pac }))}
          />
          <Divider />
          {pacientesComparacion.b ? (
            <Descriptions size="small" column={1} bordered>
              <Descriptions.Item label="Edad">{pacientesComparacion.b.edad} años</Descriptions.Item>
              <Descriptions.Item label="Grupo">{pacientesComparacion.b.tipo_sangre || 'N/A'}</Descriptions.Item>
              <Descriptions.Item label="CI">{pacientesComparacion.b.ci}</Descriptions.Item>
            </Descriptions>
          ) : (
            <Empty description="Seleccione un paciente" />
          )}
        </Card>
      </Col>
      <Col span={8}>
        <Card title="Paciente C" size="small">
          <SelectorPaciente
            valor={pacientesComparacion.c}
            onElegir={(pac) => setPacientesComparacion(prev => ({ ...prev, c: pac }))}
          />
          <Divider />
          {pacientesComparacion.c ? (
            <Descriptions size="small" column={1} bordered>
              <Descriptions.Item label="Edad">{pacientesComparacion.c.edad} años</Descriptions.Item>
              <Descriptions.Item label="Grupo">{pacientesComparacion.c.tipo_sangre || 'N/A'}</Descriptions.Item>
              <Descriptions.Item label="CI">{pacientesComparacion.c.ci}</Descriptions.Item>
            </Descriptions>
          ) : (
            <Empty description="Seleccione un paciente" />
          )}
        </Card>
      </Col>
    </Row>

    <Divider />

    <Table
      size="small"
      columns={[
        { title: 'Característica', dataIndex: 'item', key: 'item', fixed: 'left', width: 150 },
        { title: 'Paciente A', dataIndex: 'pacA', key: 'pacA' },
        { title: 'Paciente B', dataIndex: 'pacB', key: 'pacB' },
        { title: 'Paciente C', dataIndex: 'pacC', key: 'pacC' }
      ]}
      dataSource={[
        {
          key: '1',
          item: 'Edad',
          pacA: pacientesComparacion.a ? `${pacientesComparacion.a.edad} años` : '-',
          pacB: pacientesComparacion.b ? `${pacientesComparacion.b.edad} años` : '-',
          pacC: pacientesComparacion.c ? `${pacientesComparacion.c.edad} años` : '-'
        },
        {
          key: '2',
          item: 'Grupo Sanguíneo',
          pacA: pacientesComparacion.a?.tipo_sangre || '-',
          pacB: pacientesComparacion.b?.tipo_sangre || '-',
          pacC: pacientesComparacion.c?.tipo_sangre || '-'
        },
        {
          key: '3',
          item: 'CI',
          pacA: pacientesComparacion.a?.ci || '-',
          pacB: pacientesComparacion.b?.ci || '-',
          pacC: pacientesComparacion.c?.ci || '-'
        },
        {
          key: '4',
          item: 'Ciudad',
          pacA: pacientesComparacion.a?.ciudad || '-',
          pacB: pacientesComparacion.b?.ciudad || '-',
          pacC: pacientesComparacion.c?.ciudad || '-'
        },
        {
          key: '5',
          item: 'Teléfono',
          pacA: pacientesComparacion.a?.telefono || '-',
          pacB: pacientesComparacion.b?.telefono || '-',
          pacC: pacientesComparacion.c?.telefono || '-'
        },
        {
          key: '6',
          item: 'Estado Civil',
          pacA: pacientesComparacion.a ? getEstadoCivilConGenero(pacientesComparacion.a.estado_civil, pacientesComparacion.a.genero) : '-',
          pacB: pacientesComparacion.b ? getEstadoCivilConGenero(pacientesComparacion.b.estado_civil, pacientesComparacion.b.genero) : '-',
          pacC: pacientesComparacion.c ? getEstadoCivilConGenero(pacientesComparacion.c.estado_civil, pacientesComparacion.c.genero) : '-'
        },
        {
          key: '7',
          item: 'Peso',
          pacA: pacientesComparacion.a?.peso_kg ? `${pacientesComparacion.a.peso_kg} kg` : '-',
          pacB: pacientesComparacion.b?.peso_kg ? `${pacientesComparacion.b.peso_kg} kg` : '-',
          pacC: pacientesComparacion.c?.peso_kg ? `${pacientesComparacion.c.peso_kg} kg` : '-'
        },
        {
          key: '8',
          item: 'Altura',
          pacA: pacientesComparacion.a?.altura_cm ? `${pacientesComparacion.a.altura_cm} cm` : '-',
          pacB: pacientesComparacion.b?.altura_cm ? `${pacientesComparacion.b.altura_cm} cm` : '-',
          pacC: pacientesComparacion.c?.altura_cm ? `${pacientesComparacion.c.altura_cm} cm` : '-'
        },
        {
          key: '9',
          item: 'IMC',
          pacA: pacientesComparacion.a?.imc ? `${pacientesComparacion.a.imc.toFixed(1)}` : '-',
          pacB: pacientesComparacion.b?.imc ? `${pacientesComparacion.b.imc.toFixed(1)}` : '-',
          pacC: pacientesComparacion.c?.imc ? `${pacientesComparacion.c.imc.toFixed(1)}` : '-'
        }
      ]}
      pagination={false}
    />

    <Divider />

    <Button type="primary" icon={FILE_PDF_ICON_4} block>
      Generar Reporte Comparativo PDF
    </Button>
  </Modal>
);

export default ComparacionModal;
