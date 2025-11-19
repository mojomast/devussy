"""Quick test to debug phase parsing."""

import sys
sys.path.insert(0, 'src')

from pipeline.basic_devplan import BasicDevPlanGenerator

# Sample response that might come from the LLM
sample_response = """
# Development Plan

## Phase 1: Setup and Configuration

This phase sets up the initial project structure and dependencies.

- Initialize repository
- Configure dependencies
- Setup CI/CD

## Phase 2: Core Implementation

Build the main application features and functionality.

- Implement API endpoints
- Create database models
- Add authentication

## Phase 3: Testing and Deployment

Ensure quality and deploy to production.

- Write unit tests
- Setup deployment pipeline
- Deploy to production
"""

generator = BasicDevPlanGenerator(llm_client=None)
devplan = generator._parse_response(sample_response, "test-project")

print(f"\n=== Parsed DevPlan ===")
print(f"Summary: {devplan.summary}")
print(f"Number of phases: {len(devplan.phases)}")
print()

for phase in devplan.phases:
    print(f"Phase {phase.number}: {phase.title}")
    print(f"  Description: {phase.description}")
    print(f"  Steps: {len(phase.steps)}")
    print()
