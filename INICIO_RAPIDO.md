# ⚡ INICIO RÁPIDO

## 🎯 Instalación Automática (Recomendado)

### Windows:
```bash
install.bat
```

### Linux/Mac:
```bash
chmod +x install.sh
./install.sh
```

**Esto instalará automáticamente:**
- ✅ Backend con todas las dependencias
- ✅ Frontend con todas las dependencias
- ✅ Base de datos SQLite configurada
- ✅ Usuario admin creado (username: `admin`, password: `admin123`)
- ✅ Variables de entorno configuradas

---

## 🚀 Iniciar el Sistema

### Opción 1: Inicio Automático (Recomendado)

#### Windows:
```bash
start.bat
```

#### Linux/Mac:
```bash
chmod +x start.sh
./start.sh
```

**Esto iniciará automáticamente:**
- Backend en `http://localhost:8000`
- Frontend en `http://localhost:3000`

### Opción 2: Inicio Manual

**Terminal 1 - Backend:**
```bash
cd Backend/historial
source venv/bin/activate      # Linux/Mac
venv\Scripts\activate         # Windows
python manage.py runserver
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm start
```

---

## 🌐 Acceso al Sistema

**Frontend (Aplicación principal):**
- URL: `http://localhost:3000`
- Usuario: `admin`
- Contraseña: `admin123`

**Backend Admin:**
- URL: `http://localhost:8000/admin`
- Usuario: `admin`
- Contraseña: `admin123`

---

## 📚 Documentación Completa

Para instalación manual detallada: **[GUIA_INSTALACION_COMPLETA.md](./GUIA_INSTALACION_COMPLETA.md)**

---

## 🔧 Solución Rápida de Problemas

### Backend no inicia:
```bash
cd Backend/historial
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
```

### Frontend no inicia:
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Error de CORS:
Verificar archivo `Backend/historial/.env` contenga:
```
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

---

## 📋 Requisitos Previos

Antes de instalar, asegúrate de tener:
- Python 3.8+
- Node.js 16+
- npm 7+

Verificar:
```bash
python --version
node --version
npm --version
```

---

**¡Listo para usar en menos de 5 minutos! 🎉**
