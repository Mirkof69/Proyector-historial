// jest-dom añade matchers personalizados de jest para verificar el DOM.
// permite hacer cosas como:
// expect(element).toHaveTextContent(/react/i)
// aprender más: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom';

// jsdom no implementa window.matchMedia. Ant Design lo usa internamente
// (Grid/responsiveObserver para breakpoints, Table, etc.) — sin este shim
// cualquier componente de antd con lógica responsive falla al renderizar
// en los tests con "window.matchMedia is not a function".
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  }),
});
