# VPS Deployment Guide

This guide explains how to deploy the Devussy application on a VPS using Docker.

## Prerequisites

- Docker and Docker Compose installed on your VPS.
- The `devussy-testing` repository cloned onto your VPS.
- Environment variables set (either in a `.env` file or exported in the shell).

## Deployment Steps

1.  **Navigate to the web directory:**
    ```bash
    cd devussy-web
    ```

2.  **Create/Update your `.env` file:**
    Ensure you have a `.env` file in `devussy-web` with the necessary keys:
    ```bash
    REQUESTY_API_KEY=your_key_here
    STREAMING_SECRET=your_secret_here
    ```

3.  **Run with Production Compose File:**
    Use the `docker-compose.prod.yml` file which is optimized for production (no volume mounts, production nginx config).

    ```bash
    docker-compose -f docker-compose.prod.yml up --build -d
    ```

4.  **Verify Deployment:**
    - Check logs: `docker-compose -f docker-compose.prod.yml logs -f`
    - Visit your VPS IP address in the browser.

## SSL Configuration (Optional but Recommended)

The default `nginx.prod.conf` serves traffic over HTTP on port 80. To enable HTTPS:

1.  Obtain SSL certificates (e.g., using Certbot).
2.  Edit `nginx/nginx.prod.conf`:
    - Uncomment the HTTPS `server` block.
    - Update the `ssl_certificate` and `ssl_certificate_key` paths to point to your certificates.
    - Uncomment the redirect in the HTTP block if you want to force HTTPS.
3.  Restart Nginx:
    ```bash
    docker-compose -f docker-compose.prod.yml restart nginx
    ```
