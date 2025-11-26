# Phase 2: Database Schema Design and Initial Migration

**Project**: TaskFlow API
**Total Steps**: 5
**Depth Level**: detailed

## Tasks

<!-- PHASE_TASKS_START -->

### 2.1: Create the initial database schema file `src/db/schema.sql`
- Open your code editor and navigate to `src/db/`
- Create a new file named `schema.sql` inside `src/db/`
- Define tables: `users`, `tasks`, and `task_assignments` with appropriate columns
- For example, `users` should include `id` (primary key), `username`, `email`, `hashed_password`, `created_at`
- `tasks` should include `id`, `title`, `description`, `status`, `created_at`, `updated_at`
- `task_assignments` should include `id`, `task_id` (foreign key), `user_id` (foreign key), `assigned_at`
- Add foreign key constraints to enforce relationships
- Create indexes on frequently queried columns like `user_id` and `task_id`
- Save the file
- **Acceptance check:** open the file and verify that all tables and indexes are properly defined

### 2.2: Implement database connection manager in `src/db/connection.py`
- Create a new file `connection.py` inside `src/db/`
- Import necessary modules: `sqlalchemy`, `contextlib`, `os`
- Define a class `DatabaseManager` with:
- An `__init__` method that takes database URL (from environment variable or hardcoded for now)
- `__enter__` and `__exit__` methods to support context management
- Methods: `connect()`, `disconnect()`, `execute_query(query: str)` to handle database operations
- Use SQLAlchemy's `create_engine` with connection pooling
- Implement connection setup in `connect()`
- Implement `execute_query()` to run raw SQL commands
- Ensure proper closing of connections in `__exit__`
- Save the file
- **Acceptance check:** instantiate `DatabaseManager`, run a simple `SELECT 1` query, and verify it executes without errors

### 2.3: Write unit tests in `tests/unit/test_database.py`
- Create a new test file `test_database.py` inside `tests/unit/`
- Import necessary modules: `pytest`, `DatabaseManager` from `src/db/connection.py`
- Write a test `test_connection_establishment()` that:
- Creates an instance of `DatabaseManager`
- Uses context manager to connect and disconnect
- Asserts no exceptions occur
- Write a test `test_execute_query()` that:
- Executes a simple `SELECT 1` query
- Checks that the result is as expected
- Write a test `test_error_handling()` that:
- Attempts to run an invalid query
- Asserts that an exception is raised
- Save the file
- **Acceptance check:** run `pytest tests/unit/test_database.py` and ensure all tests pass

### 2.4: Run code quality checks for the database code
- Execute: `black src/db/`
- Execute: `flake8 src/db/`
- Review output for formatting issues or style violations
- Fix any issues reported by `flake8` or `black`
- Save all changes
- **Acceptance check:** ensure no errors or warnings are reported after running these tools

### 2.5: Commit the database schema and connection code
- Run: `git add src/db/schema.sql src/db/connection.py tests/unit/test_database.py`
- Run: `git commit -m "feat: add initial database schema and connection manager"`

<!-- PHASE_TASKS_END -->

## Context

<!-- PHASE_CONTEXT_START -->
This phase is part of the adaptive pipeline with complexity-aware generation.
<!-- PHASE_CONTEXT_END -->

## Outcomes

<!-- PHASE_OUTCOMES_START -->
<!-- Updates added as tasks complete -->
<!-- PHASE_OUTCOMES_END -->
