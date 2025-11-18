"""Command-line interface for DevPlan Orchestrator."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import traceback
from pathlib import Path
from typing import Any, Annotated, Optional

import typer
from dotenv import load_dotenv
from typing_extensions import Annotated

from .__version__ import __version__
from .clients.factory import create_llm_client
from .concurrency import ConcurrencyManager
from .config import AppConfig, load_config
from .feedback_manager import FeedbackManager
from .file_manager import FileManager
from .logger import get_logger, setup_logging
from .ui_tokens import render
from .markdown_output_manager import MarkdownOutputManager
from .models import DevPlan, ProjectDesign
from .interview import RepoAnalysis, RepositoryAnalyzer
from .pipeline.compose import PipelineOrchestrator
from .progress_reporter import PipelineProgressReporter
from .state_manager import StateManager
from .ui.menu import run_main_menu, run_menu, SessionSettings, apply_settings_to_config, load_last_used_preferences
from .terminal.terminal_ui import run_terminal_ui
from .terminal.phase_generator import TerminalPhaseGenerator
from .streaming import StreamingHandler

from rich.console import Console
from rich.panel import Panel
from rich.box import ROUNDED
from rich.text import Text
from rich.console import Group
from rich.align import Align

app = typer.Typer(
    name="devussy",
    help="LLM-based development plan orchestration tool",
    add_completion=False,
)

logger = get_logger(__name__)


console = Console()


def _apply_last_prefs_to_config(config: AppConfig) -> None:
    """Apply last-used UI/session preferences to the given config.

    Ensures persisted provider selection, per-provider API keys, and base URLs
    are applied before creating clients or running any steps.
    """
    try:
        prefs = load_last_used_preferences()
        apply_settings_to_config(config, prefs)
    except Exception as e:
        # Log the exception so we can debug preference loading issues
        logger.debug(f"Failed to load UI preferences: {e}", exc_info=True)
        pass


def _find_project_root(start: Path) -> Path:
    """Find project root by looking for markers like pyproject.toml or .git.

    Falls back to provided start directory.
    """
    markers = {"pyproject.toml", ".git", "requirements.txt"}
    cur = start
    for _ in range(6):
        if any((cur / m).exists() for m in markers):
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    return start


def _load_logo_text() -> str:
    """Load ASCII logo from DEVUSSYLOGO.MD near project root.

    Returns a best-effort string; falls back to a simple title when not found.
    """
    try:
        here = Path(__file__).resolve()
        root = _find_project_root(here.parent)
        logo_path = root / "DEVUSSYLOGO.MD"
        if logo_path.exists():
            return logo_path.read_text(encoding="utf-8").rstrip("\n")
    except Exception:
        pass
    return "DEVUSSY"


def _render_splash() -> None:
    """Render the startup splash with logo, version, and credits."""
    if not sys.stdout.isatty():  # keep tests and non-TTY clean
        return

    logo = _load_logo_text()
    title = Text("DevPlan Orchestrator", style="bold cyan", justify="center")
    version_line = Text(f"v{__version__}", style="magenta", justify="center")
    credit = Text(
        "Created by Kyle Durepos (with contributions by Dazlarus)", style="bold yellow", justify="center"
    )
    accent = Text("compose. code. conduct.", style="dim", justify="center")
    logo_text = Text(logo, justify="center")

    body = Group(
        logo_text,
        Text("\n"),
        title,
        version_line,
        credit,
        accent,
    )

    panel = Panel(
        Align.center(body),
        box=ROUNDED,
        border_style="cyan",
        padding=(1, 2),
        title="[LOGO] DEVUSSY",
        expand=True,
    )
    console.print(panel)


@app.callback()
def _global_callback(
    ctx: typer.Context,
    no_splash: Annotated[
        bool,
        typer.Option(
            "--no-splash",
            help="Disable startup splash screen",
            show_default=False,
        ),
    ] = False,
) -> None:
    """Global callback to render splash prior to any command."""
    try:
        env_off = os.getenv("DEVUSSY_NO_SPLASH", "").strip().lower() in {"1", "true", "yes"}
        if env_off or no_splash:
            return
        _render_splash()
    except Exception:
        # Never fail CLI due to splash issues
        pass
def _resolve_requesty_api_key(config: AppConfig) -> str:
    """Resolve a Requesty API key, prompting the user if necessary."""

    existing_key = getattr(config.llm, "api_key", None) or os.getenv("REQUESTY_API_KEY")
    if existing_key:
        return existing_key

    typer.echo(render("\n[WARN] Requesty API key not found in config or environment."))
    if not typer.confirm("Would you like to enter a Requesty API key now?", default=True):
        typer.echo(
            render("[ERROR] Requesty model selection requires an API key. Aborting."),
            err=True,
            color=True,
        )
        raise typer.Exit(code=1)

    api_key = typer.prompt("Enter your Requesty API key", hide_input=True)
    config.llm.api_key = api_key

    for stage_config in (config.design_llm, config.devplan_llm, config.handoff_llm):
        if stage_config and not getattr(stage_config, "api_key", None):
            stage_config.api_key = api_key

    return api_key


async def _fetch_requesty_models(api_key: str, base_url: str) -> list[dict]:
    """Fetch the available models from the Requesty API."""

    import aiohttp  # Lazy import so dependency is optional unless needed

    endpoint = f"{base_url.rstrip('/')}/models"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(endpoint, headers=headers) as resp:
            if resp.status >= 400:
                error_text = await resp.text()
                raise RuntimeError(
                    f"Requesty API error {resp.status}: {error_text.strip() or 'unknown error'}"
                )

            data = await resp.json()

    models = data.get("data", data.get("models", []))
    sanitized = []
    for raw in models:
        model_id = raw.get("id") or raw.get("name")
        if not model_id:
            continue

        sanitized.append(
            {
                "id": model_id,
                "name": raw.get("name", model_id),
                "description": raw.get("description", ""),
                "context_window": raw.get("context_window", raw.get("max_tokens")),
            }
        )

    return sanitized


def _select_requesty_model_interactively(config: AppConfig) -> str:
    """Interactively pull and select a Requesty model, updating config in-place."""

    provider = getattr(config.llm, "provider", "openai").lower()
    if provider != "requesty":
        typer.echo(
            render(f"\n[INFO] Active provider is '{provider}'. Switching to Requesty for this run.")
        )
        config.llm.provider = "requesty"

    base_url = (
        getattr(config.llm, "base_url", None)
        or os.getenv("REQUESTY_BASE_URL")
        or "https://router.requesty.ai/v1"
    )

    api_key = _resolve_requesty_api_key(config)

    typer.echo(render("\n[WAIT] Fetching available Requesty models...\n"))
    try:
        models = asyncio.run(_fetch_requesty_models(api_key, base_url))
    except Exception as exc:  # noqa: BLE001
        typer.echo(f"[ERROR] Failed to retrieve Requesty models: {exc}", err=True, color=True)
        raise typer.Exit(code=1)

    if not models:
        typer.echo(
            "[ERROR] Requesty returned no models. Please verify your credentials.",
            err=True,
            color=True,
        )
        raise typer.Exit(code=1)

    for index, model in enumerate(models, start=1):
        ctx = model.get("context_window")
        ctx_label = f" (ctx: {ctx})" if ctx else ""
        typer.echo(f"{index}. {model['id']}{ctx_label}")
        if model.get("description"):
            typer.echo(f"   {model['description']}")

    total = len(models)
    while True:
        choice_str = typer.prompt(
            f"\nSelect a model by number (1-{total})",
            default="1",
        )
        try:
            choice = int(choice_str)
        except ValueError:
            typer.echo("Please enter a valid number.", err=True, color=True)
            continue

        if 1 <= choice <= total:
            break

        typer.echo(f"Enter a number between 1 and {total}.", err=True, color=True)

    selected = models[choice - 1]["id"]
    config.llm.model = selected
    config.llm.api_key = api_key
    if not getattr(config.llm, "base_url", None):
        config.llm.base_url = base_url

    for stage_config in (config.design_llm, config.devplan_llm, config.handoff_llm):
        if not stage_config:
            continue
        stage_provider = getattr(stage_config, "provider", config.llm.provider)
        if stage_provider and stage_provider.lower() == "requesty":
            stage_config.model = selected
            if not getattr(stage_config, "api_key", None):
                stage_config.api_key = api_key

    typer.echo(render(f"\n[OK] Selected Requesty model: {selected}\n"))
    return selected


def _load_app_config(
    config_path: Optional[str],
    provider: Optional[str],
    model: Optional[str],
    output_dir: Optional[str],
    verbose: bool,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    load_ui_preferences: bool = True,
) -> AppConfig:
    """Load configuration with CLI overrides.

    Args:
        config_path: Path to config file
        provider: LLM provider override
        model: Model override
        output_dir: Output directory override
        verbose: Enable verbose logging
        load_ui_preferences: Whether to load UI preferences (default: True)

    Returns:
        AppConfig: Configured application config
    """
    # Load base config
    try:
        config = load_config(config_path)
    except FileNotFoundError:
        typer.echo(
            render("[WARN] Config file not found, using defaults"),
            err=True,
            color=True,
        )
        config = AppConfig()
    except ValueError as exc:
        # Config may be invalid due to environment overrides (e.g., bad provider);
        # fall back to a default AppConfig so lightweight CLI commands can still run.
        typer.echo(
            render(f"[WARN] Invalid config detected, using defaults ({exc})"),
            err=True,
            color=True,
        )
        config = AppConfig()

    # Apply CLI overrides
    if provider:
        config.llm.provider = provider
    if model:
        config.llm.model = model
    if output_dir:
        config.output_dir = Path(output_dir)
    if temperature is not None:
        config.llm.temperature = temperature
    if max_tokens is not None:
        config.llm.max_tokens = max_tokens
    if verbose:
        config.log_level = "DEBUG"

    # Apply UI preferences to config during startup (if not CLI-only commands)
    if load_ui_preferences:
        try:
            _apply_last_prefs_to_config(config)
        except Exception as e:
            # Never break startup due to preference loading issues
            logger.debug(f"Failed to load UI preferences: {e}")
            pass

    # Setup logging
    setup_logging(config.log_level, str(config.log_file), config.log_format)

    return config


def _create_orchestrator(
    config: AppConfig,
    repo_analysis: Optional[Any] = None,
    code_samples: Optional[str] = None,
    markdown_output_manager: Optional[MarkdownOutputManager] = None,
) -> PipelineOrchestrator:
    """Create a pipeline orchestrator from config.

    Args:
        config: Application configuration
        repo_analysis: Optional repository analysis for context
        code_samples: Optional formatted code samples string
        markdown_output_manager: Optional markdown output manager for saving outputs

    Returns:
        PipelineOrchestrator: Initialized orchestrator
    """
    # Before creating clients, apply last-used preferences as a final safeguard
    _apply_last_prefs_to_config(config)

    # Create LLM client
    llm_client = create_llm_client(config)

    # Create concurrency manager (controls how many phases/API calls run in parallel)
    concurrency_manager = ConcurrencyManager(max_concurrent=config.max_concurrent_requests)

    # Create file manager
    file_manager = FileManager()

    # Create state manager
    state_manager = StateManager()
    
    # Create progress reporter
    progress_reporter = PipelineProgressReporter(console=console)

    # Create orchestrator
    orchestrator = PipelineOrchestrator(
        llm_client=llm_client,
        concurrency_manager=concurrency_manager,
        file_manager=file_manager,
        git_config=config.git,
        config=config,
        state_manager=state_manager,
        progress_reporter=progress_reporter,
        repo_analysis=repo_analysis,
        code_samples=code_samples,
        markdown_output_manager=markdown_output_manager,
    )

    return orchestrator


@app.command()
def generate_design(
    project_name: Annotated[str, typer.Option("--name", help="Project name")],
    languages: Annotated[
        str,
        typer.Option("--languages", help="Comma-separated programming languages"),
    ],
    requirements: Annotated[
        str, typer.Option("--requirements", help="Project requirements")
    ],
    frameworks: Annotated[
        Optional[str],
        typer.Option("--frameworks", help="Comma-separated frameworks"),
    ] = None,
    apis: Annotated[
        Optional[str], typer.Option("--apis", help="Comma-separated APIs")
    ] = None,
    config_path: Annotated[
        Optional[str], typer.Option("--config", help="Path to config file")
    ] = None,
    provider: Annotated[
        Optional[str], typer.Option("--provider", help="LLM provider override")
    ] = None,
    model: Annotated[
        Optional[str], typer.Option("--model", help="Model override")
    ] = None,
    select_model: Annotated[
        bool,
        typer.Option(
            "--select-model",
            help="Interactively choose a Requesty model for this run",
        ),
    ] = False,
    temperature: Annotated[
        Optional[float],
        typer.Option(
            "--temperature",
            help="Sampling temperature override for the active model",
            min=0.0,
            max=2.0,
        ),
    ] = None,
    max_tokens: Annotated[
        Optional[int],
        typer.Option(
            "--max-tokens",
            help="Maximum tokens to request from the model",
            min=1,
        ),
    ] = None,
    max_concurrent: Annotated[
        Optional[int],
        typer.Option("--max-concurrent", help="Maximum concurrent API requests"),
    ] = None,
    output_dir: Annotated[
        Optional[str], typer.Option("--output-dir", help="Output directory")
    ] = None,
    output_path: Annotated[
        Optional[str],
        typer.Option("--output-path", help="Output file path for project design"),
    ] = None,
    streaming: Annotated[
        bool, typer.Option("--streaming", help="Enable token streaming")
    ] = False,
    auto_commit: Annotated[
        bool,
        typer.Option(
            "--auto-commit",
            help="Enable automatic git commits after each stage (disabled by default in interactive mode)",
            is_flag=True,
        ),
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", help="Enable verbose logging")
    ] = False,
    debug: Annotated[
        bool, typer.Option("--debug", help="Enable debug mode with full tracebacks")
    ] = False,
) -> None:
    """Generate a project design from user inputs."""
    try:
        # Validate required parameters
        if not project_name or not project_name.strip():
            typer.echo("Error: Project name is required", err=True, color=True)
            raise typer.Exit(code=1)

        if not languages or not languages.strip():
            typer.echo(
                "Error: At least one language must be specified", err=True, color=True
            )
            raise typer.Exit(code=1)

        if not requirements or not requirements.strip():
            typer.echo("Error: Project requirements are required", err=True, color=True)
            raise typer.Exit(code=1)

        # Load config
        config = _load_app_config(
            config_path,
            provider,
            model,
            output_dir,
            verbose,
            temperature,
            max_tokens,
        )

        # Apply last-used preferences (provider, models, per-provider API keys/base URLs)
        try:
            prefs = load_last_used_preferences()
            apply_settings_to_config(config, prefs)
        except Exception:
            pass

        if select_model:
            _select_requesty_model_interactively(config)

        if max_concurrent:
            config.max_concurrent_requests = max_concurrent
        if streaming:
            config.streaming_enabled = True

        # Parse lists
        languages_list = [lang.strip() for lang in languages.split(",")]
        frameworks_list = (
            [fw.strip() for fw in frameworks.split(",")] if frameworks else None
        )
        apis_list = [api.strip() for api in apis.split(",")] if apis else None

        # Create orchestrator
        orchestrator = _create_orchestrator(config)

        # Run design generation
        typer.echo("\n" + "=" * 60)
        typer.echo(f"[ROCKET] Generating project design for: {project_name}")
        typer.echo("=" * 60 + "\n")
        typer.echo(f"Languages: {', '.join(languages_list)}")
        if frameworks_list:
            typer.echo(f"Frameworks: {', '.join(frameworks_list)}")
        if apis_list:
            typer.echo(f"APIs: {', '.join(apis_list)}")
        typer.echo("\n[WAIT] Generating design (this may take a moment)...\n")

        logger.info(f"Generating project design for: {project_name}")

        async def _run():
            design = await orchestrator.project_design_gen.generate(
                project_name=project_name,
                languages=languages_list,
                requirements=requirements,
                frameworks=frameworks_list,
                apis=apis_list,
            )
            return design

        # Temporarily suppress console INFO logs and show a spinner while generating
        root_logger = logging.getLogger()
        console_handlers = [h for h in root_logger.handlers if isinstance(h, logging.StreamHandler)]
        old_levels = [h.level for h in console_handlers]
        try:
            for h in console_handlers:
                h.setLevel(logging.WARNING)
            with console.status("Generating project design...", spinner="dots"):
                design = asyncio.run(_run())
        finally:
            for h, lvl in zip(console_handlers, old_levels):
                h.setLevel(lvl)

        # Display intermediate results
        typer.echo("\n[LIST] Project Design Summary:")
        typer.echo("-" * 40)
        if design.objectives:
            typer.echo(f"Objectives: {len(design.objectives)} defined")
        if design.tech_stack:
            typer.echo(f"Tech Stack: {', '.join(design.tech_stack[:3])}")
            if len(design.tech_stack) > 3:
                typer.echo(f"            + {len(design.tech_stack) - 3} more...")
        typer.echo("-" * 40 + "\n")

        # Save output
        output_file = output_path or str(config.output_dir / "project_design.md")
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"# Project Design: {project_name}\n\n")
            f.write(f"## Architecture Overview\n\n{design.architecture_overview}\n\n")
            f.write("## Tech Stack\n\n")
            for tech in design.tech_stack:
                f.write(f"- {tech}\n")

        typer.echo(f"[OK] Project design saved to: {output_file}", color=True)
        logger.info(f"Project design saved to: {output_file}")

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"\n[ERROR] Error: {str(e)}", err=True, color=True)
        logger.error(f"Error generating project design: {e}", exc_info=True)
        if debug:
            typer.echo("\nDebug traceback:", err=True)
            typer.echo(traceback.format_exc(), err=True)
        raise typer.Exit(code=1)

def _parse_markdown_design(content: str, project_name: str) -> ProjectDesign:
    """Parse markdown project design into ProjectDesign model.
    
    Args:
        content: Raw markdown content from project design file
        project_name: Fallback project name if not found in content
    
    Returns:
        Parsed ProjectDesign model
    """
    import re
    
    # Initialize defaults
    objectives = []
    tech_stack = []
    dependencies = []
    challenges = []
    mitigations = []
    architecture_overview = ""
    
    # Extract project name from header
    name_match = re.search(r'# Project Design:\s*(.+)', content)
    if name_match:
        project_name = name_match.group(1).strip()
    
    # Extract architecture overview
    arch_match = re.search(r'## Architecture Overview\s*\n\s*(.+?)(?=\n##|\n#|\Z)', content, re.DOTALL)
    if arch_match:
        architecture_overview = arch_match.group(1).strip()
    
    # Extract tech stack
    tech_matches = re.findall(r'## Tech Stack\s*\n((?:- .+\n?)+)', content, re.DOTALL)
    if tech_matches:
        for line in tech_matches[0].split('\n'):
            if line.strip().startswith('-'):
                tech_stack.append(line.strip()[1:].strip())
    
    # Extract objectives (if present in markdown)
    obj_matches = re.findall(r'## Objectives\s*\n((?:- .+\n?)+)', content, re.DOTALL)
    if obj_matches:
        for line in obj_matches[0].split('\n'):
            if line.strip().startswith('-'):
                objectives.append(line.strip()[1:].strip())
    
    # Extract dependencies (if present)
    dep_matches = re.findall(r'## Dependencies\s*\n((?:- .+\n?)+)', content, re.DOTALL)
    if dep_matches:
        for line in dep_matches[0].split('\n'):
            if line.strip().startswith('-'):
                dependencies.append(line.strip()[1:].strip())
    
    # Extract challenges (if present)
    challenge_matches = re.findall(r'## Challenges?\s*\n((?:- .+\n?)+)', content, re.DOTALL)
    if challenge_matches:
        for line in challenge_matches[0].split('\n'):
            if line.strip().startswith('-'):
                challenges.append(line.strip()[1:].strip())
    
    # Extract mitigations (if present)
    mitigation_matches = re.findall(r'## Mitigations?\s*\n((?:- .+\n?)+)', content, re.DOTALL)
    if mitigation_matches:
        for line in mitigation_matches[0].split('\n'):
            if line.strip().startswith('-'):
                mitigations.append(line.strip()[1:].strip())
    
    return ProjectDesign(
        project_name=project_name,
        objectives=objectives if objectives else ["Generate project objectives based on requirements"],
        tech_stack=tech_stack if tech_stack else ["Technology stack to be determined"],
        architecture_overview=architecture_overview or "Architecture overview to be generated from markdown content",
        dependencies=dependencies,
        challenges=challenges,
        mitigations=mitigations
    )


@app.command()

@app.command()
def generate_devplan(
    design_file: Annotated[
        str, typer.Argument(help="Path to project design Markdown file")
    ],
    config_path: Annotated[
        Optional[str], typer.Option("--config", help="Path to config file")
    ] = None,
    provider: Annotated[
        Optional[str], typer.Option("--provider", help="LLM provider override")
    ] = None,
    model: Annotated[
        Optional[str], typer.Option("--model", help="Model override")
    ] = None,
    select_model: Annotated[
        bool,
        typer.Option(
            "--select-model",
            help="Interactively choose a Requesty model for this run",
        ),
    ] = False,
    temperature: Annotated[
        Optional[float],
        typer.Option(
            "--temperature",
            help="Sampling temperature override for the active model",
            min=0.0,
            max=2.0,
        ),
    ] = None,
    max_tokens: Annotated[
        Optional[int],
        typer.Option(
            "--max-tokens",
            help="Maximum tokens to request from the model",
            min=1,
        ),
    ] = None,
    output_dir: Annotated[
        Optional[str], typer.Option("--output-dir", help="Output directory")
    ] = None,
    output_path: Annotated[
        Optional[str],
        typer.Option("--output-path", help="Output file path for devplan"),
    ] = None,
    pre_review: Annotated[
        bool, typer.Option("--pre-review/--no-pre-review", help="Review & fix the design with the DevPlan model before planning")
    ] = False,
    feedback_file: Annotated[
        Optional[str],
        typer.Option(
            "--feedback-file",
            help="Path to YAML feedback file for iterative refinement",
        ),
    ] = None,
    max_concurrent: Annotated[
        Optional[int],
        typer.Option("--max-concurrent", help="Maximum concurrent API requests"),
    ] = None,
    streaming: Annotated[
        bool, typer.Option("--streaming", help="Enable token streaming")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", help="Enable verbose logging")
    ] = False,
    debug: Annotated[
        bool, typer.Option("--debug", help="Enable debug mode with full tracebacks")
    ] = False,
) -> None:
    """Generate a development plan from a project design."""
    try:
        # Load config
        config = _load_app_config(
            config_path,
            provider,
            model,
            output_dir,
            verbose,
            temperature,
            max_tokens,
        )

        if select_model:
            _select_requesty_model_interactively(config)

        if max_concurrent:
            config.max_concurrent_requests = max_concurrent
        if streaming:
            config.streaming_enabled = True

        # Validate input file
        if not design_file or not design_file.strip():
            typer.echo("Error: Design file path is required", err=True, color=True)
            raise typer.Exit(code=1)

        # Load project design
        design_path = Path(design_file)
        if not design_path.exists():
            typer.echo(
                f"Error: Design file not found: {design_path.absolute()}",
                err=True,
                color=True,
            )
            raise typer.Exit(code=1)

        if not design_path.is_file():
            typer.echo(
                f"Error: Path is not a file: {design_path.absolute()}",
                err=True,
                color=True,
            )
            raise typer.Exit(code=1)

        with open(design_path, "r", encoding="utf-8") as f:
            content = f.read()
            # Only support markdown files now
            design = _parse_markdown_design(content, "")

        # Create orchestrator
        orchestrator = _create_orchestrator(config)

        # Setup feedback manager if feedback file provided
        feedback_manager = None
        if feedback_file:
            feedback_path = Path(feedback_file)
            if not feedback_path.exists():
                typer.echo(
                    f"Warning: Feedback file not found: {feedback_path}",
                    err=True,
                    color=True,
                )
            else:
                feedback_manager = FeedbackManager(feedback_path)
                summary = feedback_manager.get_feedback_summary()
                total_corr = summary["total_corrections"]
                total_edits = summary["total_manual_edits"]
                typer.echo(
                    f"\n[NOTE] Loaded feedback: {total_corr} corrections, "
                    f"{total_edits} manual edits"
                )

        # Run devplan generation
        typer.echo("\n" + "=" * 60)
        typer.echo(f"[PLAN] Generating development plan for: {design.project_name}")
        typer.echo("=" * 60 + "\n")
        typer.echo("[WAIT] Step 1/2: Generating basic devplan structure...")

        logger.info(f"Generating devplan from: {design_file}")

        devplan = asyncio.run(
            orchestrator.run_devplan_only(
                design,
                feedback_manager=feedback_manager,
                pre_review=pre_review,
            )
        )

        # Display intermediate results
        typer.echo("[OK] Basic structure complete")
        typer.echo("[WAIT] Step 2/2: Generating detailed steps...")
        typer.echo("\n[STATS] DevPlan Summary:")
        typer.echo("-" * 40)
        typer.echo(f"Phases: {len(devplan.phases)} identified")
        total_steps = sum(len(phase.steps) for phase in devplan.phases)
        typer.echo(f"Total Steps: {total_steps}")
        typer.echo("-" * 40 + "\n")

        # Save output
        output_file = output_path or str(config.output_dir / "devplan.md")
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)

        devplan_md = orchestrator._devplan_to_markdown(devplan)
        from .file_manager import FileManager
        fm = FileManager()
        ok, written_path = fm.safe_write_devplan(output_file, devplan_md)
        if ok:
            typer.echo(f"[OK] DevPlan saved to: {output_file}", color=True)
            logger.info(f"DevPlan saved to: {output_file}")
        else:
            typer.echo(f"[WARN] DevPlan content failed validation; wrote candidate to: {written_path}", err=True, color=True)
            logger.warning(f"DevPlan write redirected to tmp: {written_path}")

    except typer.Exit:
        raise
    except json.JSONDecodeError as e:
        typer.echo(
            f"\n[ERROR] Error: Invalid JSON in design file: {str(e)}",
            err=True,
            color=True,
        )
        logger.error(f"JSON decode error: {e}", exc_info=True)
        if debug:
            typer.echo("\nDebug traceback:", err=True)
            typer.echo(traceback.format_exc(), err=True)
        raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"\n[ERROR] Error: {str(e)}", err=True, color=True)
        logger.error(f"Error generating devplan: {e}", exc_info=True)
        if debug:
            typer.echo("\nDebug traceback:", err=True)
            typer.echo(traceback.format_exc(), err=True)
        raise typer.Exit(code=1)


@app.command()
def generate_handoff(
    devplan_file: Annotated[str, typer.Argument(help="Path to devplan JSON file")],
    project_name: Annotated[str, typer.Option("--name", help="Project name")],
    config_path: Annotated[
        Optional[str], typer.Option("--config", help="Path to config file")
    ] = None,
    output_dir: Annotated[
        Optional[str], typer.Option("--output-dir", help="Output directory")
    ] = None,
    output_path: Annotated[
        Optional[str],
        typer.Option("--output-path", help="Output file path for handoff prompt"),
    ] = None,
    verbose: Annotated[
        bool, typer.Option("--verbose", help="Enable verbose logging")
    ] = False,
    debug: Annotated[
        bool, typer.Option("--debug", help="Enable debug mode with full tracebacks")
    ] = False,
    select_model: Annotated[
        bool, typer.Option("--select-model", help="Select model interactively")
    ] = False,
    temperature: Annotated[
        Optional[float],
        typer.Option(
            "--temperature",
            help="Sampling temperature override for the active model",
            min=0.0,
            max=2.0,
        ),
    ] = None,
    max_tokens: Annotated[
        Optional[int],
        typer.Option(
            "--max-tokens",
            help="Maximum tokens to request from the model",
            min=1,
        ),
    ] = None,
) -> None:
    """Generate a handoff prompt from a development plan."""
    try:
        # Load config
        config = _load_app_config(
            config_path,
            None,
            None,
            output_dir,
            verbose,
            temperature,
            max_tokens,
        )

        # Apply last-used preferences
        try:
            prefs = load_last_used_preferences()
            apply_settings_to_config(config, prefs)
        except Exception:
            pass

        if select_model:
            _select_requesty_model_interactively(config)

        # Validate inputs
        if not devplan_file or not devplan_file.strip():
            typer.echo("Error: DevPlan file path is required", err=True, color=True)
            raise typer.Exit(code=1)

        if not project_name or not project_name.strip():
            typer.echo("Error: Project name is required", err=True, color=True)
            raise typer.Exit(code=1)

        # Load devplan
        devplan_path = Path(devplan_file)
        if not devplan_path.exists():
            typer.echo(
                f"Error: DevPlan file not found: {devplan_path.absolute()}",
                err=True,
                color=True,
            )
            raise typer.Exit(code=1)

        if not devplan_path.is_file():
            typer.echo(
                f"Error: Path is not a file: {devplan_path.absolute()}",
                err=True,
                color=True,
            )
            raise typer.Exit(code=1)

        with open(devplan_path, "r", encoding="utf-8") as f:
            devplan_data = json.load(f)
            devplan = DevPlan.model_validate(devplan_data)

        # Create orchestrator
        orchestrator = _create_orchestrator(config)

        # Run handoff generation
        typer.echo("\n" + "=" * 60)
        typer.echo(f"[SEND] Generating handoff prompt for: {project_name}")
        typer.echo("=" * 60 + "\n")
        typer.echo("[WAIT] Creating handoff document...\n")

        logger.info(f"Generating handoff prompt from: {devplan_file}")

        handoff = asyncio.run(orchestrator.run_handoff_only(devplan, project_name))

        # Display intermediate results
        typer.echo("\n[OK] Handoff prompt generated")
        if handoff.next_steps:
            typer.echo(f"Next steps: {len(handoff.next_steps)} defined\n")

        # Save output
        output_file = output_path or str(config.output_dir / "handoff_prompt.md")
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(handoff.content)

        typer.echo(f"[OK] Handoff prompt saved to: {output_file}", color=True)
        logger.info(f"Handoff prompt saved to: {output_file}")

    except typer.Exit:
        raise
    except json.JSONDecodeError as e:
        typer.echo(
            f"\n[ERROR] Error: Invalid JSON in devplan file: {str(e)}",
            err=True,
            color=True,
        )
        logger.error(f"JSON decode error: {e}", exc_info=True)
        if debug:
            typer.echo("\nDebug traceback:", err=True)
            typer.echo(traceback.format_exc(), err=True)
        raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"\n[ERROR] Error: {str(e)}", err=True, color=True)
        logger.error(f"Error generating handoff prompt: {e}", exc_info=True)
        if debug:
            typer.echo("\nDebug traceback:", err=True)
            typer.echo(traceback.format_exc(), err=True)
        raise typer.Exit(code=1)


@app.command()
def run_full_pipeline(
    project_name: Annotated[str, typer.Option("--name", help="Project name")],
    languages: Annotated[
        str,
        typer.Option("--languages", help="Comma-separated programming languages"),
    ],
    requirements: Annotated[
        str, typer.Option("--requirements", help="Project requirements")
    ],
    frameworks: Annotated[
        Optional[str],
        typer.Option("--frameworks", help="Comma-separated frameworks"),
    ] = None,
    apis: Annotated[
        Optional[str], typer.Option("--apis", help="Comma-separated APIs")
    ] = None,
    config_path: Annotated[
        Optional[str], typer.Option("--config", help="Path to config file")
    ] = None,
    provider: Annotated[
        Optional[str], typer.Option("--provider", help="LLM provider override")
    ] = None,
    model: Annotated[
        Optional[str], typer.Option("--model", help="Model override")
    ] = None,
    select_model: Annotated[
        bool,
        typer.Option(
            "--select-model",
            help="Interactively choose a Requesty model for this run",
        ),
    ] = False,
    temperature: Annotated[
        Optional[float],
        typer.Option(
            "--temperature",
            help="Sampling temperature override for the active model",
            min=0.0,
            max=2.0,
        ),
    ] = None,
    max_tokens: Annotated[
        Optional[int],
        typer.Option(
            "--max-tokens",
            help="Maximum tokens to request from the model",
            min=1,
        ),
    ] = None,
    output_dir: Annotated[
        Optional[str], typer.Option("--output-dir", help="Output directory")
    ] = None,
    feedback_file: Annotated[
        Optional[str],
        typer.Option(
            "--feedback-file",
            help="Path to YAML feedback file for iterative refinement",
        ),
    ] = None,
    resume_from: Annotated[
        Optional[str],
        typer.Option(
            "--resume-from",
            help="Resume pipeline from a checkpoint (checkpoint key)",
        ),
    ] = None,
    max_concurrent: Annotated[
        Optional[int],
        typer.Option("--max-concurrent", help="Maximum concurrent API requests"),
    ] = None,
    streaming: Annotated[
        bool, typer.Option("--streaming", help="Enable token streaming")
    ] = False,
    pre_review: Annotated[
        bool, typer.Option("--pre-review/--no-pre-review", help="Review & fix the design with the DevPlan model before planning")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", help="Enable verbose logging")
    ] = False,
    debug: Annotated[
        bool, typer.Option("--debug", help="Enable debug mode with full tracebacks")
    ] = False,
) -> None:
    """Run the complete pipeline from inputs to handoff prompt."""
    try:
        # Validate required parameters
        if not project_name or not project_name.strip():
            typer.echo("Error: Project name is required", err=True, color=True)
            raise typer.Exit(code=1)

        if not languages or not languages.strip():
            typer.echo(
                "Error: At least one language must be specified", err=True, color=True
            )
            raise typer.Exit(code=1)

        if not requirements or not requirements.strip():
            typer.echo("Error: Project requirements are required", err=True, color=True)
            raise typer.Exit(code=1)

        # Load config
        config = _load_app_config(
            config_path,
            provider,
            model,
            output_dir,
            verbose,
            temperature,
            max_tokens,
        )

        if select_model:
            _select_requesty_model_interactively(config)

        if max_concurrent:
            config.max_concurrent_requests = max_concurrent
        if streaming:
            config.streaming_enabled = True

        # Parse lists
        languages_list = [lang.strip() for lang in languages.split(",")]
        frameworks_list = (
            [fw.strip() for fw in frameworks.split(",")] if frameworks else None
        )
        apis_list = [api.strip() for api in apis.split(",")] if apis else None

        # Create markdown output manager and initialize run directory
        markdown_output_mgr = MarkdownOutputManager(base_output_dir="outputs")
        run_dir = markdown_output_mgr.create_run_directory(project_name)
        typer.echo(f"\n[NOTE] Saving all outputs to: {run_dir}\n")
        
        # Save run metadata
        markdown_output_mgr.save_run_metadata({
            "project_name": project_name,
            "languages": languages_list,
            "requirements": requirements,
            "frameworks": frameworks_list,
            "apis": apis_list,
            "config_path": config_path,
            "provider": config.llm.provider,
            "model": config.llm.model,
        })

        # Create orchestrator with markdown output manager
        orchestrator = _create_orchestrator(config, markdown_output_manager=markdown_output_mgr)

        # Setup feedback manager if feedback file provided
        feedback_manager = None
        if feedback_file:
            feedback_path = Path(feedback_file)
            if not feedback_path.exists():
                typer.echo(
                    f"Warning: Feedback file not found: {feedback_path}",
                    err=True,
                    color=True,
                )
            else:
                feedback_manager = FeedbackManager(feedback_path)
                summary = feedback_manager.get_feedback_summary()
                total_corr = summary["total_corrections"]
                total_edits = summary["total_manual_edits"]
                typer.echo(
                    f"\n[NOTE] Loaded feedback: {total_corr} corrections, "
                    f"{total_edits} manual edits"
                )

        # Ensure output directory exists
        config.output_dir.mkdir(parents=True, exist_ok=True)

        # Handle checkpoint resumption
        if resume_from:
            typer.echo("\n" + "=" * 60)
            typer.echo(f"[REFRESH] Resuming pipeline from checkpoint: {resume_from}")
            typer.echo("=" * 60 + "\n")

            logger.info(f"Resuming pipeline from checkpoint: {resume_from}")

            try:
                design, devplan, handoff = asyncio.run(
                    orchestrator.resume_from_checkpoint(
                        checkpoint_key=resume_from,
                        output_dir=str(config.output_dir),
                        save_artifacts=True,
                        feedback_manager=feedback_manager,
                    )
                )
            except ValueError as e:
                typer.echo(f"\n[ERROR] Error: {str(e)}", err=True, color=True)
                typer.echo(
                    "\n[TIP] Use 'devussy list-checkpoints' to see "
                    "available checkpoints",
                    color=True,
                )
                raise typer.Exit(code=1)
        else:
            # Run full pipeline from start
            logger.info(f"Starting full pipeline for: {project_name}")

            design, devplan, handoff = asyncio.run(
                orchestrator.run_full_pipeline(
                    project_name=project_name,
                    languages=languages_list,
                    requirements=requirements,
                    frameworks=frameworks_list,
                    apis=apis_list,
                    output_dir=str(config.output_dir),
                    save_artifacts=True,
                    feedback_manager=feedback_manager,
                    pre_review=pre_review,
                )
            )

        logger.info("Full pipeline completed successfully")

    except typer.Exit:
        raise
    except KeyboardInterrupt:
        typer.echo("\n\n[WARN] Pipeline interrupted by user", err=True, color=True)
        logger.warning("Pipeline interrupted by user")
        raise typer.Exit(code=130)
    except Exception as e:
        typer.echo(f"\n[ERROR] Error: {str(e)}", err=True, color=True)
        logger.error(f"Error running full pipeline: {e}", exc_info=True)
        if debug:
            typer.echo("\nDebug traceback:", err=True)
            typer.echo(traceback.format_exc(), err=True)
        raise typer.Exit(code=1)


@app.command()
def init_repo(
    path: Annotated[
        Optional[str],
        typer.Argument(help="Path to initialize (defaults to current directory)"),
    ] = None,
    remote: Annotated[
        Optional[str], typer.Option("--remote", help="Git remote URL to add")
    ] = None,
    force: Annotated[
        bool,
        typer.Option(
            "--force/--no-force", help="Force initialization even if directory not empty"
        ),
    ] = False,
) -> None:
    """Initialize a new repository with DevPlan Orchestrator structure."""
    try:
        import subprocess

        # Determine target path
        target_path = Path(path) if path else Path.cwd()
        target_path = target_path.resolve()

        typer.echo("\n" + "=" * 60)
        typer.echo("[ROCKET] Initializing DevPlan Orchestrator repository")
        typer.echo("=" * 60 + "\n")
        typer.echo(f"Target directory: {target_path}\n")

        # Check if directory exists
        if not target_path.exists():
            typer.echo(f"Creating directory: {target_path}")
            target_path.mkdir(parents=True, exist_ok=True)

        # Check if directory is empty
        if list(target_path.iterdir()) and not force:
            typer.echo(
                "\n[WARN] Error: Directory is not empty. "
                "Use --force to initialize anyway.",
                err=True,
                color=True,
            )
            raise typer.Exit(code=1)

        # Initialize Git repository
        typer.echo("[WAIT] Initializing Git repository...")
        result = subprocess.run(
            ["git", "init"],
            cwd=target_path,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            typer.echo(
                f"\n[WARN] Warning: Failed to initialize Git: {result.stderr}",
                err=True,
            )
        else:
            typer.echo("[OK] Git repository initialized")

        # Create .gitignore
        typer.echo("[WAIT] Creating .gitignore...")
        gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/
.venv
*.egg-info/
dist/
build/
.pytest_cache/
.coverage
htmlcov/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# DevPlan Orchestrator
.env
.devussy_state/
logs/

# OS
.DS_Store
Thumbs.db
"""
        (target_path / ".gitignore").write_text(gitignore_content)
        typer.echo("[OK] Created .gitignore")

        # Create README.md
        typer.echo("[WAIT] Creating README.md...")
        readme_content = """# DevPlan Orchestrator Project

This project was initialized with [DevPlan Orchestrator](
https://github.com/yourusername/devplan-orchestrator).

## Getting Started

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Create a `.env` file with your API keys:
   ```
   OPENAI_API_KEY=your_key_here
   ```

3. Generate a project design:
   ```bash
   devussy generate-design --name "My Project" \
       --languages "Python" --requirements "Build a web API"
   ```

4. Generate a development plan:
   ```bash
   devussy run-full-pipeline --name "My Project" \
       --languages "Python" --requirements "Build a web API"
   ```

## Documentation

Generated documentation will be stored in the `docs/` directory.
"""
        (target_path / "README.md").write_text(readme_content)
        typer.echo("[OK] Created README.md")

        # Create config directory and config.yaml
        typer.echo("[WAIT] Creating config directory...")
        config_dir = target_path / "config"
        config_dir.mkdir(exist_ok=True)

        config_content = """# DevPlan Orchestrator Configuration

llm_provider: openai
model: gpt-4
max_concurrent_requests: 5

retry:
  max_attempts: 3
  initial_delay: 1
  max_delay: 60

streaming_enabled: false
output_dir: ./docs
log_level: INFO
"""
        (config_dir / "config.yaml").write_text(config_content)
        typer.echo("[OK] Created config/config.yaml")

        # Create .env.example
        typer.echo("[WAIT] Creating .env.example...")
        env_example_content = """# DevPlan Orchestrator Environment Variables

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
# OPENAI_ORG_ID=your_org_id_here

# Generic OpenAI-Compatible API
# GENERIC_API_KEY=your_api_key_here
# GENERIC_BASE_URL=https://api.example.com/v1

# Requesty Configuration
# REQUESTY_API_KEY=your_requesty_api_key_here
# REQUESTY_BASE_URL=https://api.requesty.com

# LLM Provider (openai, generic, requesty)
LLM_PROVIDER=openai
"""
        (target_path / ".env.example").write_text(env_example_content)
        typer.echo("[OK] Created .env.example")

        # Create docs directory
        typer.echo("[WAIT] Creating docs directory...")
        docs_dir = target_path / "docs"
        docs_dir.mkdir(exist_ok=True)
        (docs_dir / ".gitkeep").write_text("")
        typer.echo("[OK] Created docs/ directory")

        # Add remote if specified
        if remote:
            typer.echo(f"\n[WAIT] Adding remote: {remote}")
            result = subprocess.run(
                ["git", "remote", "add", "origin", remote],
                cwd=target_path,
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                typer.echo(
                    f"[WARN] Warning: Failed to add remote: {result.stderr}", err=True
                )
            else:
                typer.echo("[OK] Remote added")

        # Initial commit
        if result.returncode == 0:  # Only if git init succeeded
            typer.echo("\n[WAIT] Creating initial commit...")
            subprocess.run(
                ["git", "add", "."],
                cwd=target_path,
                capture_output=True,
                check=False,
            )
            subprocess.run(
                ["git", "commit", "-m", "init: DevPlan Orchestrator repository"],
                cwd=target_path,
                capture_output=True,
                check=False,
            )
            typer.echo("[OK] Initial commit created")

        # Success message
        typer.echo("\n" + "=" * 60)
        typer.echo("[OK] Repository initialized successfully!", color=True)
        typer.echo("=" * 60)
        typer.echo("\nNext steps:")
        typer.echo("  1. Copy .env.example to .env and add your API keys")
        typer.echo("  2. Review config/config.yaml and adjust settings")
        typer.echo(
            "  3. Run 'devussy run-full-pipeline' to generate your first devplan"
        )
        typer.echo("\n" + "=" * 60 + "\n")

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"\n[ERROR] Error: {str(e)}", err=True, color=True)
        logger.error(f"Error initializing repository: {e}", exc_info=True)
        raise typer.Exit(code=1)


