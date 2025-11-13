"""Command-line interface for DevPlan Orchestrator."""

from __future__ import annotations

import asyncio
import json
import os
import traceback
from pathlib import Path
from typing import Optional
import sys
import time
import logging

import typer
from typing_extensions import Annotated

from .__version__ import __version__
from .clients.factory import create_llm_client
from .concurrency import ConcurrencyManager
from .config import AppConfig, load_config
from .feedback_manager import FeedbackManager
from .file_manager import FileManager
from .logger import get_logger, setup_logging
from .models import DevPlan, ProjectDesign
from .pipeline.compose import PipelineOrchestrator
from .progress_reporter import PipelineProgressReporter
from .state_manager import StateManager
from .ui.menu import run_main_menu, run_menu, SessionSettings, apply_settings_to_config, load_last_used_preferences

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
    except Exception:
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
        "Created by Kyle Durepos (SLOPTIMUS PRIME)", style="bold yellow", justify="center"
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
        title="🎼 DEVUSSY",
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

    typer.echo("\n⚠️  Requesty API key not found in config or environment.")
    if not typer.confirm("Would you like to enter a Requesty API key now?", default=True):
        typer.echo(
            "❌ Requesty model selection requires an API key. Aborting.",
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
            f"\nℹ️  Active provider is '{provider}'. Switching to Requesty for this run."
        )
        config.llm.provider = "requesty"

    base_url = (
        getattr(config.llm, "base_url", None)
        or os.getenv("REQUESTY_BASE_URL")
        or "https://router.requesty.ai/v1"
    )

    api_key = _resolve_requesty_api_key(config)

    typer.echo("\n🔄 Fetching available Requesty models...\n")
    try:
        models = asyncio.run(_fetch_requesty_models(api_key, base_url))
    except Exception as exc:  # noqa: BLE001
        typer.echo(f"❌ Failed to retrieve Requesty models: {exc}", err=True, color=True)
        raise typer.Exit(code=1)

    if not models:
        typer.echo(
            "❌ Requesty returned no models. Please verify your credentials.",
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

    typer.echo(f"\n✅ Selected Requesty model: {selected}\n")
    return selected


def _load_app_config(
    config_path: Optional[str],
    provider: Optional[str],
    model: Optional[str],
    output_dir: Optional[str],
    verbose: bool,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> AppConfig:
    """Load configuration with CLI overrides.

    Args:
        config_path: Path to config file
        provider: LLM provider override
        model: Model override
        output_dir: Output directory override
        verbose: Enable verbose logging

    Returns:
        AppConfig: Configured application config
    """
    # Load base config
    try:
        config = load_config(config_path)
    except FileNotFoundError:
        typer.echo(
            "Warning: Config file not found, using defaults", err=True, color=True
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

    # Setup logging
    setup_logging(config.log_level, str(config.log_file), config.log_format)

    return config


def _create_orchestrator(config: AppConfig) -> PipelineOrchestrator:
    """Create a pipeline orchestrator from config.

    Args:
        config: Application configuration

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
        typer.echo(f"🚀 Generating project design for: {project_name}")
        typer.echo("=" * 60 + "\n")
        typer.echo(f"Languages: {', '.join(languages_list)}")
        if frameworks_list:
            typer.echo(f"Frameworks: {', '.join(frameworks_list)}")
        if apis_list:
            typer.echo(f"APIs: {', '.join(apis_list)}")
        typer.echo("\n⏳ Generating design (this may take a moment)...\n")

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
        typer.echo("\n📋 Project Design Summary:")
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

        typer.echo(f"✓ Project design saved to: {output_file}", color=True)
        logger.info(f"Project design saved to: {output_file}")

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"\n❌ Error: {str(e)}", err=True, color=True)
        logger.error(f"Error generating project design: {e}", exc_info=True)
        if debug:
            typer.echo("\nDebug traceback:", err=True)
            typer.echo(traceback.format_exc(), err=True)
        raise typer.Exit(code=1)


@app.command()
def generate_devplan(
    design_file: Annotated[
        str, typer.Argument(help="Path to project design JSON file")
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
            design_data = json.load(f)
            design = ProjectDesign.model_validate(design_data)

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
                    f"\n📝 Loaded feedback: {total_corr} corrections, "
                    f"{total_edits} manual edits"
                )

        # Run devplan generation
        typer.echo("\n" + "=" * 60)
        typer.echo(f"📝 Generating development plan for: {design.project_name}")
        typer.echo("=" * 60 + "\n")
        typer.echo("⏳ Step 1/2: Generating basic devplan structure...")

        logger.info(f"Generating devplan from: {design_file}")

        devplan = asyncio.run(
            orchestrator.run_devplan_only(
                design,
                feedback_manager=feedback_manager,
                pre_review=pre_review,
            )
        )

        # Display intermediate results
        typer.echo("✓ Basic structure complete")
        typer.echo("⏳ Step 2/2: Generating detailed steps...")
        typer.echo("\n📊 DevPlan Summary:")
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
            typer.echo(f"✓ DevPlan saved to: {output_file}", color=True)
            logger.info(f"DevPlan saved to: {output_file}")
        else:
            typer.echo(f"⚠️  DevPlan content failed validation; wrote candidate to: {written_path}", err=True, color=True)
            logger.warning(f"DevPlan write redirected to tmp: {written_path}")

    except typer.Exit:
        raise
    except json.JSONDecodeError as e:
        typer.echo(
            f"\n❌ Error: Invalid JSON in design file: {str(e)}",
            err=True,
            color=True,
        )
        logger.error(f"JSON decode error: {e}", exc_info=True)
        if debug:
            typer.echo("\nDebug traceback:", err=True)
            typer.echo(traceback.format_exc(), err=True)
        raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"\n❌ Error: {str(e)}", err=True, color=True)
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
        typer.echo(f"📤 Generating handoff prompt for: {project_name}")
        typer.echo("=" * 60 + "\n")
        typer.echo("⏳ Creating handoff document...\n")

        logger.info(f"Generating handoff prompt from: {devplan_file}")

        handoff = asyncio.run(orchestrator.run_handoff_only(devplan, project_name))

        # Display intermediate results
        typer.echo("\n✓ Handoff prompt generated")
        if handoff.next_steps:
            typer.echo(f"Next steps: {len(handoff.next_steps)} defined\n")

        # Save output
        output_file = output_path or str(config.output_dir / "handoff_prompt.md")
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(handoff.content)

        typer.echo(f"✓ Handoff prompt saved to: {output_file}", color=True)
        logger.info(f"Handoff prompt saved to: {output_file}")

    except typer.Exit:
        raise
    except json.JSONDecodeError as e:
        typer.echo(
            f"\n❌ Error: Invalid JSON in devplan file: {str(e)}",
            err=True,
            color=True,
        )
        logger.error(f"JSON decode error: {e}", exc_info=True)
        if debug:
            typer.echo("\nDebug traceback:", err=True)
            typer.echo(traceback.format_exc(), err=True)
        raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"\n❌ Error: {str(e)}", err=True, color=True)
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
                    f"\n📝 Loaded feedback: {total_corr} corrections, "
                    f"{total_edits} manual edits"
                )

        # Ensure output directory exists
        config.output_dir.mkdir(parents=True, exist_ok=True)

        # Handle checkpoint resumption
        if resume_from:
            typer.echo("\n" + "=" * 60)
            typer.echo(f"🔄 Resuming pipeline from checkpoint: {resume_from}")
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
                typer.echo(f"\n❌ Error: {str(e)}", err=True, color=True)
                typer.echo(
                    "\n💡 Tip: Use 'devussy list-checkpoints' to see "
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
        typer.echo("\n\n⚠️ Pipeline interrupted by user", err=True, color=True)
        logger.warning("Pipeline interrupted by user")
        raise typer.Exit(code=130)
    except Exception as e:
        typer.echo(f"\n❌ Error: {str(e)}", err=True, color=True)
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
        typer.echo("🚀 Initializing DevPlan Orchestrator repository")
        typer.echo("=" * 60 + "\n")
        typer.echo(f"Target directory: {target_path}\n")

        # Check if directory exists
        if not target_path.exists():
            typer.echo(f"Creating directory: {target_path}")
            target_path.mkdir(parents=True, exist_ok=True)

        # Check if directory is empty
        if list(target_path.iterdir()) and not force:
            typer.echo(
                "\n⚠️  Error: Directory is not empty. "
                "Use --force to initialize anyway.",
                err=True,
                color=True,
            )
            raise typer.Exit(code=1)

        # Initialize Git repository
        typer.echo("⏳ Initializing Git repository...")
        result = subprocess.run(
            ["git", "init"],
            cwd=target_path,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            typer.echo(
                f"\n⚠️  Warning: Failed to initialize Git: {result.stderr}",
                err=True,
            )
        else:
            typer.echo("✓ Git repository initialized")

        # Create .gitignore
        typer.echo("⏳ Creating .gitignore...")
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
        typer.echo("✓ Created .gitignore")

        # Create README.md
        typer.echo("⏳ Creating README.md...")
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
        typer.echo("✓ Created README.md")

        # Create config directory and config.yaml
        typer.echo("⏳ Creating config directory...")
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
        typer.echo("✓ Created config/config.yaml")

        # Create .env.example
        typer.echo("⏳ Creating .env.example...")
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
        typer.echo("✓ Created .env.example")

        # Create docs directory
        typer.echo("⏳ Creating docs directory...")
        docs_dir = target_path / "docs"
        docs_dir.mkdir(exist_ok=True)
        (docs_dir / ".gitkeep").write_text("")
        typer.echo("✓ Created docs/ directory")

        # Add remote if specified
        if remote:
            typer.echo(f"\n⏳ Adding remote: {remote}")
            result = subprocess.run(
                ["git", "remote", "add", "origin", remote],
                cwd=target_path,
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                typer.echo(
                    f"⚠️  Warning: Failed to add remote: {result.stderr}", err=True
                )
            else:
                typer.echo("✓ Remote added")

        # Initial commit
        if result.returncode == 0:  # Only if git init succeeded
            typer.echo("\n⏳ Creating initial commit...")
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
            typer.echo("✓ Initial commit created")

        # Success message
        typer.echo("\n" + "=" * 60)
        typer.echo("✓ Repository initialized successfully!", color=True)
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
        typer.echo(f"\n❌ Error: {str(e)}", err=True, color=True)
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
            typer.echo("\nℹ️  No checkpoints found", color=True)
            typer.echo(
                "💡 Checkpoints are created automatically when running pipelines\n"
            )
            return

        typer.echo(f"\n📦 Found {len(checkpoints)} checkpoint(s):\n")

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

            typer.echo(f"🔖 {key}")
            typer.echo(f"   Stage: {stage}")
            typer.echo(f"   Created: {time_str}")

            if verbose:
                typer.echo(f"   File: {checkpoint['file']}")

            typer.echo("")

    except Exception as e:
        typer.echo(f"\n❌ Error listing checkpoints: {str(e)}", err=True, color=True)
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
                f"\n❌ Checkpoint not found: {checkpoint_key}", err=True, color=True
            )
            typer.echo(
                "💡 Use 'devussy list-checkpoints' to see available checkpoints\n"
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

        typer.echo(f"\n🔖 Found checkpoint: {checkpoint_key}")
        typer.echo(f"   Stage: {stage}")
        typer.echo(f"   Created: {time_str}")

        # Confirm deletion unless --force is used
        if not force:
            confirmed = typer.confirm(
                "\nAre you sure you want to delete this checkpoint?"
            )
            if not confirmed:
                typer.echo("\n❌ Deletion cancelled", color=True)
                return

        # Delete the checkpoint
        state_manager.delete_checkpoint(checkpoint_key)
        typer.echo(f"\n✅ Deleted checkpoint: {checkpoint_key}", color=True)

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"\n❌ Error deleting checkpoint: {str(e)}", err=True, color=True)
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
            typer.echo("\nℹ️  No checkpoints found to clean up", color=True)
            return

        typer.echo(
            f"\n🧹 Cleaning up checkpoints (keeping {keep_latest} latest per project)"
        )
        typer.echo(f"   Current checkpoints: {checkpoints_before}")

        # Confirm cleanup unless --force is used
        if not force:
            confirmed = typer.confirm("\nProceed with cleanup?")
            if not confirmed:
                typer.echo("\n❌ Cleanup cancelled", color=True)
                return

        # Perform cleanup
        state_manager.cleanup_old_checkpoints(keep_latest=keep_latest)

        # Get checkpoint count after cleanup
        checkpoints_after = len(state_manager.list_checkpoints())
        deleted_count = checkpoints_before - checkpoints_after

        typer.echo("\n✅ Cleanup complete!")
        typer.echo(f"   Deleted: {deleted_count} checkpoints")
        typer.echo(f"   Remaining: {checkpoints_after} checkpoints", color=True)

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"\n❌ Error during cleanup: {str(e)}", err=True, color=True)
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

        # Determine interview mode
        use_llm_interview = llm_interview and not scripted
        
        if use_llm_interview:
            typer.echo("🤖 Using LLM-driven conversational interview")
            if verbose:
                typer.echo("🔍 Verbose mode enabled")
            # Import LLM interview manager
            from .llm_interview import LLMInterviewManager
            interview_manager = LLMInterviewManager(config, verbose=verbose)
            typer.echo(f"📝 Logging to: {interview_manager.log_file}")
        else:
            typer.echo("📝 Using scripted questionnaire")
            # Setup interactive questionnaire
            questions_path = Path("config/questions.yaml")
            if not questions_path.exists():
                typer.echo(
                    f"❌ Error: Questions config not found at {questions_path}",
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
        typer.echo("\n🔑 Checking API key configuration...")
        
        missing_keys = []
        design_config = config.get_llm_config_for_stage("design")
        if not design_config.api_key:
            missing_keys.append("design")
        
        if missing_keys:
            typer.echo(f"\n⚠️  Missing API keys for stages: {', '.join(missing_keys)}")
            typer.echo("   You'll need API keys to generate the project design.\n")
            
            if typer.confirm("Would you like to enter API key(s) now?", default=True):
                api_key = typer.prompt(
                    "Enter your LLM API key (will be used for all stages)",
                    hide_input=True
                )
                config.llm.api_key = api_key
                if config.design_llm:
                    config.design_llm.api_key = api_key
                typer.echo("✓ API key set for this session.\n")
            else:
                typer.echo(
                    "\n⚠️  Proceeding without API keys. Pipeline will fail during generation.\n",
                    err=True,
                )
        else:
            typer.echo("✓ API keys configured for all required stages.\n")

        # Startup chooser: Settings, Readme, or Start (interactive mode)
        # Non-TTY environments will default to 'start' internally.
        try:
            while True:
                action = run_main_menu(config)
                # LOG: After each run_main_menu return, show the current provider
                logger.debug(f"[interactive_design] Provider after run_main_menu: {getattr(config.llm, 'provider', None)}")
                if action == "start":
                    break
                if action == "select_model":
                    try:
                        _select_requesty_model_interactively(config)
                        # LOG: After interactive model selection, provider may have changed
                        logger.debug(f"[interactive_design] Provider after select_model: {getattr(config.llm, 'provider', None)}")
                    except Exception as exc:
                        typer.echo(f"⚠️  Model selection unavailable: {exc}")
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
        

        # Resume session if requested (only available for scripted mode)
        if resume_session and not use_llm_interview:
            session_path = Path(resume_session)
            if session_path.exists():
                questionnaire.load_session(session_path)
                typer.echo(f"📂 Resumed session from {resume_session}\n")
            else:
                typer.echo(
                    f"⚠️  Warning: Session file not found at {resume_session}",
                    color=True,
                )
                typer.echo("   Starting a new session instead.\n")
        elif resume_session and use_llm_interview:
            typer.echo("⚠️  Session resume not available for LLM interview mode", color=True)

        # Run interview (either LLM or scripted)
        typer.echo("")  # Add spacing
        
        if use_llm_interview:
            try:
                answers = interview_manager.run()
            except Exception as e:
                typer.echo(f"\n❌ Error during LLM interview: {e}", err=True, color=True)
                typer.echo("💡 Falling back to scripted questionnaire...", color=True)
                # Fallback to scripted mode
                questions_path = Path("config/questions.yaml")
                if questions_path.exists():
                    questionnaire = InteractiveQuestionnaireManager(questions_path)
                    answers = questionnaire.run()
                else:
                    typer.echo("❌ Cannot fall back - questions.yaml not found", err=True, color=True)
                    raise typer.Exit(code=1)
        else:
            answers = questionnaire.run()

        # Save session if requested (only available for scripted mode)
        if save_session and not use_llm_interview:
            session_path = Path(save_session)
            questionnaire.save_session(session_path)
            typer.echo(f"\n💾 Session saved to {save_session}")
        elif save_session and use_llm_interview:
            typer.echo("⚠️  Session save not available for LLM interview mode", color=True)

        # Convert to generate_design inputs
        try:
            if use_llm_interview:
                inputs = interview_manager.to_generate_design_inputs()
            else:
                inputs = questionnaire.to_generate_design_inputs()
        except ValueError as e:
            typer.echo(f"\n❌ Error: {e}", err=True, color=True)
            typer.echo("\n💡 Tip: In LLM interview mode, use /done to finalize and generate files", color=True)
            typer.echo("   The LLM needs to output a JSON summary before files can be generated.", color=True)
            raise typer.Exit(code=1)

        # Validate we have the required inputs
        if "name" not in inputs:
            typer.echo(
                "\n❌ Error: Project name is required but was not provided",
                err=True,
                color=True,
            )
            typer.echo("\n💡 Tip: Use /done during the interview to finalize", color=True)
            raise typer.Exit(code=1)

        if "languages" not in inputs:
            typer.echo(
                "\n❌ Error: At least one language must be specified",
                err=True,
                color=True,
            )
            raise typer.Exit(code=1)

        if "requirements" not in inputs:
            typer.echo(
                "\n❌ Error: Project requirements are required",
                err=True,
                color=True,
            )
            raise typer.Exit(code=1)

        # Generate design using existing pipeline
        typer.echo("\n" + "=" * 60)
        typer.echo(f"🎨 Generating project design for: {inputs['name']}")
        typer.echo("=" * 60 + "\n")
        typer.echo(f"Languages: {inputs['languages']}")
        if "frameworks" in inputs:
            typer.echo(f"Frameworks: {inputs['frameworks']}")
        if "apis" in inputs:
            typer.echo(f"APIs: {inputs['apis']}")
        typer.echo("\n⏳ Generating design (this may take a moment)...\n")

        logger.info(f"Generating project design for: {inputs['name']}")
        
        # Create timestamped project folder to avoid overwriting
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        project_slug = inputs['name'].lower().replace(" ", "-").replace("_", "-")
        project_folder = Path(config.output_dir) / f"{project_slug}_{timestamp}"
        project_folder.mkdir(parents=True, exist_ok=True)
        
        typer.echo(f"📁 Project folder: {project_folder.resolve()}\n")
        logger.info(f"Created project folder: {project_folder}")

        # Create orchestrator
        orchestrator = _create_orchestrator(config)

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
        typer.echo("\n📋 Project Design Summary:")
        typer.echo("-" * 40)
        if design.objectives:
            typer.echo(f"Objectives: {len(design.objectives)} defined")
        if design.tech_stack:
            typer.echo(f"Tech Stack: {', '.join(design.tech_stack[:3])}")
            if len(design.tech_stack) > 3:
                typer.echo(f"            + {len(design.tech_stack) - 3} more...")
        typer.echo("-" * 40 + "\n")

        # Save output to timestamped project folder
        output_file = project_folder / "project_design.md"

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"# Project Design: {inputs['name']}\n\n")
            f.write(f"## Architecture Overview\n\n{design.architecture_overview}\n\n")
            f.write("## Tech Stack\n\n")
            for tech in design.tech_stack:
                f.write(f"- {tech}\n")

        typer.echo(f"✅ Project design generated successfully!")
        typer.echo(f"📄 Saved to: {output_file.resolve()}")
        
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
                    f"\n💡 Next step: Run 'devussy generate-devplan {output_file}' to create the development plan"
                )
                return
            typer.echo("\n" + "=" * 60)
            typer.echo("🔄 Continuing with full circular development pipeline...")
            typer.echo("=" * 60 + "\n")
            typer.echo("This will generate:")
            typer.echo("  1. ✓ Project Design (complete)")
            typer.echo("  2. Development Plan (devplan.md)")
            typer.echo("  3. Handoff Document (handoff_prompt.md)")
            typer.echo(f"\n📁 Output directory: {project_folder.resolve()}")
            typer.echo("\n⏳ Running full pipeline...\n")
            
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
            typer.echo("💾 Saving files to disk...")
            typer.echo("=" * 60)
            
            # EXPLICIT FILE WRITES - Force write all files directly
            try:
                from .file_manager import FileManager
                file_mgr = FileManager()
                
                # Write project design
                design_content = f"# Project Design: {inputs['name']}\n\n"
                design_content += f"## Architecture Overview\n\n{design_result.architecture_overview}\n\n"
                design_content += "## Tech Stack\n\n"
                for tech in design_result.tech_stack:
                    design_content += f"- {tech}\n"
                design_content += f"\n## Project Details\n\n"
                design_content += f"**Languages:** {', '.join(languages_list)}\n\n"
                design_content += f"**Requirements:** {inputs['requirements']}\n\n"
                
                design_path = project_folder / "project_design.md"
                file_mgr.write_markdown(str(design_path), design_content)
                typer.echo(f"  ✅ Wrote project_design.md ({design_path.stat().st_size} bytes)")
                
                # Write devplan - Use orchestrator's markdown converter
                devplan_content = orchestrator._devplan_to_markdown(devplan_result)
                
                devplan_path = project_folder / "devplan.md"
                file_mgr.write_markdown(str(devplan_path), devplan_content)
                typer.echo(f"  ✅ Wrote devplan.md dashboard ({devplan_path.stat().st_size} bytes)")
                
                # Generate individual phase files
                phase_files = orchestrator._generate_phase_files(devplan_result, str(project_folder))
                phase_file_names = [Path(f).name for f in phase_files]
                for phase_file in phase_files:
                    phase_path = Path(phase_file)
                    typer.echo(f"  ✅ Wrote {phase_path.name} ({phase_path.stat().st_size} bytes)")
                
                # Write handoff prompt
                handoff_path = project_folder / "handoff_prompt.md"
                file_mgr.write_markdown(str(handoff_path), handoff_result.content)
                typer.echo(f"  ✅ Wrote handoff_prompt.md ({handoff_path.stat().st_size} bytes)")
                
                typer.echo("\n✅ All files written successfully!")
                typer.echo(f"\n📁 Project folder: {project_folder.resolve()}")
                typer.echo("\nVerifying files...")
                
                # Verify all files including phase files
                all_files = [design_path, devplan_path, handoff_path] + [Path(f) for f in phase_files]
                for file in all_files:
                    if file.exists():
                        typer.echo(f"  ✓ {file.name} - {file.stat().st_size} bytes")
                    else:
                        typer.echo(f"  ✗ {file.name} - MISSING!", err=True)
                
            except Exception as e:
                typer.echo(f"\n⚠️  Error writing files: {e}", err=True, color=True)
                logger.error(f"Failed to write files: {e}", exc_info=True)
                if debug:
                    import traceback
                    typer.echo(traceback.format_exc(), err=True)
                raise
            
            typer.echo("\n" + "=" * 60)
            typer.echo("✅ Circular development pipeline complete!", color=True)
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
            
            typer.echo("\n📦 Generated files:")
            typer.echo(f"\n  📄 Project Design:")
            typer.echo(f"     {design_file}")
            if files_exist["design"]:
                typer.echo(f"     ✅ File written successfully ({design_file.stat().st_size} bytes)")
            
            typer.echo(f"\n  📝 Development Plan Dashboard:")
            typer.echo(f"     {devplan_file}")
            if files_exist["devplan"]:
                typer.echo(f"     ✅ Dashboard written successfully ({devplan_file.stat().st_size} bytes)")
                typer.echo(f"     📋 Individual phase files generated for implementation agents")
            
            typer.echo(f"\n  📤 Handoff Prompt:")
            typer.echo(f"     {handoff_file}")
            if files_exist["handoff"]:
                typer.echo(f"     ✅ File written successfully ({handoff_file.stat().st_size} bytes)")
            
            # List phase files if they exist
            phase_files = list(project_folder.glob("phase*.md"))
            if phase_files:
                typer.echo(f"\n  🚀 Phase Files:")
                for phase_file in sorted(phase_files):
                    typer.echo(f"     {phase_file} ✅ ({phase_file.stat().st_size} bytes)")
            
            # Warning if any files are missing
            if not all(files_exist.values()):
                typer.echo("\n⚠️  Warning: Some files were not written to disk", err=True, color=True)
                typer.echo("\nDebug info:", err=True)
                typer.echo(f"  Project folder: {project_folder}", err=True)
                typer.echo(f"  Folder exists: {project_folder.exists()}", err=True)
                typer.echo(f"  Files in folder: {list(project_folder.glob('*.md'))}", err=True)
            else:
                typer.echo("\n✅ All files verified and saved successfully!")
            
            typer.echo("\n" + "=" * 60)
            typer.echo("💡 Next Steps:")
            typer.echo(f"   1. Review the devplan: {devplan_file}")
            typer.echo(f"   2. Open folder in explorer: {project_folder}")
            typer.echo("   3. Use these markdown files with other tools")
            typer.echo("   4. Begin Phase 0 implementation")
            typer.echo("=" * 60 + "\n")
        else:
            # Scripted mode: just suggest next step
            typer.echo(
                f"\n💡 Next step: Run 'devussy generate-devplan {output_file}' to create the development plan"
            )

    except typer.Exit:
        raise
    except Exception as e:
        logger.error(f"Error in interactive design: {e}", exc_info=True)
        if debug:
            typer.echo("\nDebug traceback:", err=True)
            typer.echo(traceback.format_exc(), err=True)
        typer.echo(f"\n❌ Error: {str(e)}", err=True, color=True)
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
                typer.echo(f"\n❌ Could not resolve Requesty API key: {e}", err=True, color=True)
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
        typer.echo(f"\n❌ Error in launch: {str(e)}", err=True, color=True)
        logger.error(f"Error in launch: {e}", exc_info=True)
        raise typer.Exit(code=1)


@app.command()
def version() -> None:
    """Show version information."""
    typer.echo(f"DevPlan Orchestrator v{__version__}")


def main() -> None:
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
