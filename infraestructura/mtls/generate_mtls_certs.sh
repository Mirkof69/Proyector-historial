#!/bin/bash
# =============================================================================
# GENERADOR DE CERTIFICADOS mTLS (Mutual TLS)
# =============================================================================
# Genera la CA (Certificate Authority) y los certificados cliente y servidor
# para la comunicación segura entre Django (Cliente) y FastAPI (Servidor).

mkdir -p certs
cd certs

echo "1. Generando CA..."
openssl genrsa -out ca.key 2048
openssl req -new -x509 -days 3650 -key ca.key -out ca.crt -subj "/C=BO/L=La Paz/O=FetalMedical/CN=FetalMedical CA"

echo "2. Generando Certificado del Servidor (FastAPI)..."
# SAN obligatorio: sin esto, clientes TLS modernos (Python ssl, urllib3)
# rechazan el certificado por "Hostname mismatch" aunque la CA sea valida,
# porque ya no aceptan el CN como fallback de hostname.
openssl genrsa -out server.key 2048
openssl req -new -key server.key -out server.csr -subj "/C=BO/L=La Paz/O=FetalMedical/CN=fastapi-server"
printf "subjectAltName=DNS:localhost,DNS:ia_service,IP:127.0.0.1" > server_san.ext
openssl x509 -req -days 365 -in server.csr -CA ca.crt -CAkey ca.key -set_serial 01 -out server.crt \
    -extfile server_san.ext
rm -f server_san.ext

echo "3. Generando Certificado del Cliente (Django)..."
openssl genrsa -out client.key 2048
openssl req -new -key client.key -out client.csr -subj "/C=BO/L=La Paz/O=FetalMedical/CN=django-client"
openssl x509 -req -days 365 -in client.csr -CA ca.crt -CAkey ca.key -set_serial 02 -out client.crt

echo "Certificados mTLS generados en ./certs/"
ls -la