@app.command()
def list_checkpoints(
    config_path: Annotated[
        Optional[str], typer.Option("--config", help="Path to config file")
    ] = None,
    verbose: Annotated[
        bool, typer.Option("--verbose", help="Show detailed information")
    ] = False,
) -> None:
    """List all available checkpoints."""
    try:
        # Load minimal config for logging setup
        _load_app_config(config_path, None, None, None, verbose)

        # Create state manager
        state_manager = StateManager()

        # Get all checkpoints
        checkpoints = state_manager.list_checkpoints()

        if not checkpoints:
            typer.echo("\n[INFO] No checkpoints found", color=True)
            typer.echo(
                "[TIP] Checkpoints are created automatically when running pipelines\n"
            )
            return

        typer.echo(f"\n[BOOKMARK] Found {len(checkpoints)} checkpoint(s):\n")

        for checkpoint in checkpoints:
            key = checkpoint["key"]
            stage = checkpoint["stage"]
            timestamp = checkpoint["timestamp"]

            # Parse timestamp for display
            try:
                from datetime import datetime

                dt = datetime.fromisoformat(timestamp)
                time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            except (ValueError, TypeError):
                time_str = timestamp

            typer.echo(f"[BOOKMARK] {key}")
            typer.echo(f"   Stage: {stage}")
            typer.echo(f"   Created: {time_str}")

            if verbose:
                typer.echo(f"   File: {checkpoint['file']}")

            typer.echo("")

    except Exception as e:
        typer.echo(f"\n[ERROR] Error listing checkpoints: {str(e)}", err=True, color=True)
        logger.error(f"Error listing checkpoints: {e}", exc_info=True)
        raise typer.Exit(code=1)


