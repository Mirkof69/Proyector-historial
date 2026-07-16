import React, { useReducer, useEffect, useState } from 'react';
import { backupService, Backup } from '../../services/backupService';
import {
    Table, Button, Tooltip, Space,
    Card, Row, Col, Statistic, Empty, Spin,
    Popconfirm, Input, Alert
} from 'antd';
import { useAntdApp } from '../../hooks/useMessage';
import {
    DatabaseOutlined,
    CloudDownloadOutlined,
    DeleteOutlined,
    ReloadOutlined,
    HistoryOutlined,
    HddOutlined,
    PlusOutlined,
    WarningOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import 'dayjs/locale/es';
import relativeTime from 'dayjs/plugin/relativeTime';

import './DatabaseBackup.css';

dayjs.extend(relativeTime);
dayjs.locale('es');

interface BackupState {
    backups: Backup[];
    loading: boolean;
    creating: boolean;
    restoring: string | null;
}

type BackupAction =
    | { type: 'SET_LOADING'; payload: boolean }
    | { type: 'SET_CREATING'; payload: boolean }
    | { type: 'SET_RESTORING'; payload: string | null }
    | { type: 'SET_BACKUPS'; payload: Backup[] };

const initialState: BackupState = {
    backups: [],
    loading: false,
    creating: false,
    restoring: null,
};

function backupReducer(state: BackupState, action: BackupAction): BackupState {
    switch (action.type) {
        case 'SET_LOADING':
            return { ...state, loading: action.payload };
        case 'SET_CREATING':
            return { ...state, creating: action.payload };
        case 'SET_RESTORING':
            return { ...state, restoring: action.payload };
        case 'SET_BACKUPS':
            return { ...state, backups: action.payload, loading: false };
        default:
            return state;
    }
}

const DatabaseBackup: React.FC = () => {
    const { modal, message } = useAntdApp();
    const [state, dispatch] = useReducer(backupReducer, initialState);
    const { backups, loading, creating, restoring } = state;
    const [confirmacionRestaurar, setConfirmacionRestaurar] = useState('');

    const loadData = React.useCallback(async () => {
        dispatch({ type: 'SET_LOADING', payload: true });
        try {
            const backupsData = await backupService.listar();
            dispatch({ type: 'SET_BACKUPS', payload: backupsData });
        } catch (error) {
            message.error('Error al cargar backups');
            dispatch({ type: 'SET_LOADING', payload: false });
        }
    }, [message]);

    useEffect(() => {
        loadData();
    }, [loadData]);

    const handleCreateBackup = async () => {
        dispatch({ type: 'SET_CREATING', payload: true });
        try {
            await backupService.crear();
            message.success('Backup creado exitosamente');
            loadData();
        } catch (error: any) {
            message.error(error?.response?.data?.message || error?.response?.data?.error || 'Error al crear backup');
        } finally {
            dispatch({ type: 'SET_CREATING', payload: false });
        }
    };

    const handleDelete = async (filename: string) => {
        try {
            await backupService.eliminar(filename);
            message.success('Backup eliminado');
            loadData();
        } catch (error) {
            message.error('Error al eliminar backup');
        }
    };

    const handleDownload = async (filename: string) => {
        try {
            const blob = await backupService.descargar(filename);
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', filename);
            document.body.appendChild(link);
            link.click();
            link.remove();
            window.URL.revokeObjectURL(url);
        } catch (error) {
            message.error('Error al descargar backup');
        }
    };

    const ejecutarRestauracion = async (filename: string) => {
        dispatch({ type: 'SET_RESTORING', payload: filename });
        try {
            const resultado = await backupService.restaurar(filename);
            message.success(`Base de datos restaurada. Backup de seguridad pre-restore: ${resultado.backup_seguridad}`);
            loadData();
        } catch (error: any) {
            message.error(error?.response?.data?.error || 'Error al restaurar base de datos');
        } finally {
            dispatch({ type: 'SET_RESTORING', payload: null });
        }
    };

    const handleRestore = (filename: string) => {
        setConfirmacionRestaurar('');
        modal.confirm({
            title: '¿Restaurar base de datos?',
            icon: <WarningOutlined style={{ color: 'red' }} />,
            width: 520,
            content: (
                <div>
                    <p>Esta acción reemplazará <strong>toda</strong> la base de datos actual con el contenido de <strong>{filename}</strong>.</p>
                    <p>Se perderán todos los datos creados después de ese backup. El sistema creará automáticamente un backup de seguridad de la base actual antes de restaurar, pero esta operación es destructiva.</p>
                    <Alert
                        message="Para confirmar, escriba RESTAURAR en el campo de abajo"
                        type="warning"
                        showIcon
                        style={{ marginBottom: 12 }}
                    />
                    <Input
                        placeholder="RESTAURAR"
                        onChange={(e) => setConfirmacionRestaurar(e.target.value)}
                    />
                </div>
            ),
            okText: 'Sí, Restaurar',
            okType: 'danger',
            cancelText: 'Cancelar',
            onOk: async () => {
                if (confirmacionRestaurar.trim() !== 'RESTAURAR') {
                    message.error('Debe escribir RESTAURAR exactamente para confirmar');
                    return Promise.reject();
                }
                await ejecutarRestauracion(filename);
            },
        });
    };

    const totalSizeBytes = backups.reduce((acc, b) => acc + (b.size || 0), 0);
    const ultimoBackup = backups[0]?.created_at;

    const columns = [
        {
            title: 'Archivo',
            dataIndex: 'filename',
            key: 'filename',
            render: (text: string) => <span style={{ fontWeight: 500 }}>{text}</span>
        },
        {
            title: 'Tamaño',
            dataIndex: 'size',
            key: 'size',
            render: (size: number) => `${(size / (1024 * 1024)).toFixed(2)} MB`
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
                            onClick={() => handleDownload(record.filename)}
                        />
                    </Tooltip>
                    <Tooltip title="Restaurar">
                        <Button
                            type="text"
                            className="action-btn restore"
                            icon={<HistoryOutlined />}
                            onClick={() => handleRestore(record.filename)}
                            loading={restoring === record.filename}
                            disabled={restoring !== null}
                        />
                    </Tooltip>
                    <Popconfirm
                        title="¿Eliminar backup?"
                        onConfirm={() => handleDelete(record.filename)}
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

            <Spin spinning={loading}>
                <Row gutter={[16, 16]} className="backup-stats-row">
                    <Col xs={24} sm={12} md={8}>
                        <Card>
                            <Statistic
                                title="Total Backups"
                                value={backups.length}
                                prefix={<DatabaseOutlined style={{ color: '#1890ff' }} />}
                                valueStyle={{ color: '#1890ff' }}
                            />
                        </Card>
                    </Col>
                    <Col xs={24} sm={12} md={8}>
                        <Card>
                            <Statistic
                                title="Espacio Usado"
                                value={(totalSizeBytes / (1024 * 1024)).toFixed(2)}
                                suffix="MB"
                                prefix={<HddOutlined style={{ color: '#722ed1' }} />}
                                valueStyle={{ color: '#722ed1' }}
                            />
                        </Card>
                    </Col>
                    <Col xs={24} sm={12} md={8}>
                        <Card>
                            <Statistic
                                title="Último Backup"
                                value={ultimoBackup ? dayjs(ultimoBackup).fromNow() : 'Nunca'}
                                prefix={<HistoryOutlined style={{ color: '#fa8c16' }} />}
                                valueStyle={{ color: '#fa8c16', fontSize: 16 }}
                            />
                        </Card>
                    </Col>
                </Row>
            </Spin>

            <div className="backup-table-card">
                <Table
                    columns={columns}
                    dataSource={backups}
                    rowKey="filename"
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
