/**
 * =============================================================================
 * GENERADOR DE PDFs OFICIALES - REPORTES MÉDICOS PROFESIONALES
 * =============================================================================
 * Sistema completo de generación de documentos PDF con formato oficial
 * Incluye: Historia Clínica, Órdenes Médicas, Resultados de Laboratorio,
 * Reportes de Ecografía, Certificados Médicos, Recetas y más
 * =============================================================================
 */

import React, { useState, useMemo } from 'react';
import {
    Modal, Button, Form, Select, DatePicker, Input, Space, Card,
    Radio, Checkbox, Alert, Divider, Typography, Row, Col,
    Steps, message, Upload, Tag, Badge
} from 'antd';
import {
    FilePdfOutlined, DownloadOutlined, PrinterOutlined, MailOutlined,
    FileTextOutlined, MedicineBoxOutlined, ExperimentOutlined,
    HeartOutlined, CalendarOutlined, SafetyOutlined, CheckCircleOutlined
} from '@ant-design/icons';

const { Title, Text } = Typography;
const { TextArea } = Input;
const { Step } = Steps;
const { Option } = Select;

interface PDFGeneratorProps {
    open: boolean;
    onCancel: () => void;
    pacienteData?: any;
    embarazoData?: any;
    moduloOrigen?: 'pacientes' | 'embarazos' | 'controles' | 'laboratorio' | 'ecografias' | 'partos';
}

interface StepContentProps {
  currentStep: number;
  tipoPDF: string;
  tiposPDF: { key: string; label: string; icon: React.ReactNode; color: string; descripcion: string }[];
  currentDateLabel: string;
  currentDateISO: string;
  pacienteData?: any;
}

