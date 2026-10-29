# Prompt de instalación — Fetal Medical Bolivia en otra PC

> Copia TODO este texto y pégalo en Claude Code (o en el asistente de IA que
> uses) abierto en la carpeta del proyecto, ya descomprimida del RAR, en la PC
> nueva. Está escrito para que el asistente lo siga paso a paso y te pregunte
> solo lo que no puede saber.

---

## Tu tarea

Instala y deja funcionando **Fetal Medical Bolivia**, un sistema de historia
clínica perinatal (obstetricia y ginecología) con inteligencia artificial, en
esta PC con Windows. El proyecto viene de otra PC dentro de un RAR, con su base
de datos respaldada y sus datasets. Al terminar debe quedar:

1. PostgreSQL 18 con **la base de datos del proyecto restaurada desde el
   respaldo** (no una base vacía ni datos de demostración nuevos).
2. Si en esta PC ya existe una base antigua con el mismo nombre: respáldala
   primero y después elimínala, para restaurar la nuestra limpia.
3. El backend (Django), el frontend (React), el servicio de IA (FastAPI con
   13 redes) y Redis funcionando, arrancando con `INICIAR.bat`.
4. Los datasets y los pesos de las redes en su lugar.
5. Todo verificado, sin errores, con las pruebas pasando.

Trabaja en español. Antes de cada paso que borre o cambie algo, dime qué vas a
hacer. Si algo falla, no lo «arregles» cambiando datos o desactivando
validaciones: averigua la causa y dímela.

---

## Qué es el sistema (contexto)

| Pieza | Tecnología | Dónde | Puerto |
|---|---|---|---|
| Frontend | React 18 + TypeScript + Ant Design 5 | `Backend/frontend/` | 3000 |
| API | Django 6 + Django REST Framework + django-tenants, servida con waitress | `Backend/` | 8000 |
| Notificaciones en vivo | Django Channels sobre uvicorn (1 worker) + **Redis** | `Backend/` | 8010 |
| Servicio de IA | FastAPI + PyTorch (13 redes entrenadas) | `Backend/Microservicio_IA/` | 8001 |
| Base de datos | **PostgreSQL 18**, una sola clínica: esquema compartido `public` y esquema `clinica` con todos los datos del hospital | servicio de Windows | 5432 |
| Caché y mensajería | Redis (Windows) | `C:\Program Files\Redis` | 6379 |

- Los usuarios viven en el esquema `public`; los datos clínicos en el esquema
  de cada clínica. Las migraciones se aplican con
  `manage.py migrate_schemas --noinput`, y los comandos por clínica con
  `manage.py tenant_command <comando> --schema=clinica`.
- Nombre, CI, teléfono, correo y dirección de las pacientes están **cifrados**
  con las claves de `Backend/.env` (`ENCRYPTION_KEY`, `ENCRYPTION_SALT`,
  `SEARCH_HMAC_KEY`). **Si esas claves cambian, los datos restaurados quedan
  ilegibles.**

---

## Reglas que no se rompen

1. **No** ejecutes `MIGRAR_Y_SEED.bat` ni ningún comando `seed_*`: cargan
   pacientes ficticios encima de los reales.
2. **No** ejecutes `instalar_postgres.ps1`: está desactualizado (instala
   PostgreSQL 16) y el respaldo es de PostgreSQL 18.4.
3. **No** cambies `SECRET_KEY`, `ENCRYPTION_KEY`, `ENCRYPTION_SALT` ni
   `SEARCH_HMAC_KEY` de `Backend/.env`. Solo puedes ajustar `DB_PASSWORD`,
   `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS` y rutas.
4. **No** borres nada dentro de `Backend/Microservicio_IA/datos/` (datasets,
   incluidos los `.zip` de `datos/crudos/`) ni de `trained_models/`.
5. **No** muestres en pantalla ni copies a otros archivos las contraseñas ni
   las claves del `.env`.
6. Antes de eliminar una base antigua, haz un `pg_dump` de ella a
   `Backend/backups/antes_de_reemplazar_<fecha>.sql`.
