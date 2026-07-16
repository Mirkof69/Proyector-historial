import React from 'react';
import { Form, Row, Col, Input, Select, Divider } from 'antd';

const PasoDatosClinicosReg: React.FC = () => (
  <>
    <Row gutter={16}>
      <Col span={8}>
        <Form.Item
          label="Grupo Sanguíneo"
          name="grupo_sanguineo"
        >
          <Select placeholder="Seleccione">
            <Select.Option value="A">A</Select.Option>
            <Select.Option value="B">B</Select.Option>
            <Select.Option value="AB">AB</Select.Option>
            <Select.Option value="O">O</Select.Option>
          </Select>
        </Form.Item>
      </Col>
      <Col span={8}>
        <Form.Item
          label="Factor RH"
          name="factor_rh"
        >
          <Select placeholder="Seleccione">
            <Select.Option value="Positivo">Positivo (+)</Select.Option>
            <Select.Option value="Negativo">Negativo (-)</Select.Option>
          </Select>
        </Form.Item>
      </Col>
      <Col span={8}>
        <Form.Item
          label="Seguro Médico"
          name="seguro_medico"
        >
          <Input placeholder="Nombre del seguro" />
        </Form.Item>
      </Col>
    </Row>

    <Divider>Antecedentes Obstétricos</Divider>

    <Row gutter={16}>
      <Col span={8}>
        <Form.Item
          label="Gestas Previas"
          name="gestas_previas"
        >
          <Input type="number" min={0} placeholder="0" />
        </Form.Item>
      </Col>
      <Col span={8}>
        <Form.Item
          label="Partos Previos"
          name="partos_previos"
        >
          <Input type="number" min={0} placeholder="0" />
        </Form.Item>
      </Col>
      <Col span={8}>
        <Form.Item
          label="Cesáreas Previas"
          name="cesareas_previas"
        >
          <Input type="number" min={0} placeholder="0" />
        </Form.Item>
      </Col>
    </Row>

    <Row gutter={16}>
      <Col span={8}>
        <Form.Item
          label="Abortos Previos"
          name="abortos_previos"
        >
          <Input type="number" min={0} placeholder="0" />
        </Form.Item>
      </Col>
      <Col span={8}>
        <Form.Item
          label="Hijos Vivos"
          name="hijos_vivos"
        >
          <Input type="number" min={0} placeholder="0" />
        </Form.Item>
      </Col>
    </Row>

    <Divider>Antecedentes Médicos</Divider>

    <Form.Item
      label="Antecedentes Personales"
      name="antecedentes_personales"
      tooltip="Enfermedades crónicas, cirugías previas, etc."
    >
      <Select
        mode="tags"
        style={{ width: '100%' }}
        placeholder="Agregue antecedentes personales"
        tokenSeparators={[',']}
      >
        <Select.Option value="Diabetes">Diabetes</Select.Option>
        <Select.Option value="Hipertensión">Hipertensión</Select.Option>
        <Select.Option value="Asma">Asma</Select.Option>
        <Select.Option value="Epilepsia">Epilepsia</Select.Option>
        <Select.Option value="Cardiopatía">Cardiopatía</Select.Option>
        <Select.Option value="Nefropatía">Nefropatía</Select.Option>
        <Select.Option value="Hipotiroidismo">Hipotiroidismo</Select.Option>
      </Select>
    </Form.Item>

    <Form.Item
      label="Antecedentes Familiares"
      name="antecedentes_familiares"
      tooltip="Enfermedades hereditarias en la familia"
    >
      <Select
        mode="tags"
        style={{ width: '100%' }}
        placeholder="Agregue antecedentes familiares"
        tokenSeparators={[',']}
      >
        <Select.Option value="Diabetes">Diabetes</Select.Option>
        <Select.Option value="Hipertensión">Hipertensión</Select.Option>
        <Select.Option value="Cáncer">Cáncer</Select.Option>
        <Select.Option value="Cardiopatías">Cardiopatías</Select.Option>
        <Select.Option value="Malformaciones congénitas">Malformaciones congénitas</Select.Option>
      </Select>
    </Form.Item>

    <Form.Item
      label="Alergias"
      name="alergias"
      tooltip="Alergias a medicamentos, alimentos, etc."
    >
      <Select
        mode="tags"
        style={{ width: '100%' }}
        placeholder="Agregue alergias conocidas"
        tokenSeparators={[',']}
      >
        <Select.Option value="Penicilina">Penicilina</Select.Option>
        <Select.Option value="Sulfas">Sulfas</Select.Option>
        <Select.Option value="AINEs">AINEs</Select.Option>
        <Select.Option value="Yodo">Yodo</Select.Option>
      </Select>
    </Form.Item>

    <Form.Item
      label="Medicamentos Actuales"
      name="medicamentos_actuales"
      tooltip="Medicamentos que toma regularmente"
    >
      <Select
        mode="tags"
        style={{ width: '100%' }}
        placeholder="Agregue medicamentos actuales"
        tokenSeparators={[',']}
      />
    </Form.Item>

    <Form.Item
      label="Cirugías Previas"
      name="cirugias_previas"
    >
      <Select
        mode="tags"
        style={{ width: '100%' }}
        placeholder="Agregue cirugías previas"
        tokenSeparators={[',']}
      >
        <Select.Option value="Cesárea">Cesárea</Select.Option>
        <Select.Option value="Apendicectomía">Apendicectomía</Select.Option>
        <Select.Option value="Colecistectomía">Colecistectomía</Select.Option>
        <Select.Option value="Histerectomía">Histerectomía</Select.Option>
      </Select>
    </Form.Item>
  </>
);

export default PasoDatosClinicosReg;
