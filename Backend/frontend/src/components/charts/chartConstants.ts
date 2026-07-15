// ==========================================
// COLORES PREDEFINIDOS
// ==========================================

// Animación de entrada consistente para todas las gráficas: suave y breve
// (no distrae al médico que revisa datos bajo presión de tiempo).
export const CHART_ANIM = {
    animationDuration: 800,
    animationBegin: 0,
    animationEasing: 'ease-out' as const,
};

export const CHART_COLORS = {
    primary: ['#1890ff', '#40a9ff', '#69c0ff', '#91d5ff', '#bae7ff'],
    medical: ['#722ed1', '#9254de', '#b37feb', '#d3adf7', '#efdbff'],
    success: ['#52c41a', '#73d13d', '#95de64', '#b7eb8f', '#d9f7be'],
    warning: ['#faad14', '#ffc53d', '#ffd666', '#ffe58f', '#fff1b8'],
    error: ['#f5222d', '#ff4d4f', '#ff7875', '#ffa39e', '#ffccc7'],
    info: ['#13c2c2', '#36cfc9', '#5cdbd3', '#87e8de', '#b5f5ec'],
    gradient: ['#1890ff', '#722ed1', '#eb2f96', '#f5222d', '#fa8c16'],
    prenatal: ['#722ed1', '#9254de', '#b37feb', '#d3adf7', '#efdbff'],
    laboratorio: ['#1890ff', '#52c41a', '#faad14', '#f5222d', '#13c2c2']
};
