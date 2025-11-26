# TaskFlow API - Project Design

## Overview
TaskFlow API is a task management REST API built with FastAPI and PostgreSQL.

## Architecture

### System Components
- **API Layer**: FastAPI with async endpoints
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Cache**: Redis for session and frequently accessed data
- **Auth**: JWT-based authentication with refresh tokens
- **Notifications**: WebSocket server for real-time updates

### Tech Stack
- Python 3.11+
- FastAPI 0.100+
- SQLAlchemy 2.0
- Alembic for migrations
- Redis for caching
- Pydantic for validation

## Database Schema

### Users Table
- id (UUID, PK)
- email (VARCHAR, unique)
- password_hash (VARCHAR)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)

### Projects Table
- id (UUID, PK)
- name (VARCHAR)
- owner_id (FK -> Users)
- created_at (TIMESTAMP)

### Tasks Table
- id (UUID, PK)
- title (VARCHAR)
- description (TEXT)
- status (ENUM: pending, in_progress, completed)
- project_id (FK -> Projects)
- assignee_id (FK -> Users)
- due_date (TIMESTAMP)
- created_at (TIMESTAMP)

## API Endpoints

### Authentication
- POST /auth/register - Register new user
- POST /auth/login - Login and get JWT
- POST /auth/refresh - Refresh access token

### Projects
- GET /projects - List user's projects
- POST /projects - Create project
- GET /projects/{id} - Get project details
- PUT /projects/{id} - Update project
- DELETE /projects/{id} - Delete project

### Tasks
- GET /projects/{project_id}/tasks - List tasks
- POST /projects/{project_id}/tasks - Create task
- GET /tasks/{id} - Get task details
- PUT /tasks/{id} - Update task
- DELETE /tasks/{id} - Delete task

## Testing Strategy

### Unit Tests
- Model validation tests
- Service layer tests
- Utility function tests

### Integration Tests
- API endpoint tests with TestClient
- Database transaction tests
- Authentication flow tests

### E2E Tests
- Full user journey tests
- WebSocket notification tests

## Security Considerations
- JWT tokens with short expiry (15 min access, 7 day refresh)
- Password hashing with bcrypt
- Rate limiting per IP and per user
- Input validation with Pydantic
- SQL injection prevention via ORM
