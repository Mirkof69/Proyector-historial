/**
 * Logger central del frontend.
 *
 * En desarrollo escribe a la consola; en producción los niveles de traza
 * (debug/info/log) quedan silenciados para no ensuciar la consola del usuario
 * final. Los errores y advertencias SIEMPRE se emiten.
 */
const isDev = process.env.NODE_ENV === 'development';

export const logger = {
  debug: (...args: unknown[]): void => {
    if (isDev) console.debug(...args);
  },
  info: (...args: unknown[]): void => {
    if (isDev) console.info(...args);
  },
  log: (...args: unknown[]): void => {
    if (isDev) console.log(...args);
  },
  warn: (...args: unknown[]): void => {
    console.warn(...args);
  },
  error: (...args: unknown[]): void => {
    console.error(...args);
  },
};

export default logger;
