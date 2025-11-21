#!/bin/sh
set -e

# Entry script for nginx container - choose HTTPS or HTTP-only config based on cert availability
DOMAIN=${LETSENCRYPT_DOMAIN:-dev.ussy.host}
CERT_DIR=/etc/letsencrypt/live/$DOMAIN
CERT_FILE=$CERT_DIR/fullchain.pem

echo "[nginx entrypoint] Using domain: $DOMAIN"

if [ -f "$CERT_FILE" ]; then
  echo "[nginx entrypoint] Certificates found for $DOMAIN; enabling HTTPS"
  envsubst '$STREAMING_SECRET $LETSENCRYPT_DOMAIN' < /etc/nginx/nginx.prod.conf.template > /etc/nginx/nginx.conf
else
  echo "[nginx entrypoint] Certificates not found for $DOMAIN ($CERT_FILE); using HTTP-only config"
  envsubst '$STREAMING_SECRET $LETSENCRYPT_DOMAIN' < /etc/nginx/nginx.prod.conf.http.template > /etc/nginx/nginx.conf
fi

exec nginx -g 'daemon off;'
