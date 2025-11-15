#!/usr/bin/env python3
"""Force reload and test the interactive mode."""

import sys
import importlib
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def force_reload_and_test():
    """Force reload all modules and test."""
    print("Force reloading modules...")
    
    # Remove any cached modules
    modules_to_remove = [name for name in sys.modules.keys() if name.startswith('src')]
    for module in modules_to_remove:
        del sys.modules[module]
    
    # Fresh import
    import src.cli
    importlib.reload(src.cli)
    
    # Get the interactive function
    interactive = src.cli.interactive
    
    # Check docstring
    docstring = interactive.__doc__ or ""
    print(f"Interactive docstring: {docstring[:200]}...")
    
    if "single window" in docstring.lower():
        print("✅ Single-window version loaded successfully!")
        return True
    else:
        print("❌ Still getting old version")
        return False

def test_direct_import():
    """Test importing the CLI directly."""
    print("\nTesting direct import...")
    
    # Clear sys.path cache
    if 'src.cli' in sys.modules:
        del sys.modules['src.cli']
    
    # Import fresh
    from src.cli import interactive
    
    docstring = interactive.__doc__ or ""
    print(f"Direct import docstring: {docstring[:200]}...")
    
    if "single window" in docstring.lower():
        print("✅ Direct import shows single-window version!")
        return True
    else:
        print("❌ Direct import shows old version")
        return False

if __name__ == "__main__":
    print("Testing module reload...")
    print("=" * 50)
    
    success1 = force_reload_and_test()
    success2 = test_direct_import()
    
    if success1 and success2:
        print("\n✅ All tests passed - single-window mode is active!")
        print("\nTry running this in a NEW terminal:")
        print("python -m src.cli interactive")
    else:
        print("\n❌ Module reload issues detected")
        print("Try completely restarting your terminal/IDE")
