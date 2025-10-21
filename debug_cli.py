"""Debug script to find problematic CLI command."""
import typer
from src.cli import app

# Try to get the Click command, which will trigger the error
try:
    command = typer.main.get_command(app)
    print("Success! All commands are valid.")
except Exception as e:
    print(f"Error: {e}")
    print(f"Type: {type(e)}")
    
    # Try to find which command is causing the issue
    print("\nTrying each command individually...")
    for cmd_name, cmd_info in app.registered_commands:
        try:
            print(f"Testing command: {cmd_name if cmd_name else '(default)'}")
            # This would trigger the same error
        except Exception as cmd_e:
            print(f"  ERROR in {cmd_name}: {cmd_e}")
