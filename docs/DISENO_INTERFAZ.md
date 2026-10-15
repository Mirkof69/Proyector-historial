# Sistema de diseño de la interfaz — Fetal Medical Bolivia

Contrato único de estilos del frontend (14/10/2026). Todo color, tipografía,
espacio, radio y sombra sale de aquí. Ninguna pantalla define colores propios.

## Por qué se rehízo

- 18.886 líneas de CSS en 49 archivos, 728 colores fijos y unos 600
  `!important`. Tres capas peleándose: `antd-overrides.css` (1.661 líneas),
  `theme-dark-fixes.css` y `theme-enhancements.css`, que existían para
  corregirse unas a otras.
- Fallos visibles medidos con capturas (`e2e/tests/pantallas.spec.js`): las
  tarjetas de cifras del panel principal quedaban casi invisibles en tema claro,
  e IA médica pintaba tarjetas negras del tema oscuro sobre el claro.
- Degradados morados y estilos distintos en cada pantalla.

## Dirección

Uso clínico: turnos largos, pantallas de hospital de calidad variable, decisiones
bajo presión. La interfaz es **tranquila, legible y densa en datos**. La
personalidad la dan la tipografía y un solo color de marca, no los adornos.

- Sin degradados de fondo en botones, tarjetas ni encabezados. Sin «glassmorphism».
- Sin sombras grandes: superficies planas separadas por borde de 1 px. Sombra
  solo en lo que flota (menús, modales, notificaciones).
- Sin emojis como iconos ni como marcadores de sección (sí `@ant-design/icons`).
- Un solo acento: el color primario. Los colores semánticos (éxito, aviso,
  peligro, información) son de estado y no se usan como decoración.
- Las cifras clínicas usan `font-variant-numeric: tabular-nums`.

## Tokens

Fuente de verdad: `frontend/src/styles/tokens.css` (variables CSS) y
`frontend/src/config/antd-theme-tokens.ts` (Ant Design), con los MISMOS valores.

### Color — claro (por defecto)

| Token | Valor | Uso |
|---|---|---|
| `--color-primario` | `#155E75` | Botón principal, enlaces, selección, foco |
| `--color-primario-hover` | `#0E4C61` | |
| `--color-primario-suave` | `#E3F1F5` | Fondo de elemento seleccionado / activo |
| `--color-fondo` | `#F4F6F8` | Fondo de la aplicación |
| `--color-superficie` | `#FFFFFF` | Tarjetas, tablas, formularios |
| `--color-superficie-2` | `#F8FAFB` | Cabecera de tabla, zonas secundarias |
| `--color-borde` | `#DDE3E8` | |
| `--color-borde-suave` | `#EBEFF2` | Separadores internos |
| `--color-texto` | `#15212B` | |
| `--color-texto-2` | `#4D5D6A` | Secundario, etiquetas |
| `--color-texto-3` | `#7A8995` | Ayudas, marcadores de posición |
| `--color-exito` | `#1E7B4F` | |
| `--color-aviso` | `#A35F00` | |
| `--color-peligro` | `#B42318` | |
| `--color-info` | `#1D5FA8` | |

Cada semántico tiene `-suave` (fondo de etiqueta/alerta) y `-borde`.

### Color — oscuro (`html.dark`, `[data-theme="dark"]`)

| Token | Valor |
|---|---|
| `--color-primario` | `#5BB6CC` |
| `--color-primario-hover` | `#7FC8DA` |
| `--color-primario-suave` | `#14313A` |
| `--color-fondo` | `#0D1318` |
| `--color-superficie` | `#141C22` |
| `--color-superficie-2` | `#1A242C` |
| `--color-borde` | `#2A3640` |
| `--color-borde-suave` | `#202B33` |
| `--color-texto` | `#E5ECF1` |
| `--color-texto-2` | `#A7B5C0` |
| `--color-texto-3` | `#7D8C97` |
| `--color-exito` | `#4CC38A` |
| `--color-aviso` | `#E3A33B` |
| `--color-peligro` | `#F2766B` |
| `--color-info` | `#6AA6E8` |

Los temas `normal` y `mocha` (que ya existen en `ThemeContext`) se definen igual,
solo cambiando estas variables: `normal` = claro con fondo blanco puro;
`mocha` = oscuro cálido (`--color-fondo #16130F`, superficies `#1E1A15`/`#26211B`,
texto `#EDE6DC`, primario `#D9A56B`). Contraste de texto ≥ 4,5:1 en los cuatro.

