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
