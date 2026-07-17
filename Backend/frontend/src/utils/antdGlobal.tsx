/**
 * Puente entre el mundo NO-React (interceptores de axios, utilidades) y las
 * instancias de modal/message/notification del <App> de antd.
 *
 * Los estáticos (Modal.error, message.success importados de 'antd') NO
 * consumen el ConfigProvider: en modo oscuro renderizaban un modal claro con
 * título ilegible (medido 1.14:1 en la auditoría). Este módulo captura las
 * instancias del contexto una vez montada la app y las expone globalmente,
 * con fallback a los estáticos si todavía no montó.
 */
import { useEffect } from 'react';
import { App as AntdApp, Modal, message as messageEstatico, notification as notificationEstatica } from 'antd';
import type { useAppProps } from 'antd/es/app/context';

let instancia: useAppProps | null = null;

export const antdGlobal = {
  get modal() {
    return instancia?.modal ?? Modal;
  },
  get message() {
    return instancia?.message ?? messageEstatico;
  },
  get notification() {
    return instancia?.notification ?? notificationEstatica;
  },
};

/** Montar UNA vez dentro de <AntdApp> (lo hace App.tsx). */
export const AntdGlobalBridge: React.FC = () => {
  const app = AntdApp.useApp();
  useEffect(() => {
    instancia = app;
    return () => {
      instancia = null;
    };
  }, [app]);
  return null;
};
