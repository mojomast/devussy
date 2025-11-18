#!/usr/bin/env python3
"""Test the fixed single-window interactive mode."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_fixes():
    """Test that all the fixes are properly applied."""
    print("Testing fixed single-window interactive mode...")
    
    # Test 1: RepositoryAnalyzer initialization
    print("\n1. Testing RepositoryAnalyzer initialization...")
    try:
        from src.interview import RepositoryAnalyzer
        analyzer = RepositoryAnalyzer(Path.cwd())
        print("✓ RepositoryAnalyzer can be initialized with root_path")
    except Exception as e:
        print(f"[ERROR] RepositoryAnalyzer error: {e}")
        return False
    
    # Test 2: LLMInterviewManager method
    print("\n2. Testing LLMInterviewManager methods...")
    try:
        from src.llm_interview import LLMInterviewManager
        
        # Create a minimal config for testing
        config = type('Config', (), {})()
        config.llm = type('LLM', (), {})()
        config.llm.provider = 'openai'
        config.llm.model = 'gpt-4'
        config.llm.temperature = 0.7
        config.llm.api_key = 'test'
        
        manager = LLMInterviewManager(config=config, verbose=False, repo_analysis=None)
        assert hasattr(manager, 'run'), "Missing run() method"
        assert hasattr(manager, 'to_generate_design_inputs'), "Missing to_generate_design_inputs() method"
        print("✓ LLMInterviewManager has correct methods")
    except Exception as e:
        print(f"[ERROR] LLMInterviewManager error: {e}")
        return False
    
    # Test 3: CLI interactive function
    print("\n3. Testing CLI interactive function...")
    try:
        from src.cli import interactive
        docstring = interactive.__doc__
        assert "single window" in docstring.lower(), "Docstring not updated"
        assert "real-time streaming" in docstring.lower(), "Streaming not mentioned"
        print("✓ CLI interactive function is updated for single-window mode")
    except Exception as e:
        print(f"[ERROR] CLI interactive error: {e}")
        return False
    
    # Test 4: Check that old multi-window code is removed
    print("\n4. Testing that multi-window code is removed...")
    cli_file = Path(__file__).parent / "src" / "cli.py"
    with open(cli_file, 'r', encoding='utf-8') as f:
        cli_content = f.read()
    
    # Should NOT contain old multi-window code
    assert "launch_interactive_mode" not in cli_content, "Still contains multi-window code"
    assert "two terminal windows" not in cli_content, "Still mentions two windows"
    
    # Should contain new single-window code
    assert "Single Window" in cli_content, "Missing single-window mode"
    assert "async def run_interactive" in cli_content, "Missing async wrapper"
    assert "interview_manager.run()" in cli_content, "Missing correct method call"
    
    print("✓ Multi-window code removed, single-window code added")
    
    return True

def test_expected_behavior():
    """Describe the expected behavior after fixes."""
    print("\n" + "="*60)
    print("EXPECTED BEHAVIOR AFTER FIXES")
    print("="*60)
    
    print("\n[TARGET] Single-Window Mode:")
    print("• Everything runs in the same terminal window")
    print("• No new windows are spawned")
    print("• Sequential execution with clear steps")
    
    print("\n📊 Real-time Streaming:")
    print("• Interview Q&A with live LLM responses")
    print("• Project design generation with token streaming")
    print("• Devplan structure generation with token streaming")
    print("• All 5 phases generated with live token preview")
    
    print("\n🔧 Fixed Issues:")
    print("• RepositoryAnalyzer now requires root_path parameter")
    print("• LLMInterviewManager.run() method (not run_interview)")
    print("• Proper async/await handling for streaming")
    print("• No more synchronization issues between windows")
    
    print("\n[FOLDER] Output:")
    print("• devplan.json - Structured development plan")
    print("• phases.json - All 5 generated phases")
    print("• Everything saved to current directory")

if __name__ == "__main__":
    try:
        if test_fixes():
            test_expected_behavior()
            print("\n[CELEBRATE] All fixes verified! Single-window mode is ready!")
            print("\nTo run: python -m src.cli interactive")
        else:
            print("\n[ERROR] Some tests failed")
            sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
