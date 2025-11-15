#!/usr/bin/env python3
"""
Demo script for Devussy terminal UI.

Simulates phase generation with fake streaming to test the UI layout and interactions.
"""

import asyncio
import random
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.terminal.terminal_ui import DevussyTerminalUI
from src.terminal.phase_state import PhaseStatus


async def simulate_phase_generation(app: DevussyTerminalUI, phase_name: str, delay: float = 0.5):
    """Simulate streaming generation for a phase.
    
    Args:
        app: Terminal UI app instance
        phase_name: Name of phase to simulate
        delay: Delay between token updates (seconds)
    """
    # Initialize phase
    app.state_manager.initialize_phase(
        phase_name,
        prompt=f"Generate {phase_name} phase...",
        api_context={"model": "gpt-4o-mini"}
    )
    app.update_phase(phase_name)
    
    # Simulate streaming tokens
    sample_content = [
        f"# {phase_name.upper()} Phase\n\n",
        "## Overview\n",
        f"This is the {phase_name} phase of the development plan.\n\n",
        "## Key Points\n",
        "- Point 1: Important consideration\n",
        "- Point 2: Another key aspect\n",
        "- Point 3: Critical requirement\n\n",
        "## Details\n",
        f"The {phase_name} phase involves several steps:\n",
        "1. First step with detailed explanation\n",
        "2. Second step with more context\n",
        "3. Third step completing the phase\n\n",
        "## Conclusion\n",
        f"The {phase_name} phase is now complete.\n",
    ]
    
    for token in sample_content:
        await asyncio.sleep(delay)
        app.state_manager.append_content(phase_name, token)
        app.update_phase(phase_name)
    
    # Mark complete
    app.state_manager.update_status(phase_name, PhaseStatus.COMPLETE)
    app.update_phase(phase_name)


async def run_demo(app: DevussyTerminalUI):
    """Run the demo simulation.
    
    Args:
        app: Terminal UI app instance
    """
    # Wait a bit for UI to initialize
    await asyncio.sleep(1)
    
    # Start all phases with staggered delays
    phases = ["plan", "design", "implement", "test", "review"]
    tasks = []
    
    for i, phase in enumerate(phases):
        # Stagger start times
        await asyncio.sleep(0.5)
        task = asyncio.create_task(simulate_phase_generation(app, phase, delay=0.1))
        tasks.append(task)
    
    # Wait for all phases to complete
    await asyncio.gather(*tasks)
    
    # Keep UI open for a bit to see final state
    await asyncio.sleep(5)
    
    # Exit
    app.exit()


def main():
    """Main entry point."""
    print("\n" + "=" * 60)
    print("Devussy Terminal UI Demo")
    print("=" * 60)
    print("\nStarting terminal UI with simulated phase generation...")
    print("Press 'q' to quit, '?' for help\n")
    
    # Create app
    app = DevussyTerminalUI()
    
    # Run demo in background
    async def run_with_demo():
        # Start demo task
        demo_task = asyncio.create_task(run_demo(app))
        
        # Run app (this blocks until app exits)
        try:
            await app.run_async()
        finally:
            # Cancel demo if still running
            if not demo_task.done():
                demo_task.cancel()
                try:
                    await demo_task
                except asyncio.CancelledError:
                    pass
    
    # Run everything
    try:
        asyncio.run(run_with_demo())
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
    
    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
