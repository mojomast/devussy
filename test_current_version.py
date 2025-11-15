#!/usr/bin/env python3
"""Test to determine which version of interactive is actually being loaded."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_current_version():
    """Test what version is actually being loaded."""
    print("Testing current version being loaded...")
    
    # Import the CLI module fresh
    import importlib
    import src.cli
    importlib.reload(src.cli)
    
    # Get the interactive function
    interactive_func = src.cli.interactive
    
    # Check the docstring
    docstring = interactive_func.__doc__ or ""
    print(f"Docstring: {docstring[:100]}...")
    
    # Check if it mentions single window
    if "single window" in docstring.lower():
        print("✅ Single-window version detected")
        return True
    elif "two terminal windows" in docstring.lower():
        print("❌ Multi-window version detected")
        return False
    else:
        print("⚠️  Unknown version")
        print(f"Full docstring: {docstring}")
        return False

def check_file_contents():
    """Check what's actually in the CLI file."""
    print("\nChecking CLI file contents...")
    
    cli_file = Path(__file__).parent / "src" / "cli.py"
    with open(cli_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Look for key indicators
    has_single_window = "Single Window" in content
    has_multi_window = "two terminal windows" in content
    has_launch_interactive = "launch_interactive_mode" in content
    
    print(f"Has 'Single Window': {has_single_window}")
    print(f"Has 'two terminal windows': {has_multi_window}")
    print(f"Has 'launch_interactive_mode': {has_launch_interactive}")
    
    if has_single_window and not has_multi_window and not has_launch_interactive:
        print("✅ File contains single-window version")
        return True
    elif has_multi_window or has_launch_interactive:
        print("❌ File contains multi-window version")
        return False
    else:
        print("⚠️  File state unclear")
        return False

def find_all_interactive_functions():
    """Find all functions named interactive in the codebase."""
    print("\nSearching for all interactive functions...")
    
    import subprocess
    result = subprocess.run(
        ['findstr', '/S', '/N', 'def interactive', 'src\\*.py'],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).parent)
    )
    
    if result.stdout:
        print("Found interactive functions:")
        print(result.stdout)
    else:
        print("No interactive functions found with findstr")
    
    # Also check for any imports of launch_interactive_mode
    result2 = subprocess.run(
        ['findstr', '/S', '/N', 'launch_interactive_mode', 'src\\*.py'],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).parent)
    )
    
    if result2.stdout:
        print("Found launch_interactive_mode references:")
        print(result2.stdout)

if __name__ == "__main__":
    print("Diagnosing version issues...")
    print("=" * 50)
    
    version_ok = test_current_version()
    file_ok = check_file_contents()
    find_all_interactive_functions()
    
    if version_ok and file_ok:
        print("\n✅ Everything looks correct - should be single-window mode")
    else:
        print("\n❌ There are still issues with the version")
        print("Try restarting your terminal and clearing Python cache")