7. Nunca subas `Backend/.env` ni `Backend/backups/` a git.

---

## Paso 0 · Revisar lo que llegó en el RAR

Comprueba que existan (y dime el tamaño de cada uno):

- `Backend/.env` → configuración y claves (sin él no se puede seguir: pídemelo).
- `Backend/backups/BASE_PARA_INSTALAR_20261029.sql` → la base real del hospital,
  sin datos de demostración (~0,6 MB: catálogos, cuentas y configuración). Su
  SHA-256 empieza por `7b211ddc0685b1a0`; verifícalo. **No** uses los
  `BASE_PARA_INSTALAR_20261021/20261026` ni los `backup_demo_*`: son la demo vieja.
- `Backend/Microservicio_IA/trained_models/` → pesos `.pth` de las redes.
- `Backend/Microservicio_IA/datos/` → datasets (~25 GB).
- `Backend/Microservicio_IA/entrenamiento/` → scripts y métricas de entrenamiento.

Las carpetas `Backend/.venv`, `Backend/Microservicio_IA/.venv` y
`node_modules` copiadas de la otra PC **no sirven aquí** (tienen rutas de la
otra máquina): se recrean en los pasos siguientes. No las uses.

## Paso 1 · Programas necesarios

Verifica cada uno y, si falta, instálalo con `winget` (pídeme permiso de
administrador cuando haga falta):

| Programa | Versión | Comando |
|---|---|---|
| Python | 3.12.x (no 3.13) | `winget install -e --id Python.Python.3.12` |
| Node.js | 20 o superior | `winget install -e --id OpenJS.NodeJS.LTS` |
| PostgreSQL | **18** | `winget install -e --id PostgreSQL.PostgreSQL.18` (anota la contraseña del superusuario `postgres` que elijo) |
| Redis para Windows | 3.0 o Memurai | instalarlo en `C:\Program Files\Redis` (como servicio «Redis») |
| Git | cualquiera | `winget install -e --id Git.Git` |

PostgreSQL debe quedar en `C:\Program Files\PostgreSQL\18\` y Redis en
`C:\Program Files\Redis\`, porque `INICIAR.bat` los busca ahí.

Tarjeta gráfica: ejecuta `nvidia-smi`. Si hay GPU NVIDIA, el servicio de IA
usará CUDA; si no, funciona igual con CPU (más lento: segundos en vez de
milisegundos por imagen).

## Paso 2 · PostgreSQL: la base de datos

1. Lee de `Backend/.env` los valores `DB_NAME`, `DB_USER`, `DB_HOST`,
   `DB_PORT` y `DB_PASSWORD`, sin mostrarlos. Si `DB_PASSWORD` no coincide con
   la contraseña del superusuario que puse al instalar, pregúntame cuál usar y
   actualiza solo esa línea.
2. Verifica que el servicio `postgresql-x64-18` esté corriendo
   (`pg_isready -h 127.0.0.1 -p 5432`).
3. **Base antigua:** si ya existe una base llamada `DB_NAME`:
   1. respáldala: `pg_dump -U <DB_USER> -F p -f Backend\backups\antes_de_reemplazar_<fecha>.sql <DB_NAME>`;
   2. dime cuántas tablas y pacientes tenía;
   3. elimínala: `dropdb -U <DB_USER> --if-exists <DB_NAME>` (cierra antes las
      conexiones abiertas si da error de «base en uso»).
4. Crea la base vacía: `createdb -U <DB_USER> -E UTF8 <DB_NAME>`.
5. **Restaura nuestro respaldo:**
   `psql -U <DB_USER> -d <DB_NAME> -v ON_ERROR_STOP=1 -q -f Backend\backups\BASE_PARA_INSTALAR_20261029.sql`.
   Debe terminar sin ningún `ERROR`. (Se probó en la PC original: 0 errores.)
6. Ajustes de rendimiento (necesitan reiniciar el servicio como administrador):
   ```sql
   ALTER SYSTEM SET max_connections = 300;
   ALTER SYSTEM SET shared_buffers = '2GB';   -- 4GB si la PC tiene 32 GB o más de RAM
   ```
   Luego `net stop postgresql-x64-18` y `net start postgresql-x64-18` en una
   consola de administrador. Solo después de esto agrega
   `DB_CONN_MAX_AGE=60` en `Backend/.env`.
7. Comprueba que la restauración trajo los datos. Valores esperados (los de la
   PC original el 29/10/2026, base real recién creada):

   | Esquema.tabla | Registros |
   |---|---|
   | `clinica.pacientes` | 0 (el hospital las registra) |
   | `clinica.tipos_examenes` | 30 |
   | `clinica.valores_referencia` | 79 |
   | `clinica.tipos_vacunas` | 3 |
   | `clinica.tipos_reporte` | 8 |
   | `clinica.horarios_atencion` | 7 |
   | `clinica.consultorios` | 1 |
   | `clinica.disponibilidades` | 10 |
   | `public.usuarios` | 11 (6 activas) |
   | tablas en total | 100 |

   Si la base se arma desde cero en vez de restaurarla: `migrate_schemas
   --noinput` y después `manage.py preparar_clinica` (crea la clínica, sus
   dominios y todos los catálogos; se puede repetir sin duplicar nada).

## Paso 3 · Backend (Django)

En `Backend/`:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe manage.py check
.venv\Scripts\python.exe manage.py migrate_schemas --noinput
.venv\Scripts\python.exe manage.py showmigrations --list | findstr "\[ \]"
```

