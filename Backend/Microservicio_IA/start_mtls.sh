#!/bin/bash
# =============================================================================
# INICIAR MICROSERVICIO IA CON mTLS
# =============================================================================
# Inicia el servidor Uvicorn exigiendo un certificado cliente firmado por la CA.

# En Docker los certificados se montan en /app/certs (ver docker-compose.yml).
# Localmente (fuera de Docker), caen en ../scripts/certs respecto a este
# directorio, que es donde los deja scripts/generate_mtls_certs.sh.
if [ -d "/app/certs" ]; then
    CERTS_DIR="${CERTS_DIR:-/app/certs}"
else
    CERTS_DIR="${CERTS_DIR:-../scripts/certs}"
fi

if [ ! -f "$CERTS_DIR/server.crt" ]; then
    echo "Error: Certificados no encontrados. Ejecute scripts/generate_mtls_certs.sh primero."
    exit 1
fi

echo "Iniciando FastAPI con soporte mTLS..."
uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8001 \
    --ssl-keyfile "$CERTS_DIR/server.key" \
    --ssl-certfile "$CERTS_DIR/server.crt" \
    --ssl-ca-certs "$CERTS_DIR/ca.crt" \
    --ssl-cert-reqs 2  # ssl.CERT_REQUIRED
