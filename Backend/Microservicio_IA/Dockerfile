# Microservicio IA Dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libgomp1 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app/

# Create directories for models and datasets
RUN mkdir -p /app/trained_models /app/datasets /app/logs

# Create non-root user
RUN useradd -m -u 1000 iauser && chown -R iauser:iauser /app
USER iauser

# Expose port
EXPOSE 8001

# Health check: con mTLS el servidor exige certificado de cliente, asi que
# el propio healthcheck debe presentar uno (ver docker-compose.yml para el
# volumen montado en /app/certs).
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import requests; requests.get('https://localhost:8001/health', timeout=5, cert=('/app/certs/client.crt','/app/certs/client.key'), verify='/app/certs/ca.crt')" || exit 1

# Run server con mTLS (certificado de cliente obligatorio). start_mtls.sh
# falla rapido y con un mensaje claro si los certificados no estan montados,
# en vez de arrancar en HTTP plano silenciosamente.
CMD ["bash", "start_mtls.sh"]
