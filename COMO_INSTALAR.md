# 🔴 INSTRUCCIONES PASO A PASO - LÉEME PRIMERO

## ⚠️ IMPORTANTE: DEBES SEGUIR ESTE ORDEN

```
1. INSTALAR (solo la primera vez)
2. INICIAR (cada vez que quieras usar el sistema)
```

---

# 📦 PASO 1: INSTALAR (PRIMERA VEZ)

## ✅ Antes de empezar, verifica que tienes instalado:

### 1. Python
```bash
python --version
```
**Debe mostrar**: `Python 3.8` o superior

❌ **Si no tienes Python:**
- Descargar: https://www.python.org/downloads/
- **IMPORTANTE**: En Windows, marca la opción "Add Python to PATH"

---

### 2. Node.js y npm
```bash
node --version
npm --version
```
**Debe mostrar**:
- Node: `v16.0.0` o superior
- npm: `7.0.0` o superior

❌ **Si no tienes Node.js:**
- Descargar: https://nodejs.org/ (versión LTS)

---

## 🚀 INSTALAR EL SISTEMA

### SI TIENES WINDOWS:

1. Abre el **Command Prompt (CMD)** o **PowerShell**
2. Navega a la carpeta del proyecto:
   ```bash
   cd Proyector-historial
   ```
3. Ejecuta:
   ```bash
   install.bat
   ```

### SI TIENES LINUX O MAC:

1. Abre la **Terminal**
2. Navega a la carpeta del proyecto:
   ```bash
   cd Proyector-historial
   ```
3. Dale permisos de ejecución:
   ```bash
   chmod +x install.sh
   ```
4. Ejecuta:
   ```bash
   ./install.sh
   ```

---

## 📋 QUÉ HACE EL SCRIPT DE INSTALACIÓN:

El script `install.bat` o `install.sh` va a:

1. ✅ Verificar que tienes Python y Node.js
2. ✅ Crear un entorno virtual de Python en `Backend/historial/venv/`
3. ✅ Instalar **60+ librerías de Python** del `requirements.txt`
4. ✅ Instalar **25+ librerías de Node.js** del `package.json`
5. ✅ Crear la base de datos SQLite
6. ✅ Aplicar todas las migraciones
7. ✅ Crear el usuario administrador (admin/admin123)
8. ✅ Configurar los archivos `.env` automáticamente

**⏱️ Tiempo estimado: 5-10 minutos**
**💾 Descarga aproximada: 500 MB**

---

## 🔍 SI EL INSTALL.BAT NO FUNCIONA:

### OPCIÓN: INSTALACIÓN MANUAL

#### PASO 1: Instalar Backend

```bash
# Ir a la carpeta del backend
cd Backend/historial

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# WINDOWS:
venv\Scripts\activate

# LINUX/MAC:
source venv/bin/activate

# Actualizar pip
python -m pip install --upgrade pip

# Instalar TODAS las dependencias (puede tardar 5 minutos)
pip install -r requirements.txt

# Crear archivo .env
echo SECRET_KEY=django-insecure-change-this > .env
echo DEBUG=True >> .env
echo ALLOWED_HOSTS=localhost,127.0.0.1 >> .env
echo CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000 >> .env

# Aplicar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser
# Username: admin
# Email: admin@example.com
# Password: admin123
# Confirmar: admin123

# Volver a la carpeta raíz
cd ../..
```

#### PASO 2: Instalar Frontend

```bash
# Ir a la carpeta del frontend
cd frontend

# Instalar TODAS las dependencias (puede tardar 5 minutos)
npm install

# Crear archivo .env
echo REACT_APP_API_URL=http://localhost:8000/api > .env

# Volver a la carpeta raíz
cd ..
```

---

# 🚀 PASO 2: INICIAR EL SISTEMA

**SOLO DESPUÉS DE INSTALAR**, puedes iniciar el sistema.

## SI TIENES WINDOWS:

