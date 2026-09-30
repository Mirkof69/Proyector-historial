# Guía de Instalación - Módulo de Vacunas

## Instalación Rápida

Sigue estos pasos para integrar el módulo de vacunas en tu sistema:

### 1. Agregar a INSTALLED_APPS

Edita `settings.py` y agrega 'vacunas' a `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ... otras apps
    'pacientes',
    'embarazos',
    'usuarios',
    'vacunas',  # Agregar aquí
    # ... otras apps
]
```

### 2. Agregar URLs

Edita el archivo `urls.py` principal y agrega las URLs del módulo:

```python
from django.urls import path, include

urlpatterns = [
    # ... otras urls
    path('api/vacunas/', include('vacunas.urls')),
    # ... otras urls
]
```

### 3. Crear Migraciones

Ejecuta los siguientes comandos para crear las tablas en la base de datos:

```bash
python manage.py makemigrations vacunas
python manage.py migrate vacunas
```

### 4. Verificar Instalación

Verifica que las tablas se crearon correctamente:

```bash
python manage.py dbshell
```

```sql
-- Verificar tablas
SELECT * FROM tipos_vacunas LIMIT 1;
SELECT * FROM registros_vacunas LIMIT 1;
```

## Datos de Prueba (Opcional)

### Crear Tipos de Vacunas Comunes

Puedes crear algunos tipos de vacunas iniciales ejecutando:

```bash
python manage.py shell
```

```python
from vacunas.models import TipoVacuna

# Toxoide Tetánico
TipoVacuna.objects.create(
    nombre="Toxoide Tetánico",
    descripcion="Vacuna contra el tétanos. Recomendada durante el embarazo para prevenir el tétanos neonatal.",
    dosis_requeridas=2,
    intervalo_dosis_dias=30,
    obligatoria_embarazo=True,
    contraindicaciones="Alergia al toxoide tetánico, reacción grave a dosis anterior",
    efectos_secundarios="Dolor en el sitio de inyección, fiebre leve, malestar general",
    activo=True
)

# Influenza
TipoVacuna.objects.create(
    nombre="Influenza (Gripe)",
    descripcion="Vacuna contra la influenza estacional. Recomendada para embarazadas en cualquier trimestre.",
    dosis_requeridas=1,
    obligatoria_embarazo=True,
    contraindicaciones="Alergia severa al huevo, reacción alérgica a dosis anterior",
    efectos_secundarios="Dolor en el sitio de inyección, dolor de cabeza, fiebre baja",
    activo=True
)

# Hepatitis B
TipoVacuna.objects.create(
    nombre="Hepatitis B",
    descripcion="Vacuna contra la hepatitis B. Se administra en 3 dosis.",
    dosis_requeridas=3,
    intervalo_dosis_dias=30,
    obligatoria_embarazo=False,
    contraindicaciones="Alergia a componentes de la vacuna, enfermedad aguda grave",
    efectos_secundarios="Dolor en el sitio de inyección, fatiga, fiebre leve",
    activo=True
)

print("Tipos de vacunas creados exitosamente!")
```

## Verificación de API

### Probar Endpoints

Una vez instalado, puedes probar los endpoints:

```bash
# Listar tipos de vacunas
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/vacunas/tipos-vacunas/

# Listar registros de vacunación
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/vacunas/registros/

# Estadísticas de vacunas
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/vacunas/tipos-vacunas/estadisticas/

# Estadísticas de registros
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/vacunas/registros/estadisticas/
```

## Acceso al Panel de Administración

1. Accede al panel de administración de Django: `http://localhost:8000/admin/`
2. Verás dos nuevas secciones en "VACUNAS":
   - Tipos de Vacunas
   - Registros de Vacunas

## Estructura Creada

Después de la instalación, tendrás:

```
vacunas/
├── __init__.py                 # Inicialización del módulo
├── admin.py                    # Configuración del panel admin
├── apps.py                     # Configuración de la app
├── models.py                   # Modelos (TipoVacuna, RegistroVacuna)
├── serializers.py              # Serializers para API
├── views.py                    # ViewSets y acciones personalizadas
├── urls.py                     # Configuración de rutas
├── migrations/                 # Migraciones de base de datos
│   └── __init__.py
├── README.md                   # Documentación completa
└── INSTALL.md                  # Esta guía
```

## Tablas de Base de Datos

### tipos_vacunas
- Almacena el catálogo de vacunas disponibles
- Campos principales: nombre, dosis_requeridas, obligatoria_embarazo

### registros_vacunas
- Almacena cada aplicación de vacuna
- Relacionada con: pacientes, embarazos, usuarios
- Incluye: fecha, dosis, lote, reacciones

## Permisos

El módulo requiere autenticación. Asegúrate de que:
- Los usuarios estén autenticados
- Se use el token de autenticación en las peticiones API
- Los permisos estén configurados correctamente

## Solución de Problemas

### Error: "No module named 'vacunas'"
- Asegúrate de que 'vacunas' esté en INSTALLED_APPS
- Reinicia el servidor Django

### Error: "relation 'tipos_vacunas' does not exist"
- Ejecuta las migraciones: `python manage.py migrate vacunas`

### Error: "Cannot import name 'Paciente'"
- Asegúrate de que el módulo 'pacientes' esté instalado
- Verifica que esté antes de 'vacunas' en INSTALLED_APPS

### Error 401 Unauthorized en API
- Agrega el token de autenticación en el header
- Verifica que el usuario esté autenticado

## Próximos Pasos

1. Crear tipos de vacunas comunes en tu sistema
2. Configurar notificaciones para próximas dosis
3. Integrar con el módulo de reportes
4. Personalizar validaciones según tus necesidades
5. Agregar más vacunas al catálogo

## Soporte

Para más información, consulta:
- `README.md`: Documentación completa del módulo
- Modelos: Revisa `models.py` para entender la estructura
- API: Revisa `views.py` para ver todos los endpoints disponibles

---

**Última actualización:** Diciembre 2025
