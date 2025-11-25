# Project Design: test@#$%

## Architecture Overview

Pattern: Clean/Hexagonal + Layered
High-level component responsibilities
Mermaid diagram (logical)
```mermaid
flowchart LR
subgraph Presentation
A[FastAPI REST API]
B[Typer CLI]
end
subgraph Application/Domain
C[Services / Use-cases]
D[Domain Models]
end
subgraph Infrastructure
E[Repositories (SQLAlchemy)]
F[Cache (Redis)]
G[Message Broker (Redis -> Dramatiq)]
H[External Clients (HTTPX) - optional]
I[(PostgreSQL)]
J[Workers (Dramatiq Consumers)]
end
A --> C
B --> C
C <--> D
C --> E
E --> I
C --> F
C --> G
J --> C
C --> H
```
Data/control flow examples
Scalability

## Tech Stack

- Language
- Python 3.12 (modern features, performance improvements, long support window).
- Web framework
- FastAPI for async-friendly, typed, self-documented REST APIs.
- Uvicorn as the ASGI server.
- Data layer
- SQLAlchemy 2.x ORM + Alembic for migrations.
- PostgreSQL in production; SQLite for local/dev/tests.
- Background jobs (optional out-of-the-box)
- Dramatiq with Redis broker for simple, robust job processing (alternative: Celery).
- Caching (optional)
- Redis for caching, rate limiting, and task broker co-location.
- Configuration
- pydantic-settings (Pydantic v2) for typed, env-driven configuration.
- CLI
- Typer for a typed, ergonomic CLI.
- HTTP client
- HTTPX (sync/async support, testability).
- Logging and observability
- structlog + stdlib logging for structured logs.
- OpenTelemetry SDK for traces/metrics; Prometheus exporter where relevant.
- Packaging and dependency management
- uv (fast, modern resolver/runner) with pyproject.toml (PEP 621).
- Alternative: Poetry if team prefers.
- Quality tooling
- Ruff (lint + format), Black (optional if you prefer Black formatting), Mypy (type-checking).
- Pytest, Hypothesis (property-based), Coverage.
- pre-commit hooks.
- Containerization and orchestration
- Docker, Docker Compose (dev).
- CI/CD
- GitHub Actions (or GitLab CI), with caching, security checks, and multi-env deploy steps.
- Documentation
- MkDocs Material (developer docs), FastAPI auto-generated API docs (Swagger/Redoc).
- FastAPI + Pydantic: excellent dev experience, type-safety, great community, automatic OpenAPI.
- SQLAlchemy: mature, flexible ORM with strong community; Alembic for safe migrations.
- Redis + Dramatiq: straightforward, reliable, scales well for most workloads.
- Tooling (Ruff/Mypy/Pytest): high ROI on maintainability and correctness.
- uv: fast installs and reproducible environments in CI/local.
- --