```bash
start.bat
```

## SI TIENES LINUX O MAC:

```bash
./start.sh
```

Esto abrirá DOS ventanas:
- Una para el Backend (Django)
- Una para el Frontend (React)

---

# 🌐 PASO 3: ACCEDER AL SISTEMA

Después de ejecutar `start.bat` o `./start.sh`:

1. **Espera 30 segundos** a que todo cargue
2. Abre tu navegador en: **http://localhost:3000**
3. Login:
   - **Usuario**: `admin`
   - **Contraseña**: `admin123`

---

# 📚 TODAS LAS LIBRERÍAS QUE SE VAN A INSTALAR

## 🐍 BACKEND (Python - requirements.txt)

### Framework Principal (2):
- ✅ Django 4.2.7
- ✅ Django REST Framework 3.14.0

### Base de Datos (2):
- ✅ psycopg2-binary 2.9.9 (PostgreSQL)
- ✅ django-extensions 3.2.3

### Autenticación y Seguridad (6):
- ✅ djangorestframework-simplejwt 5.3.0 (JWT)
- ✅ django-cors-headers 4.3.0 (CORS)
- ✅ python-decouple 3.8
- ✅ django-environ 0.11.2
- ✅ bcrypt 4.1.1
- ✅ PyJWT 2.8.0

### Cache (2):
- ✅ redis 5.0.1
- ✅ django-redis 5.4.0

### Validación (4):
- ✅ django-filter 23.5
- ✅ drf-spectacular 0.27.0
- ✅ marshmallow 3.20.1
- ✅ pydantic 2.5.2

### Generación de PDFs y Documentos (6):
- ✅ reportlab 4.0.7
- ✅ Pillow 10.1.0
- ✅ openpyxl 3.1.2
- ✅ XlsxWriter 3.1.9
- ✅ python-docx 1.1.0
- ✅ WeasyPrint 60.1

### Manejo de Fechas (3):
- ✅ python-dateutil 2.8.2
- ✅ pytz 2023.3
- ✅ arrow 1.3.0

### Tareas Asíncronas (3):
- ✅ celery 5.3.4
- ✅ django-celery-beat 2.5.0
- ✅ django-celery-results 2.5.1

### Email (2):
- ✅ django-templated-email 3.0.1
- ✅ sendgrid 6.11.0

### Análisis de Datos (4):
- ✅ numpy 1.26.2
- ✅ pandas 2.1.3
- ✅ scipy 1.11.4
- ✅ matplotlib 3.8.2

### Testing (6):
- ✅ pytest 7.4.3
- ✅ pytest-django 4.7.0
- ✅ pytest-cov 4.1.0
- ✅ factory-boy 3.3.0
- ✅ Faker 20.1.0
- ✅ coverage 7.3.2

### Utilidades (4):
- ✅ requests 2.31.0
- ✅ python-slugify 8.0.1
- ✅ Unidecode 1.3.7
- ✅ phonenumbers 8.13.26

### Logging (2):
- ✅ django-debug-toolbar 4.2.0
- ✅ sentry-sdk 1.38.0

### Calidad de Código (4):
- ✅ flake8 6.1.0
- ✅ black 23.11.0
- ✅ isort 5.12.0
- ✅ pylint 3.0.3

### WebSockets (3):
- ✅ channels 4.0.0
- ✅ channels-redis 4.1.0
- ✅ daphne 4.0.0

### Cloud Storage (2):
- ✅ django-storages 1.14.2
- ✅ boto3 1.33.7

### Otros (4):
- ✅ python-magic 0.4.27
- ✅ qrcode 7.4.2
- ✅ python-barcode 0.15.1
- ✅ cryptography 41.0.7

### Producción (2):
- ✅ gunicorn 21.2.0
- ✅ whitenoise 6.6.0

**TOTAL BACKEND: 60+ librerías**

---

## ⚛️ FRONTEND (Node.js - package.json)

