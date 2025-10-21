"""Command-line interface for DevPlan Orchestrator."""

from __future__ import annotations

import asyncio
import json
import traceback
from pathlib import Path
from typing import Optional

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
from .state_manager import StateManager

app = typer.Typer(
    name="devussy",
    help="LLM-based development plan orchestration tool",
    add_completion=False,
)

logger = get_logger(__name__)


def _load_app_config(
    config_path: Optional[str],
    provider: Optional[str],
    model: Optional[str],
    output_dir: Optional[str],
    verbose: bool,
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
    # Create LLM client
    llm_client = create_llm_client(config)

    # Create concurrency manager
    concurrency_manager = ConcurrencyManager(config.max_concurrent_requests)

    # Create file manager
    file_manager = FileManager()

    # Create state manager
    state_manager = StateManager()

    # Create orchestrator
    orchestrator = PipelineOrchestrator(
        llm_client=llm_client,
        concurrency_manager=concurrency_manager,
        file_manager=file_manager,
        git_config=config.git,
        config=config,
        state_manager=state_manager,
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
        config = _load_app_config(config_path, provider, model, output_dir, verbose)

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

        design = asyncio.run(_run())

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
    output_dir: Annotated[
        Optional[str], typer.Option("--output-dir", help="Output directory")
    ] = None,
    output_path: Annotated[
        Optional[str],
        typer.Option("--output-path", help="Output file path for devplan"),
    ] = None,
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
        config = _load_app_config(config_path, provider, model, output_dir, verbose)

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
            orchestrator.run_devplan_only(design, feedback_manager=feedback_manager)
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
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(devplan_md)

        typer.echo(f"✓ DevPlan saved to: {output_file}", color=True)
        logger.info(f"DevPlan saved to: {output_file}")

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
) -> None:
    """Generate a handoff prompt from a development plan."""
    try:
        # Load config
        config = _load_app_config(config_path, None, None, output_dir, verbose)

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
        config = _load_app_config(config_path, provider, model, output_dir, verbose)

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
            typer.echo("\n" + "=" * 60)
            typer.echo(f"🚀 Starting full pipeline for: {project_name}")
            typer.echo("=" * 60 + "\n")
            typer.echo("This will generate:")
            typer.echo("  1. Project Design")
            typer.echo("  2. Development Plan")
            typer.echo("  3. Handoff Prompt\n")

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
                )
            )

        typer.echo("\n" + "=" * 60)
        typer.echo("✓ Pipeline complete!", color=True)
        typer.echo("=" * 60)
        typer.echo("\nGenerated files:")
        typer.echo(f"  📄 Project design: {config.output_dir}/project_design.md")
        typer.echo(f"  📝 DevPlan: {config.output_dir}/devplan.md")
        typer.echo(f"  📤 Handoff prompt: {config.output_dir}/handoff_prompt.md")
        typer.echo("\n" + "=" * 60 + "\n")

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
    save_session: Annotated[
        Optional[str],
        typer.Option("--save-session", help="Save session to file (path)"),
    ] = None,
    resume_session: Annotated[
        Optional[str],
        typer.Option("--resume-session", help="Resume from saved session (path)"),
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
    """Generate a project design through interactive questions.
    
    This command provides a guided questionnaire to help you create
    a project design without needing to specify all flags upfront.
    """
    try:
        from .interactive import InteractiveQuestionnaireManager

        # Load config
        config = _load_app_config(config_path, provider, model, output_dir, verbose)

        if streaming:
            config.streaming_enabled = True

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

        # Resume session if requested
        if resume_session:
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

        # Run interactive questionnaire
        typer.echo("")  # Add spacing
        answers = questionnaire.run()

        # Save session if requested
        if save_session:
            session_path = Path(save_session)
            questionnaire.save_session(session_path)
            typer.echo(f"\n💾 Session saved to {save_session}")

        # Convert to generate_design inputs
        inputs = questionnaire.to_generate_design_inputs()

        # Validate we have the required inputs
        if "name" not in inputs:
            typer.echo(
                "\n❌ Error: Project name is required but was not provided",
                err=True,
                color=True,
            )
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

        design = asyncio.run(_run())

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
        output_file = str(config.output_dir / "project_design.md")
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"# Project Design: {inputs['name']}\n\n")
            f.write(f"## Architecture Overview\n\n{design.architecture_overview}\n\n")
            f.write("## Tech Stack\n\n")
            for tech in design.tech_stack:
                f.write(f"- {tech}\n")

        typer.echo(f"✅ Project design generated successfully!")
        typer.echo(f"📄 Saved to: {output_file}")
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
def version() -> None:
    """Show version information."""
    typer.echo(f"DevPlan Orchestrator v{__version__}")


def main() -> None:
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