@app.command()
def delete_checkpoint(
    checkpoint_key: Annotated[str, typer.Argument(help="Checkpoint key to delete")],
    config_path: Annotated[
        Optional[str], typer.Option("--config", help="Path to config file")
    ] = None,
    force: Annotated[
        bool, typer.Option("--force", help="Skip confirmation prompt")
    ] = False,
) -> None:
    """Delete a specific checkpoint."""
    try:
        # Load minimal config for logging setup
        _load_app_config(config_path, None, None, None, False)

        # Create state manager
        state_manager = StateManager()

        # Check if checkpoint exists
        checkpoint = state_manager.load_checkpoint(checkpoint_key)
        if checkpoint is None:
            typer.echo(
                f"\n[ERROR] Checkpoint not found: {checkpoint_key}", err=True, color=True
            )
            typer.echo(
                "[TIP] Use 'devussy list-checkpoints' to see available checkpoints\n"
            )
            raise typer.Exit(code=1)

        # Show checkpoint info
        stage = checkpoint.get("stage", "unknown")
        timestamp = checkpoint.get("timestamp", "unknown")

        try:
            from datetime import datetime

            dt = datetime.fromisoformat(timestamp)
            time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError):
            time_str = timestamp

        typer.echo(f"\n[BOOKMARK] Found checkpoint: {checkpoint_key}")
        typer.echo(f"   Stage: {stage}")
        typer.echo(f"   Created: {time_str}")

        # Confirm deletion unless --force is used
        if not force:
            confirmed = typer.confirm(
                "\nAre you sure you want to delete this checkpoint?"
            )
            if not confirmed:
                typer.echo("\n[ERROR] Deletion cancelled", color=True)
                return

        # Delete the checkpoint
        state_manager.delete_checkpoint(checkpoint_key)
        typer.echo(f"\n[OK] Deleted checkpoint: {checkpoint_key}", color=True)

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"\n[ERROR] Error deleting checkpoint: {str(e)}", err=True, color=True)
        logger.error(f"Error deleting checkpoint: {e}", exc_info=True)
        raise typer.Exit(code=1)


