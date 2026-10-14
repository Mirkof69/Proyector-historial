# Despliegue nativo — Fetal Medical Bolivia

Este sistema se ejecuta **sin Docker**: PostgreSQL como servicio de Windows,
Django con uvicorn, el microservicio de IA con uvicorn y el frontend servido
como estáticos. Docker se retiró por completo del proyecto.

---

## 1. Ajuste de PostgreSQL (una sola vez, requiere administrador)

Los valores por defecto de PostgreSQL asumen una máquina de 1 GB de RAM. En
esta máquina (60 GB) eso deja al sistema muy por debajo de lo que puede dar, y
—más importante— `max_connections = 100` es lo que provocaba los errores
HTTP 500 bajo carga:

> `FATAL: lo siento, ya tenemos demasiados clientes`

Los ajustes ya están escritos en `postgresql.auto.conf` mediante `ALTER SYSTEM`:

| Ajuste | Antes | Ahora | ¿Necesita reinicio? |
|---|---|---|---|
| `max_connections` | 100 | **300** | Sí |
| `shared_buffers` | 128 MB | **4 GB** | Sí |
| `effective_cache_size` | 4 GB | **16 GB** | No |
| `work_mem` | 4 MB | **16 MB** | No (ya activo) |
| `maintenance_work_mem` | 64 MB | **512 MB** | No |

### Aplicarlos

Abrir PowerShell **como administrador** y ejecutar:

```powershell
Restart-Service postgresql-x64-18 -Force
```

Verificar que quedó aplicado:

```powershell
cd "c:\Users\Miscar\Desktop\Nueva carpeta\historial\Backend"
python -c "import psycopg; c=psycopg.connect(dbname='historial',user='postgres',password='<DB_PASSWORD>',host='127.0.0.1'); cur=c.cursor(); cur.execute('SHOW max_connections'); print('max_connections =', cur.fetchone()[0])"
```

Resultado esperado: `max_connections = 300`.

### Después del reinicio: activar las conexiones persistentes

Con `max_connections = 300` ya hay margen para que Django mantenga conexiones
abiertas entre peticiones, y eso vale **8× de velocidad** en el listado de
pacientes. Añadir a `Backend/.env`:

```
DB_CONN_MAX_AGE=60
```

Medido con 100 usuarios concurrentes:

| Configuración | Listado p50 | Errores 500 |
|---|---|---|
| `max_connections=100`, `CONN_MAX_AGE=60` | 280 ms | ~1.283 |
| `max_connections=100`, `CONN_MAX_AGE=0` | 2.100 ms | 0 |
| `max_connections=300`, `CONN_MAX_AGE=60` | *pendiente de medir tras el reinicio* | |

**Por qué el valor por defecto es 0:** con 100 conexiones, mantenerlas vivas
60 s deja ~80 ociosas retenidas y la API empieza a devolver 500. Una pantalla
lenta es peor que nada; una que falla una de cada tres veces es inaceptable.
Subir `DB_CONN_MAX_AGE` **sin** haber subido antes `max_connections`
reintroduce los errores.

---

## 2. Arranque del sistema

`INICIAR.bat` levanta todo en orden (`INICIAR.bat desarrollo` para programar, `INICIAR.bat detener` para cerrar). Los componentes por separado:

```powershell
# PostgreSQL (servicio de Windows)
net start postgresql-x64-18

# Backend Django
cd Backend
python -m uvicorn asgi:application --host 0.0.0.0 --port 8000 --workers 4

# Microservicio de IA
cd Backend\Microservicio_IA
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001

# Frontend
cd Backend\frontend
npm start
```

---

## 3. Servir en una red IP (no solo localhost)

Para que otras máquinas de la clínica accedan al sistema:

**`Backend/.env`:**
```
ALLOWED_HOSTS=localhost,127.0.0.1,192.168.1.50
CORS_ALLOWED_ORIGINS=http://192.168.1.50:3000
CSRF_TRUSTED_ORIGINS=http://192.168.1.50:3000
```
(sustituir `192.168.1.50` por la IP real del servidor)

**Arrancar escuchando en todas las interfaces:**
```powershell
python -m uvicorn asgi:application --host 0.0.0.0 --port 8000 --workers 4
```

**Regla de firewall** (PowerShell como administrador):
```powershell
New-NetFirewallRule -DisplayName "Fetal Medical API" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow
```

### Cuidado con `localhost` en las URLs internas

`AI_SERVICE_URL` debe usar **`127.0.0.1`, no `localhost`**. En Windows,
`localhost` resuelve primero a `::1` (IPv6); si el microservicio escucha en
IPv4, cada llamada paga el intento fallido antes de reintentar.

Medido: `localhost` → **2.024 ms**, `127.0.0.1` → **2 ms**. Sobre el análisis
de una ecografía eso era la diferencia entre 2.342 ms y 200 ms.

---

## 4. Multi-tenant: los dominios

`django-tenants` enruta por el `Host` de la petición. Los dominios registrados
se consultan así:

```powershell
cd Backend
python -c "import os,django; os.environ.setdefault('DJANGO_SETTINGS_MODULE','settings'); django.setup(); from clientes.models import Domain; [print(d.domain, '->', d.tenant.schema_name) for d in Domain.objects.all()]"
```

Al servir en una IP hay que registrar esa IP como dominio del tenant, o la
petición no encuentra la clínica y falla la autenticación.

---

## 5. Qué se retiró

Docker se eliminó del proyecto por completo:

- `docker-compose.yml`, los 5 `Dockerfile`, `.dockerignore`, `.env.docker`
- El job `docker-build` de CI y el ecosistema `docker` de dependabot
- `.github/workflows/cd.yml` — todo el despliegue continuo estaba construido
  sobre imágenes Docker y un `docker compose up` por SSH
- `scripts/deploy.sh` — 719 líneas de despliegue con Docker Compose en Ubuntu
- `kong/` — Kong solo existía como contenedor; su `KONG_JWT_SECRET` ya caía a
  `SECRET_KEY`, así que su ausencia no cambia la firma de los JWT

**Consecuencia a tener presente:** ya no hay despliegue automatizado. El
despliegue es el arranque nativo de la sección 2. Si más adelante hace falta
automatizarlo, el reemplazo natural es un script de PowerShell que haga
`git pull`, `pip install -r requirements.txt`, `migrate`, `npm run build` y
reinicie los servicios.
