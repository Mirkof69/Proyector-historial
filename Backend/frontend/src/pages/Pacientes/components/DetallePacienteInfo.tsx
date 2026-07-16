import React from 'react';
import { Card, Descriptions, Tag, Space, Typography, Row, Col } from 'antd';
import { UserOutlined, HeartOutlined, PhoneOutlined, HomeOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { Paciente } from '../../../services/pacientesService';
import { getEstadoCivilConGenero } from '../detallePacienteUtils';

const { Text } = Typography;

interface DetallePacienteInfoProps {
  paciente: Paciente;
}

const DetallePacienteInfo: React.FC<DetallePacienteInfoProps> = ({ paciente }) => (
  <>
    <Col span={24}>
      <Card title={<span><UserOutlined /> Información Personal</span>} variant="borderless">
        <Descriptions bordered column={{ xxl: 4, xl: 3, lg: 3, md: 2, sm: 1, xs: 1 }}>
          <Descriptions.Item label="ID Clínico"><strong>{paciente.id_clinico}</strong></Descriptions.Item>
          <Descriptions.Item label="Cédula de Identidad">{paciente.ci}</Descriptions.Item>
          <Descriptions.Item label="Fecha de Nacimiento">
            {dayjs(paciente.fecha_nacimiento).format('DD/MM/YYYY')} <Tag color="blue">{paciente.edad} años</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Género">{paciente.genero}</Descriptions.Item>
          <Descriptions.Item label="Teléfono">
            <Space>
              <PhoneOutlined /> {paciente.telefono || '-'}
            </Space>
          </Descriptions.Item>
          <Descriptions.Item label="Email">{paciente.email || '-'}</Descriptions.Item>
          <Descriptions.Item label="Dirección" span="filled">
            <Space>
              <HomeOutlined /> {paciente.direccion || '-'}
            </Space>
          </Descriptions.Item>
          <Descriptions.Item label="Ciudad">{paciente.ciudad || '-'}</Descriptions.Item>
          <Descriptions.Item label="País">{paciente.pais}</Descriptions.Item>
          <Descriptions.Item label="Estado Civil">
            <Tag color="blue">{getEstadoCivilConGenero(paciente.estado_civil, paciente.genero)}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Ocupación">{paciente.ocupacion || '-'}</Descriptions.Item>
          <Descriptions.Item label="Nivel Educativo">{paciente.nivel_educativo || '-'}</Descriptions.Item>
          <Descriptions.Item label="Tipo de Sangre">{paciente.tipo_sangre || '-'}</Descriptions.Item>
          <Descriptions.Item label="Factor RH">{paciente.factor_rh || '-'}</Descriptions.Item>
        </Descriptions>
      </Card>
    </Col>

    <Col span={24}>
      <Card title={<span><HeartOutlined /> Información Médica</span>} variant="borderless">
        <Descriptions bordered column={{ xxl: 4, xl: 3, lg: 3, md: 2, sm: 1, xs: 1 }}>
          <Descriptions.Item label="Peso">
            {paciente.peso_kg ? <Text strong>{paciente.peso_kg} kg</Text> : <Text type="secondary">No registrado</Text>}
          </Descriptions.Item>
          <Descriptions.Item label="Altura">
            {paciente.altura_cm ? <Text strong>{paciente.altura_cm} cm</Text> : <Text type="secondary">No registrado</Text>}
          </Descriptions.Item>
          <Descriptions.Item label="IMC" span="filled">
            {paciente.imc ? (
              <Space>
                <Text strong style={{ fontSize: '16px' }}>{paciente.imc.toFixed(1)}</Text>
                <Tag color={
                  paciente.imc < 18.5 ? 'orange' :
                    paciente.imc < 25 ? 'green' :
                      paciente.imc < 30 ? 'gold' : 'red'
                }>
                  {paciente.imc < 18.5 ? 'Bajo Peso' :
                    paciente.imc < 25 ? 'Normal' :
                      paciente.imc < 30 ? 'Sobrepeso' : 'Obesidad'}
                </Tag>
              </Space>
            ) : (
              <Text type="secondary">No disponible</Text>
            )}
          </Descriptions.Item>
          <Descriptions.Item label="Alergias" span="filled">
            {paciente.alergias || 'Ninguna registrada'}
          </Descriptions.Item>
          <Descriptions.Item label="Enfermedades Crónicas" span="filled">
            {paciente.enfermedades_cronicas || 'Ninguna registrada'}
          </Descriptions.Item>
          <Descriptions.Item label="Contacto Emergencia">
            {paciente.contacto_emergencia_nombre || '-'}
          </Descriptions.Item>
          <Descriptions.Item label="Tel. Emergencia">
            {paciente.contacto_emergencia_telefono || '-'}
          </Descriptions.Item>
          <Descriptions.Item label="Relación">
            {paciente.contacto_emergencia_relacion || '-'}
          </Descriptions.Item>
        </Descriptions>
      </Card>
    </Col>
  </>
);

export default DetallePacienteInfo;