- `migrate_schemas` debe decir que no hay nada pendiente o aplicar solo lo que
  falte. El último comando no debe mostrar nada (ninguna migración sin aplicar).
- Cuando ya haya pacientes, comprueba que los datos cifrados se leen: el
  nombre de una paciente debe verse como texto normal, no como texto cifrado.
  Si se ve cifrado, el `.env` no es el de la PC original: detente y avísame.
  ```powershell
  .venv\Scripts\python.exe manage.py tenant_command shell --schema=clinica -c "from pacientes.models import Paciente; p=Paciente.objects.order_by('id').first(); print(p.id, p.nombre[:1] + '…')"
  ```

## Paso 4 · Frontend (React)

En `Backend/frontend/`:

```powershell
npm install
npx tsc --noEmit -p .
npm run build
```

`tsc` debe terminar con 0 errores. (`package-lock.json` no se versiona; por eso
se usa `npm install`, no `npm ci`.)

## Paso 5 · Servicio de IA

El servicio de IA usa el **Python del sistema** (no el `.venv` del backend):

```powershell
cd Backend\Microservicio_IA
# Con GPU NVIDIA:
py -3.12 -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
# Sin GPU:
py -3.12 -m pip install torch torchvision
py -3.12 -m pip install -r requirements.txt
```

Comprueba que estén los 13 pesos en `trained_models/` (y en
`entrenamiento/*/salidas/` los de origen). Luego arráncalo una vez a mano y
consulta `http://127.0.0.1:8001/health`: debe decir `"status": "healthy"` y
listar 13 redes precargadas.

## Paso 6 · Arrancar todo

Desde la raíz del proyecto: doble clic en **`INICIAR.bat`** (modo producción).
La primera vez, ejecútalo **como administrador** para que PostgreSQL y Redis
queden como servicios.

`INICIAR.bat` hace 8 pasos y dice «LISTO» al final:

1. Revisa los requisitos.
2. Cierra servicios anteriores.
3. Arranca PostgreSQL.
4. Arranca Redis.
5. Aplica las migraciones.
6. Compila el frontend si cambió.
7. Habilita la red de la clínica (agrega la IP de esta PC al `.env` y a los
   dominios).
8. Arranca la API, las notificaciones, la IA y el frontend, y comprueba que
   cada uno responda.

Otros modos: `INICIAR.bat desarrollo` y `INICIAR.bat detener`.

