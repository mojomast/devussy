# 🚀 PROMPT FOR NEXT AGENT - Interactive DevPlan Builder MVP

## Context Window Optimization - Read This First! 📋

You are taking over **DevPlan Orchestrator**, a Python tool that generates development plans using LLMs. The project owner wants to transform it into an **interactive DevPlan builder** with guided questionnaires in both CLI and web interfaces.

---

## 📍 Your Starting Point

**Repository**: `c:\Users\kyle\projects\devussy-fresh`
**Branch**: `master`
**Python**: 3.13.7
**Venv**: `.\venv\Scripts\Activate.ps1`
**Current Status**: Phase 10 complete (packaging done), ready for MVP development

### Quick Verification:
```powershell
cd C:\Users\kyle\projects\devussy-fresh
.\venv\Scripts\Activate.ps1
python -m devussy version  # Should show v0.1.0
pytest tests/ -k "test_config" -v  # Should pass
```

---

## 🎯 Your Mission: Build Interactive MVP

**Goal**: Transform from "flags-based CLI" → "guided interactive experience"

**Current (Non-Interactive)**:
```bash
devussy generate-design \
  --name "Project" \
  --languages "Python" \
  --requirements "Build an API" \
  --frameworks "FastAPI"
```

**Target (Interactive)**:
```bash
devussy interactive-design
> What is your project name? Project
> What are you building? [Web App / API / CLI Tool / ...] API
> Primary language? [Python / JavaScript / ...] Python  
> Framework? [FastAPI / Django / Flask / ...] FastAPI
> Database? [PostgreSQL / MongoDB / None] PostgreSQL
✨ Generating your design...
```

---

## 📁 Essential Files to Read (In Order)

1. **`MVP_DEVPLAN.md`** ⭐ - Your complete roadmap (6 phases, 16-24 days)
2. **`MVP_HANDOFF.md`** ⭐ - Mission brief with technical details
3. **`docs/ARCHITECTURE.md`** - System design
4. **`src/cli.py`** (lines 1-250) - Current CLI implementation
5. **`src/models.py`** - Data models (ProjectDesign, DevPlan, HandoffPrompt)

---

## 🏗️ Phase 1: Interactive CLI (Start Here!)

### Week 1 Goal: Working Interactive CLI

**Step 1 (Day 1-2): Design Question Flow**
- Create `docs/INTERACTIVE_FLOW.md`
- Map question tree: Project Type → Languages → Frameworks → etc.
- Define essential vs optional questions
- Document conditional logic

**Step 2 (Day 2-3): Build Interactive Module**
- Create `src/interactive.py`
- Implement `InteractiveQuestionnaireManager` class
- Support question types: text, choice, multi-choice, yes/no
- Load questions from `config/questions.yaml`

**Step 3 (Day 4-5): Integrate with CLI**
- Add `devussy interactive-design` command in `src/cli.py`
- Use `rich` library for beautiful prompts (already installed!)
- Implement session save/resume
- Update `generate-design` to default to interactive if no flags

**Step 4 (Day 5): Create Questions Config**
- Create `config/questions.yaml` with all questions
- Implement conditional question logic
- Add helpful examples and context

**Step 5 (Day 6-7): Testing**
- Create `tests/unit/test_interactive.py`
- Test question flow, validation, session save/resume
- Ensure existing tests still pass

---

## 🔨 Implementation Starter Template

### `src/interactive.py` (Start Here):

