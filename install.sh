#!/bin/bash

clear

echo "========================================"
echo "INSTALACION AUTOMATICA"
echo "Sistema de Historial Medico"
echo "========================================"
echo ""

echo "Verificando Python..."
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 no esta instalado"
    echo "Descarga desde: https://www.python.org/downloads/"
    exit 1
fi
python3 --version
echo ""

echo "Verificando Node.js..."
if ! command -v node &> /dev/null; then
    echo "ERROR: Node.js no esta instalado"
    echo "Descarga desde: https://nodejs.org/"
    exit 1
fi
node --version
npm --version
echo ""

echo "========================================"
echo "INSTALANDO BACKEND"
echo "========================================"
echo ""

cd Backend/historial

echo "Creando entorno virtual..."
[ -d venv ] && rm -rf venv
python3 -m venv venv
echo ""

echo "Activando entorno virtual..."
source venv/bin/activate
echo ""

echo "Actualizando pip..."
pip install --upgrade pip --quiet
echo ""

echo "Instalando dependencias de Python..."
echo "Esto puede tardar 5-10 minutos..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: No se pudieron instalar dependencias"
    exit 1
fi
echo ""

echo "Creando archivo .env..."
if [ ! -f .env ]; then
    cat > .env << EOL
SECRET_KEY=django-insecure-change-this
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
EOL
fi
echo ""

echo "Aplicando migraciones..."
python manage.py migrate
if [ $? -ne 0 ]; then
    echo "ERROR: No se pudieron aplicar migraciones"
    exit 1
fi
echo ""

echo "Creando usuario admin..."
echo "Username: admin"
echo "Password: admin123"
python manage.py shell -c "from usuarios.models import Usuario; Usuario.objects.filter(username='admin').exists() or Usuario.objects.create_superuser('admin', 'admin@example.com', 'admin123', nombre='Admin', apellido='Sistema', rol='admin')" 2>/dev/null
echo ""

cd ../..

echo "========================================"
echo "INSTALANDO FRONTEND"
echo "========================================"
echo ""

cd frontend

echo "Creando archivo .env..."
if [ ! -f .env ]; then
    echo "REACT_APP_API_URL=http://localhost:8000/api" > .env
fi
echo ""

echo "Instalando dependencias de Node.js..."
echo "Esto puede tardar 3-5 minutos..."
npm install
if [ $? -ne 0 ]; then
    echo "ERROR: No se pudieron instalar dependencias"
    exit 1
fi
echo ""

cd ..

clear
echo ""
echo "========================================"
echo "INSTALACION COMPLETADA"
echo "========================================"
echo ""
echo "Backend: Instalado"
echo "Frontend: Instalado"
echo "Base de datos: Creada"
echo "Usuario: admin"
echo "Password: admin123"
echo ""
echo "========================================"
echo "PARA INICIAR EL SISTEMA"
echo "========================================"
echo ""
echo "1. Ejecuta: ./start.sh"
echo "2. Abre: http://localhost:3000"
echo "3. Login: admin / admin123"
echo ""
echo "========================================"