Comprueba:
- `http://localhost:3000` abre el login.
- `http://localhost:8000/api/health/` responde 200.
- `http://localhost:8001/health` responde 200.
- Desde otra PC de la red: `http://<IP de esta PC>:3000`. Recomienda fijar
  una IP para el servidor.

## Paso 7 · Verificación final

En `Backend/`:

```powershell
.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
```

Esperado: unas 1.033 pruebas pasan (6 omitidas). En
`Backend/Microservicio_IA/` con el Python del sistema:
`py -3.12 -m pytest -q`.

Pruebas de navegador, con el sistema arrancado (en `Backend/e2e/`):

```powershell
npm install
npx playwright install chromium
$env:E2E_PASSWORD = "<contraseña de las cuentas de demostración: pídemela>"
npx playwright test --reporter=line
```

Esperado: 164 pasan. Incluye un recorrido de las 68 pantallas en tema claro y
oscuro sin errores.

## Paso 8 · Informe

Al final dame:
- qué instalaste y qué versiones;
- si había una base antigua y dónde quedó su respaldo;
- los conteos de la tabla del Paso 2 obtenidos aquí;
- el resultado de `INICIAR.bat`, de `pytest` y de Playwright;
- cualquier diferencia o error, con su causa.

---

## Las redes de inteligencia artificial (qué son y para qué sirven)

Todos los modelos son **supervisados**: aprendieron de miles de ejemplos que un
experto ya había etiquetado («esto es un fémur», «este trazado es patológico»)
y después se midieron en pacientes que nunca vieron. Esa medida es la que
muestra el sistema. Todo es **apoyo a la decisión**: el diagnóstico lo hace el
médico.

### 13 redes neuronales convolucionales (CNN), sobre imágenes de ecografía

Una **CNN** mira la imagen por capas. Primero unos filtros detectan bordes y
texturas, después los combina en formas (el óvalo del cráneo, la burbuja del
estómago) y al final decide o mide.

**Clasificación** (la respuesta es una categoría):

| Red | Qué hace | Fiabilidad medida |
|---|---|---|
| Plano anatómico (EfficientNet-B0) | Reconoce qué corte es: cabeza, abdomen, fémur, tórax… | 92,7 % (5.271 imágenes de 896 madres) |
| Anomalías cerebrales (EfficientNet-B0) | Cribado de anomalías en cortes de cabeza | 1 falsa alarma en 1.866 cabezas; sensibilidad real no medible: solo orienta |
| Tipo de lesión ovárica (2 EfficientNet-B0 combinadas) | Tipo probable entre 8 y alarma de carcinoma | 68,6 %; la alarma detecta 7 de 13 (si no suena, no descarta) |
| Ovario poliquístico (EfficientNet-B0) | Normal / folículo dominante / poliquístico | 80 % |

**Segmentación U-Net** (dibuja el contorno de cada estructura y el sistema
mide sobre ese dibujo):

| Red | Qué dibuja y mide | Fiabilidad medida |
|---|---|---|
| Cabeza fetal | Cráneo → circunferencia cefálica, DBP, edad gestacional | Error de 4,4 mm en otro hospital (HC18) |
| Tórax | Tórax y corazón → índice cardiotorácico | Dice 0,93; índice ±0,02 |
| Abdomen | Estómago, vena umbilical, aorta | Dice 0,69–0,84 |
| Intraparto | Pubis y cabeza → ángulo de progresión del parto | Error de 6,7° |
| Lesión ovárica | Contorno de la lesión | Dice 0,85; la encuentra en el 88 % |
| Mioma uterino | Ubicación del mioma | Lo ubica en el 96,9 % |

**Regresión con CNN** (la respuesta es un número):

| Red | Qué mide | Fiabilidad medida |
|---|---|---|
| Circunferencia cefálica (regresión) | CC en mm directamente de la imagen | R² 0,978; error de 7,0 mm |
| Fémur (red de puntos) | Marca los extremos como los calibres del ecografista → longitud | Error de 1,3 mm; 92 % dentro del 5 % |
| Circunferencia abdominal (red de puntos) | Marca los diámetros → circunferencia | Error del 2,9 %; 89 % dentro del 5 % |