```python
"""Interactive questionnaire system for guided devplan building."""

from typing import List, Dict, Any, Optional, Union
from enum import Enum
from pathlib import Path
import json
import yaml
from pydantic import BaseModel, Field
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

class QuestionType(str, Enum):
    """Types of questions that can be asked."""
    TEXT = "text"
    CHOICE = "choice"
    MULTICHOICE = "multichoice"
    YESNO = "yesno"
    NUMBER = "number"

class Question(BaseModel):
    """Represents a single question in the questionnaire."""
    id: str
    text: str
    type: QuestionType
    options: Optional[List[str]] = None
    default: Optional[Union[str, int, bool]] = None
    help_text: Optional[str] = None
    examples: Optional[List[str]] = None
    required: bool = True
    depends_on: Optional[Dict[str, Any]] = None
    validation_pattern: Optional[str] = None
    
    def should_ask(self, previous_answers: Dict[str, Any]) -> bool:
        """Determine if this question should be asked based on dependencies."""
        if not self.depends_on:
            return True
            
        for key, expected_value in self.depends_on.items():
            if key not in previous_answers:
                return False
            
            actual_value = previous_answers[key]
            
            # Handle list of acceptable values
            if isinstance(expected_value, list):
                if actual_value not in expected_value:
                    return False
            # Handle single value
            elif actual_value != expected_value:
                return False
                
        return True

class InteractiveSession(BaseModel):
    """Represents a saved interactive session."""
    session_id: str
    answers: Dict[str, Any] = Field(default_factory=dict)
    current_question_index: int = 0
    created_at: str
    last_updated: str

class InteractiveQuestionnaireManager:
    """Manages interactive questionnaire flow."""
    
    def __init__(self, questions_config_path: Path):
        """Initialize with questions configuration."""
        self.questions = self._load_questions(questions_config_path)
        self.session = InteractiveSession(
            session_id=self._generate_session_id(),
            created_at=self._get_timestamp(),
            last_updated=self._get_timestamp()
        )
        self.console = Console()
        
    def _load_questions(self, config_path: Path) -> List[Question]:
        """Load questions from YAML config."""
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        return [Question(**q) for q in config['questions']]
    
    def run(self) -> Dict[str, Any]:
        """Run the interactive questionnaire."""
        self.console.print(Panel.fit(
            "[bold cyan]🚀 DevPlan Interactive Builder[/bold cyan]\n"
            "Let's build your development plan together!",
            border_style="cyan"
        ))
        
        total_questions = len([q for q in self.questions if q.required])
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("Asking questions...", total=total_questions)
            
            for question in self.questions:
                if not question.should_ask(self.session.answers):
                    continue
                    
                answer = self._ask_question(question)
                self.session.answers[question.id] = answer
                progress.update(task, advance=1)
        
        self.console.print("\n[bold green]✨ All questions answered![/bold green]\n")
        return self.session.answers
    
    def _ask_question(self, question: Question) -> Any:
        """Ask a single question and get the answer."""
        # Display question with context
        self.console.print(f"\n[bold]{question.text}[/bold]")
        
        if question.help_text:
            self.console.print(f"[dim]{question.help_text}[/dim]")
        
        if question.examples:
            examples_str = ", ".join(question.examples[:3])
            self.console.print(f"[dim]Examples: {examples_str}[/dim]")
        
        # Get answer based on question type
        if question.type == QuestionType.TEXT:
            answer = Prompt.ask("Your answer", default=question.default)
            
        elif question.type == QuestionType.CHOICE:
            choices_str = " / ".join(question.options)
            answer = Prompt.ask(
                "Choose one",
                choices=question.options,
                default=question.default
            )
            
        elif question.type == QuestionType.MULTICHOICE:
            self.console.print("[dim]Enter comma-separated choices[/dim]")
            answer_str = Prompt.ask("Your choices")
            answer = [a.strip() for a in answer_str.split(",")]
            
        elif question.type == QuestionType.YESNO:
            answer = Confirm.ask("Yes or no?", default=question.default)
            
        elif question.type == QuestionType.NUMBER:
            answer = IntPrompt.ask("Enter a number", default=question.default)
        
        return answer
    
    def to_generate_design_inputs(self) -> Dict[str, str]:
        """Convert session answers to generate_design command inputs."""
        # Map questionnaire answers to CLI flag format
        inputs = {}
        
        if 'project_name' in self.session.answers:
            inputs['name'] = self.session.answers['project_name']
        
        if 'primary_language' in self.session.answers:
            # Handle multiple languages
            langs = self.session.answers['primary_language']
            if isinstance(langs, list):
                inputs['languages'] = ",".join(langs)
            else:
                inputs['languages'] = langs
        
        if 'requirements' in self.session.answers:
            inputs['requirements'] = self.session.answers['requirements']
        
        # Add frameworks
        frameworks = []
        if 'frontend_framework' in self.session.answers:
            frameworks.append(self.session.answers['frontend_framework'])
        if 'backend_framework' in self.session.answers:
            frameworks.append(self.session.answers['backend_framework'])
        if frameworks:
            inputs['frameworks'] = ",".join(frameworks)
        
        # Add APIs if specified
        if 'external_apis' in self.session.answers:
            inputs['apis'] = self.session.answers['external_apis']
        
        return inputs
    
    def save_session(self, path: Path) -> None:
        """Save current session to file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(self.session.dict(), f, indent=2)
        self.console.print(f"[dim]Session saved to {path}[/dim]")
    
    def load_session(self, path: Path) -> None:
        """Load session from file."""
        with open(path, 'r') as f:
            data = json.load(f)
        self.session = InteractiveSession(**data)
        self.console.print(f"[green]Session loaded from {path}[/green]")
    
    @staticmethod
    def _generate_session_id() -> str:
        """Generate unique session ID."""
        import uuid
        return str(uuid.uuid4())[:8]
    
    @staticmethod
    def _get_timestamp() -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()
```

