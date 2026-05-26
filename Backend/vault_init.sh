#!/bin/bash
# =============================================================================
# SCRIPT DE INICIALIZACIÓN HASHICORP VAULT
# =============================================================================
# Ejecutar en el servidor de Producción antes de iniciar Django.
# Requiere: VAULT_ADDR, VAULT_TOKEN como variables de entorno.

set -euo pipefail

: "${VAULT_ADDR:='http://127.0.0.1:8200'}"
: "${VAULT_TOKEN:?VAULT_TOKEN no está definido. Establecer antes de ejecutar.}"

export VAULT_ADDR
export VAULT_TOKEN

echo "Configurando HashiCorp Vault para Fetal Medical System..."

# Habilitar motor de KV v2
vault secrets enable -path=secret kv-v2 2>/dev/null || echo "KV v2 ya habilitado"

# Escribir secretos del backend
vault kv put secret/fetalmedical/backend \
    SECRET_KEY="${SECRET_KEY:?SECRET_KEY no definido}" \
    DB_PASSWORD="${DB_PASSWORD:?DB_PASSWORD no definido}" \
    DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-settings.production}" \
    AI_SERVICE_URL="${AI_SERVICE_URL:-http://fastapi:8001}" \
    ALLOWED_HOSTS="${ALLOWED_HOSTS:-fetalmedical.com,api.fetalmedical.com}"

# JWT signing keys
vault kv put secret/fetalmedical/jwt \
    JWT_SIGNING_KEY="${JWT_SIGNING_KEY:?JWT_SIGNING_KEY no definido}" \
    JWT_REFRESH_KEY="${JWT_REFRESH_KEY:?JWT_REFRESH_KEY no definido}" \
    JWT_ACCESS_TOKEN_LIFETIME_MINUTES="${JWT_ACCESS_TOKEN_LIFETIME_MINUTES:-15}" \
    JWT_REFRESH_TOKEN_LIFETIME_DAYS="${JWT_REFRESH_TOKEN_LIFETIME_DAYS:-1}"

# RabbitMQ credentials
vault kv put secret/fetalmedical/rabbitmq \
    RABBITMQ_USER="${RABBITMQ_USER:-fetalmedical}" \
    RABBITMQ_PASS="${RABBITMQ_PASS:?RABBITMQ_PASS no definido}" \
    RABBITMQ_HOST="${RABBITMQ_HOST:-rabbitmq}" \
    RABBITMQ_PORT="${RABBITMQ_PORT:-5672}"

# Redis password
vault kv put secret/fetalmedical/redis \
    REDIS_PASSWORD="${REDIS_PASSWORD:?REDIS_PASSWORD no definido}" \
    REDIS_HOST="${REDIS_HOST:-redis}" \
    REDIS_PORT="${REDIS_PORT:-6379}"

# MinIO credentials (DICOM storage on-premise)
vault kv put secret/fetalmedical/minio \
    MINIO_ACCESS_KEY="${MINIO_ACCESS_KEY:?MINIO_ACCESS_KEY no definido}" \
    MINIO_SECRET_KEY="${MINIO_SECRET_KEY:?MINIO_SECRET_KEY no definido}" \
    MINIO_BUCKET="${MINIO_BUCKET:-fetal-dicom}" \
    MINIO_ENDPOINT="${MINIO_ENDPOINT:-http://minio:9000}"

# Orthanc PACS credentials
vault kv put secret/fetalmedical/orthanc \
    ORTHANC_USER="${ORTHANC_USER:-fetalmedical}" \
    ORTHANC_PASS="${ORTHANC_PASS:?ORTHANC_PASS no definido}" \
    ORTHANC_URL="${ORTHANC_URL:-http://orthanc:8042}"

# Certificados mTLS (Vault PKI)
vault kv put secret/fetalmedical/certs \
    SERVER_CERT="${SERVER_CERT:-}" \
    SERVER_KEY="${SERVER_KEY:-}" \
    CA_CERT="${CA_CERT:-}"

echo "Secretos inicializados correctamente en Vault."
echo "ADVERTENCIA: Los secretos marcados con * no se muestran en log por seguridad."
