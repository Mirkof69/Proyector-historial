import React from 'react';
import {
  Upload, Button, Tag, Spin, Typography, Row, Col, Empty, Tooltip, Select, Space,
} from 'antd';
import {
  InboxOutlined, RobotOutlined, DownloadOutlined, FileImageOutlined,
  EyeOutlined, DeleteOutlined, ExperimentOutlined, LinkOutlined, NodeIndexOutlined,
} from '@ant-design/icons';
import { ImagenEcografica } from '../../../services/iaMedicaService';
import { API_URL } from '../../../services/api';
import { renderResultBadge, getResultClass } from '../iaMedicaHelpers';

const { Title } = Typography;
const { Dragger } = Upload;

interface GaleriaEcografiasProps {
  selectedPacienteId: number | null;
  setSelectedPacienteId: (id: number | null) => void;
  pacientesSearch: {id: number; nombre: string}[];
  searchingPaciente: boolean;
  handlePatientSearch: (query: string) => void;
  uploading: boolean;
  handleUpload: (file: File) => boolean | Promise<boolean>;
  loading: boolean;
  imagenes: ImagenEcografica[];
  analyzingId: number | null;
  analyzingCnnId: number | null;
  ecografiasVinculadas: Record<number, number>;
  handleAnalyze: (id: number) => void;
  showAnalysis: (id: number) => void;
  handleAnalyzeCNN: (img: ImagenEcografica) => void;
  handleVincularClick: (img: ImagenEcografica) => void;
  handleDelete: (id: number) => void;
}

const GaleriaEcografias: React.FC<GaleriaEcografiasProps> = ({
  selectedPacienteId, setSelectedPacienteId, pacientesSearch, searchingPaciente,
  handlePatientSearch, uploading, handleUpload, loading, imagenes, analyzingId,
  analyzingCnnId, ecografiasVinculadas, handleAnalyze, showAnalysis, handleAnalyzeCNN,
  handleVincularClick, handleDelete,
}) => (
  <div className="gallery-container">
    <div className="gallery-toolbar">
      <Title level={4} style={{ margin: 0 }}>Galería de Ecografías</Title>
    </div>

    <Row gutter={[24, 24]}>
      <Col xs={24} md={8} lg={6}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Select
            showSearch
            placeholder="Buscar y seleccionar paciente..."
            value={selectedPacienteId}
            onChange={setSelectedPacienteId}
            onSearch={handlePatientSearch}
            loading={searchingPaciente}
            filterOption={false}
            notFoundContent={searchingPaciente ? <Spin size="small" /> : 'Escriba al menos 2 caracteres'}
            style={{ width: '100%' }}
            allowClear
          >
            {pacientesSearch.map(p => (
              <Select.Option key={p.id} value={p.id}>{p.nombre}</Select.Option>
            ))}
          </Select>
          <Dragger
            customRequest={({ file }) => handleUpload(file as File)}
            showUploadList={false}
            style={{ height: '100%', minHeight: '250px' }}
            disabled={!selectedPacienteId}
          >
            {uploading ? (
              <div><Spin size="large" /><p style={{ marginTop: 16 }}>Subiendo…</p></div>
            ) : (
              <div>
                <p className="ant-upload-drag-icon"><InboxOutlined /></p>
                <p className="ant-upload-text">{selectedPacienteId ? 'Clic o arrastrar imagen aquí' : 'Seleccione un paciente primero'}</p>
                <p className="ant-upload-hint">Soporta JPG, PNG, DICOM (Max: 10MB)</p>
              </div>
            )}
          </Dragger>
        </Space>
      </Col>

      {loading ? (
        <Col span={16} style={{ textAlign: 'center', padding: '50px' }}>
          <Spin size="large" />
        </Col>
      ) : imagenes.length === 0 ? (
        <Col span={16}>
          <Empty description="No hay imágenes subidas aún" />
        </Col>
      ) : (
        imagenes.map(img => (
          <Col xs={24} sm={12} md={8} lg={6} key={img.id}>
            <div className="image-card">
              <div className="image-card-header">
                <img src={`${API_URL.replace('/api', '')}${img.url_imagen}`} alt="Ecografía" />
                <div className="image-status-badge">
                  {img.tiene_analisis ? renderResultBadge(img.analisis_resultado!.resultado) : <Tag color="processing">Pendiente</Tag>}
                </div>
              </div>
              <div className="image-card-body">
                <div className="image-title">{img.paciente_nombre}</div>
                <div className="image-meta">
                  <span><FileImageOutlined /> {img.tamanio_mb} MB • {img.tipo_imagen.replace('_', ' ')}</span>
                  <span>{new Date(img.fecha_subida).toISOString().slice(0, 10)}</span>
                </div>

                {img.tiene_analisis && (
                  <div className="cnn-result">
                    <span className={`cnn-score ${getResultClass(img.analisis_resultado!.resultado)}`}>
                      <RobotOutlined /> Confianza: {img.analisis_resultado!.confianza}%
                    </span>
                  </div>
                )}
              </div>
              <div className="image-card-footer">
                {!img.tiene_analisis ? (
                  <Button
                    type="primary"
                    block
                    icon={<RobotOutlined />}
                    loading={analyzingId === img.id}
                    onClick={() => handleAnalyze(img.id)}
                    style={{ marginBottom: 4 }}
                  >
                    Analizar (legado)
                  </Button>
                ) : (
                  <Button
                    type="default"
                    block
                    icon={<EyeOutlined />}
                    onClick={() => showAnalysis(img.id)}
                    style={{ marginBottom: 4 }}
                  >
                    Ver Resultado
                  </Button>
                )}
                <Tooltip title="Analizar con EfficientNet-B4 + Grad-CAM + SHAP">
                  <Button
                    type="primary"
                    block
                    icon={<ExperimentOutlined />}
                    loading={analyzingCnnId === img.id}
                    onClick={() => handleAnalyzeCNN(img)}
                    style={{ background: '#722ed1', borderColor: '#722ed1', marginBottom: 4 }}
                  >
                    EffNetB4 + Grad-CAM
                  </Button>
                </Tooltip>
                {ecografiasVinculadas[img.id] ? (
                  <Tooltip title={`Ver Ecografía #${ecografiasVinculadas[img.id]}`}>
                    <Button
                      type="link"
                      block
                      icon={<NodeIndexOutlined />}
                      style={{ color: '#52c41a', marginBottom: 4 }}
                      onClick={() => {
                        window.open(`/ecografias/${ecografiasVinculadas[img.id]}`, '_blank');
                      }}
                    >
                      Eco #{ecografiasVinculadas[img.id]}
                    </Button>
                  </Tooltip>
                ) : (
                  <Button
                    block
                    icon={<LinkOutlined />}
                    onClick={() => handleVincularClick(img)}
                    style={{ marginBottom: 4 }}
                  >
                    Vincular a Ecografía
                  </Button>
                )}
                <Tooltip title="Eliminar">
                  <Button danger icon={<DeleteOutlined />} onClick={() => handleDelete(img.id)} />
                </Tooltip>
              </div>
            </div>
          </Col>
        ))
      )}
    </Row>
  </div>
);

export default GaleriaEcografias;
