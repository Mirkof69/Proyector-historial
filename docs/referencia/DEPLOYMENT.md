# 🚀 DEPLOYMENT GUIDE - Sistema Médico Fetal

## Despliegue con Docker (Recomendado)

### Requisitos
- Docker 20.10+
- Docker Compose 2.0+
- 4GB RAM mínimo
- 20GB espacio en disco

### Paso 1: Preparar Entorno

```bash
# Clonar repositorio
git clone <repo-url>
cd Backend

# Copiar variables de entorno
cp .env.docker.example .env
```

### Paso 2: Configurar .env

Editar `.env` con valores de producción:

```env
SECRET_KEY=tu-secret-key-muy-segura-aqui
DEBUG=False
ALLOWED_HOSTS=tudominio.com,www.tudominio.com

DATABASE_URL=postgresql://user:pass@db:5432/dbname
REDIS_URL=redis://redis:6379/0

EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=tu-app-password
```

### Paso 3: Construir y Desplegar

```bash
# Construir imágenes
docker-compose build

# Iniciar servicios
docker-compose up -d

# Verificar estado
docker-compose ps

# Ver logs
docker-compose logs -f
```

### Paso 4: Inicializar Base de Datos

```bash
# Migrar base de datos
docker-compose exec backend python manage.py migrate

# Crear superusuario
docker-compose exec backend python manage.py createsuperuser

# Cargar datos iniciales (opcional)
docker-compose exec backend python manage.py loaddata initial_data.json
```

### Paso 5: Verificar

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Admin: http://localhost:8000/admin

---

## Despliegue Manual

### Backend (Django)

```bash
# 1. Install dependencies
pip install -r requirements.txt
pip install -r requirements.production.txt

# 2. Configure environment
export DJANGO_SETTINGS_MODULE=settings
export SECRET_KEY="your-secret-key"
export DEBUG=False

# 3. Migrate database
python manage.py migrate

# 4. Collect static files
python manage.py collectstatic --noinput

# 5. Start with Gunicorn
gunicorn --bind 0.0.0.0:8000 --workers 4 wsgi:application
```

### Frontend (React)

```bash
# 1. Install dependencies
cd frontend
npm ci --only=production

# 2. Build for production
npm run build

# 3. Serve with Nginx
# Copy build/ to /var/www/html/
# Configure Nginx (see nginx.conf)
```

---

## Configuración de Producción

### Nginx (Frontend + Reverse Proxy)

```nginx
server {
    listen 80;
    server_name tudominio.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name tudominio.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # Frontend
    location / {
        root /var/www/html;
        try_files $uri /index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Static files
    location /static/ {
        alias /path/to/staticfiles/;
    }

    # Media files
    location /media/ {
        alias /path/to/media/;
    }
}
```

### Systemd Services

#### Backend Service

```ini
# /etc/systemd/system/fetal-medical-backend.service
[Unit]
Description=Fetal Medical Backend
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/Backend
Environment="PATH=/path/to/.venv/bin"
ExecStart=/path/to/.venv/bin/gunicorn --workers 4 --bind 0.0.0.0:8000 wsgi:application

[Install]
WantedBy=multi-user.target
```

#### Celery Worker

```ini
# /etc/systemd/system/fetal-medical-celery.service
[Unit]
Description=Fetal Medical Celery Worker
After=network.target

[Service]
Type=forking
User=www-data
Group=www-data
WorkingDirectory=/path/to/Backend
Environment="PATH=/path/to/.venv/bin"
ExecStart=/path/to/.venv/bin/celery -A settings worker -l info

[Install]
WantedBy=multi-user.target
```

### Iniciar Servicios

```bash
sudo systemctl start fetal-medical-backend
sudo systemctl start fetal-medical-celery
sudo systemctl enable fetal-medical-backend
sudo systemctl enable fetal-medical-celery
```

---

## Monitoreo y Mantenimiento

### Logs

```bash
# Docker logs
docker-compose logs -f backend
docker-compose logs -f celery

# System logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### Backups

```bash
# Database backup
docker-compose exec db pg_dump -U postgres fetal_medical > backup.sql

# Restore
docker-compose exec -T db psql -U postgres fetal_medical < backup.sql

# Media files backup
tar -czf media_backup.tar.gz media/
```

### Actualización

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose build
docker-compose up -d

# Run migrations
docker-compose exec backend python manage.py migrate
```

---

## Troubleshooting

### El frontend no carga
```bash
# Verificar Nginx
sudo nginx -t
sudo systemctl status nginx

# Reconstruir frontend
docker-compose up -d --build frontend
```

### Error 502 Bad Gateway
```bash
# Verificar backend
docker-compose logs backend
sudo systemctl status fetal-medical-backend

# Reiniciar servicios
docker-compose restart backend
```

### Base de datos no conecta
```bash
# Verificar PostgreSQL
docker-compose logs db
sudo systemctl status postgresql

# Verificar credenciales en .env
```

---

## Seguridad

### Checklist de Producción

- [ ] DEBUG=False
- [ ] SECRET_KEY único y seguro
- [ ] ALLOWED_HOSTS configurado
- [ ] HTTPS activado
- [ ] Database backups automáticos
- [ ] Firewall configurado
- [ ] Fail2ban instalado
- [ ] Contraseñas fuertes
- [ ] Límites de rate limiting
- [ ] Headers de seguridad configurados

### Comandos Útiles

```bash
# Generar SECRET_KEY
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

# Test SSL
openssl s_client -connect tudominio.com:443

# Ver puertos abiertos
sudo netstat -tulpn | grep LISTEN
```

---

**Última actualización:** 2026-01-27
