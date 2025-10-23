"""Debug individual commands."""
from src import cli
import typer

commands = [
    'generate_design',
    'generate_devplan',
    'generate_handoff',
    'run_full_pipeline',
    'init_repo',
    'list_checkpoints',
    'delete_checkpoint',
    'cleanup_checkpoints',
    'interactive_design',
    'version'
]

for cmd_name in commands:
    try:
        print(f"Testing {cmd_name}...")
        cmd = getattr(cli, cmd_name, None)
        if cmd:
            # Try to create Click command from it
            typer.main.get_command_from_info(
                typer.models.CommandInfo(
                    name=cmd_name,
                    callback=cmd
                ),
                pretty_exceptions_short=False,
                rich_markup_mode=None
            )
            print(f"  ✓ {cmd_name} is OK")
    except TypeError as e:
        if "Secondary flag" in str(e):
            print(f"  ✗ {cmd_name} HAS THE ISSUE!")
        else:
            print(f"  ? {cmd_name} has error: {e}")
    except Exception as e:
        print(f"  ? {cmd_name} has error: {e}")