@app.command()
def cleanup_checkpoints(
    keep_latest: Annotated[
        int,
        typer.Option(
            "--keep", help="Number of latest checkpoints to keep per project"
        ),
    ] = 5,
    config_path: Annotated[
        Optional[str], typer.Option("--config", help="Path to config file")
    ] = None,
    force: Annotated[
        bool, typer.Option("--force", help="Skip confirmation prompt")
    ] = False,
) -> None:
    """Clean up old checkpoints, keeping only the latest N per project."""
    try:
        # Load minimal config for logging setup
        _load_app_config(config_path, None, None, None, False)

        # Create state manager
        state_manager = StateManager()

        # Get checkpoint count before cleanup
        checkpoints_before = len(state_manager.list_checkpoints())

        if checkpoints_before == 0:
            typer.echo("\n[INFO] No checkpoints found to clean up", color=True)
            return

        typer.echo(
            f"\n[BROOM] Cleaning up checkpoints (keeping {keep_latest} latest per project)"
        )
        typer.echo(f"   Current checkpoints: {checkpoints_before}")

        # Confirm cleanup unless --force is used
        if not force:
            confirmed = typer.confirm("\nProceed with cleanup?")
            if not confirmed:
                typer.echo("\n[ERROR] Cleanup cancelled", color=True)
                return

        # Perform cleanup
        state_manager.cleanup_old_checkpoints(keep_latest=keep_latest)

        # Get checkpoint count after cleanup
        checkpoints_after = len(state_manager.list_checkpoints())
        deleted_count = checkpoints_before - checkpoints_after

        typer.echo("\n[OK] Cleanup complete!")
        typer.echo(f"   Deleted: {deleted_count} checkpoints")
        typer.echo(f"   Remaining: {checkpoints_after} checkpoints", color=True)

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"\n[ERROR] Error during cleanup: {str(e)}", err=True, color=True)
        logger.error(f"Error during checkpoint cleanup: {e}", exc_info=True)
        raise typer.Exit(code=1)


@app.command()
def interactive_design(
    config_path: Annotated[
        Optional[str], typer.Option("--config", help="Path to config file")
    ] = None,
    provider: Annotated[
        Optional[str], typer.Option("--provider", help="LLM provider override")
    ] = None,
    model: Annotated[
        Optional[str], typer.Option("--model", help="Model override")
    ] = None,
    output_dir: Annotated[
        Optional[str], typer.Option("--output-dir", help="Output directory")
    ] = None,
    temperature: Annotated[
        Optional[float],
        typer.Option(
            "--temperature",
            help="Sampling temperature override for the active model",
            min=0.0,
            max=2.0,
        ),
    ] = None,
    max_tokens: Annotated[
        Optional[int],
        typer.Option(
            "--max-tokens",
            help="Maximum tokens to request from the model",
            min=1,
        ),
    ] = None,
    repo_dir: Annotated[
        Optional[str],
        typer.Option(
            "--repo-dir",
            help="Project directory to analyze for a repo-aware interview",
        ),
    ] = None,
    select_model: Annotated[
        bool,
        typer.Option(
            "--select-model",
            help="Interactively choose a Requesty model for this run",
        ),
    ] = False,
    save_session: Annotated[
        Optional[str],
        typer.Option("--save-session", help="Save session to file (path)"),
    ] = None,
    resume_session: Annotated[
        Optional[str],
        typer.Option("--resume-session", help="Resume from saved session (path)"),
    ] = None,
    llm_interview: Annotated[
        bool, typer.Option("--llm-interview/--no-llm-interview", help="Use LLM-driven conversational interview (default: true)")
    ] = True,
    scripted: Annotated[
        bool, typer.Option("--scripted", help="Use original scripted questionnaire instead of LLM interview")
    ] = False,
    streaming: Annotated[
        bool, typer.Option("--streaming", help="Enable token streaming")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", help="Enable verbose logging")
    ] = False,
    debug: Annotated[
        bool, typer.Option("--debug", help="Enable debug mode")
    ] = False,
) -> None:
    """Generate a project design through interactive questions.
    
    This command provides a guided questionnaire to help you create
    a project design without needing to specify all flags upfront.
    By default, uses an LLM-driven conversational interview.
    """
    try:
        from .interactive import InteractiveQuestionnaireManager

        # Load config
        config = _load_app_config(
            config_path,
            provider,
            model,
            output_dir,
            verbose,
            temperature,
            max_tokens,
        )

        if streaming:
            config.streaming_enabled = True

        # Interactive interview defaults to no automatic git commits to avoid noisy graphs.
        # Always disable auto-commit for this command to keep git history clean.
        if getattr(config, "git", None):
            config.git.commit_after_design = False
            config.git.commit_after_devplan = False
            config.git.commit_after_handoff = False
            config.git.auto_push = False

        # Determine interview mode
        use_llm_interview = llm_interview and not scripted

        # Optional repository analysis for LLM-driven interview mode
        # Only run if repository tools are enabled in preferences
        repo_analysis = None
        if use_llm_interview and repo_dir:
            # Reload preferences to get the latest settings from menu
            try:
                prefs = load_last_used_preferences()
                logger.debug(f"CLI reload - Loaded preferences: {prefs}")
                logger.debug(f"CLI reload - repository_tools_enabled attribute: {getattr(prefs, 'repository_tools_enabled', 'ATTRIBUTE_NOT_FOUND')}")
                logger.debug(f"CLI reload - All attributes: {[attr for attr in dir(prefs) if not attr.startswith('_')]}")
            except Exception as e:
                logger.debug(f"CLI reload - Exception loading preferences: {e}")
                pass
            
            # Check if repository tools are enabled in user preferences
            repository_tools_enabled = getattr(prefs, 'repository_tools_enabled', False)
            
            if repository_tools_enabled:
                try:
                    root = Path(repo_dir).resolve()
                    if root.exists() and root.is_dir():
                        analyzer = RepositoryAnalyzer(root)
                        repo_analysis = analyzer.analyze()
                    elif verbose:
                        typer.echo(
                            f"[WARN] Repo directory not found or not a directory: {root}",
                            err=True,
                            color=True,
                        )
                except Exception as exc:
                    if verbose:
                        typer.echo(
                            f"[WARN] Repo analysis failed ({exc}). Continuing without it.",
                            err=True,
                            color=True,
                        )
            elif verbose:
                typer.echo(
                    "[NOTE] Repository tools disabled in settings - skipping repository analysis",
                    color=True,
                )

        else:
            typer.echo("[SCRIPT] Using scripted questionnaire")
            # Setup interactive questionnaire
            questions_path = Path("config/questions.yaml")
            if not questions_path.exists():
                typer.echo(
                    f"[ERROR] Error: Questions config not found at {questions_path}",
                    err=True,
                    color=True,
                )
                typer.echo(
                    "   Please ensure config/questions.yaml exists in your project.",
                    err=True,
                )
                raise typer.Exit(code=1)
            questionnaire = InteractiveQuestionnaireManager(questions_path)

        # Apply last-used preferences as defaults for this session
        try:
            prefs = load_last_used_preferences()
            apply_settings_to_config(config, prefs)
            
            # Check for experimental features and warn user
            experimental_features = []
            if getattr(prefs, 'debug_ui_mode', False):
                experimental_features.append("Debug UI Mode")
            if getattr(prefs, 'experimental_single_window', False):
                experimental_features.append("Experimental Single Window")
            if getattr(prefs, 'mock_api_mode', False):
                experimental_features.append("Mock API Mode")
            if getattr(prefs, 'performance_profiler', False):
                experimental_features.append("Performance Profiler")
            if getattr(prefs, 'experimental_pipeline', False):
                experimental_features.append("Experimental Pipeline")
            if getattr(prefs, 'ai_code_review', False):
                experimental_features.append("AI Code Review")
                
            if experimental_features:
                typer.echo("\n[WARN] EXPERIMENTAL FEATURES ACTIVE [WARN]", color=True)
                typer.echo("The following experimental features are enabled:", color=True)
                for feature in experimental_features:
                    typer.echo(f"  - {feature}", color=True)
                typer.echo("\nThese features are for development/testing and may be unstable.", color=True)
                typer.echo("Use 'Testing' menu to disable if needed.\n", color=True)
                
        except Exception:
            pass

        # LOG: Snapshot provider after applying persisted preferences (before runtime Settings)
        logger.debug(f"[interactive_design] Provider after prefs: {getattr(config.llm, 'provider', None)}")

        # Ensure an API key is available before asking questions that may
        # require LLM access. If not present in config or env, prompt the
        # user to enter one interactively (runtime only; not persisted).
        try:
            llm_cfg = config.llm
        except Exception:
            llm_cfg = None

        # Check stage-specific API keys
        typer.echo("\n[KEY] Checking API key configuration...")
        
        missing_keys = []
        design_config = config.get_llm_config_for_stage("design")
        if not design_config.api_key:
            missing_keys.append("design")
        
        if missing_keys:
            typer.echo(f"\n[WARN] Missing API keys for stages: {', '.join(missing_keys)}")
            typer.echo("   You'll need API keys to generate the project design.\n")
            
            if typer.confirm("Would you like to enter API key(s) now?", default=True):
                api_key = typer.prompt(
                    "Enter your LLM API key (will be used for all stages)",
                    hide_input=True
                )
                config.llm.api_key = api_key
                if config.design_llm:
                    config.design_llm.api_key = api_key
                typer.echo("[OK] API key set for this session.\n")
            else:
                typer.echo(
                    "\n[WARN] Proceeding without API keys. Pipeline will fail during generation.\n",
                    err=True,
                )
        else:
            typer.echo("[OK] API keys configured for all required stages.\n")

        # Startup chooser: Settings, Readme, or Start (interactive mode)
        # Non-TTY environments will default to 'start' internally.
        try:
            while True:
                action = run_main_menu(config)
                # LOG: After each run_main_menu return, show the current provider
                logger.debug(f"[interactive_design] Provider after run_main_menu: {getattr(config.llm, 'provider', None)}")
                if action == "start":
                    # CHECK FOR REPOSITORY TOOLS - Only ask after user selects "start"
                    repository_context = None
                    
                    # DEBUG: Add detailed logging to understand the flow
                    logger.info("=== REPOSITORY TOOLS DETECTION START ===")
                    
                    # Reload preferences to get the latest settings from menu
                    try:
                        prefs = load_last_used_preferences()
                        logger.info(f"CLI repo tools reload - Loaded preferences successfully")
                        repo_tools_enabled = getattr(prefs, 'repository_tools_enabled', False)
                        logger.info(f"CLI repo tools reload - repository_tools_enabled = {repo_tools_enabled} (type: {type(repo_tools_enabled)})")
                        logger.debug(f"CLI repo tools reload - All attributes: {[attr for attr in dir(prefs) if not attr.startswith('_')]}")
                    except Exception as e:
                        logger.error(f"CLI repo tools reload - Exception loading preferences: {e}")
                        repo_tools_enabled = False
                    
                    logger.info(f"Repository tools enabled check result: {repo_tools_enabled}")
                    
                    if repo_tools_enabled:
                        logger.info("Repository tools ENABLED - entering repository tools flow")
                        print("\n[TOOLS] Repository Tools Enabled")
                        print("=" * 50)
                        
                        # Ask for repository path
                        repo_path = typer.prompt(
                            "What is the path to your project's repository?",
                            default=".",
                            show_default=True
                        ).strip()
                        
                        logger.info(f"User entered repository path: {repo_path}")
                        
                        # Ask for project type
                        project_type = typer.prompt(
                            "Are we starting a new project or working on an existing one?",
                            default="existing",
                            type=str
                        ).strip().lower()
                        
                        # Validate and retry if invalid
                        while project_type not in ["new", "existing"]:
                            typer.echo("Please enter 'new' or 'existing'")
                            project_type = typer.prompt(
                                "Are we starting a new project or working on an existing one?",
                                default="existing",
                                type=str
                            ).strip().lower()
                        
                        logger.info(f"User selected project type: {project_type}")
                        
                        try:
                            import subprocess
                            
                            # Clean and validate the repository path
                            # Remove quotes and normalize path
                            clean_repo_path = repo_path.strip().strip('"').strip("'")
                            repo_root = Path(clean_repo_path).resolve()
                            
                            logger.info(f"Cleaned repository path: {clean_repo_path}")
                            logger.info(f"Resolved repository root: {repo_root}")
                            
                            # Validate that the path is reasonable
                            # Allow "." for current directory, check resolved path instead
                            if clean_repo_path and len(clean_repo_path.strip()) < 1:
                                print("[WARN] Warning: Invalid repository path provided")
                                print("Continuing with normal interview flow...")
                                logger.warning("Invalid repository path provided - falling back to normal flow")
                                repository_context = None
                            else:
                                # Create directory if it doesn't exist for new projects
                                if project_type == "new":
                                    repo_root.mkdir(parents=True, exist_ok=True)
                                    print(f"\n[INIT] Initializing new repository at: {repo_root}")
                                    
                                    # Run init_repo directly instead of subprocess
                                    try:
                                        # Create basic repository structure
                                        init_git = subprocess.run([
                                            "git", "init"
                                        ], cwd=repo_root, capture_output=True, text=True, check=False)
                                        
                                        if init_git.returncode == 0:
                                            print("[OK] Git repository initialized")
                                            
                                            # Create .gitignore
                                            gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/
.venv
*.egg-info/
dist/
build/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# DevPlan Orchestrator
.env
.devussy_state/
logs/

# OS
.DS_Store
Thumbs.db
"""
                                            (repo_root / ".gitignore").write_text(gitignore_content)
                                            print("[OK] Created .gitignore")
                                            
                                            # Create README.md
                                            readme_content = """# DevPlan Project

Generated by DevPlan Orchestrator.

## Getting Started

