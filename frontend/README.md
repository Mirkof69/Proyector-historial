# Frontend - Historia Clínica Obstétrica

Frontend de React 18 + TypeScript usando Ant Design 5.x.

## Tecnologías

- **React 18** - UI library
- **TypeScript 4.9** - Type safety
- **Ant Design 5** - Component library
- **Recharts** - Charts & graphs
- **React Router 6** - Client-side routing
- **Axios** - HTTP client (API proxy via src/setupProxy.js)

El sistema de mensajes/modales utiliza el patrón `App.useApp()` de antd v5.

## Scripts disponibles

En el directorio del proyecto, puedes ejecutar:

### `npm start`

Inicia el servidor de desarrollo.
Abre [http://localhost:3000](http://localhost:3000) para verlo en el navegador.

La página se recargará si haces modificaciones.
También verás errores de lint en la consola.

### `npm test`

Ejecuta el test runner en modo interactivo.

### `npm run build`

Compila la app para producción en la carpeta `build`.

### `npm run eject`

**Nota: esta es una operación irreversible.**

## Proxy de API

El proxy de API está configurado en `src/setupProxy.js` para redirigir peticiones al backend Django durante el desarrollo.
