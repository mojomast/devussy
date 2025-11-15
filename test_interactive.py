#!/usr/bin/env python3
"""Test script for the interactive mode workflow."""

import sys
import json
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config import load_config
from src.window_manager import WindowManager

def test_window_manager():
    """Test the window manager functionality."""
    print("🧪 Testing Window Manager...")
    
    # Load config
    config = load_config()
    print(f"✓ Config loaded: {config.llm.provider}:{config.llm.model}")
    
    # Create window manager
    wm = WindowManager(config)
    print(f"✓ Window manager created")
    print(f"  Temp dir: {wm.temp_dir}")
    print(f"  Devplan file: {wm.devplan_file}")
    
    # Create scripts
    interview_script = wm._create_interview_script()
    terminal_script = wm._create_terminal_script()
    
    print(f"✓ Interview script created: {interview_script}")
    print(f"✓ Terminal script created: {terminal_script}")
    
    # Verify script content
    with open(interview_script, 'r', encoding='utf-8') as f:
        interview_content = f.read()
        assert "LLMInterviewManager" in interview_content
        assert "devplan_file" in interview_content
        print("✓ Interview script contains expected content")
    
    with open(terminal_script, 'r', encoding='utf-8') as f:
        terminal_content = f.read()
        assert "run_terminal_ui" in terminal_content
        assert "TerminalPhaseGenerator" in terminal_content
        print("✓ Terminal script contains expected content")
    
    # Test file waiting with a fake file
    print("✓ Testing file waiting mechanism...")
    
    # Create a test devplan file
    test_devplan = {
        "project_name": "Test Project",
        "summary": "Test summary",
        "phases": []
    }
    
    with open(wm.devplan_file, 'w', encoding='utf-8') as f:
        json.dump(test_devplan, f)
    
    # Test waiting (should return True immediately)
    result = wm.wait_for_devplan(timeout=1)
    assert result == True
    print("✓ File waiting mechanism works")
    
    # Cleanup
    wm.cleanup()
    print("✓ Cleanup completed")
    
    print("\n🎉 All tests passed! The interactive mode system is working correctly.")
    return True

if __name__ == "__main__":
    try:
        test_window_manager()
        print("\n✅ Interactive mode is ready to use!")
        print("\nTo launch interactive mode, run:")
        print("  python -m src.cli interactive")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
