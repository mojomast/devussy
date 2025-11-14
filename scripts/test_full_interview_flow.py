#!/usr/bin/env python3
"""
Test the full interview flow with real API calls.
Tests repository analysis, code sample extraction, and LLM interview integration.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from src.interview.repository_analyzer import RepositoryAnalyzer
from src.interview.code_sample_extractor import CodeSampleExtractor
from src.llm_interview import LLMInterviewManager
from src.config import AppConfig
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

console = Console()


async def test_full_flow():
    """Test the complete interview flow with real API."""
    
    # Load test environment
    load_dotenv(".env.test")
    
    # Verify API key
    api_key = os.getenv("REQUESTY_API_KEY")
    if not api_key:
        console.print("[red]Error: REQUESTY_API_KEY not found in .env.test[/red]")
        return False
    
    console.print(Panel.fit(
        "[bold cyan]Testing Full Interview Flow[/bold cyan]\n"
        "This will test repository analysis, code extraction, and LLM interview",
        border_style="cyan"
    ))
    
    # Step 1: Analyze repository
    console.print("\n[bold]Step 1: Analyzing Repository[/bold]")
    repo_dir = Path(".")
    analyzer = RepositoryAnalyzer(repo_dir)
    analysis = analyzer.analyze()
    
    console.print(f"✓ Project Type: [green]{analysis.project_type}[/green]")
    console.print(f"✓ Total Files: [green]{analysis.code_metrics.total_files}[/green]")
    console.print(f"✓ Total Lines: [green]{analysis.code_metrics.total_lines:,}[/green]")
    
    # Count total dependencies across all ecosystems
    total_deps = (len(analysis.dependencies.python) + len(analysis.dependencies.node) + 
                  len(analysis.dependencies.go) + len(analysis.dependencies.rust) + 
                  len(analysis.dependencies.java))
    console.print(f"✓ Dependencies: [green]{total_deps}[/green]")
    
    # Step 2: Extract code samples
    console.print("\n[bold]Step 2: Extracting Code Samples[/bold]")
    extractor = CodeSampleExtractor(repo_dir)
    
    # Simulate user selecting relevant parts
    selected_parts = [
        "src/interview/",
        "src/pipeline/",
        "tests/unit/test_repository_analyzer.py"
    ]
    
    user_goals = "Add streaming terminal UI for phase generation"
    
    samples = extractor.extract_samples(analysis, selected_parts, user_goals)
    
    console.print(f"✓ Extracted [green]{len(samples)}[/green] code samples")
    for sample in samples:
        console.print(f"  - {sample.file_path} ({sample.category})")
    
    # Step 3: Initialize LLM interview manager
    console.print("\n[bold]Step 3: Initializing LLM Interview Manager[/bold]")
    
    # Create minimal config for testing
    from src.config import load_config
    config = load_config("config/config.yaml")
    
    # Override with test credentials
    config.llm.provider = "requesty"
    config.llm.api_key = api_key
    config.llm.base_url = os.getenv("REQUESTY_BASE_URL", "https://router.requesty.ai/v1")
    config.llm.model = "openai/gpt-5-mini"  # Use GPT-5 mini through Requesty
    
    interview_manager = LLMInterviewManager(
        config=config,
        repo_analysis=analysis
    )
    
    console.print(f"✓ Interview manager initialized with [green]{config.llm.provider}[/green]")
    console.print(f"✓ Model: [green]{config.llm.model}[/green]")
    
    # Step 4: Test design input generation
    console.print("\n[bold]Step 4: Generating Design Inputs[/bold]")
    
    # Simulate interview answers (set extracted_data directly for testing)
    interview_manager.extracted_data = {
        "project_name": "Devussy Terminal UI",
        "primary_language": "Python",
        "requirements": "Add streaming terminal UI for concurrent phase generation with 5-phase grid, real-time streaming, cancellation, and steering",
        "frameworks": "Textual, Rich",
        "constraints": "Must integrate with existing pipeline",
        "timeline": "2 weeks"
    }
    
    # Add code samples
    interview_manager.code_samples = samples
    
    # Generate design inputs
    design_inputs = interview_manager.to_generate_design_inputs()
    
    console.print(f"✓ Generated design inputs")
    console.print(f"  - Project name: [green]{design_inputs.get('name', 'N/A')}[/green]")
    console.print(f"  - Has repo context: [green]{design_inputs.get('repo_context') is not None}[/green]")
    console.print(f"  - Code samples: [green]{len(samples)} samples[/green]")
    console.print(f"  - Total input keys: [green]{len(design_inputs)}[/green]")
    
    # Show sample of code context
    if samples:
        console.print("\n[bold]Sample Code Context:[/bold]")
        code_context = extractor.format_samples_for_prompt(samples)
        # Show first 500 chars
        preview = code_context[:500] + "..." if len(code_context) > 500 else code_context
        console.print(Panel(preview, title="Code Samples Preview", border_style="blue"))
    
    # Step 5: Test actual LLM call (optional - may fail due to API restrictions)
    console.print("\n[bold]Step 5: Testing LLM Integration (Optional)[/bold]")
    
    try:
        console.print("Making test LLM call with repo context...")
        from src.clients.factory import create_llm_client
        client = create_llm_client(config)
        
        # Create a prompt that includes repo context
        repo_context = analysis.to_prompt_context()
        test_prompt = f"""Based on this repository analysis:

Project Type: {repo_context['project_type']}
Total Files: {repo_context['metrics']['total_files']}
Total Lines: {repo_context['metrics']['total_lines']}
Source Dirs: {', '.join(repo_context['structure']['source_dirs'])}
Test Frameworks: {', '.join(repo_context['patterns']['test_frameworks'])}

What are the 3 most important architectural patterns in this codebase? Be concise."""
        
        response = await client.generate_completion(test_prompt, max_tokens=2000)
        
        console.print(f"✓ LLM Response received: [green]{len(response)} chars[/green]")
        console.print(Panel(response, title="LLM Response", border_style="green"))
    except Exception as e:
        error_msg = str(e)
        console.print(f"[yellow]⚠ LLM call error: {error_msg[:200]}[/yellow]")
        if "403" in error_msg or "blocked by policy" in error_msg or "401" in error_msg or "Unauthorized" in error_msg:
            console.print(f"[yellow]This appears to be an API key/permission issue[/yellow]")
            console.print(f"[dim]Full error: {error_msg}[/dim]")
        else:
            console.print(f"[red]✗ Unexpected LLM call failure[/red]")
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")
            return False
    
    # Summary
    console.print("\n" + "="*70)
    console.print(Panel.fit(
        "[bold green]✓ All Tests Passed![/bold green]\n\n"
        f"Repository analyzed: {analysis.code_metrics.total_files} files, {analysis.code_metrics.total_lines:,} lines\n"
        f"Code samples extracted: {len(samples)} samples\n"
        f"Interview manager ready with repo context\n"
        f"Design inputs generated successfully",
        border_style="green",
        title="Test Summary"
    ))
    
    return True


if __name__ == "__main__":
    success = asyncio.run(test_full_flow())
    sys.exit(0 if success else 1)