### Modelos supervisados sobre tablas (no son redes neuronales)

| Modelo | Tipo | Qué hace | Fiabilidad medida |
|---|---|---|---|
| Cardiotocografía | **Gradient boosting** (muchos árboles de decisión pequeños, cada uno corrige al anterior); clasificación supervisada | Clasifica el monitoreo fetal: normal, sospechoso o patológico | 96 % en 423 registros; detecta el 94 % de los patológicos |
| Peso al nacer | **Regresión lineal Ridge**; regresión supervisada | Estima el peso del bebé en gramos a partir de la biometría | Error de 183 g, medido con partos simulados: solo demostración hasta reentrenarlo con partos reales |

### Evaluados y descartados

Se entrenaron y se midieron, y **no** pasan a servicio porque no alcanzaron la
fiabilidad necesaria:

- acidemia fetal por CTG (AUC 0,73);
- parto prematuro por electrohisterograma (sin señal);
- translucencia nucal (94,8 % en el mismo hospital, 68,6 % en otro);
- cardiopatía por variables maternas (AUC 0,70);
- cáncer cervicouterino por factores de riesgo;
- riesgo materno general;
- la antigua EfficientNet-B4 de «14 patologías».

### Dónde se usan en el sistema

- Menú **Análisis CNN (IA)**:
  - pestaña Ecografía: «Analizar» y «Informe completo»;
  - pestaña Ecografía ginecológica;
  - pestaña Cardiotocografía.
- **Partos → Trabajo de parto → Registrar tacto**: ángulo de progresión desde
  la imagen.
- **Ficha de cada ecografía**: «IA medida» y el peso al nacer previsto.
- Menú **Guía de IA**: explica cada modelo con su fiabilidad medida y lleva a
  su pantalla con «Usar ahora».

Los datasets con que se entrenaron están en `Backend/Microservicio_IA/datos/`:
FETAL_PLANES_DB, HC18, Large-Scale Fetal Head Biometry, FOCUS, Fetal Abdominal
Structures, IUGC 2024, Fetal Brain Abnormalities, Multicentre Fetal Biometry,
MMOTU (ovario), miomas, ovario poliquístico, CTG de 2.126 registros, entre
otros. Los originales comprimidos están en `datos/crudos/`. Las métricas de
cada red están en `entrenamiento/*/salidas/*/metricas.json` y en
`docs/sistema/10_inteligencia_artificial.md`.

---

## Problemas conocidos y su solución

| Síntoma | Causa | Qué hacer |
|---|---|---|
| PostgreSQL arranca con `pg_ctl` y cuelga conexiones (error 487) | No corre como servicio de Windows | Ejecutar `INICIAR.bat` como administrador una vez |
| Las notificaciones no llegan en vivo | Redis apagado, o `REDIS_URL` vacío | Arrancar el servicio «Redis»; `INICIAR.bat` define `REDIS_URL` |
| Error 500 «demasiados clientes» | `max_connections` en 100 | Paso 2.6 |
| Otras PC no entran | La IP del servidor cambió (DHCP) | `INICIAR.bat` la agrega solo; fijar la IP |
| Login no guarda la sesión | Se mezcló `localhost` con `127.0.0.1` | Usar siempre la misma dirección |
| Un médico nuevo no entra en producción | El MFA es obligatorio para médicos y administradores | Configurar Google Authenticator en el primer ingreso |
| `UNREGISTERED` en las imágenes de StarUML | StarUML sin licencia | Solo afecta la exportación por línea de comandos |
| Error al instalar `torch` | Versión de Python o de CUDA incorrecta | Usar Python 3.12 y la URL `cu124` (o la versión CPU) |

Documentación completa:
- `docs/sistema/` (requisitos, casos de uso, arquitectura, IA, despliegue);
- `docs/sistema/11_despliegue_y_operacion.md` para la operación diaria;
- `RESPALDO_DIARIO.bat` para programar el respaldo automático diario.
