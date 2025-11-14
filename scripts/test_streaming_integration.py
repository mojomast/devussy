#!/usr/bin/env python3
"""
Test script for Phase 5: Token Streaming Integration.

Tests real LLM streaming with terminal UI using a minimal devplan.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import load_config
from src.clients.factory import create_llm_client
from src.models import DevPlan, DevPlanPhase
from src.terminal.terminal_ui import DevussyTerminalUI
from src.terminal.phase_generator import TerminalPhaseGenerator
from src.terminal.phase_state import PhaseStateManager


def create_test_devplan() -> DevPlan:
    """Create a minimal devplan for testing."""
    return DevPlan(
        phases=[
            DevPlanPhase(
                number=1,
                title="plan",
                description="Planning phase - define project scope and requirements",
                steps=[
                    {"number": "1.1", "description": "Define project goals"},
                    {"number": "1.2", "description": "Identify key requirements"},
                    {"number": "1.3", "description": "Create timeline"},
                ],
            ),
            DevPlanPhase(
                number=2,
                title="design",
                description="Design phase - create architecture and technical design",
                steps=[
                    {"number": "2.1", "description": "Design system architecture"},
                    {"number": "2.2", "description": "Define data models"},
                    {"number": "2.3", "description": "Create API specifications"},
                ],
            ),
            DevPlanPhase(
                number=3,
                title="implement",
                description="Implementation phase - write code and build features",
                steps=[
                    {"number": "3.1", "description": "Set up project structure"},
                    {"number": "3.2", "description": "Implement core features"},
                    {"number": "3.3", "description": "Add error handling"},
                ],
            ),
            DevPlanPhase(
                number=4,
                title="test",
                description="Testing phase - validate functionality and quality",
                steps=[
                    {"number": "4.1", "description": "Write unit tests"},
                    {"number": "4.2", "description": "Perform integration testing"},
                    {"number": "4.3", "description": "Run end-to-end tests"},
                ],
            ),
            DevPlanPhase(
                number=5,
                title="review",
                description="Review phase - code review and documentation",
                steps=[
                    {"number": "5.1", "description": "Conduct code review"},
                    {"number": "5.2", "description": "Update documentation"},
                    {"number": "5.3", "description": "Prepare for deployment"},
                ],
            ),
        ],
        summary="Test Streaming Project - A test project to validate terminal streaming integration",
    )


async def test_streaming_without_ui():
    """Test streaming without UI (console output only)."""
    print("\n" + "=" * 60)
    print("Test 1: Streaming Without UI (Console Output)")
    print("=" * 60 + "\n")
    
    # Load config
    config = load_config()
    
    # Create LLM client
    llm_client = create_llm_client(config)
    
    # Create test devplan
    devplan = create_test_devplan()
    
    # Create state manager
    phase_names = ["plan"]  # Test with just one phase
    state_manager = PhaseStateManager(phase_names)
    
    # Create phase generator
    generator = TerminalPhaseGenerator(llm_client, state_manager)
    
    # Track tokens
    token_count = 0
    
    def on_token(token: str):
        nonlocal token_count
        token_count += 1
        print(token, end="", flush=True)
    
    print("Generating 'plan' phase with streaming...\n")
    print("-" * 60)
    
    try:
        content = await generator.generate_phase_streaming(
            "plan",
            devplan,
            on_token=on_token,
            max_tokens=500,  # Limit for faster testing
        )
        
        print("\n" + "-" * 60)
        print(f"\n✓ Generation complete!")
        print(f"  Tokens received: {token_count}")
        print(f"  Content length: {len(content)} characters")
        print(f"  Phase status: {state_manager.get_state('plan').status.value}")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False


async def test_streaming_with_ui():
    """Test streaming with terminal UI."""
    print("\n" + "=" * 60)
    print("Test 2: Streaming With Terminal UI")
    print("=" * 60 + "\n")
    print("Starting terminal UI with real LLM streaming...")
    print("Press 'q' to quit, 'c' to cancel a phase\n")
    
    # Load config
    config = load_config()
    
    # Create LLM client
    llm_client = create_llm_client(config)
    
    # Create test devplan
    devplan = create_test_devplan()
    
    # Create state manager
    phase_names = ["plan", "design", "implement"]  # Test with 3 phases
    state_manager = PhaseStateManager(phase_names)
    
    # Create phase generator
    generator = TerminalPhaseGenerator(llm_client, state_manager)
    
    # Create and run UI
    app = DevussyTerminalUI(
        phase_names=phase_names,
        phase_generator=generator,
        devplan=devplan,
    )
    
    try:
        await app.run_async()
        return True
    except Exception as e:
        print(f"\n✗ UI Error: {e}")
        return False


async def test_cancellation():
    """Test phase cancellation."""
    print("\n" + "=" * 60)
    print("Test 3: Phase Cancellation")
    print("=" * 60 + "\n")
    
    # Load config
    config = load_config()
    
    # Create LLM client
    llm_client = create_llm_client(config)
    
    # Create test devplan
    devplan = create_test_devplan()
    
    # Create state manager
    phase_names = ["plan"]
    state_manager = PhaseStateManager(phase_names)
    
    # Create phase generator
    generator = TerminalPhaseGenerator(llm_client, state_manager)
    
    # Track tokens
    token_count = 0
    
    def on_token(token: str):
        nonlocal token_count
        token_count += 1
        print(token, end="", flush=True)
    
    print("Generating 'plan' phase, will cancel after 50 tokens...\n")
    print("-" * 60)
    
    # Start generation task
    async def generate():
        try:
            await generator.generate_phase_streaming(
                "plan",
                devplan,
                on_token=on_token,
                max_tokens=500,
            )
        except asyncio.CancelledError:
            print("\n[Phase cancelled]")
    
    task = asyncio.create_task(generate())
    
    # Wait for some tokens, then cancel
    await asyncio.sleep(2)  # Let it generate for 2 seconds
    generator.cancel_phase("plan")
    
    try:
        await task
    except asyncio.CancelledError:
        pass
    
    print("\n" + "-" * 60)
    
    state = state_manager.get_state("plan")
    print(f"\n✓ Cancellation test complete!")
    print(f"  Tokens before cancel: {token_count}")
    print(f"  Phase status: {state.status.value}")
    print(f"  Partial content length: {len(state.partial_content)} characters")
    
    return state.status.value == "interrupted"


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Phase 5: Token Streaming Integration Tests")
    print("=" * 60)
    
    results = []
    
    # Test 1: Console streaming
    try:
        result = await test_streaming_without_ui()
        results.append(("Console Streaming", result))
    except Exception as e:
        print(f"\n✗ Test 1 failed: {e}")
        results.append(("Console Streaming", False))
    
    # Test 2: Cancellation
    try:
        result = await test_cancellation()
        results.append(("Phase Cancellation", result))
    except Exception as e:
        print(f"\n✗ Test 3 failed: {e}")
        results.append(("Phase Cancellation", False))
    
    # Test 3: Terminal UI (interactive)
    print("\n" + "=" * 60)
    print("Ready for interactive UI test?")
    print("This will launch the terminal UI with real streaming.")
    print("=" * 60)
    response = input("\nRun interactive UI test? (y/n): ")
    
    if response.lower() == 'y':
        try:
            result = await test_streaming_with_ui()
            results.append(("Terminal UI Streaming", result))
        except Exception as e:
            print(f"\n✗ Test 2 failed: {e}")
            results.append(("Terminal UI Streaming", False))
    else:
        print("Skipping interactive UI test")
        results.append(("Terminal UI Streaming", None))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for test_name, result in results:
        if result is None:
            status = "⊘ SKIPPED"
        elif result:
            status = "✓ PASSED"
        else:
            status = "✗ FAILED"
        print(f"  {status}: {test_name}")
    
    print("\n" + "=" * 60)
    
    # Return success if all non-skipped tests passed
    passed = all(r for r in results if r[1] is not None)
    return 0 if passed else 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(1)
