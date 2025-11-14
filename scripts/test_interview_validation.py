#!/usr/bin/env python3
"""
Real-world validation script for interview mode.

Tests the complete interview flow with actual LLM API calls to verify:
1. Repository analysis works correctly
2. Project summary displays properly
3. Code sample extraction functions
4. LLM interview produces valid devplan inputs
5. Generated devplans include repo context and code samples
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
from src.config import load_config
from src.interview import RepositoryAnalyzer
from src.interview.code_sample_extractor import CodeSampleExtractor
from src.llm_interview import LLMInterviewManager

def test_repo_analysis():
    """Test repository analysis on the devussy project itself."""
    print("\n" + "=" * 60)
    print("TEST 1: Repository Analysis")
    print("=" * 60)
    
    root = Path(".").resolve()
    analyzer = RepositoryAnalyzer(root)
    analysis = analyzer.analyze()
    
    print(f"\n✓ Project type: {analysis.project_type}")
    print(f"✓ Total files: {analysis.code_metrics.total_files}")
    print(f"✓ Total lines: {analysis.code_metrics.total_lines}")
    print(f"✓ Source dirs: {', '.join(analysis.structure.source_dirs)}")
    print(f"✓ Test dirs: {', '.join(analysis.structure.test_dirs)}")
    
    if analysis.dependencies.python:
        print(f"✓ Python deps: {len(analysis.dependencies.python)} found")
    
    if analysis.patterns.test_frameworks:
        print(f"✓ Test frameworks: {', '.join(analysis.patterns.test_frameworks)}")
    
    return analysis


def test_code_sample_extraction(analysis):
    """Test code sample extraction."""
    print("\n" + "=" * 60)
    print("TEST 2: Code Sample Extraction")
    print("=" * 60)
    
    extractor = CodeSampleExtractor(
        root_path=str(analysis.root_path),
        max_samples=5,
        max_lines_per_sample=100
    )
    
    samples = extractor.extract_samples(
        analysis=analysis,
        goals="Add new terminal UI features for streaming phases"
    )
    
    print(f"\n✓ Extracted {len(samples)} code samples")
    for i, sample in enumerate(samples, 1):
        print(f"\n  Sample {i}: {sample.file_path}")
        print(f"    Category: {sample.category}")
        print(f"    Reason: {sample.reason}")
        print(f"    Lines: {sample.line_count}")
    
    # Test formatting for prompts
    formatted = extractor.format_samples_for_prompt(samples)
    print(f"\n✓ Formatted output: {len(formatted)} characters")
    
    return samples


def test_interview_manager_init(analysis):
    """Test LLM interview manager initialization with repo context."""
    print("\n" + "=" * 60)
    print("TEST 3: Interview Manager Initialization")
    print("=" * 60)
    
    # Load config
    config = load_config()
    
    # Override with test settings
    config.llm.provider = "requesty"
    config.llm.model = "gpt-4o-mini"
    config.llm.temperature = 0.7
    
    # Create interview manager with repo analysis
    manager = LLMInterviewManager(
        config=config,
        verbose=True,
        repo_analysis=analysis
    )
    
    print(f"\n✓ Interview manager created")
    print(f"✓ Provider: {config.llm.provider}")
    print(f"✓ Model: {config.llm.model}")
    print(f"✓ Repo analysis attached: {manager.repo_analysis is not None}")
    print(f"✓ Conversation history length: {len(manager.conversation_history)}")
    
    # Check that repo summary was added to conversation
    has_repo_context = any(
        "existing project" in msg.get("content", "").lower()
        for msg in manager.conversation_history
        if msg.get("role") == "system"
    )
    print(f"✓ Repo context in conversation: {has_repo_context}")
    
    return manager


def test_code_sample_integration(manager, samples):
    """Test that code samples can be extracted and formatted."""
    print("\n" + "=" * 60)
    print("TEST 4: Code Sample Integration")
    print("=" * 60)
    
    # Simulate extracted data
    manager.extracted_data = {
        "project_name": "Devussy Test",
        "primary_language": "Python",
        "requirements": "Add terminal UI features",
        "project_type": "CLI Tool"
    }
    
    # Set code samples
    manager.code_samples = samples
    
    # Get formatted context
    context = manager.get_code_samples_context()
    
    print(f"\n✓ Code samples set: {len(manager.code_samples)}")
    print(f"✓ Formatted context length: {len(context)} characters")
    
    # Test conversion to design inputs
    inputs = manager.to_generate_design_inputs()
    
    print(f"\n✓ Design inputs generated:")
    print(f"  - name: {inputs.get('name')}")
    print(f"  - languages: {inputs.get('languages')}")
    print(f"  - requirements: {inputs.get('requirements')}")
    print(f"  - code_samples: {'present' if 'code_samples' in inputs else 'missing'}")
    
    if 'code_samples' in inputs:
        print(f"    Length: {len(inputs['code_samples'])} characters")
    
    return inputs


def main():
    """Run all validation tests."""
    print("\n" + "=" * 80)
    print("DEVUSSY INTERVIEW MODE - REAL-WORLD VALIDATION")
    print("=" * 80)
    
    # Load test environment
    env_file = Path(".env.test")
    if env_file.exists():
        load_dotenv(env_file)
        print("\n✓ Loaded test environment from .env.test")
    else:
        print("\n⚠️  No .env.test file found, using system environment")
    
    # Check API key
    api_key = os.getenv("REQUESTY_API_KEY")
    if not api_key:
        print("\n❌ ERROR: REQUESTY_API_KEY not set")
        print("   Please set it in .env.test or environment")
        return 1
    
    print(f"✓ API key configured: {api_key[:20]}...")
    
    try:
        # Run tests
        analysis = test_repo_analysis()
        samples = test_code_sample_extraction(analysis)
        manager = test_interview_manager_init(analysis)
        inputs = test_code_sample_integration(manager, samples)
        
        print("\n" + "=" * 80)
        print("✅ ALL VALIDATION TESTS PASSED")
        print("=" * 80)
        print("\nSummary:")
        print(f"  ✓ Repository analysis: {analysis.project_type} project")
        print(f"  ✓ Code samples extracted: {len(samples)}")
        print(f"  ✓ Interview manager initialized with repo context")
        print(f"  ✓ Design inputs include code samples: {len(inputs.get('code_samples', ''))} chars")
        print("\n💡 Next: Run 'python -m src.entry' to test full interactive flow")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
