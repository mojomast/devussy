
You are an expert software developer creating a detailed, step-by-step implementation plan. You have been given a high-level phase description and need to break it down into precise, numbered, actionable steps that a "lesser coding agent" (an AI with basic coding skills) can execute.

### Repository Context
- **Type**: python
- **Files**: 42
- **Lines**: 1337
- **Description**: A test application
- **Version**: 1.0.0
- **Author**: Test Author

#### Dependencies
- **python**: fastapi, uvicorn


Use existing patterns and directory structure in your implementation steps.




## Phase to Detail

**Phase : **


## Project Context

# Project: 
### Technology Stack
- None specified


## Your Task

Break this phase into **specific, numbered, actionable steps** using the format: `.X: [Action description]`

### Requirements

1. **Numbering**: Use the format `.1`, `.2`, etc.
   - Each step should have a unique sub-number
   - Steps should be ordered logically (dependencies first)

2. **Actionability & Depth**: Each step must be:
   - Clear and unambiguous
   - Implementable by someone with basic coding skills
   - Testable or verifiable
   - Specific about what to create/modify
   - Expanded with 3–10 sub-bullets ("- ") providing concrete details, file paths, CLI commands, and acceptance checks

3. **Completeness**: Include steps for:
   - Creating files/directories
   - Implementing functions/classes
   - Writing tests
   - Running quality checks (linting, formatting)
   - Git commits at logical milestones
   - Documentation updates
   - User-facing features (help text, examples, error messages if applicable)

4. **Git Commits**: After significant sub-tasks, include a step like:
   - `.X: Commit: git add [files] && git commit -m "[type]: [description]"`
   - Use conventional commit types: `feat:`, `fix:`, `test:`, `docs:`, `chore:`

5. **File Paths**: Be specific about file paths when creating or modifying files
   - Example: "Create `src/models/user.py`" not "Create the user model"

6. **Code Quality**: Include steps for:
   - Running linters (e.g., `flake8 src/`)
   - Running formatters (e.g., `black src/`)
   - Running tests (e.g., `pytest tests/`)

### Example Format (DO NOT COPY - adapt to your specific phase)

```
.1: Create the database schema file `src/db/schema.sql`
- Define tables for users, posts, and comments
- Include foreign key relationships
- Add indexes for performance

.2: Implement database connection manager in `src/db/connection.py`
- Create `DatabaseManager` class with context manager support
- Add methods: connect(), disconnect(), execute_query()
- Handle connection pooling

.3: Write unit tests in `tests/unit/test_database.py`
- Test connection establishment
- Test query execution
- Test error handling

.4: Run code quality checks
- Execute: `black src/db/`
- Execute: `flake8 src/db/`
- Fix any issues found

.5: Commit database infrastructure
- Run: `git add src/db/ tests/unit/test_database.py`
- Run: `git commit -m "feat: implement database connection manager"`
```

## Output Format

Please provide a numbered list of steps in the format described above. Each step should:
- Start with the step number: `.X:`
- Have a clear action verb (Create, Implement, Add, Update, Test, Run, Commit)
- Include specific details about what to build
- MUST include sub-bullets with concrete instructions (at least 3), not placeholders

Focus on making each step implementable and verifiable. The goal is that someone following these steps can build this phase successfully without needing to make significant architectural decisions.

---

## Output Instructions

Provide ONLY the numbered list of implementation steps in the format specified above. Do not include:
- Questions about proceeding to next steps
- Requests for approval or confirmation
- Progress update instructions
- Handoff notes or status updates
- References to updating devplan.md or phase files

Simply output the complete list of steps for this phase, then stop. Each step should be actionable and include the required sub-bullets with concrete details.
