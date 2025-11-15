#!/bin/bash

# ==============================================================================
# SCRIPT DE INSTALACIÓN AUTOMÁTICA
# Sistema de Historial Médico Obstétrico
# ==============================================================================

echo "=================================="
echo "🚀 INSTALACIÓN AUTOMÁTICA"
echo "Sistema de Historial Médico"
echo "=================================="
echo ""

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ==============================================================================
# VERIFICAR REQUISITOS
# ==============================================================================

echo "📋 Verificando requisitos..."
echo ""

# Verificar Python
if ! command -v python3 &> /dev/null
then
    echo -e "${RED}❌ Python 3 no está instalado${NC}"
    echo "Descarga Python desde: https://www.python.org/downloads/"
    exit 1
else
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✅ $PYTHON_VERSION${NC}"
fi

# Verificar pip
if ! command -v pip3 &> /dev/null
then
    echo -e "${RED}❌ pip no está instalado${NC}"
    exit 1
else
    echo -e "${GREEN}✅ pip instalado${NC}"
fi

# Verificar Node.js
if ! command -v node &> /dev/null
then
    echo -e "${RED}❌ Node.js no está instalado${NC}"
    echo "Descarga Node.js desde: https://nodejs.org/"
    exit 1
else
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✅ Node.js $NODE_VERSION${NC}"
fi

# Verificar npm
if ! command -v npm &> /dev/null
then
    echo -e "${RED}❌ npm no está instalado${NC}"
    exit 1
else
    NPM_VERSION=$(npm --version)
    echo -e "${GREEN}✅ npm $NPM_VERSION${NC}"
fi

# Verificar PostgreSQL
if ! command -v psql &> /dev/null
then
    echo -e "${YELLOW}⚠️  PostgreSQL no detectado (opcional si usas SQLite)${NC}"
else
    PSQL_VERSION=$(psql --version)
    echo -e "${GREEN}✅ $PSQL_VERSION${NC}"
fi

echo ""
echo "=================================="
echo "✅ Todos los requisitos cumplidos"
echo "=================================="
echo ""

# ==============================================================================
# INSTALACIÓN BACKEND
# ==============================================================================

echo "🔧 INSTALANDO BACKEND..."
echo ""

cd Backend/historial

# Crear entorno virtual
echo "📦 Creando entorno virtual..."
python3 -m venv venv

# Activar entorno virtual
echo "🔄 Activando entorno virtual..."
source venv/bin/activate

# Actualizar pip
echo "⬆️  Actualizando pip..."
pip install --upgrade pip --quiet

# Instalar dependencias
echo "📚 Instalando dependencias de Python (puede tardar 2-3 minutos)..."
pip install -r requirements.txt --quiet

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Dependencias de Python instaladas${NC}"
else
    echo -e "${RED}❌ Error instalando dependencias de Python${NC}"
    exit 1
fi

# Crear archivo .env si no existe
if [ ! -f .env ]; then
    echo "📝 Creando archivo .env..."
    cat > .env << EOL
# Django
SECRET_KEY=django-insecure-change-this-in-production-$(date +%s)
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Base de datos (SQLite por defecto)
DATABASE_ENGINE=django.db.backends.sqlite3
DATABASE_NAME=db.sqlite3

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# JWT
ACCESS_TOKEN_LIFETIME=60
REFRESH_TOKEN_LIFETIME=1440
EOL
    echo -e "${GREEN}✅ Archivo .env creado${NC}"
else
    echo -e "${YELLOW}⚠️  Archivo .env ya existe, no se sobrescribe${NC}"
fi

# Aplicar migraciones
echo "🗄️  Aplicando migraciones de base de datos..."
python manage.py migrate

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Migraciones aplicadas correctamente${NC}"
else
    echo -e "${RED}❌ Error aplicando migraciones${NC}"
    exit 1
fi

# Crear superusuario automáticamente
echo "👤 Creando superusuario por defecto..."
echo "   Username: admin"
echo "   Password: admin123"
python manage.py shell << EOF
from django.contrib.auth import get_user_model
from usuarios.models import Usuario

User = Usuario
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='admin123',
        nombre='Administrador',
        apellido='Sistema',
        rol='admin'
    )
    print('Superusuario creado exitosamente')
else:
    print('Superusuario ya existe')
EOF

echo -e "${GREEN}✅ Backend instalado correctamente${NC}"
echo ""

# Volver al directorio raíz
cd ../..

# ==============================================================================
# INSTALACIÓN FRONTEND
# ==============================================================================

echo "⚛️  INSTALANDO FRONTEND..."
echo ""

cd frontend

# Crear archivo .env si no existe
if [ ! -f .env ]; then
    echo "📝 Creando archivo .env para frontend..."
    cat > .env << EOL
REACT_APP_API_URL=http://localhost:8000/api
EOL
    echo -e "${GREEN}✅ Archivo .env creado${NC}"
else
    echo -e "${YELLOW}⚠️  Archivo .env ya existe, no se sobrescribe${NC}"
fi

# Instalar dependencias
echo "📚 Instalando dependencias de Node.js (puede tardar 3-5 minutos)..."
npm install

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Dependencias de Node.js instaladas${NC}"
else
    echo -e "${RED}❌ Error instalando dependencias de Node.js${NC}"
    exit 1
fi

cd ..

# ==============================================================================
# FINALIZACIÓN
# ==============================================================================

echo ""
echo "=================================="
echo "🎉 INSTALACIÓN COMPLETADA"
echo "=================================="
echo ""
echo "📋 CREDENCIALES DE ACCESO:"
echo "   Username: admin"
echo "   Password: admin123"
echo ""
echo "🚀 PARA INICIAR EL SISTEMA:"
echo ""
echo "Terminal 1 - Backend:"
echo "   cd Backend/historial"
echo "   source venv/bin/activate"
echo "   python manage.py runserver"
echo ""
echo "Terminal 2 - Frontend:"
echo "   cd frontend"
echo "   npm start"
echo ""
echo "🌐 ACCESO:"
echo "   Frontend: http://localhost:3000"
echo "   Backend Admin: http://localhost:8000/admin"
echo ""
echo "📚 DOCUMENTACIÓN:"
echo "   Ver GUIA_INSTALACION_COMPLETA.md para más detalles"
echo ""
echo "=================================="
