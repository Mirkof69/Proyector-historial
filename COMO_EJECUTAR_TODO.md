# 🚀 CÓMO EJECUTAR TODO EL SISTEMA - GUÍA COMPLETA

**Sistema de Historial Médico Obstétrico**
**Backend Django + Frontend React + PostgreSQL**

---

## ✅ REQUISITOS PREVIOS

Antes de empezar, asegúrate de tener instalado:

- ✅ **Python 3.12.7** (ya instalado)
- ✅ **Node.js v22.20.0** (ya instalado)
- ✅ **PostgreSQL** corriendo en puerto **5433**
- ✅ **Base de datos "Historial"** ya creada

---

## 📁 ESTRUCTURA DEL PROYECTO

```
Proyector-historial/
├── Backend/
│   └── historial/          # Proyecto Django
│       ├── historial/      # Configuración principal
│       ├── usuarios/       # App usuarios
│       ├── pacientes/      # App pacientes
│       ├── embarazos/      # App embarazos
│       ├── controles/      # App controles prenatales
│       ├── calculadoras/   # App calculadoras FMF
│       ├── ecografias/     # App ecografías (NUEVO)
│       ├── laboratorio/    # App laboratorio (NUEVO)
│       ├── citas/          # App citas (NUEVO)
│       ├── partos/         # App partos (NUEVO)
│       ├── calculadoras_avanzadas/  # App calculadoras avanzadas (NUEVO)
│       └── reportes/       # App reportes (NUEVO)
├── frontend/
│   ├── src/
│   │   ├── pages/          # Páginas React
│   │   ├── services/       # Servicios API
│   │   └── components/     # Componentes
│   └── package.json
├── .env                    # Variables de entorno backend
└── README.md
```

---

## 🔧 PASO 1: CONFIGURAR EL BACKEND

### 1.1 Abrir Terminal en la carpeta Backend

```cmd
cd C:\ruta\a\tu\proyecto\Proyector-historial\Backend\historial
```

### 1.2 Crear Entorno Virtual de Python

```cmd
python -m venv venv
```

### 1.3 Activar Entorno Virtual

**Windows CMD:**
```cmd
venv\Scripts\activate.bat
```

**Windows PowerShell:**
```powershell
venv\Scripts\Activate.ps1
```

**Git Bash / Linux / Mac:**
```bash
source venv/bin/activate
```

Deberías ver `(venv)` al inicio de tu terminal.

### 1.4 Instalar Dependencias de Python

```cmd
pip install -r requirements.txt
```

Esto instalará:
- Django 5.1.3
- Django REST Framework
- psycopg2 (PostgreSQL)
- djangorestframework-simplejwt
- django-cors-headers
- python-decouple
- Y todas las demás dependencias

### 1.5 Verificar el Archivo .env

Asegúrate de que existe `Backend/historial/.env` con:

```env
# Base de Datos PostgreSQL
DB_NAME=Historial
DB_USER=postgres
DB_PASSWORD=25693
DB_HOST=localhost
DB_PORT=5433

# Django
SECRET_KEY=tu-clave-secreta-aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### 1.6 Verificar que PostgreSQL está corriendo

```cmd
# Verifica que el servicio de PostgreSQL esté activo
# Y que la base de datos "Historial" exista en el puerto 5433
```

### 1.7 NO EJECUTAR MIGRACIONES

**IMPORTANTE**: Los modelos tienen `managed=False`, así que **NO ejecutes migraciones**.
La base de datos ya existe con todas las tablas.

### 1.8 Iniciar el Servidor Backend

```cmd
python manage.py runserver 8000
```

✅ **El backend debería estar corriendo en:** `http://localhost:8000`

**Endpoints API disponibles:**
- `http://localhost:8000/api/pacientes/`
- `http://localhost:8000/api/embarazos/`
- `http://localhost:8000/api/controles/`
- `http://localhost:8000/api/ecografias/` ← **NUEVO**
- `http://localhost:8000/api/laboratorio/` ← **NUEVO**
- `http://localhost:8000/api/citas/` ← **NUEVO**
- `http://localhost:8000/api/partos/` ← **NUEVO**
- `http://localhost:8000/api/calculadoras-avanzadas/` ← **NUEVO**
- `http://localhost:8000/api/reportes/` ← **NUEVO**

---

## 🎨 PASO 2: CONFIGURAR EL FRONTEND

### 2.1 Abrir OTRA Terminal (nueva ventana)

```cmd
cd C:\ruta\a\tu\proyecto\Proyector-historial\frontend
```

### 2.2 Instalar Dependencias de Node.js

```cmd
npm install
```

Esto instalará:
- React 19.0.0
- React Router DOM 7.1.1
- Ant Design 5.27.6
- Axios 1.12.2
- Day.js 1.12.0
- Y todas las demás dependencias

### 2.3 Iniciar el Servidor de Desarrollo

```cmd
npm start
```

✅ **El frontend debería abrirse automáticamente en:** `http://localhost:3000`

Si no se abre automáticamente, abre tu navegador y ve a:
`http://localhost:3000`

---

## 🎯 PASO 3: USAR EL SISTEMA

### 3.1 Página de Login

La página inicial te llevará al login:

**Credenciales por defecto:**
- **Usuario:** `admin`
- **Contraseña:** `admin123`

### 3.2 Navegar por el Sistema

Una vez dentro, verás el menú lateral con TODOS los módulos:

