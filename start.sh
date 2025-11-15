#!/bin/bash

# ==============================================================================
# SCRIPT PARA INICIAR EL SISTEMA COMPLETO
# Sistema de Historial Médico Obstétrico
# ==============================================================================

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "=================================="
echo "🚀 INICIANDO SISTEMA"
echo "Sistema de Historial Médico"
echo "=================================="
echo ""

# Verificar que las instalaciones están completas
if [ ! -d "Backend/historial/venv" ]; then
    echo -e "${YELLOW}⚠️  Backend no está instalado${NC}"
    echo "Ejecuta primero: ./install.sh"
    exit 1
fi

if [ ! -d "frontend/node_modules" ]; then
    echo -e "${YELLOW}⚠️  Frontend no está instalado${NC}"
    echo "Ejecuta primero: ./install.sh"
    exit 1
fi

# Función para limpiar procesos al salir
cleanup() {
    echo ""
    echo "🛑 Deteniendo servidores..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "✅ Servidores detenidos"
    exit 0
}

# Capturar Ctrl+C
trap cleanup SIGINT SIGTERM

echo -e "${BLUE}📡 Iniciando Backend...${NC}"
cd Backend/historial
source venv/bin/activate
python manage.py runserver > ../../backend.log 2>&1 &
BACKEND_PID=$!
cd ../..

sleep 3

echo -e "${BLUE}⚛️  Iniciando Frontend...${NC}"
cd frontend
npm start > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

sleep 5

echo ""
echo "=================================="
echo -e "${GREEN}✅ SISTEMA INICIADO${NC}"
echo "=================================="
echo ""
echo "🌐 ACCESO:"
echo "   Frontend: http://localhost:3000"
echo "   Backend Admin: http://localhost:8000/admin"
echo ""
echo "📋 CREDENCIALES:"
echo "   Username: admin"
echo "   Password: admin123"
echo ""
echo "📊 LOGS:"
echo "   Backend: tail -f backend.log"
echo "   Frontend: tail -f frontend.log"
echo ""
echo "🛑 Para detener: Presiona Ctrl+C"
echo ""
echo "=================================="

# Mantener el script corriendo
wait
