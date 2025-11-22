# Deployment Notes & Troubleshooting

This document contains critical information for deploying the Devussy streaming server to a VPS.

## 🚨 Critical: Before You Deploy

**ALWAYS** verify the integrity of `streaming_server/app.py` before pushing.
We have seen issues where `app.py` gets corrupted (e.g., `IndentationError`, missing functions) during edits.

### 1. Verify Syntax
Run this command locally to check for syntax errors:
```bash
python -m py_compile devussy-web/streaming_server/app.py
```
If it produces no output, the syntax is valid.

### 2. Check for "Orphaned" Code
Ensure that `design_stream` and other functions are properly defined and not cut off.

## VPS Deployment Checklist

1.  **Secrets**: Ensure `.env` on the VPS contains:
    *   `STREAMING_SECRET` (Must match what Nginx expects)
    *   `REQUESTY_API_KEY` (Or other LLM provider key)

2.  **Pull Latest Code**:
    ```bash
    git pull origin devussy-testing
    ```

3.  **Rebuild Containers**:
    **Crucial**: If you changed Python code, you MUST rebuild the container if you are using the production compose file (which does not mount volumes).
    ```bash
    docker compose -f docker-compose.prod.yml up -d --build
    ```

4.  **Verify Logs**:
    Check if the server started correctly:
    ```bash
    docker compose -f docker-compose.prod.yml logs -f streaming-server
    ```

## Troubleshooting Streaming

If streaming "is not working" (hanging, 403, or connection closed):

### 1. Check Nginx Logs
```bash
docker compose -f docker-compose.prod.yml logs -f nginx
```
*   **403 Forbidden**: The `X-Streaming-Proxy-Key` header is missing or incorrect. Check `STREAMING_SECRET` in `.env`.
*   **502 Bad Gateway**: The `streaming-server` is down. Check its logs.
*   **Buffering**: Ensure `proxy_buffering off;` is in `nginx.conf`.

### 2. Check Streaming Server Logs
```bash
docker compose -f docker-compose.prod.yml logs -f streaming-server
```
*   Look for Python tracebacks (like `IndentationError`).
*   Look for "Application startup complete".

### 3. Test Locally on VPS
You can try to hit the streaming endpoint directly from the VPS shell to verify the container is responding:
```bash
curl -X POST http://localhost:8000/api/design/stream \
  -H "Content-Type: application/json" \
  -H "X-Streaming-Proxy-Key: YOUR_SECRET_HERE" \
  -d '{"projectName": "Test", "requirements": "Test"}'
```
(Replace `YOUR_SECRET_HERE` with the value from `.env`)

## Common Issues

*   **IndentationError**: Python is sensitive to whitespace. Copy-pasting code can sometimes mess this up.
*   **Missing Imports**: If `app.py` was edited partially, imports might be missing.
*   **Old Image**: Forgetting to run `--build` means the VPS runs the old code.
