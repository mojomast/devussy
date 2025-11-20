# DevPlan: Deploy devussy-web to a VPS (for streaming-friendly hosting)

This dev plan outlines a recommended architecture and step-by-step deployment plan for hosting the frontend and the streaming-enabled backend on a VPS. The plan focuses on reliability, streaming support (SSE or WebSocket), security, and a reproducible approach using Docker + Docker Compose.

Goals
- Host both the Next.js frontend and a streaming-enabled Python backend on the same VPS (or across multiple VMs / hosts).
- Provide robust streaming (SSE or WebSocket) for LLM token updates.
- Securely store and avoid committing LLM API keys to the repository.
- Provide automated deployments and easy rollback.

Recommended architecture (MVP)
- One VPS (DigitalOcean, AWS EC2, Hetzner, etc.) running:
  - nginx (reverse proxy, TLS termination)
  - docker-compose services:
    - frontend: Next.js production build served by Node/PM2 or a static export (port 3000)
    - streaming_server: FastAPI + Uvicorn (ASGI) for SSE/WebSocket streaming (port 8000)
    - optional: backend sync wrapper (for fallbacks) if needed

Why Docker + nginx + systemd?
- Docker reduces environment/dependency mismatch and allows consistent deployments.
- nginx acts as TLS termination and as a stable ingress for both frontend and streaming backend.
- systemd can manage the docker-compose process or run without it if you prefer a containerless approach.

High-level tasks
1. Decide streaming transport type (SSE recommended unless bidirectional interaction is needed).
2. Add a FastAPI wrapper that uses the existing ProjectDesign generator pipeline to produce streamed tokens. (We previously recommended and planned this.)
3. Containerize services using the included Dockerfiles.
4. Add a docker-compose file to orchestrate frontend + streaming server.
5. Add nginx config to proxy `/api/design/stream` to the streaming server and `/api/design` to synchronous path (fallback).
6. Configure secrets and env variables via a `.env` file or the VPS secrets store (systemd, docker secrets, etc.) — do NOT commit secrets.
7. Configure systemd to manage docker-compose or run containers using a user-level service. Alternatively, use `docker-compose up -d` within a startup script and systemd service to run it.
8. Add health checks, logging, and monitoring.

Detailed Implementation Steps

Phase 0 — Planning & prerequisites
- Select the VPS provider and decide the host OS (Ubuntu 22.04 recommended).
- Decide whether to use Docker or not. Docker is recommended.
- Ensure domain is ready and DNS can be updated.

Phase 1 — Implement a streaming server (FastAPI) (2–4 days)
1. Create `streaming_server/app.py` using FastAPI. Add endpoints:
   - POST `/api/design` (synchronous fallback returning a JSON payload)
   - POST `/api/design/stream` (SSE or WebSocket endpoint streaming tokens)
2. Use the existing `ProjectDesignGenerator` to generate results, adding code to consume tokens and yield SSE events.
3. Add a header-based API key check for inbound traffic from the front-end or Vercel (if used as proxy). Use a header like `X-Streaming-Proxy-Key` and require it in the server env (or use standard Authorization header).
4. Implement test code to mock LLM output and validate token streaming flow.
5. Add `streaming_server/Dockerfile`: base image python:3.12, install requirements, copy `src` & `streaming_server` code, run `uvicorn streaming_server.app:app --host 0.0.0.0 --port 8000 --loop uvloop --workers 1`.

Phase 2 — Frontend adjustments & fallback (1 day)
1. Update frontend code to open SSE / WebSocket connection to `/api/design/stream` and display incremental token updates.
2. Add fallback if the streaming connection fails (call POST `/api/design` to fetch the full response).
3. Add a config flag to use streaming or not (ENV var `USE_STREAMING` or feature toggle in the app's UI).

Phase 3 — Containerization & orchestration (1 day)
1. Add `docker-compose.yml` with services:
   - `frontend` builds Next app: runs `npm run build`, and `npm run start` (production server).
   - `streaming-server` builds and runs `uvicorn` with the `streaming_server` app.
2. Add environment variables via `.env` file for container secrets — use Docker secrets or OS-level secrets for production.
3. Add `scripts/deploy-vps.sh` that builds and starts `docker-compose` and optionally pushes images.

Phase 4 — Reverse proxy & TLS (0.5 day)
1. NGINX configuration (nginx site file) to proxy requests:
   - `/` → `frontend:3000`
   - `/api/design/stream` → `streaming-server:8000`
   - `/api/design` → `streaming-server:8000` (fallback)
2. Use Certbot to request certificates for TLS and enable redirect to `https`.
3. Add HTTP security headers.

Phase 5 — Deployment & automation (0.5–1 day)
1. Provide a `systemd` service file to `docker-compose up` the stack on boot, or run `docker-compose` under a systemd-managed service.
2. Apply firewall rules (UFW to allow ports 80, 443 only).
3. Add a deployment script to build images and restart services.

Phase 6 — Monitoring & testing (0.5–1 day)
1. Implement health endpoints for both services and validate with a simple check script or via UptimeRobot.
2. Add logs shipping to file or services like Grafana Agent or Papertrail.
3. Add basic metrics: frequency of requests, average token count, request latency.

CI/CD / Deploy workflow suggestion
- Build Docker images for frontend & streaming server in CI (GitHub Actions).
- Push to a container registry or the VPS as tar file for local load.
- Use a deployment action/step to SSH into the VPS and run the deploy script.

Secrecy handling: API Key
- Never commit secret keys to the repo. Use one of the following:
  - Docker secrets and `docker-compose` to pass secret values to containers.
  - Systemd environment file `env.conf` that is stored on the server and is not part of the repo.
  - Export env variable at runtime before starting the service.
  - Use a remote secret manager (e.g., HashiCorp Vault, AWS Secrets Manager) if available.

Roadmap & file changes needed
- Add `streaming_server` folder with FastAPI code and `Dockerfile`.
- Add `docker-compose.yml` at repo root with `frontend` and `streaming-server` services.
- Add `nginx` site config file (e.g., `nginx/nginx.conf`) for use on VPS.
- Add `scripts/deploy-vps.sh` which uses `docker-compose pull`/`docker-compose up -d` and restarts services.

Testing & Acceptance criteria
1. Local development: `docker-compose up --build` should bring up both the frontend and the streaming server with correct routing (via nginx or port mapping).
2. Streaming: POST to `/api/design/stream` should return SSE events (or WebSocket messages) that the frontend consumes. The server should respond with at least one token event within 5 seconds.
3. Security: The streaming server rejects requests missing `X-Streaming-Proxy-Key` header or equivalent.
4. Production build & SSL: After deploying to the VPS and pointing DNS, the site should be available under the domain with HTTPS.
5. Secret management: The API key must be set via environment variables or docker secrets — it should not be present in the repository.

Rollback & troubleshooting
- If new deploy breaks: revert the `docker-compose` or sysctl and restart the previous container image.
- For debugging, tail logs from `docker-compose logs -f` and check `uvicorn` and `next` logs.

Follow-up / Additional enhancements
- Add autoscaling: run streaming server behind a load balancer if load increases.
- Add an identity check or auth layer for the streaming endpoint.
- Provide a lightweight admin dashboard to restart services and check metrics via a simple `/status` endpoint secured with a key.

Attachments included below (templates):
- `docker-compose.yml` (example skeleton)
- `streaming_server/Dockerfile` (skeleton)
- `nginx/nginx.conf` (example)
- `scripts/deploy-vps.sh` (example)
