# Phase 4: Core CRUD API for Projects and Tasks

**Project**: TaskFlow API
**Total Steps**: 10
**Depth Level**: detailed

## Tasks

<!-- PHASE_TASKS_START -->

### 4.1: Create the directory structure for core API modules
- Inside the project root, create a folder `src/api/`
- Within `src/api/`, create files `projects.py` and `tasks.py`
- Create an `__init__.py` file in `src/api/` to make it a package
- Verify directory structure exists: `src/api/projects.py`, `src/api/tasks.py`, `src/api/__init__.py`
- Run: `git add src/api/ && git commit -m "chore: set up API module directories and files"`

### 4.2: Define Pydantic models for Project and Task schemas
- Create `src/schemas/project.py` with `ProjectCreate`, `ProjectRead`, `ProjectUpdate` classes
- Create `src/schemas/task.py` with `TaskCreate`, `TaskRead`, `TaskUpdate` classes
- In each, define relevant fields (e.g., `name`, `description`, `status`, `due_date`)
- Use `pydantic.BaseModel` as base class
- Save files and verify syntax correctness
- Run: `black src/schemas/` and `flake8 src/schemas/`
- Commit: `git add src/schemas/ && git commit -m "chore: add Pydantic schemas for projects and tasks"`

### 4.3: Create SQLAlchemy ORM models for Project and Task
- Create `src/models/project.py` with `Project` class
- Create `src/models/task.py` with `Task` class
- Define columns: `id`, `name`, `description`, `status`, `created_at`, `updated_at`, `due_date`
- Set relationships: `Project` has many `Task`s
- Ensure models inherit from `Base` (imported from core setup)
- Save and verify syntax
- Run: `flake8 src/models/`
- Commit: `git add src/models/ && git commit -m "feat: define ORM models for Project and Task"`

### 4.4: Implement CRUD operation functions in `src/api/projects.py`
- Create functions: `create_project`, `get_project`, `update_project`, `delete_project`, `list_projects`
- Use SQLAlchemy session to interact with database
- Handle exceptions (e.g., `NoResultFound`)
- Add docstrings for each function
- Save file and verify correctness
- Run: `flake8 src/api/`
- Commit: `git add src/api/ && git commit -m "feat: implement CRUD functions for projects"`

### 4.5: Implement CRUD operation functions in `src/api/tasks.py`
- Create functions: `create_task`, `get_task`, `update_task`, `delete_task`, `list_tasks`
- Link tasks to projects via foreign key
- Handle errors and invalid inputs
- Document each function
- Save and verify syntax
- Run: `flake8 src/api/`
- Commit: `git add src/api/ && git commit -m "feat: implement CRUD functions for tasks"`

### 4.6: Create FastAPI route endpoints for Projects in `src/api/projects.py`
- Import FastAPI `APIRouter`
- Create a router instance `router = APIRouter()`
- Define routes:
- `POST /projects/` to create a project
- `GET /projects/` to list all projects
- `GET /projects/{project_id}` to retrieve a project
- `PUT /projects/{project_id}` to update a project
- `DELETE /projects/{project_id}` to delete a project
- Call the corresponding CRUD functions within each route
- Return appropriate response models and status codes
- Save and verify syntax
- Run: `flake8 src/api/`
- Commit: `git add src/api/projects.py && git commit -m "feat: add Project endpoints"`

### 4.7: Create FastAPI route endpoints for Tasks in `src/api/tasks.py`
- Import `APIRouter` and instantiate `router`
- Define routes:
- `POST /tasks/` to create a task
- `GET /tasks/` to list all tasks
- `GET /tasks/{task_id}` to retrieve a task
- `PUT /tasks/{task_id}` to update a task
- `DELETE /tasks/{task_id}` to delete a task
- Implement calls to CRUD functions
- Ensure proper response models and error handling
- Save and verify syntax
- Run: `flake8 src/api/`
- Commit: `git add src/api/tasks.py && git commit -m "feat: add Task endpoints"`

### 4.8: Integrate API routers into main FastAPI application
- Locate or create `src/main.py`
- Import project and task routers
- Include routers in FastAPI app with `app.include_router()`
- Set URL prefixes, e.g., `/api/projects` and `/api/tasks`
- Save and verify syntax
- Run: `flake8 src/`
- Run: `uvicorn src.main:app --reload`
- Test endpoints with curl or browser
- Commit: `git add src/main.py && git commit -m "chore: include project and task routers in main app"`

### 4.9: Write basic test cases for API endpoints in `tests/integration/test_projects_tasks.py`
- Create test functions for each route:
- Create project and task
- Retrieve project and task
- List projects and tasks
- Update project and task
- Delete project and task
- Use `httpx` or `TestClient` for requests
- Check response status codes and payload correctness
- Save test file
- Run: `pytest tests/`
- Fix any failing tests or issues
- Commit: `git add tests/ && git commit -m "test: add integration tests for project and task APIs"`

### 4.10: Run code quality and testing routines
- Execute: `black src/`
- Execute: `flake8 src/`
- Execute: `pytest tests/`
- Confirm all checks pass without errors
- Final commit: `git add . && git commit -m "chore: finalize core CRUD API for projects and tasks"`

<!-- PHASE_TASKS_END -->

## Context

<!-- PHASE_CONTEXT_START -->
This phase is part of the adaptive pipeline with complexity-aware generation.
<!-- PHASE_CONTEXT_END -->

## Outcomes

<!-- PHASE_OUTCOMES_START -->
<!-- Updates added as tasks complete -->
<!-- PHASE_OUTCOMES_END -->
