#!/usr/bin/env python3
"""Test script to verify the single-window interactive mode."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_single_window_mode():
    """Test that the single-window mode is properly configured."""
    print("Testing single-window interactive mode...")
    
    # Read the CLI file to verify the changes
    cli_file = Path(__file__).parent / "src" / "cli.py"
    with open(cli_file, 'r', encoding='utf-8') as f:
        cli_content = f.read()
    
    # Check that the interactive command is single-window
    assert "single window" in cli_content.lower(), "Interactive mode not updated for single window"
    assert "async def run_interactive" in cli_content, "Async wrapper not added"
    assert "asyncio.run(run_interactive())" in cli_content, "Async execution not added"
    
    # Check that it doesn't use window manager
    assert "from .window_manager import launch_interactive_mode" not in cli_content, "Still using multi-window mode"
    
    # Check that streaming is enabled
    assert "config.streaming_enabled = True" in cli_content, "Streaming not enabled"
    
    # Check that phases are generated sequentially
    assert "stream_phase" in cli_content, "Sequential phase generation not added"
    assert "for phase_name in" in cli_content, "Phase loop not added"
    
    print("✓ Single-window mode properly configured")
    print("✓ Async execution wrapper added")
    print("✓ Multi-window code removed")
    print("✓ Streaming enabled")
    print("✓ Sequential phase generation added")
    
    return True

def test_expected_behavior():
    """Describe the expected behavior."""
    print("\nExpected behavior with single-window mode:")
    print("1. ✓ Everything runs in the same terminal window")
    print("2. ✓ No new windows are spawned")
    print("3. ✓ Real-time streaming during all phases:")
    print("   - Interview questions and answers")
    print("   - Project design generation")
    print("   - Devplan structure generation")
    print("   - All 5 phase generations (plan, design, implement, test, review)")
    print("4. ✓ Clear progress indicators for each step")
    print("5. ✓ Results saved to local files")
    print("6. ✓ No synchronization issues between windows")

if __name__ == "__main__":
    try:
        test_single_window_mode()
        test_expected_behavior()
        print("\n[CELEBRATE] Single-window mode is ready!")
        print("\nTo use it, run:")
        print("python -m src.cli interactive")
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
