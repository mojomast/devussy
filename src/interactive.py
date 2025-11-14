"""Interactive questionnaire system for guided devplan building."""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from pydantic import BaseModel, Field
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, IntPrompt, Prompt

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
        """Determine if this question should be asked based on dependencies.

        Args:
            previous_answers: Dictionary of previously answered questions

        Returns:
            bool: True if question should be asked, False otherwise
        """
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
        """Initialize with questions configuration.

        Args:
            questions_config_path: Path to YAML file containing questions
        """
        self.questions = self._load_questions(questions_config_path)
        self.session = InteractiveSession(
            session_id=self._generate_session_id(),
            created_at=self._get_timestamp(),
            last_updated=self._get_timestamp(),
        )
        self.console = Console()

    def _load_questions(self, config_path: Path) -> List[Question]:
        """Load questions from YAML config.

        Args:
            config_path: Path to questions YAML file

        Returns:
            List[Question]: List of Question objects

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config is invalid
        """
        if not config_path.exists():
            raise FileNotFoundError(f"Questions config not found: {config_path}")

        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        if not config or "questions" not in config:
            raise ValueError("Invalid questions config: missing 'questions' key")

        return [Question(**q) for q in config["questions"]]

    def run(self) -> Dict[str, Any]:
        """Run the interactive questionnaire.

        Returns:
            Dict[str, Any]: Dictionary of all answers
        """
        self.console.print(
            Panel.fit(
                "[bold cyan]🚀 DevPlan Interactive Builder[/bold cyan]\n"
                "Let's build your development plan together!",
                border_style="cyan",
            )
        )

        # Count total questions to ask (considering dependencies)
        total_questions = len([q for q in self.questions if q.required])

        # Use a simple, non-blocking status update while prompting.
        # Rich's live spinner can interfere with terminal input in some shells,
        # so avoid using it while waiting for user input.
        self.console.print(f"[dim]Asking questions... ({total_questions} total)[/dim]\n")

        answered = 0
        for question in self.questions:
            if not question.should_ask(self.session.answers):
                continue

            # Show a lightweight progress indicator that won't steal input focus
            self.console.print(f"[bold]Question {answered + 1}/{total_questions}[/bold]")

            answer = self._ask_question(question)
            self.session.answers[question.id] = answer
            self.session.last_updated = self._get_timestamp()
            answered += 1

        self.console.print("\n[bold green]✨ All questions answered![/bold green]\n")
        return self.session.answers

    def _ask_question(self, question: Question) -> Any:
        """Ask a single question and get the answer.

        Args:
            question: Question object to ask

        Returns:
            Any: The answer provided by the user
        """
        # Display question with context
        self.console.print(f"\n[bold]{question.text}[/bold]")

        if question.help_text:
            self.console.print(f"[dim]{question.help_text}[/dim]")

        if question.examples:
            examples_str = ", ".join(question.examples[:3])
            self.console.print(f"[dim]Examples: {examples_str}[/dim]")

        # Get answer based on question type
        if question.type == QuestionType.TEXT:
            answer = Prompt.ask("Your answer", default=question.default or "")
            if not answer and question.required:
                self.console.print("[yellow]This question is required.[/yellow]")
                return self._ask_question(question)

        elif question.type == QuestionType.CHOICE:
            if question.options:
                self.console.print(f"[dim]Options: {' / '.join(question.options)}[/dim]")
            answer = Prompt.ask(
                "Choose one",
                choices=question.options if question.options else None,
                default=question.default,
            )

        elif question.type == QuestionType.MULTICHOICE:
            self.console.print("[dim]Enter comma-separated choices[/dim]")
            answer_str = Prompt.ask("Your choices")
            answer = [a.strip() for a in answer_str.split(",") if a.strip()]
            if not answer and question.required:
                self.console.print("[yellow]Please provide at least one choice.[/yellow]")
                return self._ask_question(question)

        elif question.type == QuestionType.YESNO:
            answer = Confirm.ask("Yes or no?", default=question.default if question.default is not None else True)

        elif question.type == QuestionType.NUMBER:
            answer = IntPrompt.ask("Enter a number", default=question.default or 0)

        else:
            # Fallback to text input
            answer = Prompt.ask("Your answer", default=question.default or "")

        return answer

    def to_generate_design_inputs(self) -> Dict[str, str]:
        """Convert session answers to generate_design command inputs.

        Returns:
            Dict[str, str]: Dictionary of inputs for generate_design
        """
        inputs = {}

        # Map project name
        if "project_name" in self.session.answers:
            inputs["name"] = self.session.answers["project_name"]

        # Map languages
        if "primary_language" in self.session.answers:
            langs = [self.session.answers["primary_language"]]
            
            # Add additional languages if provided
            if "additional_languages" in self.session.answers:
                additional = self.session.answers["additional_languages"]
                if isinstance(additional, str) and additional:
                    langs.extend([lang.strip() for lang in additional.split(",") if lang.strip()])
                elif isinstance(additional, list):
                    langs.extend(additional)
            
            inputs["languages"] = ",".join(langs)

        # Map requirements
        if "requirements" in self.session.answers:
            inputs["requirements"] = self.session.answers["requirements"]

        # Collect frameworks
        frameworks = []
        if "frontend_framework" in self.session.answers:
            fw = self.session.answers["frontend_framework"]
            if fw and fw != "None (backend only)":
                frameworks.append(fw)
        
        if "backend_framework" in self.session.answers:
            fw = self.session.answers["backend_framework"]
            if fw:
                frameworks.append(fw)
        
        if frameworks:
            inputs["frameworks"] = ",".join(frameworks)

        # Map database
        if "database" in self.session.answers:
            db = self.session.answers["database"]
            if db and db != "None":
                if "frameworks" in inputs:
                    inputs["frameworks"] += f",{db}"
                else:
                    inputs["frameworks"] = db

        # Map external APIs
        if "external_apis" in self.session.answers:
            apis = self.session.answers["external_apis"]
            if isinstance(apis, str) and apis:
                inputs["apis"] = apis
            elif isinstance(apis, list):
                inputs["apis"] = ",".join(apis)

        # Add deployment platform to requirements if specified
        if "deployment_platform" in self.session.answers:
            platform = self.session.answers["deployment_platform"]
            if platform and platform != "Not sure yet":
                if "requirements" in inputs:
                    inputs["requirements"] += f" Deploy to {platform}."
                else:
                    inputs["requirements"] = f"Deploy to {platform}."

        # Add testing requirements to requirements
        if "testing_requirements" in self.session.answers:
            testing = self.session.answers["testing_requirements"]
            if testing:
                if "requirements" in inputs:
                    inputs["requirements"] += f" Testing: {testing}."
                else:
                    inputs["requirements"] = f"Testing: {testing}."

        # Add CI/CD if requested
        if self.session.answers.get("ci_cd"):
            if "requirements" in inputs:
                inputs["requirements"] += " Include CI/CD pipeline setup."
            else:
                inputs["requirements"] = "Include CI/CD pipeline setup."

        # Add authentication if requested
        if self.session.answers.get("authentication"):
            if "requirements" in inputs:
                inputs["requirements"] += " Include user authentication."
            else:
                inputs["requirements"] = "Include user authentication."

        return inputs

    def save_session(self, path: Path) -> None:
        """Save current session to file.

        Args:
            path: Path to save session JSON file
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.session.model_dump(), f, indent=2)
        self.console.print(f"[dim]Session saved to {path}[/dim]")

    def load_session(self, path: Path) -> None:
        """Load session from file.

        Args:
            path: Path to session JSON file

        Raises:
            FileNotFoundError: If session file doesn't exist
        """
        if not path.exists():
            raise FileNotFoundError(f"Session file not found: {path}")

        with open(path, "r") as f:
            data = json.load(f)
        self.session = InteractiveSession(**data)
        self.console.print(f"[green]Session loaded from {path}[/green]")

    @staticmethod
    def _generate_session_id() -> str:
        """Generate unique session ID.

        Returns:
            str: Unique session identifier
        """
        return str(uuid.uuid4())[:8]

    @staticmethod
    def _get_timestamp() -> str:
        """Get current timestamp.

        Returns:
            str: ISO format timestamp
        """
        return datetime.now().isoformat()
