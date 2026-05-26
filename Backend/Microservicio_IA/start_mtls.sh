#!/bin/bash
# =============================================================================
# INICIAR MICROSERVICIO IA CON mTLS
# =============================================================================
# Inicia el servidor Uvicorn exigiendo un certificado cliente firmado por la CA.

CERTS_DIR="../scripts/certs"

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