const StepContent: React.FC<StepContentProps> = ({
  currentStep,
  tipoPDF,
  tiposPDF,
  currentDateLabel,
  currentDateISO,
  pacienteData,
}) => {
  switch (currentStep) {
    case 0:
      return (
        <div>
          <Title level={4} style={{ marginBottom: 16 }}>📄 Selección de Documento</Title>
          <Alert
            message="Seleccione el tipo de documento PDF a generar"
            description="Cada tipo de documento tiene un formato oficial específico según normativas médicas"
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />

          <Form.Item
            name="tipo_pdf"
            rules={[{ required: true, message: 'Seleccione un tipo de PDF' }]}
          >
            <Radio.Group
              value={tipoPDF}
              onChange={(e) => {}}
              style={{ width: '100%' }}
            >
              <Row gutter={[16, 16]}>
                {tiposPDF.map(tipo => (
                  <Col xs={24} md={12} key={tipo.key}>
                    <Card
                      hoverable
                      onClick={() => {}}
                      style={{
                        borderColor: tipoPDF === tipo.key ? '#1890ff' : '#d9d9d9',
                        borderWidth: tipoPDF === tipo.key ? 2 : 1
                      }}
                    >
                      <Radio value={tipo.key}>
                        <Space>
                          <Badge color={tipo.color} />
                          <span style={{ fontSize: 16 }}>{tipo.icon} {tipo.label}</span>
                        </Space>
                      </Radio>
                      <Text type="secondary" style={{ display: 'block', marginTop: 8, fontSize: 12 }}>
                        {tipo.descripcion}
                      </Text>
                    </Card>
                  </Col>
                ))}
              </Row>
            </Radio.Group>
          </Form.Item>
        </div>
      );

    case 1:
      return (
        <div>
          <Alert
            message="Complete los datos específicos del documento"
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />

          <Form.Item
            label="Médico Responsable"
            name="medico"
            rules={[{ required: true, message: 'Ingrese el nombre del médico' }]}
          >
            <Select placeholder="Seleccione el médico">
              <Option value="dr_garcia">Dr. Juan García - Ginecobstetra</Option>
              <Option value="dra_lopez">Dra. María López - Medicina Fetal</Option>
              <Option value="dr_martinez">Dr. Pedro Martínez - Obstetra</Option>
              <Option value="dra_rodriguez">Dra. Ana Rodríguez - Perinatóloga</Option>
            </Select>
          </Form.Item>

          <Form.Item
            label="Fecha del Documento"
            name="fecha_documento"
            initialValue={currentDateISO}
          >
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>

          {tipoPDF === 'orden_medica' && (
            <>
              <Form.Item label="Tipo de Orden" name="tipo_orden">
                <Select placeholder="Seleccione...">
                  <Option value="laboratorio">Exámenes de Laboratorio</Option>
                  <Option value="ecografia">Ecografía</Option>
                  <Option value="radiologia">Radiología</Option>
                  <Option value="interconsulta">Interconsulta</Option>
                </Select>
              </Form.Item>
              <Form.Item label="Indicaciones" name="indicaciones">
                <TextArea rows={4} placeholder="Especifique los exámenes o procedimientos ordenados..." />
              </Form.Item>
            </>
          )}

          {tipoPDF === 'receta_medica' && (
            <>
              <Form.Item label="Medicamentos Prescritos" name="medicamentos">
                <TextArea rows={6} placeholder="Ejemplo:&#10;1. Ácido Fólico 5mg - 1 tableta cada 24 horas - 30 días&#10;2. Sulfato Ferroso 300mg - 1 tableta cada 12 horas - 30 días" />
              </Form.Item>
              <Form.Item label="Recomendaciones" name="recomendaciones">
                <TextArea rows={3} placeholder="Recomendaciones adicionales para la paciente..." />
              </Form.Item>
            </>
          )}

          {tipoPDF === 'certificado_medico' && (
            <>
              <Form.Item label="Motivo del Certificado" name="motivo_certificado">
                <Select placeholder="Seleccione...">
                  <Option value="reposo">Reposo Médico</Option>
                  <Option value="aptitud">Aptitud Física</Option>
                  <Option value="incapacidad">Incapacidad Temporal</Option>
                  <Option value="tramite">Trámite Administrativo</Option>
                </Select>
              </Form.Item>
              <Form.Item label="Días de Reposo" name="dias_reposo">
                <Input type="number" placeholder="Número de días" />
              </Form.Item>
              <Form.Item label="Diagnóstico" name="diagnostico">
                <TextArea rows={2} placeholder="Diagnóstico que justifica el certificado..." />
              </Form.Item>
            </>
          )}

          {tipoPDF === 'reporte_ecografia' && (
            <>
              <Form.Item label="Tipo de Ecografía" name="tipo_ecografia">
                <Select placeholder="Seleccione...">
                  <Option value="obstetrica_1t">Obstétrica 1er Trimestre</Option>
                  <Option value="obstetrica_2t">Obstétrica 2do Trimestre</Option>
                  <Option value="obstetrica_3t">Obstétrica 3er Trimestre</Option>
                  <Option value="anatomica">Anatómica Fetal</Option>
                  <Option value="doppler">Doppler</Option>
                </Select>
              </Form.Item>
              <Form.Item label="Hallazgos" name="hallazgos">
                <TextArea rows={5} placeholder="Descripción de los hallazgos ecográficos..." />
              </Form.Item>
              <Form.Item label="Conclusión" name="conclusion">
                <TextArea rows={3} placeholder="Conclusión del estudio..." />
              </Form.Item>
            </>
          )}

          <Divider />
          <Form.Item label="Adjuntar Archivos" name="archivos_adjuntos">
            <Upload.Dragger
              name="files"
              multiple
              beforeUpload={() => false}
              onChange={(info) => {
                message.success(`${info.file.name} agregado correctamente`);
              }}
            >
              <p className="ant-upload-drag-icon">
                📎
              </p>
              <p className="ant-upload-text">
                Click o arrastre archivos para adjuntar
              </p>
              <p className="ant-upload-hint">
                Soporta imágenes, PDFs, resultados de laboratorio, etc.
              </p>
            </Upload.Dragger>
          </Form.Item>

          <Form.Item label="Observaciones Adicionales" name="observaciones">
            <TextArea rows={3} placeholder="Cualquier información adicional relevante..." />
          </Form.Item>
        </div>
      );

    case 2:
      return (
        <div>
          <Alert
            message="Configuración final y generación"
            type="success"
            showIcon
            style={{ marginBottom: 16 }}
          />

          <Card title="Opciones de Generación" size="small">
            <Form.Item name="incluir_logo" valuePropName="checked">
              <Checkbox>Incluir logo de la institución</Checkbox>
            </Form.Item>
            <Form.Item name="incluir_pie" valuePropName="checked">
              <Checkbox>Incluir pie de página con datos de contacto</Checkbox>
            </Form.Item>
            <Form.Item name="incluir_firma" valuePropName="checked">
              <Checkbox>Incluir espacio para firma y sello</Checkbox>
            </Form.Item>
            <Form.Item name="incluir_qr" valuePropName="checked">
              <Checkbox>Incluir código QR de verificación</Checkbox>
            </Form.Item>
            <Form.Item name="copias" label="Número de Copias" initialValue={1}>
              <Select>
                <Option value={1}>1 copia (Original)</Option>
                <Option value={2}>2 copias</Option>
                <Option value={3}>3 copias</Option>
              </Select>
            </Form.Item>
          </Card>

          <Divider />

          <Card title="Vista Previa" size="small">
            <Space direction="vertical" style={{ width: '100%' }}>
              <Tag color="blue">Tipo: {tiposPDF.find(t => t.key === tipoPDF)?.label}</Tag>
              <Tag color="green">Paciente: {pacienteData?.nombre_completo || 'No especificado'}</Tag>
              <Tag color="purple">Fecha: {currentDateLabel}</Tag>
            </Space>
          </Card>
        </div>
      );

    default:
      return null;
  }
};