### `config/questions.yaml` (Start Here):

```yaml
questions:
  - id: project_name
    text: "What is your project name?"
    type: text
    help_text: "Choose a short, descriptive name for your project"
    examples:
      - "my-awesome-app"
      - "ecommerce-api"
      - "data-pipeline"
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
      - "Mobile App"
      - "Desktop App"
      - "Other"
    help_text: "This helps us ask the right follow-up questions"
    required: true
    
  - id: primary_language
    text: "What is your primary programming language?"
    type: choice
    options:
      - "Python"
      - "JavaScript"
      - "TypeScript"
      - "Go"
      - "Rust"
      - "Java"
      - "C#"
      - "Ruby"
      - "PHP"
      - "Other"
    required: true
    
  - id: additional_languages
    text: "Any additional languages? (comma-separated, or press Enter to skip)"
    type: text
    required: false
    
  - id: requirements
    text: "Describe what you want to build in 1-2 sentences"
    type: text
    help_text: "Be specific about key features and goals"
    examples:
      - "Build a REST API for managing user accounts with JWT authentication"
      - "Create a CLI tool for processing CSV files and generating reports"
    required: true
    
  - id: frontend_framework
    text: "Which frontend framework?"
    type: choice
    options:
      - "React"
      - "Vue"
      - "Svelte"
      - "Angular"
      - "Vanilla JS"
      - "None (backend only)"
    depends_on:
      project_type: "Web Application"
    
  - id: backend_framework
    text: "Which backend framework?"
    type: choice
    options:
      - "FastAPI"
      - "Django"
      - "Flask"
      - "Express.js"
      - "NestJS"
      - "Spring Boot"
      - "Rails"
      - "Other"
    depends_on:
      project_type: ["Web Application", "REST API"]
    
  - id: database
    text: "What database will you use?"
    type: choice
    options:
      - "PostgreSQL"
      - "MySQL"
      - "MongoDB"
      - "Redis"
      - "SQLite"
      - "None"
    depends_on:
      project_type: ["Web Application", "REST API", "Data Pipeline"]
    
  - id: authentication
    text: "Do you need authentication?"
    type: yesno
    default: true
    depends_on:
      project_type: ["Web Application", "REST API"]
    
  - id: external_apis
    text: "Any external APIs to integrate? (comma-separated, or press Enter to skip)"
    type: text
    help_text: "e.g., Stripe, SendGrid, Twilio, OpenAI"
    required: false
    
  - id: deployment_platform
    text: "Where will you deploy?"
    type: choice
    options:
      - "AWS"
      - "Google Cloud"
      - "Azure"
      - "Heroku"
      - "Vercel"
      - "Railway"
      - "DigitalOcean"
      - "Self-hosted"
      - "Not sure yet"
    required: false
    
  - id: testing_requirements
    text: "What level of testing do you need?"
    type: choice
    options:
      - "Comprehensive (unit + integration + e2e)"
      - "Standard (unit + integration)"
      - "Basic (unit tests only)"
      - "Minimal"
    default: "Standard (unit + integration)"
    
  - id: ci_cd
    text: "Do you want CI/CD pipeline setup?"
    type: yesno
    default: true
    help_text: "Automated testing and deployment"
```

### Add to `src/cli.py` (New Command):