1. Add your API keys to .env file
2. Run devussy to generate project plans
"""
                                            (repo_root / "README.md").write_text(readme_content)
                                            print("[OK] Created README.md")
                                            
                                            print("[OK] Repository initialized successfully!")
                                            
                                            # Create repository context for new projects
                                            repository_context = {
                                                "path": clean_repo_path,
                                                "type": "new",
                                                "analysis_output": f"New repository initialized at: {repo_root}",
                                                "analysis_object": None
                                            }
                                            logger.info(f"Repository context created for new project: {repository_context}")
                                        else:
                                            print(f"[WARN] Warning: Git initialization failed: {init_git.stderr}")
                                            logger.warning(f"Git initialization failed for new project")
                                            
                                    except Exception as e:
                                        print(f"[WARN] Warning: Repository initialization failed: {e}")
                                        logger.error(f"Repository initialization failed: {e}")
                                else:
                                    # For existing projects, verify the directory exists
                                    if not repo_root.exists() or not repo_root.is_dir():
                                        print(f"[WARN] Warning: Directory does not exist: {repo_root}")
                                        print("Continuing with normal interview flow...")
                                        logger.warning(f"Directory does not exist: {repo_root}")
                                        repository_context = None
                                    else:
                                        print(f"\n[ANALYZE] Analyzing existing repository at: {repo_root}")
                                        
                                        # Run repository analysis directly instead of subprocess
                                        try:
                                            analyzer = RepositoryAnalyzer(repo_root)
                                            analysis = analyzer.analyze()
                                            
                                            # Convert analysis to readable output for user feedback
                                            analysis_output = f"Repository Analysis\n"
                                            analysis_output += f"Root: {analysis.root_path}\n"
                                            analysis_output += f"Project type: {analysis.project_type or 'unknown'}\n"
                                            analysis_output += f"Total files: {analysis.code_metrics.total_files}, total lines: {analysis.code_metrics.total_lines}\n"
                                            
                                            if analysis.structure.directories:
                                                analysis_output += f"Top-level directories: {', '.join(sorted(analysis.structure.directories))}\n"
                                            if analysis.dependencies.python:
                                                analysis_output += f"Python dependencies: {', '.join(sorted(analysis.dependencies.python))}\n"
                                            if analysis.dependencies.node:
                                                analysis_output += f"Node dependencies: {', '.join(sorted(analysis.dependencies.node))}\n"
                                            
                                            print("[OK] Repository analyzed successfully!")
                                            print(f"[INFO] Analysis complete - {analysis.code_metrics.total_files} files analyzed")
                                            
                                            # Create repository context for enhanced interview
                                            repository_context = {
                                                "path": clean_repo_path,
                                                "type": "existing",
                                                "analysis_output": analysis_output,
                                                "analysis_object": analysis
                                            }
                                            logger.info(f"Repository context created: {repository_context}")
                                        except Exception as e:
                                            print(f"[WARN] Warning: Repository analysis failed: {e}")
                                            print("Continuing with normal interview flow...")
                                            logger.error(f"Repository analysis failed: {e}")
                                            repository_context = None
                        except Exception as e:
                            print(f"[WARN] Warning: Repository tools failed: {e}")
                            print("Continuing with normal interview flow...")
                            logger.error(f"Repository tools failed: {e}")
                            repository_context = None
                    else:
                        logger.info("Repository tools DISABLED - skipping repository tools flow")
                        print("[NOTE] Repository tools disabled in settings - using normal interview flow")
                    
                    logger.info(f"=== REPOSITORY TOOLS DETECTION END ===")
                    logger.info(f"Final repository_context: {repository_context}")
                    
                    # Continue to normal interview flow after repository tools
                    break
                
                if action == "select_model":
                    try:
                        _select_requesty_model_interactively(config)
                        # LOG: After interactive model selection, provider may have changed
                        logger.debug(f"[interactive_design] Provider after select_model: {getattr(config.llm, 'provider', None)}")
                    except Exception as exc:
                        typer.echo(f"[WARN] Model selection unavailable: {exc}")
                    continue
                if action == "quit":
                    raise typer.Exit(code=0)
                # Any other actions are handled inside run_main_menu (e.g., Options/Readme)
        except typer.Exit:
            # Propagate exit so CLI terminates as requested
            raise
        except Exception as e:
            if verbose:
                typer.echo(f"(startup menu unavailable: {e})")
        
        # CREATE INTERVIEW MANAGER AFTER REPOSITORY TOOLS FLOW
        # This ensures we have the latest repository analysis from the tools flow
        interview_manager = None
        questionnaire = None
        
        if use_llm_interview:
            typer.echo("[ROBOT] Using LLM-driven conversational interview")
            if verbose:
                typer.echo("[DEBUG] Verbose mode enabled")
            
            # Import LLM interview manager
            from .llm_interview import LLMInterviewManager
            
            # Use repository analysis from tools flow if available, otherwise fall back to original
            final_repo_analysis = None
            if repository_context and "analysis_object" in repository_context:
                final_repo_analysis = repository_context["analysis_object"]
                typer.echo(f"[NOTE] Using repository analysis from tools flow")
            elif repo_analysis:
                final_repo_analysis = repo_analysis
                typer.echo(f"[NOTE] Using repository analysis from --repo-dir parameter")
            
            # Create markdown output manager with initial timestamp-based directory
            # We'll use a temporary name until we get the actual project name from the interview
            from datetime import datetime
            temp_project_name = f"interview_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            temp_markdown_mgr = MarkdownOutputManager(base_output_dir="outputs")
            run_dir = temp_markdown_mgr.create_run_directory(temp_project_name)
            typer.echo(f"[NOTE] Interview outputs will be saved to: {run_dir}\n")
            
            interview_manager = LLMInterviewManager(
                config,
                verbose=verbose,
                repo_analysis=final_repo_analysis,
                markdown_output_manager=temp_markdown_mgr,
            )
            typer.echo(f"[NOTE] Logging to: {interview_manager.log_file}")
        else:
            typer.echo("[SCRIPT] Using scripted questionnaire")
            # Setup interactive questionnaire
            questions_path = Path("config/questions.yaml")
            if not questions_path.exists():
                typer.echo(
                    f"[ERROR] Error: Questions config not found at {questions_path}",
                    err=True,
                    color=True,
                )
                typer.echo(
                    "   Please ensure config/questions.yaml exists in your project.",
                    err=True,
                )
                raise typer.Exit(code=1)
            questionnaire = InteractiveQuestionnaireManager(questions_path)
        

        # Resume session if requested (only available for scripted mode)
        if resume_session and not use_llm_interview:
            session_path = Path(resume_session)
            if session_path.exists():
                questionnaire.load_session(session_path)
                typer.echo(f"[FOLDER] Resumed session from {resume_session}\n")
            else:
                typer.echo(
                    f"[WARN] Warning: Session file not found at {resume_session}",
                    color=True,
                )
                typer.echo("   Starting a new session instead.\n")
        elif resume_session and use_llm_interview:
            typer.echo("[WARN] Session resume not available for LLM interview mode", color=True)

        # Run interview (either LLM or scripted)
        typer.echo("")  # Add spacing
        
        if use_llm_interview:
            try:
                answers = interview_manager.run()
            except Exception as e:
                typer.echo(f"\n[ERROR] Error during LLM interview: {e}", err=True, color=True)
                typer.echo("[TIP] Falling back to scripted questionnaire...", color=True)
                # Fallback to scripted mode
                questions_path = Path("config/questions.yaml")
                if questions_path.exists():
                    questionnaire = InteractiveQuestionnaireManager(questions_path)
                    answers = questionnaire.run()
                else:
                    typer.echo("[ERROR] Cannot fall back - questions.yaml not found", err=True, color=True)
                    raise typer.Exit(code=1)
        else:
            answers = questionnaire.run()

        # Save session if requested (only available for scripted mode)
        if save_session and not use_llm_interview:
            session_path = Path(save_session)
            questionnaire.save_session(session_path)
            typer.echo(f"\n[SAVE] Session saved to {save_session}")
        elif save_session and use_llm_interview:
            typer.echo("[WARN] Session save not available for LLM interview mode", color=True)

        # Convert to generate_design inputs
        try:
            if use_llm_interview:
                inputs = interview_manager.to_generate_design_inputs()
            else:
                inputs = questionnaire.to_generate_design_inputs()
        except ValueError as e:
            typer.echo(f"\n[ERROR] Error: {e}", err=True, color=True)
            typer.echo("\n[TIP] Tip: In LLM interview mode, use /done to finalize and generate files", color=True)
            typer.echo("   The LLM needs to output a JSON summary before files can be generated.", color=True)
            raise typer.Exit(code=1)

        # Validate we have the required inputs
        if "name" not in inputs:
            typer.echo(
                "\n[ERROR] Error: Project name is required but was not provided",
                err=True,
                color=True,
            )
            typer.echo("\n[TIP] Use /done during the interview to finalize", color=True)
            raise typer.Exit(code=1)

        if "languages" not in inputs:
            typer.echo(
                "\n[ERROR] Error: At least one language must be specified",
                err=True,
                color=True,
            )
            raise typer.Exit(code=1)

        if "requirements" not in inputs:
            typer.echo(
                "\n[ERROR] Error: Project requirements are required",
                err=True,
                color=True,
            )
            raise typer.Exit(code=1)

        # Generate design using existing pipeline
        typer.echo("\n" + "=" * 60)
        typer.echo(f"[DESIGN] Generating project design for: {inputs['name']}")
        typer.echo("=" * 60 + "\n")
        typer.echo(f"Languages: {inputs['languages']}")
        if "frameworks" in inputs:
            typer.echo(f"Frameworks: {inputs['frameworks']}")
        if "apis" in inputs:
            typer.echo(f"APIs: {inputs['apis']}")
        typer.echo("\n[WAIT] Generating design (this may take a moment)...\n")

        logger.info(f"Generating project design for: {inputs['name']}")
        
        # Create timestamped project folder to avoid overwriting
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        project_slug = inputs['name'].lower().replace(" ", "-").replace("_", "-")
        
        # Check if Repo Tools are enabled and repository context exists
        if repository_context and "path" in repository_context:
            # Use external repository's docs folder when Repo Tools are enabled
            repo_path = Path(repository_context["path"])
            base_output_dir = repo_path / "docs"
            typer.echo(f"[TOOLS] Using repository tools - output to: {base_output_dir.resolve()}")
            
            # CRITICAL FIX: Update config.output_dir to use repository-specific path
            # This ensures the orchestrator uses the correct output directory
            config.output_dir = base_output_dir
            logger.info(f"Repository Tools enabled - using repo path: {repo_path}")
            logger.info(f"Base output directory set to: {base_output_dir}")
        else:
            # Use default output directory when Repo Tools are disabled
            base_output_dir = config.output_dir
            logger.info(f"Repository Tools disabled - using default output dir: {base_output_dir}")
        
        project_folder = Path(base_output_dir) / f"{project_slug}_{timestamp}"
        project_folder.mkdir(parents=True, exist_ok=True)
        
        typer.echo(f"[FOLDER] Project folder: {project_folder.resolve()}\n")
        logger.info(f"Created project folder: {project_folder}")
        
        # Rename markdown output manager's run directory now that we have project name
        if use_llm_interview and temp_markdown_mgr:
            try:
                run_dir = temp_markdown_mgr.rename_run_directory(inputs['name'])
                typer.echo(f"[NOTE] Interview and pipeline outputs saved to: {run_dir}\n")
                
                # Save run metadata with actual project name
                temp_markdown_mgr.save_run_metadata({
                    "project_name": inputs['name'],
                    "languages": inputs.get('languages', ''),
                    "requirements": inputs.get('requirements', ''),
                    "frameworks": inputs.get('frameworks', ''),
                    "apis": inputs.get('apis', ''),
                    "provider": config.llm.provider,
                    "model": config.llm.model,
                })
            except Exception as e:
                logger.warning(f"Failed to rename markdown output directory: {e}")
                # temp_markdown_mgr is still valid, just with the temporary name

        # Extract code samples if available from interview
        code_samples = inputs.get("code_samples")
        if code_samples:
            logger.info(f"Code samples available ({len(code_samples)} chars)")

        # Create orchestrator with repo analysis, code samples, and markdown output manager
        orchestrator = _create_orchestrator(
            config,
            repo_analysis=repo_analysis,
            code_samples=code_samples,
            markdown_output_manager=temp_markdown_mgr if use_llm_interview else None,
        )
        
        # Add debugging output for repository context
        if repository_context and "path" in repository_context:
            logger.info(f"Creating orchestrator with repository context:")
            logger.info(f"  Repository path: {repository_context['path']}")
            logger.info(f"  Repository type: {repository_context.get('type', 'unknown')}")
            logger.info(f"  Output directory in config: {config.output_dir}")
        else:
            logger.info("Creating orchestrator without repository context")
            logger.info(f"  Output directory in config: {config.output_dir}")

        # Parse lists
        languages_list = [lang.strip() for lang in inputs["languages"].split(",")]
        frameworks_list = (
            [fw.strip() for fw in inputs["frameworks"].split(",")]
            if "frameworks" in inputs
            else None
        )
        apis_list = (
            [api.strip() for api in inputs["apis"].split(",")]
            if "apis" in inputs
            else None
        )

        async def _run():
            design = await orchestrator.project_design_gen.generate(
                project_name=inputs["name"],
                languages=languages_list,
                requirements=inputs["requirements"],
                frameworks=frameworks_list,
                apis=apis_list,
            )
            return design

        # Suppress console INFO logs and show spinner during design generation
        root_logger = logging.getLogger()
        console_handlers = [h for h in root_logger.handlers if isinstance(h, logging.StreamHandler)]
        old_levels = [h.level for h in console_handlers]
        try:
            for h in console_handlers:
                h.setLevel(logging.WARNING)
            with console.status("Generating project design...", spinner="dots"):
                design = asyncio.run(_run())
        finally:
            for h, lvl in zip(console_handlers, old_levels):
                h.setLevel(lvl)

        # Display intermediate results
        typer.echo("\n[LIST] Project Design Summary:")
        typer.echo("-" * 40)
        if design.objectives:
            typer.echo(f"Objectives: {len(design.objectives)} defined")
        if design.tech_stack:
            typer.echo(f"Tech Stack: {', '.join(design.tech_stack[:3])}")
            if len(design.tech_stack) > 3:
                typer.echo(f"            + {len(design.tech_stack) - 3} more...")
        typer.echo("-" * 40 + "\n")

        # Save output to timestamped project folder - COMPLETE VERSION
        output_file = project_folder / "project_design.md"

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"# Project Design: {inputs['name']}\n\n")
            f.write(f"## Architecture Overview\n\n{design.architecture_overview}\n\n")
            
            f.write("## Objectives\n\n")
            if design.objectives:
                for obj in design.objectives:
                    f.write(f"- {obj}\n")
            else:
                f.write("No specific objectives defined.\n")
            
            f.write("\n## Tech Stack\n\n")
            if design.tech_stack:
                for tech in design.tech_stack:
                    f.write(f"- {tech}\n")
            else:
                f.write("No tech stack specified.\n")
            
            f.write("\n## Dependencies\n\n")
            if design.dependencies:
                for dep in design.dependencies:
                    f.write(f"- {dep}\n")
            else:
                f.write("No dependencies specified.\n")
            
            f.write("\n## Challenges\n\n")
            if design.challenges:
                for challenge in design.challenges:
                    f.write(f"- {challenge}\n")
            else:
                f.write("No challenges identified.\n")
            
            f.write("\n## Mitigations\n\n")
            if design.mitigations:
                for mitigation in design.mitigations:
                    f.write(f"- {mitigation}\n")
            else:
                f.write("No mitigations specified.\n")

        typer.echo(f"[OK] Project design generated successfully!")
        typer.echo(f"[FILE] Saved to: {output_file.resolve()}")
        
        # Ask if user wants to conduct a design review interview
        design_review_completed = False
        if use_llm_interview and sys.stdout.isatty():
            typer.echo("\n" + "=" * 60)
            typer.echo("[QUESTION] Design Review Opportunity")
            typer.echo("=" * 60)
            typer.echo("\nThe initial project design has been generated.")
            typer.echo("You can now review it and conduct a second interview to:")
            typer.echo("  • Refine architectural decisions")
            typer.echo("  • Add missing requirements or constraints")
            typer.echo("  • Adjust technology choices")
            typer.echo("  • Clarify implementation details")
            
            try:
                conduct_design_review = typer.confirm(
                    "\nWould you like to conduct a design review interview?", default=False
                )
            except Exception:
                conduct_design_review = False

            if conduct_design_review:
                typer.echo("\n[ROBOT] Starting design review interview...")
                typer.echo("-" * 60)
                typer.echo("Review the generated design and provide feedback.")
                typer.echo("Type /done when you're finished with the review.\n")

                # Create a new interview manager for design review
                review_manager = LLMInterviewManager(
                    config=config,
                    verbose=verbose,
                    repo_analysis=repo_analysis,
                    markdown_output_manager=temp_markdown_mgr if use_llm_interview else None,
                    mode="design_review",
                )

                # Build rich design-review context
                try:
                    design_md = temp_markdown_mgr.load_stage_output("project_design")
                except Exception:
                    # Fallback to a simple markdown from the structured design
                    design_md = (
                        f"# Project Design: {design.project_name}\n\n{design.architecture_overview}\n"
                    )

                # Optional: placeholder values for future integration
                devplan_md = None
                review_md = None
                repo_summary_md = None

                review_manager.set_design_review_context(
                    design_md=design_md,
                    devplan_md=devplan_md,
                    review_md=review_md,
                    repo_summary_md=repo_summary_md,
                )

                try:
                    # Run design review interview
                    review_answers = review_manager.run()

                    if review_answers is not None:
                        typer.echo("\n[OK] Design review completed!")

                        feedback = review_manager.to_design_review_feedback()

                        # Merge feedback into design_inputs
                        if feedback.get("updated_requirements"):
                            inputs["requirements"] += (
                                "\n\n[Design Review Adjustments]\n"
                                + feedback["updated_requirements"].strip()
                            )

                        new_constraints = feedback.get("new_constraints") or []
                        if new_constraints:
                            constraint_block = "\n".join(f"- {c}" for c in new_constraints)
                            inputs["requirements"] += (
                                "\n\n[Additional Constraints from Design Review]\n"
                                + constraint_block
                            )

                        updated_stack = feedback.get("updated_tech_stack") or []
                        if updated_stack:
                            existing_langs = [
                                s.strip()
                                for s in (inputs.get("languages") or "").split(",")
                                if s.strip()
                            ]
                            for tech in updated_stack:
                                if tech not in existing_langs:
                                    existing_langs.append(tech)
                            inputs["languages"] = ",".join(existing_langs)

                        # Regenerate design with review feedback
                        typer.echo("\n[REFRESH] Regenerating design with review feedback...\n")
                        design_stream = StreamingHandler.create_console_handler(
                            prefix="[design-v2] "
                        )
                        design = asyncio.run(
                            orchestrator.project_design_gen.generate(
                                project_name=inputs["name"],
                                languages=inputs["languages"].split(","),
                                requirements=inputs["requirements"],
                                frameworks=inputs.get("frameworks", "").split(",")
                                if inputs.get("frameworks")
                                else None,
                                apis=inputs.get("apis", "").split(",")
                                if inputs.get("apis")
                                else None,
                                streaming_handler=design_stream,
                            )
                        )
                        typer.echo("\n[OK] Updated design generated with review feedback!")

                        # Save updated design - raw LLM response if available
                        if getattr(design, "raw_llm_response", None):
                            temp_markdown_mgr.save_stage_output(
                                "design_review", design.raw_llm_response
                            )
                            logger.info(
                                "Saved raw LLM review response "
                                f"({len(design.raw_llm_response)} chars)"
                            )
                        else:
                            # Fallback: reuse existing structured design save logic here
                            pass
                    else:
                        typer.echo(
                            "\n[NOTE] Design review cancelled, continuing with original design..."
                        )

                except Exception as e:
                    logger.warning(f"Design review interview failed: {e}")
                    typer.echo(f"\n[WARN] Design review failed: {e}", err=True, color=True)
                    typer.echo("Continuing with original design...")
            else:
                typer.echo(
                    "\n[OK] Skipping design review, continuing with original design..."
                )
        
        # For LLM interview mode, automatically continue through full pipeline
        if use_llm_interview:
            proceed = False
            try:
                if sys.stdout.isatty():
                    proceed = typer.confirm("Proceed to run full pipeline now? (DevPlan + Handoff)", default=False)
                else:
                    proceed = False
            except Exception:
                proceed = False
            if not proceed:
                typer.echo(
                    f"\n[IDEA] Next step: Run 'devussy generate-devplan {output_file}' to create the development plan"
                )
                return
            typer.echo("\n" + "=" * 60)
            typer.echo("[REFRESH] Continuing with full circular development pipeline...")
            typer.echo("=" * 60 + "\n")
            typer.echo("This will generate:")
            typer.echo("  1. [OK] Project Design (complete)")
            typer.echo("  2. Development Plan (devplan.md)")
            typer.echo("  3. Handoff Document (handoff_prompt.md)")
            typer.echo(f"\n[FOLDER] Output directory: {project_folder.resolve()}")
            typer.echo("\n[WAIT] Running full pipeline...\n")
            
            # Run only DevPlan + Handoff using the design we just created
            async def _run_devplan_and_handoff():
                detailed_devplan = await orchestrator.run_devplan_only(
                    project_design=design,
                    feedback_manager=None,
                )
                handoff = await orchestrator.run_handoff_only(
                    devplan=detailed_devplan,
                    project_name=inputs["name"],
                    project_summary=detailed_devplan.summary or "",
                    architecture_notes=design.architecture_overview or "",
                )
                return design, detailed_devplan, handoff

            # Temporarily reduce console log verbosity during user-facing pipeline output
            root_logger = logging.getLogger()
            console_handlers = [h for h in root_logger.handlers if isinstance(h, logging.StreamHandler)]
            old_levels = [h.level for h in console_handlers]
            try:
                for h in console_handlers:
                    h.setLevel(logging.WARNING)
                # Allow orchestrator to render streaming progress directly (no outer spinner)
                design_result, devplan_result, handoff_result = asyncio.run(_run_devplan_and_handoff())
            finally:
                for h, lvl in zip(console_handlers, old_levels):
                    h.setLevel(lvl)
            
            typer.echo("\n" + "=" * 60)
            typer.echo("[SAVE] Saving files to disk...")
            typer.echo("=" * 60)
            
            # EXPLICIT FILE WRITES - Force write all files directly
            try:
                from .file_manager import FileManager
                file_mgr = FileManager()
                
                # Write project design - COMPLETE VERSION
                design_content = f"# Project Design: {inputs['name']}\n\n"
                design_content += f"## Architecture Overview\n\n{design_result.architecture_overview}\n\n"
                
                design_content += "## Objectives\n\n"
                if design_result.objectives:
                    for obj in design_result.objectives:
                        design_content += f"- {obj}\n"
                else:
                    design_content += "No specific objectives defined.\n"
                
                design_content += "\n## Tech Stack\n\n"
                if design_result.tech_stack:
                    for tech in design_result.tech_stack:
                        design_content += f"- {tech}\n"
                else:
                    design_content += "No tech stack specified.\n"
                
                design_content += "\n## Dependencies\n\n"
                if design_result.dependencies:
                    for dep in design_result.dependencies:
                        design_content += f"- {dep}\n"
                else:
                    design_content += "No dependencies specified.\n"
                
                design_content += "\n## Challenges\n\n"
                if design_result.challenges:
                    for challenge in design_result.challenges:
                        design_content += f"- {challenge}\n"
                else:
                    design_content += "No challenges identified.\n"
                
                design_content += "\n## Mitigations\n\n"
                if design_result.mitigations:
                    for mitigation in design_result.mitigations:
                        design_content += f"- {mitigation}\n"
                else:
                    design_content += "No mitigations specified.\n"
                
                design_content += f"\n## Project Details\n\n"
                design_content += f"**Languages:** {', '.join(languages_list)}\n\n"
                design_content += f"**Requirements:** {inputs['requirements']}\n\n"
                if frameworks_list:
                    design_content += f"**Frameworks:** {', '.join(frameworks_list)}\n\n"
                if apis_list:
                    design_content += f"**APIs:** {', '.join(apis_list)}\n\n"
                
                design_path = project_folder / "project_design.md"
                file_mgr.write_markdown(str(design_path), design_content)
                typer.echo(f"  [OK] Wrote project_design.md ({design_path.stat().st_size} bytes)")
                
                # Write devplan - Use orchestrator's markdown converter
                devplan_content = orchestrator._devplan_to_markdown(devplan_result)
                
                devplan_path = project_folder / "devplan.md"
                file_mgr.write_markdown(str(devplan_path), devplan_content)
                typer.echo(f"  [OK] Wrote devplan.md dashboard ({devplan_path.stat().st_size} bytes)")
                
                # Generate individual phase files
                phase_files = orchestrator._generate_phase_files(devplan_result, str(project_folder))
                phase_paths = [Path(f) for f in phase_files]
                if phase_paths:
                    preview = phase_paths[0].name
                    if len(phase_paths) > 1:
                        preview = f"{phase_paths[0].name} … {phase_paths[-1].name}"
                    total_bytes = sum(p.stat().st_size for p in phase_paths if p.exists())
                    phase_label = "phase file" if len(phase_paths) == 1 else "phase files"
                    typer.echo(
                        render(
                            f"  [OK] Wrote {len(phase_paths)} {phase_label} ({preview}, {total_bytes:,} bytes total)"
                        )
                    )
                
                # Write handoff prompt
                handoff_path = project_folder / "handoff_prompt.md"
                file_mgr.write_markdown(str(handoff_path), handoff_result.content)
                typer.echo(f"  [OK] Wrote handoff_prompt.md ({handoff_path.stat().st_size} bytes)")
                
                typer.echo("\n[OK] All files written successfully!")
                typer.echo(f"\n[FOLDER] Project folder: {project_folder.resolve()}")
                typer.echo("\nVerifying files...")
                
                # Verify all files including phase files
                all_files = [design_path, devplan_path, handoff_path] + [Path(f) for f in phase_files]
                for file in all_files:
                    if file.exists():
                        typer.echo(f"  [OK] {file.name} - {file.stat().st_size} bytes")
                    else:
                        typer.echo(f"  [ERROR] {file.name} - MISSING!", err=True)
                
            except Exception as e:
                typer.echo(f"\n[WARN] Error writing files: {e}", err=True, color=True)
                logger.error(f"Failed to write files: {e}", exc_info=True)
                if debug:
                    import traceback
                    typer.echo(traceback.format_exc(), err=True)
                raise
            
            typer.echo("\n" + "=" * 60)
            typer.echo("[OK] Circular development pipeline complete!", color=True)
            typer.echo("=" * 60)
            
            # Build absolute paths for display using project folder
            design_file = project_folder / "project_design.md"
            devplan_file = project_folder / "devplan.md"
            handoff_file = project_folder / "handoff_prompt.md"
            
            # Verify files exist
            files_exist = {
                "design": design_file.exists(),
                "devplan": devplan_file.exists(),
                "handoff": handoff_file.exists()
            }
            
            typer.echo("\n[BOOKMARK] Generated files:")
            typer.echo(f"\n  [FILE] Project Design:")
            typer.echo(f"     {design_file}")
            if files_exist["design"]:
                typer.echo(f"     [OK] File written successfully ({design_file.stat().st_size} bytes)")
            
            typer.echo(f"\n  [DASHBOARD] Development Plan Dashboard:")
            typer.echo(f"     {devplan_file}")
            if files_exist["devplan"]:
                typer.echo(f"     [OK] Dashboard written successfully ({devplan_file.stat().st_size} bytes)")
                typer.echo(f"     [LIST] Individual phase files generated for implementation agents")
            
            typer.echo(f"\n  [SEND] Handoff Prompt:")
            typer.echo(f"     {handoff_file}")
            if files_exist["handoff"]:
                typer.echo(f"     [OK] File written successfully ({handoff_file.stat().st_size} bytes)")
            
            # List phase files if they exist
            phase_files = list(project_folder.glob("phase*.md"))
            if phase_files:
                typer.echo(f"\n  [ROCKET] Phase Files:")
                for phase_file in sorted(phase_files):
                    typer.echo(f"     {phase_file} [OK] ({phase_file.stat().st_size} bytes)")
            
            # Warning if any files are missing
            if not all(files_exist.values()):
                typer.echo("\n[WARN] Warning: Some files were not written to disk", err=True, color=True)
                typer.echo("\nDebug info:", err=True)
                typer.echo(f"  Project folder: {project_folder}", err=True)
                typer.echo(f"  Folder exists: {project_folder.exists()}", err=True)
                typer.echo(f"  Files in folder: {list(project_folder.glob('*.md'))}", err=True)
            else:
                typer.echo("\n[OK] All files verified and saved successfully!")
            
            typer.echo("\n" + "=" * 60)
            typer.echo("[IDEA] Next Steps:")
            typer.echo(f"   1. Review the devplan: {devplan_file}")
            typer.echo(f"   2. Open folder in explorer: {project_folder}")
            typer.echo("   3. Use these markdown files with other tools")
            typer.echo("   4. Begin Phase 0 implementation")
            typer.echo("=" * 60 + "\n")
        else:
            # Scripted mode: just suggest next step
            typer.echo(
                f"\n[IDEA] Next step: Run 'devussy generate-devplan {output_file}' to create the development plan"
            )

    except typer.Exit:
        raise
    except Exception as e:
        logger.error(f"Error in interactive design: {e}", exc_info=True)
        if debug:
            typer.echo("\nDebug traceback:", err=True)
            typer.echo(traceback.format_exc(), err=True)
        typer.echo(f"\n[ERROR] Error: {str(e)}", err=True, color=True)
        raise typer.Exit(code=1)


def _serialize_repo_analysis(analysis: RepoAnalysis) -> dict:
    """Convert RepoAnalysis dataclass into a JSON-safe dict."""
    return {
        "root_path": str(analysis.root_path),
        "project_type": analysis.project_type,
        "structure": {
            "directories": analysis.structure.directories,
            "files": analysis.structure.files,
            "source_dirs": analysis.structure.source_dirs,
            "test_dirs": analysis.structure.test_dirs,
            "config_dirs": analysis.structure.config_dirs,
            "ci_dirs": analysis.structure.ci_dirs,
        },
        "dependencies": {
            "manifests": [str(p) for p in analysis.dependencies.manifests],
            "python": analysis.dependencies.python,
            "node": analysis.dependencies.node,
            "go": analysis.dependencies.go,
            "rust": analysis.dependencies.rust,
            "java": analysis.dependencies.java,
        },
        "code_metrics": {
            "total_files": analysis.code_metrics.total_files,
            "total_lines": analysis.code_metrics.total_lines,
        },
        "patterns": {
            "test_frameworks": analysis.patterns.test_frameworks,
            "build_tools": analysis.patterns.build_tools,
        },
        "config_files": [str(p) for p in analysis.config_files.files],
        "errors": analysis.errors,
    }


@app.command()
def interview(
    directory: Annotated[
        str,
        typer.Argument(help="Project directory to analyze and interview"),
    ] = ".",
    output: Annotated[
        Optional[str],
        typer.Option("--output", help="Output path for generated devplan"),
    ] = None,
    config_path: Annotated[
        Optional[str], typer.Option("--config", help="Path to config file")
    ] = None,
    provider: Annotated[
        Optional[str], typer.Option("--provider", help="LLM provider override")
    ] = None,
    model: Annotated[
        Optional[str], typer.Option("--model", help="Model override")
    ] = None,
    select_model: Annotated[
        bool,
        typer.Option(
            "--select-model",
            help="Interactively choose a Requesty model for this run",
        ),
    ] = False,
    temperature: Annotated[
        Optional[float],
        typer.Option(
            "--temperature",
            help="Sampling temperature override",
            min=0.0,
            max=2.0,
        ),
    ] = None,
    max_tokens: Annotated[
        Optional[int],
        typer.Option(
            "--max-tokens",
            help="Maximum tokens to request from the model",
            min=1,
        ),
    ] = None,
    streaming: Annotated[
        bool, typer.Option("--streaming", help="Enable token streaming")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", help="Enable verbose logging")
    ] = False,
    debug: Annotated[
        bool, typer.Option("--debug", help="Enable debug mode")
    ] = False,
) -> None:
    """Interview an existing codebase to generate a context-aware devplan.
    
    This command analyzes your project directory, conducts an LLM-driven
    interview about your development goals, and generates a devplan that
    respects your existing patterns and architecture.
    
    Example:
        devussy interview .
        devussy interview /path/to/project --output devplan-interview.json
    """
    try:
        # Validate directory
        root = Path(directory).resolve()
        if not root.exists() or not root.is_dir():
            typer.echo(
                f"[ERROR] Error: Directory not found or not a directory: {root}",
                err=True,
                color=True,
            )
            raise typer.Exit(code=1)

        typer.echo("\n" + "=" * 60)
        typer.echo("[INTERVIEW] Devussy Interview Mode")
        typer.echo("=" * 60)
        typer.echo(f"\n[FOLDER] Analyzing: {root}\n")

        # Run the interactive design with LLM interview and repo analysis
        interactive_design(
            config_path=config_path,
            provider=provider,
            model=model,
            output_dir=str(root / "docs") if output is None else str(Path(output).parent),
            temperature=temperature,
            max_tokens=max_tokens,
            repo_dir=str(root),
            select_model=select_model,
            save_session=None,
            resume_session=None,
            llm_interview=True,
            scripted=False,
            streaming=streaming,
            verbose=verbose,
            debug=debug,
        )

        typer.echo("\n" + "=" * 60)
        typer.echo("[OK] Interview complete!")
        typer.echo("=" * 60 + "\n")

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(
            f"\n[ERROR] Error during interview: {e}",
            err=True,
            color=True,
        )
        logger.error(f"Error in interview command: {e}", exc_info=True)
        if debug:
            typer.echo("\nDebug traceback:", err=True)
            typer.echo(traceback.format_exc(), err=True)
        raise typer.Exit(code=1)


@app.command()
def analyze_repo(
    directory: Annotated[
        str,
        typer.Argument(help="Project directory to analyze"),
    ] = ".",
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Output analysis as JSON instead of a summary"),
    ] = False,
) -> None:
    """Analyze an existing project directory and print a summary or JSON."""
    try:
        root = Path(directory).resolve()
        if not root.exists() or not root.is_dir():
            typer.echo(
                f"Error: Directory not found or not a directory: {root}",
                err=True,
                color=True,
            )
            raise typer.Exit(code=1)

        analyzer = RepositoryAnalyzer(root)
        analysis = analyzer.analyze()

        if json_output:
            typer.echo(json.dumps(_serialize_repo_analysis(analysis), indent=2))
            return

        typer.echo("\n[FOLDER] Repository Analysis")
        typer.echo("=" * 60)
        typer.echo(f"Root: {analysis.root_path}")
        typer.echo(f"Project type: {analysis.project_type or 'unknown'}")
        typer.echo(
            f"Total files: {analysis.code_metrics.total_files}, "
            f"total lines: {analysis.code_metrics.total_lines}"
        )
        typer.echo("")

        if analysis.structure.directories:
            typer.echo("Top-level directories:")
            typer.echo("  " + ", ".join(sorted(analysis.structure.directories)))
        if analysis.structure.files:
            typer.echo("Top-level files:")
            typer.echo("  " + ", ".join(sorted(analysis.structure.files)))

        if analysis.dependencies.python or analysis.dependencies.node:
            typer.echo("")
            if analysis.dependencies.python:
                typer.echo(
                    "Python deps: " + ", ".join(sorted(analysis.dependencies.python))
                )
            if analysis.dependencies.node:
                typer.echo(
                    "Node deps: " + ", ".join(sorted(analysis.dependencies.node))
                )

        if analysis.patterns.test_frameworks or analysis.patterns.build_tools:
            typer.echo("")
            if analysis.patterns.test_frameworks:
                typer.echo(
                    "Test frameworks: "
                    + ", ".join(sorted(analysis.patterns.test_frameworks))
                )
            if analysis.patterns.build_tools:
                typer.echo(
                    "Build tools: " + ", ".join(sorted(analysis.patterns.build_tools))
                )

        if analysis.config_files.files:
            typer.echo("")
            typer.echo("Config files:")
            for path in analysis.config_files.files:
                typer.echo(f"  - {path}")

        if analysis.errors:
            typer.echo("")
            typer.echo("Warnings / errors:")
            for err in analysis.errors:
                typer.echo(f"  - {err}")

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(
            f"\n[ERROR] Error analyzing repository: {e}",
            err=True,
            color=True,
        )
        logger.error(f"Error in analyze_repo: {e}", exc_info=True)
        raise typer.Exit(code=1)


@app.command()
def launch(
    config_path: Annotated[Optional[str], typer.Option("--config", help="Path to config file")] = None,
    provider: Annotated[Optional[str], typer.Option("--provider", help="LLM provider override")] = None,
    model: Annotated[Optional[str], typer.Option("--model", help="Model override")] = None,
    output_dir: Annotated[Optional[str], typer.Option("--output-dir", help="Output directory")] = None,
    verbose: Annotated[bool, typer.Option("--verbose", help="Verbose logs")] = False,
) -> None:
    """Launch Devussy using the configured/default provider, then run the interview."""
    try:
        # Let _load_app_config resolve provider from config/.env unless overridden via --provider
        cfg = _load_app_config(config_path, provider, model, output_dir, verbose)

        # If the resolved provider is Requesty, ensure its API key is available
        resolved_provider = (cfg.llm.provider or "").lower()
        if resolved_provider == "requesty":
            try:
                _resolve_requesty_api_key(cfg)
            except Exception as e:
                typer.echo(f"\n[ERROR] Could not resolve Requesty API key: {e}", err=True, color=True)
                raise typer.Exit(code=1)

        # Run the LLM interview flow (same as interactive_design with defaults),
        # passing through the resolved provider so behavior matches configuration.
        interactive_design(
            config_path=config_path,
            provider=cfg.llm.provider,
            model=model,
            output_dir=output_dir,
            temperature=None,
            max_tokens=None,
            select_model=False,
            save_session=None,
            resume_session=None,
            llm_interview=True,
            scripted=False,
            streaming=False,
            verbose=verbose,
            debug=False,
        )

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"\n[ERROR] Error in launch: {str(e)}", err=True, color=True)
        logger.error(f"Error in launch: {e}", exc_info=True)
        raise typer.Exit(code=1)


@app.command()
def generate_terminal(
    devplan_file: Annotated[
        str, 
        typer.Argument(help="Path to devplan JSON file from interview or generation")
    ],
    config_path: Annotated[
        Optional[str], 
        typer.Option("--config", help="Path to config file")
    ] = None,
    provider: Annotated[
        Optional[str], 
        typer.Option("--provider", help="LLM provider override")
    ] = None,
    model: Annotated[
        Optional[str], 
        typer.Option("--model", help="Model override")
    ] = None,
    select_model: Annotated[
        bool,
        typer.Option("--select-model", help="Interactively choose a Requesty model for this run")
    ] = False,
    temperature: Annotated[
        Optional[float],
        typer.Option(
            "--temperature",
            help="Sampling temperature override for the active model",
            min=0.0,
            max=2.0,
        ),
    ] = None,
    max_tokens: Annotated[
        Optional[int],
        typer.Option(
            "--max-tokens",
            help="Maximum tokens to request from the model",
            min=1,
        ),
    ] = None,
    max_concurrent: Annotated[
        Optional[int],
        typer.Option("--max-concurrent", help="Maximum concurrent API requests")
    ] = None,
    output_dir: Annotated[
        Optional[str], 
        typer.Option("--output-dir", help="Output directory")
    ] = None,
    verbose: Annotated[
        bool, 
        typer.Option("--verbose", help="Enable verbose logging")
    ] = False,
    debug: Annotated[
        bool, 
        typer.Option("--debug", help="Enable debug mode with full tracebacks")
    ] = False,
) -> None:
    """Launch the terminal streaming UI for phase generation from a devplan."""
    try:
        # Load config
        config = _load_app_config(
            config_path,
            provider,
            model,
            output_dir,
            verbose,
            temperature,
            max_tokens,
        )

        if select_model:
            _select_requesty_model_interactively(config)

        if max_concurrent:
            config.max_concurrent_requests = max_concurrent

        # Validate devplan file
        if not devplan_file or not devplan_file.strip():
            typer.echo("Error: DevPlan file path is required", err=True, color=True)
            raise typer.Exit(code=1)

        devplan_path = Path(devplan_file)
        if not devplan_path.exists():
            typer.echo(
                f"Error: DevPlan file not found: {devplan_path.absolute()}",
                err=True,
                color=True,
            )
            raise typer.Exit(code=1)

        if not devplan_path.is_file():
            typer.echo(
                f"Error: Path is not a file: {devplan_path.absolute()}",
                err=True,
                color=True,
            )
            raise typer.Exit(code=1)

        # Load devplan
        with open(devplan_path, "r", encoding="utf-8") as f:
            devplan_data = json.load(f)
            devplan = DevPlan.model_validate(devplan_data)

        # Apply last-used preferences
        try:
            prefs = load_last_used_preferences()
            apply_settings_to_config(config, prefs)
        except Exception:
            pass

        # Create phase generator
        llm_client = create_llm_client(config)
        from .terminal.phase_state import PhaseStateManager
        state_manager = PhaseStateManager(["plan", "design", "implement", "test", "review"])
        phase_generator = TerminalPhaseGenerator(llm_client, state_manager)

        # Display startup info
        typer.echo("\n" + "=" * 60)
        typer.echo(f"[LOGO] Launching Devussy Terminal UI")
        typer.echo("=" * 60 + "\n")
        typer.echo(f"DevPlan: {devplan.summary[:50] if devplan.summary else 'Development Plan'}")
        typer.echo(f"Phases: {len(devplan.phases)} configured")
        typer.echo(f"Provider: {config.llm.provider}")
        typer.echo(f"Model: {config.llm.model}")
        typer.echo("\n[ROCKET] Starting terminal UI...\n")

        # Launch terminal UI
        run_terminal_ui(
            phase_names=["plan", "design", "implement", "test", "review"],
            phase_generator=phase_generator,
            devplan=devplan,
        )

    except json.JSONDecodeError as e:
        typer.echo(
            f"\n[ERROR] Error: Invalid JSON in devplan file: {str(e)}",
            err=True,
            color=True,
        )
        logger.error(f"JSON decode error: {e}", exc_info=True)
        if debug:
            typer.echo("\nDebug traceback:", err=True)
            typer.echo(traceback.format_exc(), err=True)
        raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"\n[ERROR] Error: {str(e)}", err=True, color=True)
        logger.error(f"Error in generate_terminal: {e}", exc_info=True)
        if debug:
            typer.echo("\nDebug traceback:", err=True)
            typer.echo(traceback.format_exc(), err=True)
        raise typer.Exit(code=1)


@app.command()
def interactive(
    config_path: Annotated[
        Optional[str], 
        typer.Option("--config", help="Path to config file")
    ] = None,
    provider: Annotated[
        Optional[str], 
        typer.Option("--provider", help="LLM provider override")
    ] = None,
    model: Annotated[
        Optional[str], 
        typer.Option("--model", help="Model override")
    ] = None,
    select_model: Annotated[
        bool,
        typer.Option("--select-model", help="Interactively choose a Requesty model for this run")
    ] = False,
    temperature: Annotated[
        Optional[float],
        typer.Option(
            "--temperature",
            help="Sampling temperature override for the active model",
            min=0.0,
            max=2.0,
        ),
    ] = None,
    max_tokens: Annotated[
        Optional[int],
        typer.Option(
            "--max-tokens",
            help="Maximum tokens to request from the model",
            min=1,
        ),
    ] = None,
    output_dir: Annotated[
        Optional[str], 
        typer.Option("--output-dir", help="Output directory")
    ] = None,
    verbose: Annotated[
        bool, 
        typer.Option("--verbose", help="Enable verbose logging")
    ] = False,
    debug: Annotated[
        bool, 
        typer.Option("--debug", help="Enable debug mode with full tracebacks")
    ] = False,
) -> None:
    """Launch interactive mode with real-time streaming in a single window.
    
    This command runs the complete interactive workflow in your current terminal:
    1. Interactive LLM-driven requirements gathering with streaming
    2. Real-time project design generation with streaming
    3. Real-time devplan generation with streaming  
    4. Real-time phase generation (plan, design, implement, test, review) with streaming in terminal UI
    Everything runs in terminal UI with full real-time token streaming.
    """
    async def run_interactive():
        try:
            # Load config
            config = _load_app_config(
                config_path,
                provider,
                model,
                output_dir,
                verbose,
                temperature,
                max_tokens,
            )

            if select_model:
                _select_requesty_model_interactively(config)

            # Apply last-used preferences
            try:
                prefs = load_last_used_preferences()
                apply_settings_to_config(config, prefs)
            except Exception:
                pass

            # Enable streaming for real-time feedback
            config.streaming_enabled = True
            
            print("[LOGO] DevUssY Interactive Mode - Single Window")
            print("=" * 50)
            print("Running everything in this terminal with real-time streaming...")
            print()
            
            # Create markdown output manager with initial timestamp-based directory
            # We'll rename it once we get the actual project name from the interview
            from datetime import datetime
            temp_project_name = f"interactive_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            markdown_output_mgr = MarkdownOutputManager(base_output_dir="outputs")
            run_dir = markdown_output_mgr.create_run_directory(temp_project_name)
            print(f"[NOTE] All outputs will be saved to: {run_dir}\n")
            
            # Step 1: Run interview with terminal UI
            print("[LIST] Step 1: Interactive Requirements Gathering")
            print("-" * 40)
            
            # Only analyze repository if repository tools are enabled
            repo_analysis = None
            try:
                prefs = load_last_used_preferences()
                repository_tools_enabled = getattr(prefs, 'repository_tools_enabled', False)
                
                if repository_tools_enabled:
                    from .interview import RepositoryAnalyzer
                    analyzer = RepositoryAnalyzer(Path.cwd())
                    repo_analysis = analyzer.analyze()
                    if repo_analysis:
                        print(f"[FOLDER] Analyzed repository: {repo_analysis.project_type}")
                elif verbose:
                    print("[NOTE] Repository tools disabled - skipping repository analysis")
            except Exception as e:
                logging.warning(f"Repository analysis failed: {e}")
            
            print("[ROCKET] Launching console-based interactive interview (fallback)...")
            print("You'll stay in this terminal while we gather project requirements.\n")

            # Run interview using the existing console-based LLMInterviewManager
            from .llm_interview import LLMInterviewManager

            interview_manager = LLMInterviewManager(
                config=config,
                verbose=verbose,
                repo_analysis=repo_analysis,
                markdown_output_manager=markdown_output_mgr,
            )

            # Run the (blocking) console interview in a background thread so
            # its internal asyncio.run() calls are not nested inside the
            # interactive command's event loop.
            answers = await asyncio.to_thread(interview_manager.run)
            if not answers:
                print("[ERROR] Interview was cancelled or failed.")
                return

            # Convert collected data to generate_design inputs
            interview_data = interview_manager.to_generate_design_inputs()

            print("[OK] Interview completed successfully!")
            
            # Rename markdown output manager's run directory now that we have project name
            if interview_data.get("name"):
                try:
                    run_dir = markdown_output_mgr.rename_run_directory(interview_data["name"])
                    print(f"[NOTE] Outputs relocated to: {run_dir}\n")
                    
                    # Save run metadata with actual project name
                    markdown_output_mgr.save_run_metadata({
                        "project_name": interview_data["name"],
                        "languages": interview_data.get("languages", ""),
                        "requirements": interview_data.get("requirements", ""),
                        "frameworks": interview_data.get("frameworks", ""),
                        "apis": interview_data.get("apis", ""),
                        "provider": config.llm.provider,
                        "model": config.llm.model,
                    })
                except Exception as e:
                    logger.warning(f"Failed to rename markdown output directory: {e}")
            
            # Continue with full pipeline automatically
            print("\n" + "=" * 60)
            print("[REFRESH] Continuing with full circular development pipeline...")
            print("=" * 60 + "\n")
            print("This will generate:")
            print("  1. Project Design")
            print("  2. Development Plan (devplan.md)")
            print("  3. Individual Phase Files")
            print("  4. Handoff Document")
            print(f"\n[FOLDER] Output directory: {Path.cwd()}")
            print("\n[WAIT] Running full pipeline...\n")
            
            # Step 2: Generate design with streaming
            print("\n[TARGET] Step 2: Project Design Generation")
            print("-" * 40)
            
            # Convert to design inputs
            design_inputs = interview_data
            
            # Create orchestrator with repo analysis, code samples, and markdown output manager
            code_samples = design_inputs.get("code_samples")
            orchestrator = _create_orchestrator(
                config, 
                repo_analysis=repo_analysis, 
                code_samples=code_samples,
                markdown_output_manager=markdown_output_mgr
            )
            
            print("[STREAM] Generating project design with real-time streaming...\n")
            design_stream = StreamingHandler.create_console_handler(prefix="[design] ")
            design = await orchestrator.project_design_gen.generate(
                project_name=design_inputs["name"],
                languages=design_inputs["languages"].split(","),
                requirements=design_inputs["requirements"],
                frameworks=design_inputs.get("frameworks", "").split(",") if design_inputs.get("frameworks") else None,
                apis=design_inputs.get("apis", "").split(",") if design_inputs.get("apis") else None,
                streaming_handler=design_stream,
            )
            print("\n[OK] Project design generated!")
            
            # Save project design to markdown output manager - RAW LLM RESPONSE
            if design.raw_llm_response:
                # Save the full raw markdown response from the LLM
                markdown_output_mgr.save_stage_output("project_design", design.raw_llm_response)
                logger.info(f"Saved raw LLM design response ({len(design.raw_llm_response)} chars)")
            else:
                # Fallback to structured format if raw response not available
                design_content = f"""## Architecture Overview