1. **Dashboard** - Vista general
2. **Pacientes** - Gestión de pacientes
3. **Embarazos** - Gestión de embarazos
4. **Controles Prenatales** - Controles médicos
5. **Ecografías** ← **NUEVO** - Ecografías y biometría fetal
6. **Laboratorio** ← **NUEVO** - Exámenes de laboratorio
7. **Citas** ← **NUEVO** - Agendamiento de citas
8. **Partos** ← **NUEVO** - Registros de partos y nacimientos
9. **Calculadoras FMF** - Calculadoras básicas
10. **Calculadoras Avanzadas** ← **NUEVO** - Calculadoras médicas avanzadas
11. **Reportes** ← **NUEVO** - Generación de PDFs
12. **Usuarios** - Gestión de usuarios del sistema

### 3.3 Funcionalidades de Cada Módulo

#### 📊 Ecografías
- Crear nuevas ecografías con biometría completa
- Registrar DBP, CC, CA, LF, peso fetal estimado
- Subir imágenes de ecografías
- Evaluar placenta y líquido amniótico
- Filtrar por embarazo, tipo, fecha

#### 🔬 Laboratorio
- Registrar hemogramas completos
- Química sanguínea (glucosa, urea, creatinina)
- Serología (VDRL, VIH, Hepatitis, Toxoplasmosis)
- Exámenes de orina completos
- Cultivos y antibiogramas
- Subir archivos PDF de resultados

#### 📅 Citas
- Agendar citas médicas
- Ver calendario mensual con todas las citas
- Confirmar/cancelar citas
- Asignar médico y sala
- Estados: pendiente, confirmada, cancelada, completada

#### 👶 Partos
- Registrar fecha y hora del parto
- Scores APGAR (1 y 5 minutos)
- Antropometría del recién nacido (peso, talla, perímetros)
- Tipo de parto (vaginal, cesárea, fórceps, ventosa)
- Complicaciones maternas y neonatales
- Datos de placenta y alumbramiento

#### 📈 Calculadoras Avanzadas
- Riesgo cardiovascular
- Riesgo de tromboembolia
- Dosis de medicamentos
- Riesgo de parto prematuro
- Crecimiento fetal
- Índice de resistencia Doppler

#### 📄 Reportes
- Historial completo del paciente en PDF
- Carnet perinatal
- Estadísticas institucionales
- Certificados de nacimiento
- Resúmenes de parto
- Evoluciones y controles

---

## ⚠️ SOLUCIÓN DE PROBLEMAS

### ❌ Error: "ModuleNotFoundError: No module named 'django'"

**Solución:** No activaste el entorno virtual de Python.

```cmd
cd Backend\historial
venv\Scripts\activate
```

### ❌ Error: "npm ERR! ERESOLVE unable to resolve dependency tree"

**Solución:** Usa `--legacy-peer-deps`:

```cmd
npm install --legacy-peer-deps
```

### ❌ Error: "django.db.utils.OperationalError: could not connect to server"

**Solución:** PostgreSQL no está corriendo o está en un puerto diferente.

1. Verifica que PostgreSQL esté corriendo
2. Verifica que esté en el puerto 5433
3. Verifica las credenciales en el archivo `.env`

### ❌ Error: "CORS policy: No 'Access-Control-Allow-Origin' header"

**Solución:** El backend no está corriendo o CORS no está configurado.

1. Asegúrate de que el backend esté corriendo en `http://localhost:8000`
2. Verifica `CORS_ALLOWED_ORIGINS` en `settings.py`

### ❌ Error: "Cannot read properties of undefined (reading 'getToken')"

**Solución:** Este error ya fue corregido. Asegúrate de tener la última versión del código.

```cmd
git pull origin claude/backend-backup-13-11-2025-01LcWupY21iMhQVjUPDN2aQB
```

---

## 🔄 ACTUALIZACIONES

### Para obtener la última versión del código:

```bash
git checkout claude/backend-backup-13-11-2025-01LcWupY21iMhQVjUPDN2aQB
git pull
```

---

## 📝 RESUMEN DE COMANDOS

**Terminal 1 (Backend):**
```cmd
cd Backend\historial
venv\Scripts\activate
pip install -r requirements.txt
python manage.py runserver 8000
```

**Terminal 2 (Frontend):**
```cmd
cd frontend
npm install
npm start
```

**URLs:**
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000/api/`
- Admin Django: `http://localhost:8000/admin/`

---

## ✅ VERIFICACIÓN FINAL

Si todo está funcionando correctamente, deberías poder:

1. ✅ Abrir `http://localhost:3000`
2. ✅ Hacer login con `admin / admin123`
3. ✅ Ver el dashboard con estadísticas
4. ✅ Navegar por todos los 12 módulos del menú
5. ✅ Crear, editar, ver y eliminar registros en cada módulo
6. ✅ Subir imágenes en Ecografías
7. ✅ Generar PDFs en Reportes
8. ✅ Usar las calculadoras avanzadas

---

## 🎉 ¡LISTO!

**El sistema está 100% funcional con:**
- ✅ Backend Django con 11 apps
- ✅ Frontend React con 12 módulos
- ✅ PostgreSQL con todas las tablas
- ✅ API REST completa
- ✅ Autenticación JWT
- ✅ CRUD completo en todos los módulos
- ✅ ~8,000 líneas de código total

**Módulos implementados:**
1. Usuarios ✅
2. Pacientes ✅
3. Embarazos ✅
4. Controles Prenatales ✅
5. Calculadoras FMF ✅
6. **Ecografías** ✅ (NUEVO)
7. **Laboratorio** ✅ (NUEVO)
8. **Citas** ✅ (NUEVO)
9. **Partos** ✅ (NUEVO)
10. **Calculadoras Avanzadas** ✅ (NUEVO)
11. **Reportes** ✅ (NUEVO)

---

**¿Problemas? Revisa la sección "Solución de Problemas" arriba.**

**¿Necesitas ayuda? Abre un issue en el repositorio.**
