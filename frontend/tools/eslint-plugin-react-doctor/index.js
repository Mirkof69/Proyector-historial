/**
 * Declara ante ESLint las reglas de react-doctor, sin implementarlas.
 *
 * Por qué existe
 * --------------
 * `react-doctor` analiza el código con oxlint, no con ESLint, pero honra los
 * comentarios `// eslint-disable-next-line react-doctor/<regla>` — hay 23
 * archivos que los usan y son correctos para esa herramienta.
 *
 * ESLint, en cambio, no conoce esas reglas y trata cada comentario como
 * error: «Definition for rule 'react-doctor/...' was not found». Eran 25 de
 * los 27 errores de lint del proyecto, puro ruido, y por eso el CI ejecutaba
 * ESLint con `continue-on-error: true` — es decir, ESLint no vigilaba nada.
 *
 * Este plugin declara las reglas como no-op para que ESLint acepte los
 * comentarios. Cada herramienta hace su trabajo: react-doctor sigue
 * aplicándolas de verdad, y ESLint deja de gritar por algo que no le
 * corresponde y puede volver a ser una barrera que bloquee.
 *
 * Si algún día se añade una regla nueva de react-doctor, hay que declararla
 * aquí también.
 */

/** Regla vacía: nunca reporta nada. La aplica react-doctor, no ESLint. */
const reglaNoOperativa = {
  meta: {
    type: 'problem',
    docs: { description: 'Declarada para ESLint; la aplica react-doctor (oxlint).' },
    schema: [],
  },
  create: () => ({}),
};

module.exports = {
  rules: {
    'exhaustive-deps': reglaNoOperativa,
    'no-adjust-state-on-prop-change': reglaNoOperativa,
    'no-initialize-state': reglaNoOperativa,
    'prefer-dynamic-import': reglaNoOperativa,
  },
};
