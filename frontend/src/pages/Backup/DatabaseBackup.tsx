import React, { useReducer, useEffect } from 'react';
import { backupService, Backup } from '../../services/backupService';
import {
    Table, Button, Tooltip, Space,
    Card, Statistic, Empty, Spin,
    Popconfirm, Input, Alert, Typography, Upload
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
    UploadOutlined,
    WarningOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import 'dayjs/locale/es';
import relativeTime from 'dayjs/plugin/relativeTime';

import './DatabaseBackup.css';

const { Title, Text } = Typography;

dayjs.extend(relativeTime);
dayjs.locale('es');

interface BackupState {
    backups: Backup[];
    loading: boolean;
    creating: boolean;
    uploading: boolean;
    restoring: string | null;
}

type BackupAction =
    | { type: 'SET_LOADING'; payload: boolean }
    | { type: 'SET_CREATING'; payload: boolean }
    | { type: 'SET_UPLOADING'; payload: boolean }
    | { type: 'SET_RESTORING'; payload: string | null }
    | { type: 'SET_BACKUPS'; payload: Backup[] };

const initialState: BackupState = {
    backups: [],
    loading: false,
    creating: false,
    uploading: false,
    restoring: null,
};

function backupReducer(state: BackupState, action: BackupAction): BackupState {
    switch (action.type) {
        case 'SET_LOADING':
            return { ...state, loading: action.payload };
        case 'SET_CREATING':
            return { ...state, creating: action.payload };
        case 'SET_UPLOADING':
            return { ...state, uploading: action.payload };
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
    const { backups, loading, creating, uploading, restoring } = state;

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

    const handleUpload = async (archivo: File) => {
        dispatch({ type: 'SET_UPLOADING', payload: true });
        try {
            const resultado = await backupService.cargar(archivo);
            message.success(`Respaldo cargado: ${resultado.filename}. Ya se puede restaurar desde la lista.`);
            loadData();
        } catch (error: any) {
            message.error(error?.response?.data?.error || 'No se pudo cargar el respaldo');
        } finally {
            dispatch({ type: 'SET_UPLOADING', payload: false });
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

    // El botón se habilita recién al escribir RESTAURAR. Antes el onOk comparaba
    // un useState que el modal había copiado en el primer render (''), así que
    // rechazaba siempre y «Restaurar» no se podía usar desde la pantalla.
    const handleRestore = (filename: string) => {
        const dialogo = modal.confirm({
            title: '¿Restaurar base de datos?',
            icon: <WarningOutlined className="backup-page__icono-peligro" />,
            width: 520,
            content: (
                <div>
                    <p>Esta acción reemplazará <strong>toda</strong> la base de datos actual con el contenido de <strong>{filename}</strong>.</p>
                    <p>Se perderán todos los datos creados después de ese backup. El sistema creará automáticamente un backup de seguridad de la base actual antes de restaurar, pero esta operación es destructiva.</p>
                    <Alert
                        message="Para confirmar, escriba RESTAURAR en el campo de abajo"
                        type="warning"
                        showIcon
                        className="backup-page__aviso-restaurar"
                    />
                    <Input
                        placeholder="RESTAURAR"
                        aria-label="Confirmación de restauración"
                        onChange={(e) => dialogo.update({
                            okButtonProps: { disabled: e.target.value.trim() !== 'RESTAURAR' },
                        })}
                    />
                </div>
            ),
            okText: 'Sí, Restaurar',
            okType: 'danger',
            okButtonProps: { disabled: true },
            cancelText: 'Cancelar',
            onOk: () => ejecutarRestauracion(filename),
        });
    };

    const totalSizeBytes = backups.reduce((acc, b) => acc + (b.size || 0), 0);
    const ultimoBackup = backups[0]?.created_at;

    const columns = [
        {
            title: 'Archivo',
            dataIndex: 'filename',
            key: 'filename',
            render: (text: string) => <span className="backup-page__archivo">{text}</span>
        },
        {
            title: 'Tamaño',
            dataIndex: 'size',
            key: 'size',
            render: (size: number) => <span className="tabular-nums">{`${(size / (1024 * 1024)).toFixed(2)} MB`}</span>
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
                            className="backup-page__accion--descargar"
                            aria-label={`Descargar ${record.filename}`}
                            icon={<CloudDownloadOutlined />}
                            onClick={() => handleDownload(record.filename)}
                        />
                    </Tooltip>
                    <Tooltip title="Restaurar">
                        <Button
                            type="text"
                            className="backup-page__accion--restaurar"
                            aria-label={`Restaurar ${record.filename}`}
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
                                className="backup-page__accion--eliminar"
                                aria-label={`Eliminar ${record.filename}`}
                                icon={<DeleteOutlined />}
                            />
                        </Tooltip>
                    </Popconfirm>
                </Space>
            )
        }
    ];

    return (
        <div className="backup-page page-container">
            <header className="backup-page__cabecera">
                <div>
                    <Title level={2}>Copias de Seguridad</Title>
                    <Text type="secondary">
                        Gestión y restauración de base de datos
                    </Text>
                </div>
                <Space>
                    <Button
                        icon={<ReloadOutlined />}
                        onClick={loadData}
                        loading={loading}
                    >
                        Actualizar
                    </Button>
                    <Upload
                        accept=".sql"
                        showUploadList={false}
                        beforeUpload={(archivo) => {
                            handleUpload(archivo as File);
                            return false;
                        }}
                    >
                        <Button icon={<UploadOutlined />} loading={uploading}>
                            Cargar respaldo
                        </Button>
                    </Upload>
                    <Button
                        type="primary"
                        icon={<PlusOutlined />}
                        onClick={handleCreateBackup}
                        loading={creating}
                    >
                        Crear Backup
                    </Button>
                </Space>
            </header>

            <Spin spinning={loading}>
                <div className="backup-page__cifras">
                    <Card size="small">
                        <Statistic
                            title={<><DatabaseOutlined />Total Backups</>}
                            value={backups.length}
                        />
                    </Card>
                    <Card size="small">
                        <Statistic
                            title={<><HddOutlined />Espacio Usado</>}
                            value={(totalSizeBytes / (1024 * 1024)).toFixed(2)}
                            suffix="MB"
                        />
                    </Card>
                    <Card size="small" className="backup-page__cifra-texto">
                        <Statistic
                            title={<><HistoryOutlined />Último Backup</>}
                            value={ultimoBackup ? dayjs(ultimoBackup).fromNow() : 'Nunca'}
                        />
                    </Card>
                </div>
            </Spin>

            <Card>
                <Table
                    columns={columns}
                    dataSource={backups}
                    rowKey="filename"
                    loading={loading}
                    pagination={{ defaultPageSize: 10 }}
                    locale={{
                        emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No hay backups disponibles" />
                    }}
                    scroll={{ x: 560 }}
                />
            </Card>
        </div>
    );
};

export default DatabaseBackup;