```python
@app.command()
def interactive_design(
    config_path: Annotated[
        Optional[Path], typer.Option("--config", "-c", help="Path to config file")
    ] = None,
    output_dir: Annotated[
        Optional[Path], typer.Option("--output-dir", "-o", help="Output directory")
    ] = None,
    save_session: Annotated[
        Optional[Path], typer.Option("--save-session", help="Save session to file")
    ] = None,
    resume_session: Annotated[
        Optional[Path], typer.Option("--resume-session", help="Resume from saved session")
    ] = None,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Enable verbose logging")
    ] = False,
    debug: Annotated[
        bool, typer.Option("--debug", help="Enable debug mode")
    ] = False,
) -> None:
    """Generate a project design through interactive questions."""
    try:
        from src.interactive import InteractiveQuestionnaireManager
        
        # Load config
        config = _load_app_config(config_path, None, None, output_dir, verbose)
        
        # Setup interactive questionnaire
        questions_path = Path("config/questions.yaml")
        questionnaire = InteractiveQuestionnaireManager(questions_path)
        
        # Resume session if requested
        if resume_session and resume_session.exists():
            questionnaire.load_session(resume_session)
            typer.echo(f"📂 Resumed session from {resume_session}\n")
        
        # Run interactive questionnaire
        answers = questionnaire.run()
        
        # Save session if requested
        if save_session:
            questionnaire.save_session(save_session)
        
        # Convert to generate_design inputs
        inputs = questionnaire.to_generate_design_inputs()
        
        # Generate design using existing pipeline
        typer.echo("\n" + "=" * 60)
        typer.echo("🎨 Generating your project design...")
        typer.echo("=" * 60 + "\n")
        
        orchestrator = _create_orchestrator(config)
        
        async def _run():
            return await orchestrator.run_design_only(
                project_name=inputs['name'],
                languages_list=inputs['languages'].split(','),
                requirements=inputs['requirements'],
                frameworks_list=inputs.get('frameworks', '').split(',') if inputs.get('frameworks') else None,
                apis_list=inputs.get('apis', '').split(',') if inputs.get('apis') else None,
            )
        
        design = asyncio.run(_run())
        
        # Save design
        output_path = config.output_dir / "project_design.json"
        with open(output_path, 'w') as f:
            json.dump(design.dict(), f, indent=2)
        
        typer.echo(f"\n✅ Project design generated!")
        typer.echo(f"📄 Saved to: {output_path}")
        typer.echo(f"\n💡 Next: Run 'devussy generate-devplan {output_path}'")
        
    except Exception as e:
        logger.error(f"Error in interactive design: {e}", exc_info=True)
        if debug:
            raise
        typer.echo(f"❌ Error: {e}", err=True)
        raise typer.Exit(code=1)
```

---

## 🧪 Testing Template

### `tests/unit/test_interactive.py`:

```python
"""Tests for interactive questionnaire system."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from src.interactive import (
    InteractiveQuestionnaireManager,
    Question,
    QuestionType,
    InteractiveSession
)

@pytest.fixture
def sample_questions_config(tmp_path):
    """Create a sample questions config file."""
    config = {
        'questions': [
            {
                'id': 'project_name',
                'text': 'What is your project name?',
                'type': 'text',
                'required': True
            },
            {
                'id': 'project_type',
                'text': 'What type of project?',
                'type': 'choice',
                'options': ['Web App', 'API', 'CLI'],
                'required': True
            }
        ]
    }
    
    config_path = tmp_path / "test_questions.yaml"
    import yaml
    with open(config_path, 'w') as f:
        yaml.dump(config, f)
    
    return config_path

def test_load_questions(sample_questions_config):
    """Test loading questions from config."""
    manager = InteractiveQuestionnaireManager(sample_questions_config)
    
    assert len(manager.questions) == 2
    assert manager.questions[0].id == 'project_name'
    assert manager.questions[0].type == QuestionType.TEXT

def test_conditional_questions():
    """Test that conditional questions only appear when appropriate."""
    q1 = Question(
        id='project_type',
        text='Project type?',
        type=QuestionType.CHOICE,
        options=['Web App', 'API']
    )
    
    q2 = Question(
        id='frontend',
        text='Frontend?',
        type=QuestionType.CHOICE,
        options=['React', 'Vue'],
        depends_on={'project_type': 'Web App'}
    )
    
    # Should ask when project_type is Web App
    assert q2.should_ask({'project_type': 'Web App'}) == True
    
    # Should not ask when project_type is API
    assert q2.should_ask({'project_type': 'API'}) == False

def test_session_save_load(sample_questions_config, tmp_path):
    """Test saving and loading sessions."""
    manager = InteractiveQuestionnaireManager(sample_questions_config)
    
    # Add some answers
    manager.session.answers = {
        'project_name': 'Test Project',
        'project_type': 'Web App'
    }
    
    # Save session
    session_path = tmp_path / "test_session.json"
    manager.save_session(session_path)
    
    # Load in new manager
    manager2 = InteractiveQuestionnaireManager(sample_questions_config)
    manager2.load_session(session_path)
    
    assert manager2.session.answers == manager.session.answers

def test_to_generate_design_inputs(sample_questions_config):
    """Test converting answers to generate_design inputs."""
    manager = InteractiveQuestionnaireManager(sample_questions_config)
    
    manager.session.answers = {
        'project_name': 'My App',
        'primary_language': 'Python',
        'requirements': 'Build an API',
        'backend_framework': 'FastAPI'
    }
    
    inputs = manager.to_generate_design_inputs()
    
    assert inputs['name'] == 'My App'
    assert inputs['languages'] == 'Python'
    assert inputs['requirements'] == 'Build an API'
    assert 'FastAPI' in inputs.get('frameworks', '')
```

