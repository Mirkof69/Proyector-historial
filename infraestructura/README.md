# infraestructura

Configuración de los servicios que rodean al sistema.

| Carpeta o archivo | Para qué sirve |
|---|---|
| `nginx/backend.conf`, `nginx/frontend.conf` | Proxy inverso de la API y del frontend compilado (despliegue con nginx) |
| `redis/` | Arranque de Redis y limpieza de la caché |
| `vault/vault_init.sh` | Carga de secretos en HashiCorp Vault (opcional; el backend lo lee si existen `VAULT_ADDR` y `VAULT_TOKEN`) |
| `mtls/` | Certificados y arranque del servicio de IA con TLS mutuo (`certs/` no se versiona) |
| `tunel/` | Publicación por Internet con Caddy y Cloudflare Tunnel (local, fuera de Git; se lanza con `scripts\PUBLICAR_WEB.bat`) |
| `DESPLIEGUE_MEDIDO.md` | Mediciones de carga y la configuración que resultó de ellas (workers, límites de conexión) |
