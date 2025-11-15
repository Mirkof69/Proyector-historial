#!/bin/bash

clear

echo "========================================"
echo "INICIANDO SISTEMA"
echo "Sistema de Historial Medico"
echo "========================================"
echo ""

if [ ! -d "Backend/historial/venv" ]; then
    echo "ERROR: Backend no esta instalado"
    echo "Ejecuta primero: ./install.sh"
    exit 1
fi

if [ ! -d "frontend/node_modules" ]; then
    echo "ERROR: Frontend no esta instalado"
    echo "Ejecuta primero: ./install.sh"
    exit 1
fi

cleanup() {
    echo ""
    echo "Deteniendo servidores..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "Servidores detenidos"
    exit 0
}

trap cleanup SIGINT SIGTERM

echo "Iniciando Backend..."
cd Backend/historial
source venv/bin/activate
python manage.py runserver > ../../backend.log 2>&1 &
BACKEND_PID=$!
cd ../..

sleep 3

echo "Iniciando Frontend..."
cd frontend
npm start > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

sleep 5

echo ""
echo "========================================"
echo "SISTEMA INICIADO"
echo "========================================"
echo ""
echo "Frontend: http://localhost:3000"
echo "Backend Admin: http://localhost:8000/admin"
echo ""
echo "Usuario: admin"
echo "Password: admin123"
echo ""
echo "Para detener: Presiona Ctrl+C"
echo ""
echo "========================================"

wait
