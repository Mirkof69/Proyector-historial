# Fetal Medical System

Sistema integral de gestión médica materno-fetal con inteligencia artificial para asistencia diagnóstica.

## 🚀 Características Principales

- **Gestión Clínica Completa**: Pacientes, Embarazos, Controles Prenatales, Partos.
- **Inteligencia Artificial**: Asistente médico integrado para análisis de riesgos (Preeclampsia, Diabetes, RCIU) y soporte de decisiones.
- **Dashboard Avanzado**: Estadísticas en tiempo real y visualización de datos con gráficos interactivos.
- **Módulos Especializados**:
  - Ecografías y visualización DICOM.
  - Laboratorio y análisis de resultados.
  - Calculadoras clínicas avanzadas.
- **Seguridad**: Gestión de roles y permisos granulares.

## 🛠️ Tecnologías

- **Backend**: Django REST Framework (Python)
- **Frontend**: React + TypeScript + Vite + Ant Design
- **Microservicio IA**: FastAPI + Scikit-learn/TensorFlow
- **Base de Datos**: PostgreSQL
- **Infraestructura**: Docker & Docker Compose

## 📋 Requisitos Previos

- Docker y Docker Compose
- Node.js 18+ (para desarrollo local)
- Python 3.11+ (para desarrollo local)

## 🔧 Instalación y Despliegue

### Usando Docker (Recomendado)

1. **Clonar el repositorio**
   ```bash
   git clone <repo-url>
   cd fetal-medical-system
   ```

2. **Iniciar servicios**
   ```bash
   docker-compose up -d --build
   ```

3. **Acceder a la aplicación**
   - Frontend: `http://localhost`
   - Backend API: `http://localhost:8000`
   - IA Service: `http://localhost:5000`

### Desarrollo Local

#### Backend
```bash
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

#### Microservicio IA
```bash
cd backend/ia_microservice
pip install -r requirements.txt
uvicorn server:app --reload --port 5000
```

#### Frontend
```bash
cd backend/frontend
npm install
npm run dev
```

## 📚 Estructura del Proyecto

```
/backend
  /controles       # Módulo de Controles Prenatales
  /embarazos       # Módulo de Embarazos
  /frontend        # Aplicación React
  /ia_microservice # Servicio de Inteligencia Artificial
  /pacientes       # Gestión de Pacientes
  /reportes        # Sistema de Reportes
  ...
```

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo [LICENSE](LICENSE) para más detalles.