---

## ⚡ Quick Commands Reference

```powershell
# Activate environment
cd C:\Users\kyle\projects\devussy-fresh
.\venv\Scripts\Activate.ps1

# Run tests
pytest tests/unit/test_interactive.py -v
pytest tests/ -v  # All tests
pytest --cov=src --cov-report=html  # With coverage

# Run the interactive CLI
python -m src.cli interactive-design --verbose

# Format code
black src/interactive.py
isort src/interactive.py

# Check code quality
flake8 src/interactive.py

# Git workflow
git checkout -b feature/interactive-questionnaire
git add src/interactive.py config/questions.yaml tests/unit/test_interactive.py
git commit -m "feat: add interactive questionnaire system"
```

---

## 📊 Success Checklist

Week 1 Goal - Interactive CLI:
- [ ] `docs/INTERACTIVE_FLOW.md` created with question tree
- [ ] `config/questions.yaml` created with 10-15 questions
- [ ] `src/interactive.py` implemented with all classes
- [ ] `devussy interactive-design` command works
- [ ] Session save/resume working
- [ ] Tests in `tests/unit/test_interactive.py` pass
- [ ] Can generate a design from interactive answers
- [ ] Documentation updated

---

## 🎯 After Week 1: Phase 2 - Web Interface

Once interactive CLI works, start Phase 2:
- Install: `pip install fastapi uvicorn websockets`
- Create `src/api/app.py` with FastAPI
- Build REST API endpoints
- Add WebSocket for real-time streaming
- Create simple HTML/JS web UI

**See `MVP_DEVPLAN.md` Phase 2 for details.**

---

## 📚 Resources

- **Rich documentation**: https://rich.readthedocs.io/
- **FastAPI docs**: https://fastapi.tiangolo.com/
- **Typer docs**: https://typer.tiangolo.com/
- **Pydantic**: https://docs.pydantic.dev/

---

## 🆘 If You Get Stuck

1. **Check existing code**: Look at `src/cli.py` for patterns
2. **Run tests frequently**: `pytest tests/unit/test_interactive.py -v`
3. **Use debugger**: `import pdb; pdb.set_trace()`
4. **Read `MVP_DEVPLAN.md`**: Detailed breakdown of all phases
5. **Check `docs/ARCHITECTURE.md`**: Understand the system design

---

## ✨ Final Notes

- **Start small**: Get basic questionnaire working first, then add features
- **Test frequently**: Write tests as you go
- **Commit often**: Small, focused commits with good messages
- **Keep backward compatibility**: Don't break existing CLI commands
- **User experience matters**: Make the interactive flow smooth and helpful

**You got this! Build something awesome! 🚀**

---

**Estimated Time**: 1 week for interactive CLI, 2-3 weeks for web interface
**Priority**: Interactive CLI first, then web interface
**Blocker**: None - ready to start!

Good luck! 🎉