const PDFGenerator: React.FC<PDFGeneratorProps> = ({
    open,
    onCancel,
    pacienteData,
    embarazoData,
    moduloOrigen
}) => {
    const [form] = Form.useForm();
    const [currentStep, setCurrentStep] = useState(0);
    const [tipoPDF] = useState<string>('historia_clinica');
    const [generandoPDF, setGenerandoPDF] = useState(false);

    const tiposPDF = [
        {
            key: 'historia_clinica',
            label: 'Historia Clínica Completa',
            icon: <FileTextOutlined />,
            color: 'blue',
            descripcion: 'Documento oficial con historial médico completo del paciente'
        },
        {
            key: 'orden_medica',
            label: 'Orden Médica',
            icon: <MedicineBoxOutlined />,
            color: 'green',
            descripcion: 'Orden para exámenes, procedimientos o tratamientos'
        },
        {
            key: 'resultado_laboratorio',
            label: 'Resultado de Laboratorio',
            icon: <ExperimentOutlined />,
            color: 'purple',
            descripcion: 'Reporte oficial de resultados de análisis de laboratorio'
        },
        {
            key: 'reporte_ecografia',
            label: 'Reporte de Ecografía',
            icon: <HeartOutlined />,
            color: 'pink',
            descripcion: 'Informe técnico de estudio ecográfico obstétrico'
        },
        {
            key: 'certificado_medico',
            label: 'Certificado Médico',
            icon: <SafetyOutlined />,
            color: 'cyan',
            descripcion: 'Certificado médico para reposo, trabajo o trámites'
        },
        {
            key: 'receta_medica',
            label: 'Receta Médica',
            icon: <MedicineBoxOutlined />,
            color: 'orange',
            descripcion: 'Prescripción médica con medicamentos y dosis'
        },
        {
            key: 'informe_parto',
            label: 'Informe de Parto',
            icon: <HeartOutlined />,
            color: 'red',
            descripcion: 'Reporte oficial del nacimiento y condiciones del parto'
        },
        {
            key: 'carnet_prenatal',
            label: 'Carnet de Control Prenatal',
            icon: <CalendarOutlined />,
            color: 'green',
            descripcion: 'Carnet con todos los controles prenatales registrados'
        }
    ];

    const handleGenerarPDF = async (values: any) => {
        setGenerandoPDF(true);
        try {
            // Simular generación de PDF (en producción llamaría al backend)
            await new Promise(resolve => setTimeout(resolve, 2000));

            // Crear objeto con datos del PDF
            const pdfData = {
                tipo: tipoPDF,
                paciente: pacienteData,
                embarazo: embarazoData,
                ...values,
                fecha_generacion: new Date().toISOString(),
                generado_por: 'Sistema',
                institucion: 'Hospital Materno Infantil',
                logo: '/logo-hospital.png'
            };

            console.log('Generando PDF:', pdfData);

            // Descargar PDF simulado
            message.success({
                content: 'PDF generado exitosamente',
                duration: 3,
                icon: <CheckCircleOutlined style={{ color: '#52c41a' }} />
            });

            // Resetear formulario
            form.resetFields();
            setCurrentStep(0);
            onCancel();
        } catch (error) {
            message.error('Error generando PDF');
            console.error(error);
        } finally {
            setGenerandoPDF(false);
        }
    };

    const currentDateLabel = useMemo(() => new Date().toISOString().slice(0, 10), []);
    const currentDateISO = useMemo(() => new Date().toISOString().split('T')[0], []);

    return (
        <Modal
            title={
                <Space>
                    <FilePdfOutlined style={{ fontSize: 24, color: '#ff4d4f' }} />
                    <span>Generador de PDFs Oficiales</span>
                    <Badge count="Profesional" style={{ backgroundColor: '#52c41a' }} />
                </Space>
            }
            open={open}
            onCancel={onCancel}
            width={900}
            footer={null}
        >
            <Form
                form={form}
                layout="vertical"
                onFinish={handleGenerarPDF}
            >
                <Steps current={currentStep} style={{ marginBottom: 24 }}>
                    <Step title="Tipo" description="Seleccione documento" />
                    <Step title="Datos" description="Complete información" />
                    <Step title="Generar" description="Configuración final" />
                </Steps>

                <StepContent
                    currentStep={currentStep}
                    tipoPDF={tipoPDF}
                    tiposPDF={tiposPDF}
                    currentDateLabel={currentDateLabel}
                    currentDateISO={currentDateISO}
                    pacienteData={pacienteData}
                />

                <Divider />

                <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
                    {currentStep > 0 && (
                        <Button onClick={() => setCurrentStep(prev => prev - 1)}>
                            Anterior
                        </Button>
                    )}
                    {currentStep < 2 && (
                        <Button type="primary" onClick={() => setCurrentStep(prev => prev + 1)}>
                            Siguiente
                        </Button>
                    )}
                    {currentStep === 2 && (
                        <Space>
                            <Button
                                type="primary"
                                htmlType="submit"
                                icon={<DownloadOutlined />}
                                loading={generandoPDF}
                            >
                                Generar y Descargar PDF
                            </Button>
                            <Button
                                icon={<PrinterOutlined />}
                                onClick={() => message.info('Función de impresión directa')}
                            >
                                Generar e Imprimir
                            </Button>
                            <Button
                                icon={<MailOutlined />}
                                onClick={() => message.info('Función de envío por email')}
                            >
                                Generar y Enviar
                            </Button>
                        </Space>
                    )}
                </Space>
            </Form>
        </Modal>
    );
};

export default PDFGenerator;