{design.architecture_overview}

## Objectives

"""
                if design.objectives:
                    for obj in design.objectives:
                        design_content += f"- {obj}\n"
                else:
                    design_content += "No specific objectives defined.\n"
                
                design_content += "\n## Tech Stack\n\n"
                if design.tech_stack:
                    for tech in design.tech_stack:
                        design_content += f"- {tech}\n"
                else:
                    design_content += "No tech stack specified.\n"
                
                design_content += "\n## Dependencies\n\n"
                if design.dependencies:
                    for dep in design.dependencies:
                        design_content += f"- {dep}\n"
                else:
                    design_content += "No dependencies specified.\n"
                
                design_content += "\n## Challenges\n\n"
                if design.challenges:
                    for challenge in design.challenges:
                        design_content += f"- {challenge}\n"
                else:
                    design_content += "No challenges identified.\n"
                
                design_content += "\n## Mitigations\n\n"
                if design.mitigations:
                    for mitigation in design.mitigations:
                        design_content += f"- {mitigation}\n"
                else:
                    design_content += "No mitigations specified.\n"
                
                design_content += f"\n## Project Details\n\n"
                design_content += f"**Project Name:** {design.project_name}\n\n"
                design_content += f"**Languages:** {design_inputs['languages']}\n\n"
                design_content += f"**Requirements:** {design_inputs['requirements']}\n\n"
                if design_inputs.get("frameworks"):
                    design_content += f"**Frameworks:** {design_inputs['frameworks']}\n\n"
                if design_inputs.get("apis"):
                    design_content += f"**APIs:** {design_inputs['apis']}\n\n"
                
                markdown_output_mgr.save_stage_output("project_design", design_content)
                logger.warning("Raw LLM response not available, saved structured format")
            
            # Ask if user wants to conduct a second interview about the project design
            print("\n" + "=" * 60)
            print("[QUESTION] Design Review Opportunity")
            print("=" * 60)
            print("\nThe initial project design has been generated.")
            print("You can now review it and conduct a second interview to:")
            print("  • Refine architectural decisions")
            print("  • Add missing requirements or constraints")
            print("  • Adjust technology choices")
            print("  • Clarify implementation details")
            print("\nWould you like to conduct a design review interview?")

            conduct_design_review = input("\nEnter 'yes' to review, or press Enter to continue: ").strip().lower()

            if conduct_design_review in ["yes", "y"]:
                print("\n[ROBOT] Starting design review interview...")
                print("-" * 60)
                print("Review the generated design and provide feedback.")
                print("Type /done when you're finished with the review.\n")

                # Create a new interview manager for design review
                review_manager = LLMInterviewManager(
                    config=config,
                    verbose=verbose,
                    repo_analysis=repo_analysis,
                    markdown_output_manager=markdown_output_mgr,
                    mode="design_review",
                )

                # Build rich design-review context
                try:
                    design_md = markdown_output_mgr.save_stage_output  # placeholder to satisfy type checkers
                except Exception:
                    design_md = None

                try:
                    design_md = markdown_output_mgr.load_stage_output("project_design")
                except Exception:
                    # Fallback to a simple markdown from the structured design
                    design_md = (
                        f"# Project Design: {design.project_name}\n\n{design.architecture_overview}\n"
                    )

                # Optional: placeholder values for future integration
                devplan_md = None
                review_md = None
                repo_summary_md = None

                review_manager.set_design_review_context(
                    design_md=design_md,
                    devplan_md=devplan_md,
                    review_md=review_md,
                    repo_summary_md=repo_summary_md,
                )

                try:
                    # Run design review interview
                    review_answers = await asyncio.to_thread(review_manager.run)

                    if review_answers is not None:
                        print("\n[OK] Design review completed!")

                        feedback = review_manager.to_design_review_feedback()

                        # Merge feedback into design_inputs
                        if feedback.get("updated_requirements"):
                            design_inputs["requirements"] += (
                                "\n\n[Design Review Adjustments]\n"
                                + feedback["updated_requirements"].strip()
                            )

                        new_constraints = feedback.get("new_constraints") or []
                        if new_constraints:
                            constraint_block = "\n".join(f"- {c}" for c in new_constraints)
                            design_inputs["requirements"] += (
                                "\n\n[Additional Constraints from Design Review]\n"
                                + constraint_block
                            )

                        updated_stack = feedback.get("updated_tech_stack") or []
                        if updated_stack:
                            existing_langs = [
                                s.strip()
                                for s in (design_inputs.get("languages") or "").split(",")
                                if s.strip()
                            ]
                            for tech in updated_stack:
                                if tech not in existing_langs:
                                    existing_langs.append(tech)
                            design_inputs["languages"] = ",".join(existing_langs)

                        # Regenerate design with review feedback
                        print("\n[REFRESH] Regenerating design with review feedback...\n")
                        design_stream = StreamingHandler.create_console_handler(
                            prefix="[design-v2] "
                        )
                        design = await orchestrator.project_design_gen.generate(
                            project_name=design_inputs["name"],
                            languages=design_inputs["languages"].split(","),
                            requirements=design_inputs["requirements"],
                            frameworks=design_inputs.get("frameworks", "").split(",")
                            if design_inputs.get("frameworks")
                            else None,
                            apis=design_inputs.get("apis", "").split(",")
                            if design_inputs.get("apis")
                            else None,
                            streaming_handler=design_stream,
                        )
                        print("\n[OK] Updated design generated with review feedback!")

                        # Save updated design - raw LLM response if available
                        if getattr(design, "raw_llm_response", None):
                            markdown_output_mgr.save_stage_output(
                                "design_review", design.raw_llm_response
                            )
                            logger.info(
                                "Saved raw LLM review response "
                                f"({len(design.raw_llm_response)} chars)"
                            )
                        else:
                            # Fallback: reuse existing structured design save logic here
                            pass
                    else:
                        print(
                            "\n[NOTE] Design review cancelled, continuing with original design..."
                        )

                except Exception as e:
                    logger.warning(f"Design review interview failed: {e}")
                    print(f"\n[WARN] Design review failed: {e}")
                    print("Continuing with original design...")
            else:
                print("\n[OK] Skipping design review, continuing with original design...")
            
            # Step 3: Generate devplan with streaming
            print("\n[LIST] Step 3: Development Plan Generation")
            print("-" * 40)
            
            print("[LIST] Creating complete development plan with real-time streaming...\n")
            devplan_stream = StreamingHandler.create_console_handler(prefix="[devplan] ")
            
            # Run complete devplan generation including individual phase files
            detailed_devplan = await orchestrator.run_devplan_only(
                project_design=design,
                feedback_manager=None,
                streaming_handler=devplan_stream,
            )
            
            print("\n[OK] Development plan generated!")
            
            # DEBUG: Check if we have raw_basic_response
            print(f"[DEBUG] detailed_devplan type: {type(detailed_devplan)}")
            print(f"[DEBUG] Has raw_basic_response: {hasattr(detailed_devplan, 'raw_basic_response')}")
            if hasattr(detailed_devplan, 'raw_basic_response'):
                print(f"[DEBUG] raw_basic_response length: {len(detailed_devplan.raw_basic_response) if detailed_devplan.raw_basic_response else 0}")
            
            # Save devplan to markdown output manager - RAW LLM RESPONSES
            if hasattr(detailed_devplan, 'raw_basic_response') and detailed_devplan.raw_basic_response:
                # Save the basic devplan raw response
                markdown_output_mgr.save_stage_output("basic_devplan", detailed_devplan.raw_basic_response)
                print(f"[SAVE] Saved basic devplan to archive ({len(detailed_devplan.raw_basic_response)} chars)")
                logger.info(f"Saved raw basic devplan response ({len(detailed_devplan.raw_basic_response)} chars)")
            else:
                print("[WARN] No raw basic devplan response available")
            
            # Save the full detailed devplan markdown (converted from structured model)
            devplan_content = orchestrator._devplan_to_markdown(detailed_devplan)
            markdown_output_mgr.save_stage_output("detailed_devplan", devplan_content)
            print(f"[SAVE] Saved detailed devplan to archive ({len(devplan_content)} chars)")
            logger.info(f"Saved detailed devplan markdown ({len(devplan_content)} chars)")
            
            # Step 4: Generate handoff document
            print("\n[SEND] Step 4: Handoff Document Generation")
            print("-" * 40)
            
            print("[SEND] Creating handoff document with real-time streaming...\n")
            handoff_stream = StreamingHandler.create_console_handler(prefix="[handoff] ")
            handoff = await orchestrator.run_handoff_only(
                devplan=detailed_devplan,
                project_name=design_inputs["name"],
                project_summary=detailed_devplan.summary or "",
                architecture_notes=design.architecture_overview or "",
                streaming_handler=handoff_stream,
            )
            
            print("\n[OK] Handoff document generated!")
            
            # Save handoff to markdown output manager
            markdown_output_mgr.save_stage_output("handoff_prompt", handoff.content)
            
            # Save all results to disk in the generated output folder (NOT project root)
            print("\n" + "=" * 60)
            print("[SAVE] Saving files to output directory...")
            print("=" * 60)
            
            # Use the run_dir (generated output folder) instead of current directory
            output_path = Path(output_dir) if output_dir else Path(run_dir)
            print(f"[FOLDER] Output directory: {output_path.resolve()}\n")
            
            try:
                from .file_manager import FileManager
                file_mgr = FileManager()
                
                # Write project design - RAW LLM RESPONSE (with fallback to structured)
                if design.raw_llm_response:
                    # Use the full raw markdown from LLM
                    design_content = f"# Project Design: {design_inputs['name']}\n\n{design.raw_llm_response}"
                else:
                    # Fallback to structured format
                    design_content = f"# Project Design: {design_inputs['name']}\n\n"
                    design_content += f"## Architecture Overview\n\n{design.architecture_overview}\n\n"
                    
                    design_content += "## Objectives\n\n"
                    if design.objectives:
                        for obj in design.objectives:
                            design_content += f"- {obj}\n"
                    else:
                        design_content += "No specific objectives defined.\n"
                    
                    design_content += "\n## Tech Stack\n\n"
                    if design.tech_stack:
                        for tech in design.tech_stack:
                            design_content += f"- {tech}\n"
                    else:
                        design_content += "No tech stack specified.\n"
                    
                    design_content += "\n## Dependencies\n\n"
                    if design.dependencies:
                        for dep in design.dependencies:
                            design_content += f"- {dep}\n"
                    else:
                        design_content += "No dependencies specified.\n"
                    
                    design_content += "\n## Challenges\n\n"
                    if design.challenges:
                        for challenge in design.challenges:
                            design_content += f"- {challenge}\n"
                    else:
                        design_content += "No challenges identified.\n"
                    
                    design_content += "\n## Mitigations\n\n"
                    if design.mitigations:
                        for mitigation in design.mitigations:
                            design_content += f"- {mitigation}\n"
                    else:
                        design_content += "No mitigations specified.\n"
                    
                    design_content += f"\n## Project Details\n\n"
                    design_content += f"**Languages:** {design_inputs['languages']}\n\n"
                    design_content += f"**Requirements:** {design_inputs['requirements']}\n\n"
                    if design_inputs.get("frameworks"):
                        design_content += f"**Frameworks:** {design_inputs['frameworks']}\n\n"
                    if design_inputs.get("apis"):
                        design_content += f"**APIs:** {design_inputs['apis']}\n\n"
                
                design_path = output_path / "project_design.md"
                file_mgr.write_markdown(str(design_path), design_content)
                print(f"  [OK] Wrote project_design.md ({design_path.stat().st_size} bytes)")
                
                # Write devplan dashboard (structured with phase pointers)
                devplan_content = orchestrator._devplan_to_markdown(detailed_devplan)
                devplan_path = output_path / "devplan.md"
                file_mgr.write_markdown(str(devplan_path), devplan_content)
                print(f"  [OK] Wrote devplan.md dashboard ({devplan_path.stat().st_size} bytes)")
                
                # Write raw devplan from LLM (full detailed text as it came from the API)
                # Debug: Check what attributes the devplan has
                if hasattr(detailed_devplan, 'raw_basic_response'):
                    if detailed_devplan.raw_basic_response:
                        raw_devplan_path = output_path / "devplan_raw.md"
                        file_mgr.write_markdown(str(raw_devplan_path), detailed_devplan.raw_basic_response)
                        print(f"  [OK] Wrote devplan_raw.md (full LLM response, {raw_devplan_path.stat().st_size} bytes)")
                    else:
                        print(f"  [WARN] devplan.raw_basic_response exists but is None or empty")
                        logger.warning("raw_basic_response attribute exists but has no value")
                else:
                    print(f"  [WARN] devplan object does not have raw_basic_response attribute")
                    logger.warning(f"DevPlan attributes: {[attr for attr in dir(detailed_devplan) if not attr.startswith('_')]}")
                
                # Generate individual phase files (also saves to markdown output manager via orchestrator)
                phase_files = orchestrator._generate_phase_files(detailed_devplan, str(output_path))
                phase_paths = [Path(f) for f in phase_files]
                if phase_paths:
                    preview = phase_paths[0].name
                    if len(phase_paths) > 1:
                        preview = f"{phase_paths[0].name} … {phase_paths[-1].name}"
                    total_bytes = sum(p.stat().st_size for p in phase_paths if p.exists())
                    phase_label = "phase file" if len(phase_paths) == 1 else "phase files"
                    print(
                        render(
                            f"  [OK] Wrote {len(phase_paths)} {phase_label} ({preview}, {total_bytes:,} bytes total)"
                        )
                    )
                
                # Write handoff prompt
                handoff_path = output_path / "handoff_prompt.md"
                file_mgr.write_markdown(str(handoff_path), handoff.content)
                print(f"  [OK] Wrote handoff_prompt.md ({handoff_path.stat().st_size} bytes)")
                
                print("\n[OK] All files written successfully!")
                print(f"\n[FOLDER] All outputs saved to: {output_path.resolve()}")
                
            except Exception as e:
                print(f"\n[WARN] Error writing files: {e}")
                logger.error(f"Error writing files: {e}", exc_info=True)
                # Fallback: save devplan as JSON
                devplan_file = output_path / "devplan.json"
                with open(devplan_file, 'w', encoding='utf-8') as f:
                    json.dump(detailed_devplan.model_dump(), f, indent=2)
                print(f"  [FILE] Saved devplan as JSON: {devplan_file}")
            
            print("\n" + "=" * 60)
            print("[OK] Interactive mode completed successfully!")
            print("=" * 60)
            
            # Summary of generated files
            print(f"\n[BOOKMARK] Generated files in: {output_path.resolve()}")
            print(f"\n  [FILE] Project Design: project_design.md")
            print(f"  [DASHBOARD] Development Plan Dashboard: devplan.md (structured with phase links)")
            print(f"  [FILE] Raw DevPlan: devplan_raw.md (full LLM response as generated)")
            print(f"  [ROCKET] Individual Phase Files: phase1.md, phase2.md, etc.")
            print(f"  [SEND] Handoff Document: handoff_prompt.md")
            
            print(f"\n[FOLDER] Output Directory: {output_path.resolve()}")
            print("   - All generated files (design, devplan, phases, handoff)")
            print("   - Ready to review and implement")
            
            print("\n[IDEA] Next Steps:")
            print("   1. Review the devplan: devplan.md")
            print("   2. Check devplan_raw.md for full LLM details")
            print("   3. Start implementing Phase 1")
            print("   4. Use individual phase files for focused work")
            print("=" * 60 + "\n")
            
        except typer.Exit:
            raise
        except Exception as e:
            logger.error(f"Error in interactive mode: {e}", exc_info=True)
            if debug:
                typer.echo("\nDebug traceback:", err=True)
                typer.echo(traceback.format_exc(), err=True)
            typer.echo(f"\n[ERROR] Error: {str(e)}", err=True, color=True)
            raise typer.Exit(code=1)
    
    # Run the async function
    asyncio.run(run_interactive())


@app.command()
def version() -> None:
    """Show version information."""
    typer.echo(f"DevPlan Orchestrator v{__version__}")


def main() -> None:
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
