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

// Colores de serie: variables de tokens.css, así cambian con el tema. Las
// series son categóricas (distinguibles entre sí), no tonos de un mismo azul.
// Los semánticos (éxito, aviso, peligro, información) solo para estados.
const G = (n: number) => `var(--grafico-${n})`;
const SERIES = [G(1), G(2), G(3), G(4), G(5), G(6)];

export const CHART_COLORS = {
    primary: SERIES,
    medical: [G(6), G(1), G(2), G(3), G(4), G(5)],
    success: ['var(--color-exito)', ...SERIES],
    warning: ['var(--color-aviso)', ...SERIES],
    error: ['var(--color-peligro)', ...SERIES],
    info: ['var(--color-info)', ...SERIES],
    gradient: SERIES,
    prenatal: [G(6), G(1), G(2), G(3), G(4), G(5)],
    laboratorio: [G(2), G(4), G(3), G(5), G(1), G(6)],
};
