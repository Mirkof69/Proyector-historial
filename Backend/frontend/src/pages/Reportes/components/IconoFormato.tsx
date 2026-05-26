import React from 'react';
import { FilePdfOutlined, FileExcelOutlined } from '@ant-design/icons';

interface IconoFormatoProps {
  formato: string;
}

const IconoFormato: React.FC<IconoFormatoProps> = ({ formato }) => {
  return formato === 'PDF'
    ? <FilePdfOutlined style={{ fontSize: '24px', color: '#ff4d4f' }} />
    : <FileExcelOutlined style={{ fontSize: '24px', color: '#52c41a' }} />;
};

export default IconoFormato;
