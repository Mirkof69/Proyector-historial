
import React from 'react';
import { Spin } from 'antd';
import { LoadingOutlined } from '@ant-design/icons';

interface GlobalLoaderProps {
    tip?: string;
    fullscreen?: boolean;
    style?: React.CSSProperties;
    className?: string;
}

const antIcon = <LoadingOutlined style={{ fontSize: 48 }} spin />;

export const GlobalLoader: React.FC<GlobalLoaderProps> = ({ tip = 'Cargando sistema...', fullscreen = false, style, className }) => {

    const baseStyle: React.CSSProperties = fullscreen ? {
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        backgroundColor: 'rgba(255, 255, 255, 0.8)',
        backdropFilter: 'blur(5px)',
        zIndex: 9999,
    } : {
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        padding: '40px',
        width: '100%',
        height: '100%'
    };

    const combinedStyle = { ...baseStyle, ...style };

    return (
        <div style={combinedStyle} className={className}>
            <Spin indicator={antIcon} tip={tip} size="large">
                <div style={{ padding: '50px' }} />
            </Spin>
        </div>
    );
};
