# Handoff Prompt: Interactive DevPlan Builder MVP

## 🎯 Mission Brief

You are taking over the **DevPlan Orchestrator** project. The tool currently generates development plans and handoff prompts using LLMs, but it requires all inputs upfront via CLI flags.

**Your Mission**: Transform this into an **interactive DevPlan builder** where users are guided through intelligent questions to build better devplans.

**MVP Goal**: Users should be able to use either:
1. **Interactive CLI** - Guided conversation with smart questions
2. **Web Interface** - Browser-based questionnaire with real-time streaming

---

## 📊 Current State

### ✅ What's Working
- **Core Pipeline**: User inputs → Project Design → Basic DevPlan → Detailed DevPlan → Handoff Prompt
- **CLI**: 9 functional commands (`generate-design`, `generate-devplan`, `generate-handoff`, `run-full-pipeline`, etc.)
- **LLM Providers**: OpenAI, Generic OpenAI-compatible, Requesty (factory pattern)
- **Testing**: 227/242 tests passing (93.8%)
- **Package**: Built and ready (`devussy-0.1.0.tar.gz` + `.whl` in `dist/`)
- **Documentation**: Comprehensive (README, ARCHITECTURE, EXAMPLES, PROVIDERS, TESTING)

### ❌ What's Missing (Your Mission)
1. **Interactive questioning system** - No guided UX, users must know all flags
2. **Web interface** - Zero web UI exists (Phase 11 was planned but never started)
3. **Smart adaptive questions** - No context-aware question flow
4. **Session management** - Can't save/resume interactive sessions

### Current CLI Usage (Non-Interactive)
```bash
# User must provide everything upfront:
devussy generate-design \
  --name "My Project" \
  --languages "Python,JavaScript" \
  --requirements "Build an API" \
  --frameworks "FastAPI,React" \
  --apis "Stripe,SendGrid"
```

**Problem**: Users don't know what to provide, questions aren't adaptive, no guidance.

---

## 🗂️ Project Structure

```
devussy-fresh/
├── src/
│   ├── cli.py              # CLI commands (Typer) - needs interactive mode
│   ├── llm_client.py       # Abstract LLM client interface
│   ├── config.py           # Pydantic config system
│   ├── models.py           # ProjectDesign, DevPlan, HandoffPrompt models
│   ├── templates.py        # Jinja2 template loader
│   ├── clients/
│   │   ├── factory.py      # LLM client factory
│   │   ├── openai_client.py
│   │   ├── generic_client.py
│   │   └── requesty_client.py
│   ├── pipeline/
│   │   ├── compose.py      # PipelineOrchestrator
│   │   ├── project_design.py
│   │   ├── basic_devplan.py
│   │   ├── detailed_devplan.py
│   │   └── handoff_prompt.py
│   └── (need to create)
│       ├── interactive.py  # ⭐ NEW: Interactive questionnaire system
│       └── api/            # ⭐ NEW: FastAPI web interface
│           ├── app.py
│           ├── routes.py
│           ├── auth.py
│           └── static/     # Web UI files
├── templates/              # Jinja2 prompt templates
│   ├── project_design.jinja
│   ├── basic_devplan.jinja
│   ├── detailed_devplan.jinja
│   └── handoff_prompt.jinja
├── tests/                  # 242 tests (57% coverage)
│   ├── unit/
│   ├── integration/
│   └── conftest.py
├── docs/
│   ├── ARCHITECTURE.md
│   ├── EXAMPLES.md
│   ├── PROVIDERS.md
│   └── TESTING.md
├── config/
│   └── config.yaml         # Default configuration
├── dist/                   # Built packages (v0.1.0)
├── MVP_DEVPLAN.md          # ⭐ YOUR ROADMAP
└── MVP_HANDOFF.md          # ⭐ THIS FILE
```

---

## 🎯 Your Mission: Phase 1 - Interactive CLI

**Start here**: Build the interactive questioning system for CLI

### Step 1: Design the Question Flow (1 day)

Create `docs/INTERACTIVE_FLOW.md` documenting:

**Essential Questions** (always ask):
1. Project name
2. What are you building? (web app, API, CLI tool, data pipeline, etc.)
3. Primary programming language(s)
4. Main requirements/goals

**Conditional Questions** (context-dependent):
- If "web app" → Ask about frontend framework
- If "API" → Ask about database, authentication
- If "Python" → Ask about async vs sync, packaging needs
- If "JavaScript" → Ask about TypeScript, Node.js version

**Advanced Questions** (optional):
- External APIs to integrate
- Deployment platform
- Testing requirements
- CI/CD preferences

**Question Flow Logic**:
```
Start → Project Type? 
  ├─ Web App → Languages? → Frontend? → Backend? → Database?
  ├─ API → Language? → Framework? → Auth? → Database?
  ├─ CLI Tool → Language? → Distribution method?
  └─ Data Pipeline → Language? → Data sources? → Schedule?
```

### Step 2: Create Interactive Module (2 days)

Build `src/interactive.py`:

```python
from typing import List, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel

class QuestionType(Enum):
    TEXT = "text"           # Free-form text
    CHOICE = "choice"       # Single selection
    MULTICHOICE = "multi"   # Multiple selections
    YESNO = "yesno"        # Boolean
    
class Question(BaseModel):
    id: str
    text: str
    type: QuestionType
    options: Optional[List[str]] = None
    help_text: Optional[str] = None
    validation: Optional[str] = None
    required: bool = True
    depends_on: Optional[Dict[str, Any]] = None  # Conditional logic
    
class InteractiveQuestionnaireManager:
    def __init__(self, questions_config: Dict):
        self.questions = self._load_questions(questions_config)
        self.answers: Dict[str, Any] = {}
        self.current_index = 0
        
    async def get_next_question(self) -> Optional[Question]:
        """Get next question based on previous answers."""
        # Logic to determine which question to ask next
        # based on conditional dependencies
        
    def answer_question(self, question_id: str, answer: Any) -> bool:
        """Save answer and validate."""
        
    def go_back(self) -> Optional[Question]:
        """Allow user to go back and change previous answer."""
        
    def save_session(self, path: Path) -> None:
        """Save current session state."""
        
    def load_session(self, path: Path) -> None:
        """Resume from saved session."""
        
    def to_project_inputs(self) -> Dict[str, Any]:
        """Convert answers to generate_design inputs."""
```

**Key Features**:
- Load questions from `config/questions.yaml`
- Validate answers based on question type
- Support conditional questions (only ask if previous answer matches)
- Save/resume sessions
- Provide helpful examples and context

### Step 3: Integrate with CLI (2 days)

Update `src/cli.py`:

```python
@app.command()
def interactive_design(
    config_path: Optional[Path] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    output_dir: Optional[Path] = None,
    verbose: bool = False,
    debug: bool = False,
) -> None:
    """Generate a project design through interactive questions."""
    from rich.prompt import Prompt, Confirm
    from rich.progress import Progress
    from src.interactive import InteractiveQuestionnaireManager
    
    typer.echo("🚀 Welcome to DevPlan Interactive Builder!")
    typer.echo("I'll ask you a few questions to help build your devplan.\n")
    
    # Load questionnaire
    questionnaire = InteractiveQuestionnaireManager(...)
    
    # Ask questions one by one
    with Progress() as progress:
        task = progress.add_task("Questions", total=questionnaire.total_questions)
        
        while question := await questionnaire.get_next_question():
            # Display question with context
            if question.type == QuestionType.TEXT:
                answer = Prompt.ask(question.text, default=question.default)
            elif question.type == QuestionType.CHOICE:
                # Use rich.prompt.Prompt with choices
                answer = Prompt.ask(question.text, choices=question.options)
            # ... etc
            
            questionnaire.answer_question(question.id, answer)
            progress.update(task, advance=1)
    
    # Convert to project design inputs
    inputs = questionnaire.to_project_inputs()
    
    # Generate design (reuse existing logic)
    orchestrator = _create_orchestrator(config)
    design = asyncio.run(orchestrator.run_design_only(**inputs))
    
    typer.echo(f"\n✅ Design generated! Saved to {output_path}")
```

**Also update**:
- Make `generate-design` check if no flags provided → launch interactive mode
- Add `--from-session PATH` flag to resume saved session
- Add `--save-session PATH` to save progress

### Step 4: Create Questions Config (1 day)

Create `config/questions.yaml`:

```yaml
questions:
  - id: project_name
    text: "What is your project name?"
    type: text
    help_text: "e.g., my-awesome-app, api-service, data-processor"
    required: true
    
  - id: project_type
    text: "What type of project are you building?"
    type: choice
    options:
      - "Web Application"
      - "REST API"
      - "CLI Tool"
      - "Data Pipeline"
      - "Library/Package"
      - "Other"
    required: true
    
  - id: primary_language
    text: "What is your primary programming language?"
    type: choice
    options:
      - Python
      - JavaScript
      - TypeScript
      - Go
      - Rust
      - Java
      - Other
    required: true
    
  - id: frontend_framework
    text: "Which frontend framework do you want to use?"
    type: choice
    options:
      - React
      - Vue
      - Svelte
      - Angular
      - None (backend only)
    depends_on:
      project_type: "Web Application"
    
  - id: backend_framework
    text: "Which backend framework?"
    type: choice
    options:
      - FastAPI
      - Django
      - Flask
      - Express.js
      - Other
    depends_on:
      project_type: ["Web Application", "REST API"]
      
  # ... more questions ...
```

### Step 5: Testing (1 day)

Create `tests/unit/test_interactive.py`:

```python
import pytest
from src.interactive import InteractiveQuestionnaireManager, Question, QuestionType

def test_question_flow():
    """Test that questions are asked in correct order."""
    
def test_conditional_questions():
    """Test that conditional questions only appear when appropriate."""
    
def test_session_save_resume():
    """Test saving and resuming sessions."""
    
def test_validation():
    """Test answer validation."""
    
def test_going_back():
    """Test editing previous answers."""
```

---

## 🌐 Phase 2: Web Interface (After Phase 1)

Once interactive CLI works, build FastAPI web interface:

### Key Files to Create:
- `src/api/app.py` - FastAPI application
- `src/api/routes.py` - API endpoints
- `src/api/models.py` - Request/response models
- `src/api/static/index.html` - Simple web UI
- `src/api/websocket.py` - Real-time streaming

### API Endpoints:
```
GET  /api/questions/start       - Start new session, get first question
POST /api/questions/{id}/answer - Submit answer, get next question  
GET  /api/session/{id}          - Get current session state
WS   /ws/generate               - WebSocket for real-time LLM streaming
```

**See `MVP_DEVPLAN.md` for detailed Phase 2 breakdown.**

---

## 🔧 Technical Notes

### Dependencies Already Available:
- `typer` - CLI framework ✅
- `rich` - Beautiful terminal output ✅
- `pydantic` - Data validation ✅
- `jinja2` - Templating ✅
- `asyncio` - Async support ✅

### Dependencies to Add:
```bash
pip install fastapi uvicorn websockets
```

### Configuration:
- All config in `config/config.yaml` and `.env`
- Use existing `Config` class in `src/config.py`
- Add new section for interactive features:
  ```yaml
  interactive:
    questions_config: config/questions.yaml
    session_dir: .devussy_sessions/
    default_timeout: 1800  # 30 minutes
  ```

### Testing Strategy:
- Mock user input using `unittest.mock.patch`
- Test questionnaire logic independently
- Integration tests for full interactive flow
- Use existing test fixtures from `tests/conftest.py`

---

## 📚 Key Files to Review

**Understand the Architecture**:
1. `docs/ARCHITECTURE.md` - System design overview
2. `src/cli.py` - Current CLI implementation (lines 1-1145)
3. `src/pipeline/compose.py` - Pipeline orchestrator
4. `src/models.py` - Data models (ProjectDesign, DevPlan, etc.)

**Understand the Pipeline**:
1. `src/pipeline/project_design.py` - How designs are generated
2. `templates/project_design.jinja` - Project design prompt template
3. `src/llm_client.py` - LLM client interface

**Configuration**:
1. `config/config.yaml` - Default configuration
2. `src/config.py` - Config loading and validation

---

## 🚀 Getting Started

### Environment Setup:
```powershell
cd C:\Users\kyle\projects\devussy-fresh
.\venv\Scripts\Activate.ps1

# Verify everything works
devussy.exe version  # Should show v0.1.0
pytest tests/ -v     # Should pass 227/242 tests

# Install additional dependencies
pip install fastapi uvicorn websockets pyyaml
```

### Development Workflow:
```bash
# 1. Create feature branch
git checkout -b feature/interactive-questionnaire

# 2. Make changes, test frequently
pytest tests/unit/test_interactive.py -v

# 3. Run full test suite
pytest tests/ --cov=src

# 4. Commit with conventional commits
git commit -m "feat: add interactive questionnaire manager"

# 5. Update documentation
# Edit MVP_DEVPLAN.md to mark tasks complete
```

---

## ✅ Success Criteria

You've completed the MVP when:

1. **Interactive CLI Works**:
   ```bash
   devussy interactive-design
   # Asks questions one by one
   # Saves session automatically
   # Generates design at the end
   ```

2. **Web Interface Works**:
   ```bash
   uvicorn src.api.app:app --reload
   # Opens browser to http://localhost:8000
   # Interactive questionnaire in browser
   # Real-time streaming of LLM responses
   ```

3. **Documentation Updated**:
   - `docs/INTERACTIVE_FLOW.md` exists
   - `docs/API.md` documents all endpoints
   - `README.md` shows interactive examples
   - Templates updated to reflect interactive approach

4. **Tests Pass**:
   - All new code has 80%+ coverage
   - Existing 227 tests still pass
   - New interactive tests added

---

## 🎯 Immediate Next Steps (Day 1)

1. **Read `MVP_DEVPLAN.md`** - Your detailed roadmap
2. **Create `docs/INTERACTIVE_FLOW.md`** - Design the question tree
3. **Start `src/interactive.py`** - Build the questionnaire manager
4. **Create `config/questions.yaml`** - Define the questions

**Good luck! You got this! 🚀**

---

## Questions? Context?

- **Why interactive?** Users don't know what inputs are needed, guidance improves quality
- **Why web interface?** Lowers barrier to entry, better UX for non-technical users
- **Why not just use a form?** Interactive = contextual, adaptive, smarter questions
- **What about PyPI?** Optional, not blocking MVP. Can publish later.

---

## 📞 Handoff Notes

- Package is built and installable (`pip install -e .`)
- CLI works perfectly (Typer 0.19.2, Python 3.13)
- No blockers, ready to build
- Project owner wants interactive experience as MVP priority
- PyPI publication can wait

**Previous agent completed**: Phase 10 packaging (11/11 tasks) ✅
**Your mission**: Build interactive MVP (Phases 1-6 in MVP_DEVPLAN.md)

**Time estimate**: 3-5 weeks for complete MVP
**Quick win target**: Interactive CLI working in 1 week

---

*Good luck building something amazing! 🎉*