### Framework Principal (3):
- ✅ react 19.2.0
- ✅ react-dom 19.2.0
- ✅ react-scripts 5.0.1

### UI Components (2):
- ✅ antd 5.27.6 (Ant Design)
- ✅ @ant-design/icons 5.5.2
- ✅ @ant-design/charts 2.2.3

### Routing (1):
- ✅ react-router-dom 6.30.1

### HTTP Client (1):
- ✅ axios 1.12.2

### Fechas (2):
- ✅ dayjs 1.11.18
- ✅ moment 2.30.1

### PDFs y Capturas (2):
- ✅ jspdf 3.0.3
- ✅ html2canvas 1.4.1

### Gráficas y Charts (3):
- ✅ chart.js 4.4.7
- ✅ react-chartjs-2 5.3.0
- ✅ recharts 2.15.0

### 3D Graphics (2):
- ✅ three 0.170.0 (Three.js)
- ✅ @types/three 0.170.0

### TypeScript (1):
- ✅ typescript 4.9.5

### React Admin (2):
- ✅ react-admin 5.12.1
- ✅ ra-data-simple-rest 5.12.1

### Testing (4):
- ✅ @testing-library/dom 10.4.1
- ✅ @testing-library/jest-dom 6.9.1
- ✅ @testing-library/react 16.3.0
- ✅ @testing-library/user-event 13.5.0

### TypeScript Types (4):
- ✅ @types/jest 27.5.2
- ✅ @types/node 16.18.126
- ✅ @types/react 19.2.2
- ✅ @types/react-dom 19.2.2
- ✅ @types/react-router-dom 5.3.3

### Otros (1):
- ✅ web-vitals 2.1.4

### DevDependencies (2):
- ✅ eslint 8.57.0
- ✅ prettier 3.4.2

**TOTAL FRONTEND: 30+ librerías**

---

# ❌ ERRORES COMUNES Y SOLUCIONES

## Error: "Python no se reconoce como comando"

**Solución:**
1. Reinstala Python desde https://www.python.org/
2. **MARCA** la opción "Add Python to PATH"
3. Reinicia tu computadora

---

## Error: "npm no se reconoce como comando"

**Solución:**
1. Reinstala Node.js desde https://nodejs.org/
2. Reinicia tu computadora

---

## Error: "No module named 'django'"

**Solución:**
```bash
cd Backend/historial
venv\Scripts\activate    # Windows
source venv/bin/activate # Linux/Mac
pip install -r requirements.txt
```

---

## Error: "Cannot find module 'react'"

**Solución:**
```bash
cd frontend
npm install
```

---

## Error: "Port 3000 is already in use"

**Solución:**
```bash
# Windows
netstat -ano | findstr :3000
taskkill /PID <numero_que_aparece> /F

# Linux/Mac
lsof -ti:3000 | xargs kill -9
```

---

## Error: CORS en el navegador

**Solución:**
1. Ir a `Backend/historial/.env`
2. Verificar que tenga:
   ```
   CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
   ```
3. Reiniciar el backend

---

# ✅ CHECKLIST ANTES DE EMPEZAR

- [ ] Tengo Python 3.8+ instalado
- [ ] Tengo Node.js 16+ instalado
- [ ] Tengo al menos 2 GB de espacio libre
- [ ] Tengo conexión a internet (para descargar)
- [ ] He descargado/clonado el proyecto completo
- [ ] Estoy en la carpeta `Proyector-historial`

---

# 🎯 RESUMEN RÁPIDO

```bash
# 1. PRIMERA VEZ - INSTALAR
install.bat          # Windows
./install.sh         # Linux/Mac

# 2. CADA VEZ - INICIAR
start.bat            # Windows
./start.sh           # Linux/Mac

# 3. ACCEDER
http://localhost:3000
Usuario: admin
Contraseña: admin123
```

---

**¿Problemas? Lee la sección de ERRORES COMUNES arriba ⬆️**