### Tipografía

- Interfaz: **IBM Plex Sans** (400, 500, 600), empaquetada con `@fontsource`
  para que funcione sin internet en la red del hospital. Respaldo:
  `"Segoe UI", system-ui, sans-serif`.
- Números e identificadores (CI, código de paciente, valores de laboratorio):
  **IBM Plex Mono** 400/500.
- Escala (px): 12 · 13 · 14 (base) · 16 · 18 · 22 · 28. Títulos de página 22/600;
  títulos de tarjeta 16/600; etiquetas 13/500. `text-wrap: balance` en títulos.
- La escala de letra accesible de `ThemeContext` (`fontScaleFactor`) se sigue
  aplicando sobre la base.

### Espacio, radio, sombra

- Espaciado en múltiplos de 4: `--esp-1` 4 · `--esp-2` 8 · `--esp-3` 12 ·
  `--esp-4` 16 · `--esp-5` 24 · `--esp-6` 32.
- Radio: `--radio-sm` 4, `--radio` 6, `--radio-lg` 8. Nada de 16–24 px.
- Sombra: `--sombra-flotante` solo para capas que flotan.
- Ritmo: separar grupos con `gap` (flex/grid), no con márgenes sueltos.

## Patrones

- **Encabezado de página**: título 22/600 + una línea de descripción en
  `--color-texto-2` + acciones a la derecha. Un solo botón primario por pantalla.
- **Tarjetas de cifras**: superficie blanca, borde, etiqueta 13/500 en
  `--color-texto-2`, cifra 28/600 tabular; color semántico solo si la cifra
  indica un estado (p. ej. riesgo alto en `--color-peligro`).
- **Tablas**: cabecera en `--color-superficie-2`, filas de 44–48 px, sin
  rayado de colores; estados como `Tag` semántico.
- **Formularios**: etiquetas arriba, una columna en móvil y dos en escritorio.
- **Menú lateral**: superficie, elemento activo con `--color-primario-suave` y
  texto primario; sin barras de color decorativas.
- **Foco visible** en todo lo interactivo: `outline: 2px solid var(--color-primario)`.
- `prefers-reduced-motion`: sin animaciones de entrada.
- Móvil (≤ 768 px): sin scroll horizontal de la página; las tablas anchas
  desplazan dentro de su propio contenedor.

## Reglas para el código

1. Colores, radios, sombras y fuentes **solo** con `var(--…)` en CSS, o con
   `theme.useToken()` en componentes. Prohibido un hex fijo fuera de
   `tokens.css` y `antd-theme-tokens.ts`.
2. `!important` solo para ganarle a un estilo en línea de Ant Design que no
   tiene token, y con un comentario que diga cuál.
3. Los estilos en línea (`style={{…}}`) solo para valores dinámicos; los
   estáticos van a la hoja de la página.
4. Una pantalla no redefine `.ant-*` globalmente: se ajusta por token o con una
   clase de la página (`.pacientes-tabla .ant-table…`).

## Verificación

- `npx playwright test tests/pantallas.spec.js`: recorre 68 pantallas × 2 temas;
  falla si hay error de JavaScript, error 500, pantalla en blanco o desborde
  horizontal, y guarda capturas en `e2e/test-results/pantallas/`.
- `npx tsc --noEmit`, `CI=true npx react-scripts test`, `npm run build`.

## Resultado medido (14/10/2026)

| | Antes | Después |
|---|---|---|
| Líneas de CSS | 18.886 en 49 archivos | 7.675 |
| `!important` | ~600 | 13 (movimiento reducido, impresión y el tooltip de Recharts; comentados) |
| Degradados, desenfoques, emojis de interfaz | en casi todas las pantallas | 0 |
| Colores fijos fuera de `tokens.css` / `antd-theme-tokens.ts` | 728 en CSS + cientos en línea | 0 |
| Pantallas sin error (68 × claro/oscuro) | 132/134 | 136/136 |

Hallazgos de paso: cinco hojas de estilo (Pacientes, Embarazos, Controles,
Citas, Laboratorio) nunca se importaban; otras (Usuarios, NotFound,
calculadoras) redefinían `.ant-btn`, `.ant-table` o animaciones para toda la
aplicación; varias páginas declaraban variables en `:root` y cambiaban el tema
de las demás pantallas al cargarse.

