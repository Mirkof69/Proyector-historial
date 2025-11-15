# 🚀 GUÍA DE INSTALACIÓN COMPLETA - Sistema de Historial Médico Obstétrico

## 📋 REQUISITOS PREVIOS

Antes de empezar, asegúrate de tener instalado:

1. **Python 3.8+** - [Descargar](https://www.python.org/downloads/)
   - Verifica: `python --version` o `python3 --version`

2. **Node.js 16+** y **npm** - [Descargar](https://nodejs.org/)
   - Verifica: `node --version` y `npm --version`

3. **PostgreSQL** - [Descargar](https://www.postgresql.org/download/)
   - Verifica: `psql --version`

4. **Git** (ya lo tienes si descargaste el proyecto)

---

# 🔧 PARTE 1: INSTALACIÓN DEL BACKEND

## Paso 1: Navegar al directorio del backend

```bash
cd Proyector-historial/Backend/historial
```

## Paso 2: Crear entorno virtual de Python

### En Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

### En Linux/Mac:
```bash
python3 -m venv venv
source venv/bin/activate
```

**Verás `(venv)` al inicio de tu terminal cuando esté activado.**

## Paso 3: Instalar dependencias de Python

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Esto instalará:**
- Django 5.1.3
- Django REST Framework
- djangorestframework-simplejwt (JWT)
- django-cors-headers (CORS)
- psycopg2-binary (PostgreSQL)
- python-decouple (variables de entorno)
- Pillow (imágenes)
- Y todas las demás dependencias

## Paso 4: Configurar la base de datos PostgreSQL

### Opción A: Crear base de datos manualmente

```bash
# Entrar a PostgreSQL
psql -U postgres

# Dentro de psql, ejecutar:
CREATE DATABASE historial_medico;
CREATE USER historial_user WITH PASSWORD 'historial_pass';
ALTER ROLE historial_user SET client_encoding TO 'utf8';
ALTER ROLE historial_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE historial_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE historial_medico TO historial_user;
\q
```

### Opción B: Restaurar desde el archivo SQL (si tienes datos)

```bash
psql -U postgres -f ../../historial.sql
```

## Paso 5: Configurar variables de entorno

Crear archivo `.env` en `Backend/historial/`:

```bash
# En Backend/historial/
touch .env
```

**Contenido del archivo `.env`:**

```env
# Django
SECRET_KEY=tu-secret-key-super-segura-aqui-cambiarla
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Base de datos
DATABASE_NAME=historial_medico
DATABASE_USER=historial_user
DATABASE_PASSWORD=historial_pass
DATABASE_HOST=localhost
DATABASE_PORT=5432

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# JWT (opcional, usa valores por defecto si no se especifican)
ACCESS_TOKEN_LIFETIME=60
REFRESH_TOKEN_LIFETIME=1440
```

## Paso 6: Aplicar migraciones

```bash
python manage.py migrate
```

**Verás algo como:**
```
Running migrations:
  Applying usuarios.0001_initial... OK
  Applying pacientes.0001_initial... OK
  Applying embarazos.0001_initial... OK
  Applying controles.0001_initial... OK
  ...
```

## Paso 7: Crear superusuario (admin)

```bash
python manage.py createsuperuser
```

**Te pedirá:**
- Username: `admin` (o el que quieras)
- Email: `admin@example.com`
- Password: `admin123` (o el que quieras)
- Confirmar password

## Paso 8: Cargar datos de prueba (opcional)

```bash
python manage.py shell
```

Dentro del shell de Django:

```python
from usuarios.models import Usuario

# Crear médico de prueba
Usuario.objects.create_user(
    username='medico1',
    email='medico@hospital.com',
    password='medico123',
    nombre='Juan',
    apellido='Pérez',
    rol='medico',
    especialidad='Obstetricia',
    matricula='MP12345'
)

# Crear enfermera de prueba
Usuario.objects.create_user(
    username='enfermera1',
    email='enfermera@hospital.com',
    password='enfermera123',
    nombre='María',
    apellido='García',
    rol='enfermero'
)

# Salir
exit()
```

## Paso 9: Iniciar el servidor backend

```bash
python manage.py runserver
```

**Verás:**
```
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK (Windows) or CONTROL-C (Linux/Mac).
```

### ✅ Verificar que funciona:

Abre tu navegador en: `http://localhost:8000/admin`
- Deberías ver la pantalla de login del admin de Django
- Inicia sesión con el superusuario que creaste

---

# ⚛️ PARTE 2: INSTALACIÓN DEL FRONTEND

## Paso 1: Abrir una NUEVA terminal

**NO cierres la terminal del backend**, abre una nueva.

## Paso 2: Navegar al directorio del frontend

```bash
cd Proyector-historial/frontend
```

## Paso 3: Instalar dependencias de Node.js

```bash
npm install
```

**Esto instalará (puede tardar 2-5 minutos):**
- React 19.0.0
- TypeScript
- Ant Design 5.27.6
- React Router DOM 6.30.1
- Axios 1.12.2
- Day.js
- jsPDF
- Y todas las demás dependencias (~200MB)

**Si ves warnings, no te preocupes. Son normales.**

## Paso 4: Configurar variables de entorno

Crear archivo `.env` en `frontend/`:

```bash
# En frontend/
touch .env
```

**Contenido del archivo `.env`:**

```env
REACT_APP_API_URL=http://localhost:8000/api
```

## Paso 5: Iniciar el servidor frontend

```bash
npm start
```

**Verás:**
```
Compiled successfully!

You can now view frontend in the browser.

  Local:            http://localhost:3000
  On Your Network:  http://192.168.x.x:3000

Note that the development build is not optimized.
```

**Se abrirá automáticamente en tu navegador:** `http://localhost:3000`

---

# 🎯 VERIFICAR QUE TODO FUNCIONA

## 1. Backend funcionando ✅

- Terminal 1 muestra: `"GET /api/... HTTP/1.1" 200`
- Puedes acceder a: `http://localhost:8000/admin`

## 2. Frontend funcionando ✅

- Terminal 2 muestra: `Compiled successfully!`
- Navegador abre: `http://localhost:3000`
- Ves la página de login o landing page

## 3. Integración Backend ↔ Frontend ✅

### Probar Login:

1. Ir a `http://localhost:3000`
2. Hacer login con:
   - **Username**: `admin`
   - **Password**: `admin123`
3. Deberías entrar al Dashboard con estadísticas

### Verificar en la consola del navegador (F12):

- **NO debe haber errores CORS**
- **NO debe haber errores 401 (Unauthorized)**
- Deberías ver peticiones exitosas: `200 OK`

### Verificar en la terminal del backend:

Deberías ver peticiones llegando:
```
[14/Nov/2025 21:50:00] "POST /api/usuarios/login/ HTTP/1.1" 200 1234
[14/Nov/2025 21:50:05] "GET /api/pacientes/estadisticas/ HTTP/1.1" 200 567
```

---

# 📦 RESUMEN DE COMANDOS

## Iniciar TODO el sistema (siempre):

### Terminal 1 - Backend:
```bash
cd Proyector-historial/Backend/historial
source venv/bin/activate  # Windows: venv\Scripts\activate
python manage.py runserver
```

### Terminal 2 - Frontend:
```bash
cd Proyector-historial/frontend
npm start
```

---

# 🔧 SOLUCIÓN DE PROBLEMAS COMUNES

## Problema 1: "ModuleNotFoundError: No module named 'django'"

**Solución:**
```bash
# Activar el entorno virtual
source venv/bin/activate  # o venv\Scripts\activate
pip install -r requirements.txt
```

## Problema 2: "django.db.utils.OperationalError: FATAL: database does not exist"

**Solución:**
```bash
# Crear la base de datos
psql -U postgres
CREATE DATABASE historial_medico;
\q
python manage.py migrate
```

## Problema 3: "npm: command not found"

**Solución:**
- Instalar Node.js desde: https://nodejs.org/

## Problema 4: "Port 3000 is already in use"

**Solución:**
```bash
# Windows
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:3000 | xargs kill -9
```

## Problema 5: CORS Error en el navegador

**Solución:**
1. Verificar que el backend esté corriendo
2. Verificar archivo `.env` del backend tenga:
   ```
   CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
   ```
3. Reiniciar el servidor backend

## Problema 6: "npm install" falla

**Solución:**
```bash
# Limpiar caché y reinstalar
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

## Problema 7: Error con psycopg2

**Solución:**
```bash
# Windows
pip install psycopg2-binary

# Linux
sudo apt-get install python3-dev libpq-dev
pip install psycopg2-binary

# Mac
brew install postgresql
pip install psycopg2-binary
```

---

# 📚 ESTRUCTURA DE ARCHIVOS IMPORTANTES

```
Proyector-historial/
│
├── Backend/historial/
│   ├── venv/                    # Entorno virtual (se crea)
│   ├── .env                     # Variables de entorno (CREAR)
│   ├── manage.py                # Comando principal Django
│   ├── requirements.txt         # Dependencias Python
│   ├── historial/               # Configuración Django
│   │   └── settings.py          # Configuración principal
│   ├── usuarios/                # App de usuarios
│   ├── pacientes/               # App de pacientes
│   ├── embarazos/               # App de embarazos
│   ├── controles/               # App de controles
│   └── calculadoras/            # App de calculadoras
│
├── frontend/
│   ├── node_modules/            # Dependencias Node (se crea)
│   ├── .env                     # Variables de entorno (CREAR)
│   ├── package.json             # Dependencias y scripts
│   ├── public/                  # Archivos públicos
│   └── src/                     # Código fuente
│       ├── components/          # Componentes React
│       ├── pages/               # Páginas
│       ├── services/            # Servicios API
│       ├── types/               # TypeScript types
│       └── utils/               # Utilidades
│
└── historial.sql                # Backup de base de datos (opcional)
```

---

# ✅ CHECKLIST DE INSTALACIÓN

## Backend:
- [ ] Python 3.8+ instalado
- [ ] PostgreSQL instalado y corriendo
- [ ] Entorno virtual creado (`venv/`)
- [ ] Dependencias instaladas (`pip install -r requirements.txt`)
- [ ] Base de datos creada (`historial_medico`)
- [ ] Archivo `.env` configurado
- [ ] Migraciones aplicadas (`python manage.py migrate`)
- [ ] Superusuario creado (`python manage.py createsuperuser`)
- [ ] Servidor corriendo (`python manage.py runserver`)
- [ ] Admin accesible en `http://localhost:8000/admin`

## Frontend:
- [ ] Node.js y npm instalados
- [ ] Dependencias instaladas (`npm install`)
- [ ] Archivo `.env` configurado
- [ ] Servidor corriendo (`npm start`)
- [ ] Aplicación abierta en `http://localhost:3000`
- [ ] Login funciona correctamente
- [ ] Dashboard muestra estadísticas
- [ ] No hay errores CORS en consola

---

# 🎓 USUARIOS DE PRUEBA

Después de crear usuarios con los comandos anteriores:

| Username    | Password     | Rol       | Descripción                |
|-------------|--------------|-----------|----------------------------|
| admin       | admin123     | admin     | Superusuario (acceso total)|
| medico1     | medico123    | medico    | Médico obstetra            |
| enfermera1  | enfermera123 | enfermero | Enfermera                  |

---

# 📞 CONTACTO Y AYUDA

Si tienes problemas:

1. **Verifica los logs:**
   - Backend: Terminal donde corre `python manage.py runserver`
   - Frontend: Terminal donde corre `npm start`
   - Navegador: Consola del navegador (F12 → Console)

2. **Errores comunes:** Revisa la sección "Solución de problemas" arriba

3. **Base de datos:** Verifica que PostgreSQL esté corriendo:
   ```bash
   # Windows
   services.msc → PostgreSQL

   # Linux
   sudo systemctl status postgresql

   # Mac
   brew services list
   ```

---

# 🚀 PRÓXIMOS PASOS

Una vez que todo esté funcionando:

1. **Explorar el sistema:**
   - Dashboard con estadísticas
   - CRUD de Pacientes
   - CRUD de Embarazos
   - CRUD de Controles Prenatales
   - Calculadoras FMF
   - Gestión de Usuarios

2. **Crear datos de prueba:**
   - Registrar pacientes
   - Crear embarazos
   - Registrar controles prenatales
   - Probar calculadoras
   - Generar PDF de historial médico

3. **Revisar documentación:**
   - `README_COMPLETO.md` - Documentación completa del frontend
   - `INTEGRACION_BACKEND_FRONTEND.md` - Guía de integración

---

**¡Listo! Ahora tienes el sistema completo funcionando. 🎉**

**Fecha**: 2025-11-14
**Versión**: 1.0.0
