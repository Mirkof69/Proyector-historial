# Cómo levantar el sistema, y por qué así

Números medidos el **4 de septiembre de 2026** contra el servidor real, con
100 usuarias simultáneas durante tres minutos y las cuentas de los tres roles.
No son estimaciones.

Máquina de la prueba: 16 núcleos lógicos, 60 GB de RAM, PostgreSQL 18.4 nativo.

---

## El comando

```
python -m uvicorn asgi:application --host 0.0.0.0 --port 8000 --workers 8
```

**`--workers 8`, no 4.** Es el único parámetro que cambió el resultado de
verdad. Mismo código, misma máquina, misma prueba:

| | 4 workers | 8 workers |
|---|---|---|
| Peticiones servidas | 5.022 | **6.305** |
| Fallos | 0 | **0** |
| Peticiones por segundo | 28,0 | **35,1** |
| Mediana | 1.100 ms | **490 ms** |
| p95 | 4.500 ms | **3.000 ms** |
| p99 | 5.600 ms | **4.300 ms** |

La mediana se parte por la mitad. Django atiende cada petición de forma
síncrona, así que con cuatro procesos las cien usuarias hacen cola; con ocho,
no. La regla práctica es **la mitad de los núcleos**, y con 16 núcleos eso son
8. Subir más empieza a competir por las conexiones a la base.

`--host 0.0.0.0` para que el sistema sea accesible desde la red de la clínica.
Para pruebas en la misma máquina, `127.0.0.1` — pero **nunca `localhost`**: en
Windows resuelve primero a IPv6 y cada llamada al microservicio paga ~2 s de
intento fallido.

---

## Entrar desde otro equipo de la clínica

Esto no funcionaba, y fallaba de la peor manera posible: con un **404**, que
parece una dirección mal escrita en vez de lo que era.

El sistema es multi-tenant. Cada clínica vive en su propio esquema de base de
datos, y django-tenants decide a cuál entrar **mirando la dirección por la que
llegó la petición**. Esa correspondencia vive en una tabla, y el 5 de
septiembre de 2026 esa tabla tenía exactamente dos filas:

    localhost   -> clinica_demo
    127.0.0.1   -> clinica_demo

Las dos apuntan al mismo ordenador. Es decir, el sistema funcionaba
**únicamente en la máquina donde corre**. Desde el equipo de recepción o el del
consultorio, `http://192.168.0.6:8000` devolvía 404 siempre.

### Los tres pasos, y hacen falta los tres

**1. Registrar la dirección como dominio de la clínica**

```
python manage.py registrar_dominio --detectar-ip --tenant clinica_demo
```

`--detectar-ip` averigua la IP de este equipo en la red local. Si la red usa
DHCP y la IP cambia, se vuelve a ejecutar. Para ver lo que hay registrado:
`python manage.py registrar_dominio --listar`.

**2. Añadir la misma dirección al `.env`**

```
ALLOWED_HOSTS=localhost,127.0.0.1,192.168.0.6,clinica-demo.localhost,clinica-demo.127.0.0.1
CORS_ALLOWED_ORIGINS=...,http://192.168.0.6:3000,http://192.168.0.6:3100
CSRF_TRUSTED_ORIGINS=...,http://192.168.0.6:3000,http://192.168.0.6:3100
```

Sin esto Django rechaza la petición antes de llegar al enrutador de tenants,
así que el paso 1 por sí solo no basta.

**3. Escuchar en todas las interfaces**

```
python -m uvicorn asgi:application --host 0.0.0.0 --port 8000 --workers 8
```

Con `--host 127.0.0.1` el servidor solo acepta conexiones de la propia máquina,
por muy bien configurado que esté todo lo demás.

### Verificado

Con los tres pasos aplicados, medido contra el servidor real:

| Dirección | Antes | Ahora |
|---|---|---|
| `127.0.0.1:8034` | 401 (correcto, sin sesión) | 401 |
| `localhost:8034` | 401 | 401 |
| `192.168.0.6:8034` | **404** | **401** |

Y un inicio de sesión completo por la IP de red: **200 en 1,0 s**.

El 401 es la respuesta correcta: significa «te reconozco, pero no has iniciado
sesión». El 404 significaba «no sé de qué clínica me hablas».

---

## El requisito de 150 altas por minuto

Medido aparte, porque el perfil de uso normal no lo prueba: hay que empujar
solo escrituras.

| | Medido | Objetivo |
|---|---|---|
| Altas por minuto sostenidas | **228** | 150 |
| Fallos | **0** | — |
| Mediana por alta | **140 ms** | — |
| p95 por alta | **230 ms** | — |

Se cumple con un 52% de margen. Y lo importante no es solo el ritmo, sino que
la latencia por alta —140 ms— no da señales de saturación: el sistema no está
al límite, está cómodo.

---

## PostgreSQL

Los ajustes van en el `.env`, no en el código:

```
DB_CONN_MAX_AGE=60
```

**Solo si la base tiene `max_connections = 300`.** Con los 100 por defecto,
`CONN_MAX_AGE=60` retenía 87 conexiones ociosas de 100 y la API devolvía 500
una de cada tres veces. Por eso el valor por defecto en el código es 0, que
funciona con cualquier configuración: es el `.env` de cada despliegue el que
decide subirlo, y quien lo suba tiene que haber ajustado la base antes.

`APLICAR_AJUSTES_POSTGRES.bat` deja la base como corresponde. Después hay que
reiniciar el servicio `postgresql-x64-18`.

---

## El límite de intentos de login

```
LOGIN_THROTTLE_RATE=20/min
```

Veinte por minuto y por IP, contando **solo los intentos fallidos**. Esa
distinción es la diferencia entre que la clínica pueda trabajar o no.

En una clínica todo el personal sale a internet por una sola IP. Contando
todos los intentos, en el cambio de turno entraban veinte personas y las demás
recibían 429 — medido: **23 de 100 usuarias no pudieron entrar**, y como se
quedaron sin sesión, sus 1.249 peticiones siguientes fueron 401. Un 27,7% de
fallos que no venía de ningún error del sistema.

Contando solo los fallos, las 100 entran (verificado: 100 de 100, cero 429) y
el ataque que el límite frena sigue frenado, porque quien recorre una lista de
usuarios genera fallos, no aciertos.

---

## El microservicio de IA

```
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

Con **su propio intérprete**: el Python 3.12 del sistema, que es el que tiene
torch y `python-multipart`. El entorno virtual de Django no los tiene y no
debe tenerlos.

En `.env` del backend:

```
AI_SERVICE_URL=http://127.0.0.1:8001
```

Con IP, no con `localhost`, por lo dicho arriba.

---

## El frontend

```
python servir_produccion.py
```

Sirve `build/` con gzip y cacheo de un año para los archivos con hash en el
nombre. La carga inicial son **395 KB comprimidos** (377 de JavaScript, 18 de
CSS): unos 2 segundos en 3G normal y unos 8 en 3G lento, **solo la primera
vez** — después queda en la caché del navegador y las pantallas siguientes
solo piden datos, que van comprimidos y por debajo de 50 KB.

Bajar esos 377 KB de forma significativa implica sustituir Ant Design, que es
otro proyecto y no una optimización.
