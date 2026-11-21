import { getWebSocketUrl } from './NotificationsContext';

describe('getWebSocketUrl', () => {
  it('en desarrollo usa el mismo puerto que la API', () => {
    expect(getWebSocketUrl('http://192.168.0.6:8000/api', 'development', undefined)).toBe('ws://192.168.0.6:8000/ws/notifications/');
  });
  it('en producción la API (WSGI) está en el 8000 y los WebSockets en el 8010', () => {
    expect(getWebSocketUrl('http://192.168.0.6:8000/api', 'production', undefined)).toBe('ws://192.168.0.6:8010/ws/notifications/');
  });
  it('REACT_APP_WS_URL manda sobre todo', () => {
    expect(getWebSocketUrl('http://x:8000/api', 'production', 'wss://clinica.bo/ws/notifications/')).toBe('wss://clinica.bo/ws/notifications/');
  });
  it('una API en otro puerto no se toca', () => {
    expect(getWebSocketUrl('http://x:9000/api', 'production', undefined)).toBe('ws://x:9000/ws/notifications/');
  });
});
