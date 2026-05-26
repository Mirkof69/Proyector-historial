import { useMemo } from 'react';
import { App } from 'antd';

export const useMessage = () => {
  const { message } = App.useApp();
  return message;
};

export const useAntdApp = () => {
  const { message, notification, modal } = App.useApp();
  return useMemo(() => ({ message, notification, modal }), [message, notification, modal]);
};
