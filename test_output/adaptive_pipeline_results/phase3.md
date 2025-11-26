# Phase 3: User Authentication and Authorization

**Project**: TaskFlow API
**Total Steps**: 10
**Depth Level**: detailed

## Tasks

<!-- PHASE_TASKS_START -->

### 3.1: Set Up Authentication Dependencies and Environment
- Install necessary libraries: run `pip install fastapi uvicorn sqlalchemy alembic passlib[bcrypt] python-jose redis`
- Update your `requirements.txt` or environment file to include these packages
- Create a `.env` file in the project root to store secret keys and configuration variables (e.g., `SECRET_KEY`, Redis URL)
- Run `pip freeze > requirements.txt` to lock dependencies
- Commit these changes with: `git add requirements.txt .env` and `git commit -m "chore: add dependencies for authentication"`

### 3.2: Create User Model in `src/models/user.py`
- Define a SQLAlchemy model class `User` with fields: `id`, `username`, `email`, `hashed_password`, `is_active`, `created_at`
- Add unique constraints on `username` and `email`
- Ensure password is stored hashed
- Include a `__repr__` method for debugging
- Save the file as `src/models/user.py`
- Run migrations: generate migration with `alembic revision --autogenerate -m "Add user table"`
- Apply migrations: `alembic upgrade head`
- Commit: `git add src/models/user.py migrations/ && git commit -m "feat: create User model and migration"`

### 3.3: Implement User Registration Endpoint in `src/api/auth.py`
- Create a new file `src/api/auth.py` if not existing
- Define an API router with `APIRouter()`
- Add a POST endpoint `/register` accepting `username`, `email`, `password`
- In the handler:
- Hash the password using `passlib.context.CryptContext`
- Check if `username` or `email` already exists in the database
- Create a new `User` record with hashed password
- Save to database session and commit
- Return a success message or user info (excluding password)
- Test registration with sample data using `curl` or `httpie`
- Register the router in your main `app.py`
- Commit: `git add src/api/auth.py` and `git commit -m "feat: add user registration endpoint"`

### 3.4: Implement User Login Endpoint in `src/api/auth.py`
- In `src/api/auth.py`, add a POST endpoint `/login`
- Accept `username` and `password`
- Retrieve user by `username` from database
- Verify password with `passlib`
- If valid, generate JWT token using `python-jose` with user info
- Store token in response (or set as cookie if needed)
- Return token and user info (excluding password)
- Test login with correct and incorrect credentials
- Update `app.py` to include the auth router
- Commit: `git add src/api/auth.py` and `git commit -m "feat: add user login endpoint"`

### 3.5: Create Dependencies for Authentication in `src/dependencies/auth.py`
- Create a new file `src/dependencies/auth.py`
- Implement `get_current_user()` function
- Extract token from request headers
- Decode JWT token and verify signature
- Retrieve user from database using ID from token
- Raise HTTP 401 if invalid or not found
- Implement `oauth2_scheme` using `OAuth2PasswordBearer`
- Test dependency by creating a protected route that requires authentication
- Commit: `git add src/dependencies/auth.py` and `git commit -m "feat: create auth dependencies for protected routes"`

### 3.6: Implement Authorization Logic for User Permissions
- Decide on user roles if needed (e.g., admin, user)
- Extend `User` model with a `role` field if necessary
- Create a decorator or dependency that checks user role before allowing certain actions
- Add sample protected route that only allows admin users
- Test role-based access control
- Commit: `git add src/models/user.py src/api/auth.py src/dependencies/auth.py` and `git commit -m "feat: add authorization checks"`

### 3.7: Integrate Redis for Token Blacklisting or Session Management (Optional)
- Use `redis` dependency to connect in a dedicated `src/redis_client.py`
- Create a `RedisClient` class to handle connection pooling
- Add functions to blacklist tokens or manage sessions
- Modify login endpoint to store tokens in Redis if implementing logout or token revocation
- Test Redis connection and basic store/retrieve operations
- Commit: `git add src/redis_client.py` and `git commit -m "feat: integrate Redis for session management"`

### 3.8: Write Tests for Authentication and Authorization
- Create test files in `tests/integration/test_auth.py`
- Test registration flow with valid and invalid data
- Test login with correct and incorrect credentials
- Test protected routes with valid and invalid tokens
- Verify error messages and status codes
- Run tests: `pytest tests/`
- Commit: `git add tests/integration/test_auth.py` and `pytest` output validation

### 3.9: Run Code Quality and Formatting Checks
- Execute `black src/`
- Execute `flake8 src/`
- Fix any issues reported
- Run tests again to confirm no regressions
- Commit: `git add src/` and `git commit -m "chore: run code quality checks and validate"`

### 3.10: Final Documentation and User Guidance
- Update `README.md` or equivalent docs with instructions on registration, login, and token usage
- Add example requests and expected responses
- Document token expiration and refresh if applicable
- Commit: `git add README.md` and `git commit -m "docs: update auth usage instructions"`

<!-- PHASE_TASKS_END -->

## Context

<!-- PHASE_CONTEXT_START -->
This phase is part of the adaptive pipeline with complexity-aware generation.
<!-- PHASE_CONTEXT_END -->

## Outcomes

<!-- PHASE_OUTCOMES_START -->
<!-- Updates added as tasks complete -->
<!-- PHASE_OUTCOMES_END -->
