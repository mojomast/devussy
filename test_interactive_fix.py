#!/usr/bin/env python3
"""Test script to verify the interactive mode fix."""

import sys
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.window_manager import WindowManager
from src.config import AppConfig

def test_script_creation():
    """Test that scripts are created with correct paths."""
    print("Testing script creation...")
    
    # Create temp config
    config = AppConfig()
    
    # Create window manager
    window_manager = WindowManager(config)
    
    # Test interview script creation
    interview_script = window_manager._create_interview_script()
    print(f"✓ Interview script created at: {interview_script}")
    
    # Test terminal script creation  
    terminal_script = window_manager._create_terminal_script()
    print(f"✓ Terminal script created at: {terminal_script}")
    
    # Verify scripts exist
    assert interview_script.exists(), "Interview script not created"
    assert terminal_script.exists(), "Terminal script not created"
    
    # Read and verify script content
    with open(interview_script, 'r', encoding='utf-8') as f:
        interview_content = f.read()
    with open(terminal_script, 'r', encoding='utf-8') as f:
        terminal_content = f.read()
    
    print("✓ Interview script contains correct src path:")
    print(f"  {interview_content.split('sys.path.insert')[1].split(')')[0]})")
    
    print("✓ Terminal script contains correct src path:")
    print(f"  {terminal_content.split('sys.path.insert')[1].split(')')[0]})")
    
    # Test that the paths are absolute and point to the actual src directory
    expected_src = Path(__file__).parent / "src"
    assert str(expected_src) in interview_content, f"Expected src path {expected_src} not in interview script"
    assert str(expected_src) in terminal_content, f"Expected src path {expected_src} not in terminal script"
    
    # Test that streaming is enabled in both scripts
    assert "config.streaming_enabled = True" in interview_content, "Streaming not enabled in interview script"
    assert "config.streaming_enabled = True" in terminal_content, "Streaming not enabled in terminal script"
    
    print("✓ Streaming is enabled in both scripts!")
    print("✓ All script path tests passed!")
    
    # Cleanup
    window_manager.cleanup()
    
    return True

if __name__ == "__main__":
    try:
        test_script_creation()
        print("\n🎉 All tests passed! The interactive mode fix should work correctly.")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
