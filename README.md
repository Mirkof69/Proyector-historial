# Sistema Clínico Fetal Medical Bolivia

Fetal Medical Bolivia es una plataforma integrada de alta disponibilidad diseñada para la gestión del historial clínico obstétrico digital y el análisis inteligente de imágenes de ecografía obstétrica mediante Inteligencia Artificial (IA).

Este sistema es propiedad exclusiva de **Mirkof Guzman**. Todos los derechos están reservados.

---

## 🏗️ Arquitectura General del Sistema

El sistema sigue una arquitectura distribuida basada en microservicios y multi-tenancy (multi-inquilino) para permitir que distintas clínicas u hospitales compartan la misma infraestructura de base de datos bajo esquemas aislados y seguros.

```
                  ┌──────────────────────┐
                  │   Cliente (React)    │
                  └──────────┬───────────┘
                             │ (Puerto 3000 / Nginx)
                             ▼
                  ┌──────────────────────┐
                  │  Kong API Gateway   │
                  └──────────┬───────────┘
                             │ (Puerto 8000)
              ┌──────────────┴──────────────┐
              ▼                             ▼
   ┌────────────────────┐         ┌────────────────────┐
   │  Backend Django    │         │ Microservicio IA   │
   │  (Multi-Tenancy)   │         │ (FastAPI + PyTorch)│
   └──────────┬─────────┘         └────────────────────┘
              │ (Puerto 8000)                (Puerto 8001)
              ▼
   ┌────────────────────┐
   │ PostgreSQL (DB)    │
   └────────────────────┘
```

1.  **Backend (Django REST Framework)**:
    *   Ubicación: `Backend/`
    *   Gestiona la lógica clínica, auditorías, citas, laboratorios, triajes y roles.
    *   Implementa **Multi-Tenancy** a nivel de base de datos utilizando `django-tenants`, aislando los datos de cada clínica en un esquema de PostgreSQL independiente.
2.  **Frontend (React SPA)**:
    *   Ubicación: `Backend/frontend/`
    *   Construido en React con TypeScript, empaquetado con Vite y estilizado usando Ant Design.
3.  **Microservicio de IA (FastAPI + PyTorch)**:
    *   Ubicación: `Backend/Microservicio_IA/`
    *   Implementa inferencia clínica en tiempo real con un modelo convolucional **EfficientNet-B4** (con soporte de PyTorch y MONAI).
    *   Realiza detección automática de patologías fetales, estimación de biometría fetal (BPD, HC, AC, FL) y generación de mapas de calor visuales mediante **Grad-CAM**.
4.  **API Gateway (Kong)**:
    *   Ubicación de configuración: `kong/`
    *   Centraliza y orquesta todas las peticiones externas redirigiéndolas al servicio correspondiente de forma segura.

---

## 🛠️ Requisitos del Sistema

*   **Sistema Operativo**: Windows 10/11 o Linux.
*   **Python**: Versión 3.11+.
*   **Node.js**: Versión 18+.
*   **PostgreSQL**: Base de datos activa corriendo localmente en el puerto `5432`.

---

## 🔧 Puesta en Marcha (Instalación y Ejecución)

El repositorio cuenta con scripts automatizados de comandos de Windows (`.bat` y `.ps1`) en la raíz del proyecto para facilitar el despliegue del sistema completo:

### 1. Preparación de la Base de Datos (PostgreSQL)
Si no tienes PostgreSQL instalado, ejecuta el script de PowerShell para automatizar su descarga e instalación en Windows:
```powershell
# Ejecutar en PowerShell como Administrador:
.\instalar_postgres.ps1
```

### 2. Migración y Carga de Datos Iniciales (Seeders)
Una vez que PostgreSQL está corriendo localmente, inicializa los esquemas de base de datos, ejecuta las migraciones de Django y carga los médicos y clínicas semilla:
```bash
# Ejecutar en consola:
MIGRAR_Y_SEED.bat
```

### 3. Iniciar el Sistema Completo
Para levantar simultáneamente el Frontend (React), el Backend (Django), el Microservicio de IA (FastAPI) y el API Gateway:
```bash
# Iniciar todos los servicios:
INICIAR_SISTEMA.bat
```
*(También puedes usar `start_all.bat` o `start_system.bat` según el nivel de depuración requerido).*

---

## 📂 Organización de Carpetas en el Repositorio

*   `/Backend`: Contiene el código fuente de Django del backend y las apps del negocio.
    *   `Backend/frontend/`: Código fuente de la interfaz de usuario en React.
    *   `Backend/Microservicio_IA/`: Código de FastAPI para las predicciones del modelo convolucional.
        *   `Microservicio_IA/trained_models/`: Contiene los pesos preentrenados del modelo `efficientnet_b4.pth`.
*   `/zip`: Carpeta de almacenamiento centralizado de recursos estáticos. Contiene:
    *   Todos los datasets de imágenes de ultrasonido comprimidos en archivos `.zip` y `.rar` (~5.5 GB).
    *   Los documentos en formato Word y PDF (`fetal_medical_ieee.docx`, propuestas de historial clínico).
    *   La carpeta `docs/` con las imágenes de diagramas UML del diseño del sistema.
    *   Archivos complementarios de especificación técnica de API e instalación en formato `.md`.

---

## 📄 Licencia

Este software está sujeto al **Contrato de Licencia de Software Propietario**.

*   **Propietario intelectual**: Mirkof Guzman.
*   **Copyright**: © 2026 Mirkof Guzman. Todos los derechos reservados.
*   Queda estrictamente prohibida la copia, reproducción, modificación, venta, sublicenciamiento o redistribución del código y documentación de este sistema sin el consentimiento explícito y por escrito del propietario.
