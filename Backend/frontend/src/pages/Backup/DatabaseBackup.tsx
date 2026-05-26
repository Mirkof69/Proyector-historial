import React, { useReducer, useEffect } from 'react';
import { backupService, Backup, BackupStats } from '../../services/backupService';
import {
    Table, Button, Tag, Tooltip, Space,
    Card, Row, Col, Statistic, Empty, Spin,
    Popconfirm, Modal, Progress, Alert
} from 'antd';
import { useAntdApp } from '../../hooks/useMessage';
import {
    DatabaseOutlined,
    CloudDownloadOutlined,
    DeleteOutlined,
    ReloadOutlined,
    HistoryOutlined,
    HddOutlined,
    ScheduleOutlined,
    PlusOutlined,
    WarningOutlined,
    CheckCircleOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';
import 'dayjs/locale/es';
import relativeTime from 'dayjs/plugin/relativeTime';

import './DatabaseBackup.css';

dayjs.extend(relativeTime);
dayjs.locale('es');

interface BackupState {
    backups: any[];
    stats: any | null;
    loading: boolean;
    creating: boolean;
    restoring: boolean;
}

type BackupAction =
    | { type: 'SET_LOADING'; payload: boolean }
    | { type: 'SET_CREATING'; payload: boolean }
    | { type: 'SET_RESTORING'; payload: boolean }
    | { type: 'SET_DATA'; payload: { backups: any[]; stats: any | null } }
    | { type: 'SET_BACKUPS'; payload: any[] };

const initialState: BackupState = {
    backups: [],
    stats: null,
    loading: false,
    creating: false,
    restoring: false,
};

function backupReducer(state: BackupState, action: BackupAction): BackupState {
    switch (action.type) {
        case 'SET_LOADING':
            return { ...state, loading: action.payload };
        case 'SET_CREATING':
            return { ...state, creating: action.payload };
        case 'SET_RESTORING':
            return { ...state, restoring: action.payload };
        case 'SET_DATA':
            return { ...state, backups: action.payload.backups, stats: action.payload.stats, loading: false };
        case 'SET_BACKUPS':
            return { ...state, backups: action.payload };
        default:
            return state;
    }
}

const DatabaseBackup: React.FC = () => {
    const { message } = useAntdApp();
    const [state, dispatch] = useReducer(backupReducer, initialState);
    const { backups, stats, loading, creating, restoring } = state;

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        dispatch({ type: 'SET_LOADING', payload: true });
        try {
            const [backupsData, statsData] = await Promise.all([
                backupService.listar(),
                backupService.obtenerEstadisticas()
            ]);
            dispatch({ type: 'SET_DATA', payload: { backups: backupsData, stats: statsData } });
        } catch (error) {
            message.error('Error al cargar backups');
            dispatch({ type: 'SET_LOADING', payload: false });
        }
    };

    const handleCreateBackup = async () => {
        dispatch({ type: 'SET_CREATING', payload: true });
        try {
            await backupService.crear({ type: 'manual' });
            message.success('Backup creado exitosamente');
            loadData();
        } catch (error) {
            message.error('Error al crear backup');
        } finally {
            dispatch({ type: 'SET_CREATING', payload: false });
        }
    };

    const handleDelete = async (id: number) => {
        try {
            await backupService.eliminar(id);
            message.success('Backup eliminado');
            loadData();
        } catch (error) {
            message.error('Error al eliminar backup');
        }
    };

    const handleRestore = async (id: number) => {
        Modal.confirm({
            title: '¿Restaurar base de datos?',
            icon: <WarningOutlined style={{ color: 'red' }} />,
            content: (
                <div>
                    <p>Esta acción reemplazará la base de datos actual con la versión seleccionada.</p>
                    <p><strong>¡Se perderán todos los datos creados después de este backup!</strong></p>
                    <Alert
                        message="Advertencia de Seguridad"
                        description="Se recomienda crear un backup manual antes de restaurar."
                        type="warning"
                        showIcon
                    />
                </div>
            ),
            okText: 'Sí, Restaurar',
            okType: 'danger',
            cancelText: 'Cancelar',
            onOk: async () => {
                dispatch({ type: 'SET_RESTORING', payload: true });
                try {
                    await backupService.restaurar(id, true);
                    message.success('Base de datos restaurada exitosamente');
                } catch (error) {
                    message.error('Error al restaurar base de datos');
                } finally {
                    dispatch({ type: 'SET_RESTORING', payload: false });
                }
            }
        });
    };

    const handleDownload = async (id: number, filename: string) => {
        try {
            const blob = await backupService.descargar(id);
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', filename);
            document.body.appendChild(link);
            link.click();
            link.remove();
        } catch (error) {
            message.error('Error al descargar backup');
        }
    };

    const getTypeColor = (type: string) => {
        switch (type) {
            case 'manual': return 'default';
            case 'daily': return 'blue';
            case 'weekly': return 'purple';
            case 'monthly': return 'green';
            default: return 'default';
        }
    };

    const columns = [
        {
            title: 'Archivo',
            dataIndex: 'filename',
            key: 'filename',
            render: (text: string) => <span style={{ fontWeight: 500 }}>{text}</span>
        },
        {
            title: 'Tipo',
            dataIndex: 'type',
            key: 'type',
            render: (type: string) => (
                <Tag color={getTypeColor(type)} className={`type-tag ${type}`}>
                    {type.toUpperCase()}
                </Tag>
            )
        },
        {
            title: 'Tamaño',
            dataIndex: 'size_mb',
            key: 'size',
            render: (size: number) => `${size.toFixed(2)} MB`
        },
        {
            title: 'Fecha',
            dataIndex: 'created_at',
            key: 'created_at',
            render: (date: string) => (
                <Tooltip title={dayjs(date).format('DD/MM/YYYY HH:mm:ss')}>
                    <span>{dayjs(date).fromNow()}</span>
                </Tooltip>
            ),
            sorter: (a: Backup, b: Backup) =>
                new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
        },
        {
            title: 'Acciones',
            key: 'acciones',
            render: (_: any, record: Backup) => (
                <Space>
                    <Tooltip title="Descargar">
                        <Button
                            type="text"
                            className="action-btn download"
                            icon={<CloudDownloadOutlined />}
                            onClick={() => handleDownload(record.id!, record.filename)}
                        />
                    </Tooltip>
                    <Tooltip title="Restaurar">
                        <Button
                            type="text"
                            className="action-btn restore"
                            icon={<HistoryOutlined />}
                            onClick={() => handleRestore(record.id!)}
                            disabled={restoring}
                        />
                    </Tooltip>
                    <Popconfirm
                        title="¿Eliminar backup?"
                        onConfirm={() => handleDelete(record.id!)}
                        okText="Sí"
                        cancelText="No"
                    >
                        <Tooltip title="Eliminar">
                            <Button
                                type="text"
                                className="action-btn delete"
                                icon={<DeleteOutlined />}
                            />
                        </Tooltip>
                    </Popconfirm>
                </Space>
            )
        }
    ];

    return (
        <div className="backup-page fade-in">
            <div className="backup-header">
                <div>
                    <h2>Copias de Seguridad</h2>
                    <div style={{ color: 'var(--text-secondary)' }}>
                        Gestión y restauración de base de datos
                    </div>
                </div>
                <Space>
                    <Button
                        icon={<ReloadOutlined />}
                        onClick={loadData}
                        loading={loading}
                    >
                        Actualizar
                    </Button>
                    <Button
                        type="primary"
                        icon={<PlusOutlined />}
                        onClick={handleCreateBackup}
                        loading={creating}
                    >
                        Crear Backup
                    </Button>
                </Space>
            </div>

            <Spin spinning={loading} tip="Cargando estadísticas…">
                {stats && (
                    <Row gutter={[16, 16]} className="backup-stats-row">
                        <Col xs={24} sm={12} md={6}>
                            <Card>
                                <Statistic
                                    title="Total Backups"
                                    value={stats.total_backups}
                                    prefix={<DatabaseOutlined style={{ color: '#1890ff' }} />}
                                    suffix={<CheckCircleOutlined style={{ color: '#52c41a', fontSize: 16 }} />}
                                    valueStyle={{ color: '#1890ff' }}
                                />
                            </Card>
                        </Col>
                        <Col xs={24} sm={12} md={6}>
                            <Card>
                                <Statistic
                                    title="Espacio Usado"
                                    value={stats.total_size_mb.toFixed(2)}
                                    suffix="MB"
                                    prefix={<HddOutlined style={{ color: '#722ed1' }} />}
                                    valueStyle={{ color: '#722ed1' }}
                                />
                                <Progress
                                    percent={Math.min((stats.total_size_mb / 1000) * 100, 100)}
                                    size="small"
                                    status={stats.total_size_mb > 800 ? 'exception' : 'active'}
                                    style={{ marginTop: 8 }}
                                />
                            </Card>
                        </Col>
                        <Col xs={24} sm={12} md={6}>
                            <Card>
                                <Statistic
                                    title="Programación"
                                    value="Diario"
                                    prefix={<ScheduleOutlined style={{ color: '#52c41a' }} />}
                                    valueStyle={{ color: '#52c41a', fontSize: 20 }}
                                />
                            </Card>
                        </Col>
                        <Col xs={24} sm={12} md={6}>
                            <Card>
                                <Statistic
                                    title="Último Backup"
                                    value={stats.ultimo_backup ? dayjs(stats.ultimo_backup).fromNow() : 'Nunca'}
                                    prefix={<HistoryOutlined style={{ color: '#fa8c16' }} />}
                                    valueStyle={{ color: '#fa8c16', fontSize: 16 }}
                                />
                            </Card>
                        </Col>
                    </Row>
                )}
            </Spin>

            <div className="backup-table-card">
                <Table
                    columns={columns}
                    dataSource={backups}
                    rowKey="id"
                    loading={loading}
                    pagination={{ pageSize: 10 }}
                    locale={{
                        emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No hay backups disponibles" />
                    }}
                />
            </div>
        </div>
    );
};

export default DatabaseBackup;
