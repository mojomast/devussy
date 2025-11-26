"""
Run the full adaptive pipeline and save all outputs to test_output/adaptive_pipeline_results/

This script runs through the complete adaptive pipeline:
1. Complexity Analysis
2. Design Generation
3. Design Validation
4. LLM Sanity Review
5. Correction Loop (if needed)
6. DevPlan Generation
7. Handoff Prompt Generation
"""

import asyncio
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.interview.complexity_analyzer import LLMComplexityAnalyzer, ComplexityAnalyzer
from src.pipeline.design_validator import DesignValidator
from src.pipeline.llm_sanity_reviewer import LLMSanityReviewer, LLMSanityReviewerWithLLM
from src.pipeline.design_correction_loop import DesignCorrectionLoop, LLMDesignCorrectionLoop
from src.clients.requesty_client import RequestyClient


@dataclass
class LLMConfig:
    """Simple LLM configuration."""
    api_key: str
    model: str = "openai/gpt-4.1-nano"
    base_url: str = "https://router.requesty.ai/v1"
    temperature: float = 0.7
    max_tokens: int = 4096


@dataclass 
class SimpleConfig:
    """Simple config wrapper for RequestyClient."""
    llm: LLMConfig
    debug: bool = False


OUTPUT_DIR = Path("test_output/adaptive_pipeline_results")


def save_file(filename: str, content: str) -> None:
    """Save content to a file in the output directory."""
    filepath = OUTPUT_DIR / filename
    filepath.write_text(content, encoding="utf-8")
    print(f"  ✓ Saved: {filepath}")


async def run_full_pipeline():
    """Run the complete adaptive pipeline with a sample project."""
    
    print("=" * 60)
    print("ADAPTIVE PIPELINE - FULL TEST RUN")
    print("=" * 60)
    print(f"Output Directory: {OUTPUT_DIR.absolute()}")
    print()
    
    # Sample project: Medium complexity web API
    interview_data = {
        "project_name": "TaskFlow API",
        "project_type": "web_app",
        "requirements": """
Build a task management REST API with the following features:
- User authentication with JWT tokens
- CRUD operations for tasks and projects
- Real-time notifications via WebSockets
- PostgreSQL database with proper migrations
- Redis caching for frequently accessed data
- Rate limiting and request throttling
- Comprehensive API documentation (OpenAPI/Swagger)
- Unit and integration test coverage > 80%
""",
        "languages": ["Python", "TypeScript"],
        "frameworks": ["FastAPI", "SQLAlchemy", "Alembic", "Redis"],
        "apis": "Stripe for payments, SendGrid for emails",
        "team_size": "2-3",
    }
    
    # Initialize LLM client
    api_key = os.environ.get("REQUESTY_API_KEY", "")
    if not api_key:
        print("WARNING: REQUESTY_API_KEY not set, using empty key")
    
    llm_config = LLMConfig(api_key=api_key, model="openai/gpt-4.1-nano")
    config = SimpleConfig(llm=llm_config)
    client = RequestyClient(config)
    
    # =========================================================================
    # STAGE 1: Complexity Analysis
    # =========================================================================
    print("\n" + "=" * 60)
    print("STAGE 1: Complexity Analysis")
    print("=" * 60)
    
    # Static analysis first
    static_analyzer = ComplexityAnalyzer()
    static_profile = static_analyzer.analyze(interview_data)
    
    static_result = f"""# Static Complexity Analysis

## Profile Summary
- **Score**: {static_profile.score}
- **Estimated Phases**: {static_profile.estimated_phase_count}
- **Depth Level**: {static_profile.depth_level}
- **Confidence**: {static_profile.confidence}

## Breakdown
- Project Type: {interview_data.get('project_type', 'N/A')}
- Languages: {', '.join(interview_data.get('languages', []))}
- Frameworks: {', '.join(interview_data.get('frameworks', []))}
- Team Size: {interview_data.get('team_size', 'N/A')}
"""
    save_file("01_static_complexity.md", static_result)
    
    # LLM-driven analysis
    llm_analyzer = LLMComplexityAnalyzer(client)
    llm_result = await llm_analyzer.analyze_with_llm(interview_data)
    
    llm_complexity_md = f"""# LLM Complexity Analysis

## Profile Summary
- **Score**: {llm_result.complexity_score}
- **Estimated Phases**: {llm_result.estimated_phase_count}
- **Depth Level**: {llm_result.depth_level}
- **Confidence**: {llm_result.confidence}

## Rationale
{llm_result.rationale}

## Hidden Risks
{chr(10).join(f'- {risk}' for risk in llm_result.hidden_risks)}

## Follow-up Questions
{chr(10).join(f'- {q}' for q in llm_result.follow_up_questions) if llm_result.follow_up_questions else 'None needed (confidence > 0.7)'}
"""
    save_file("02_llm_complexity.md", llm_complexity_md)
    
    print(f"  Static Score: {static_profile.score}, LLM Score: {llm_result.complexity_score}")
    print(f"  Depth Level: {llm_result.depth_level}")
    
    # =========================================================================
    # STAGE 2: Design Generation (Mock for now)
    # =========================================================================
    print("\n" + "=" * 60)
    print("STAGE 2: Design Generation")
    print("=" * 60)
    
    # Generate a mock design based on complexity
    design_doc = f"""# TaskFlow API - Project Design

## Overview
TaskFlow API is a task management REST API built with FastAPI and PostgreSQL.

## Architecture

### System Components
- **API Layer**: FastAPI with async endpoints
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Cache**: Redis for session and frequently accessed data
- **Auth**: JWT-based authentication with refresh tokens
- **Notifications**: WebSocket server for real-time updates

### Tech Stack
- Python 3.11+
- FastAPI 0.100+
- SQLAlchemy 2.0
- Alembic for migrations
- Redis for caching
- Pydantic for validation

## Database Schema

### Users Table
- id (UUID, PK)
- email (VARCHAR, unique)
- password_hash (VARCHAR)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)

### Projects Table
- id (UUID, PK)
- name (VARCHAR)
- owner_id (FK -> Users)
- created_at (TIMESTAMP)

### Tasks Table
- id (UUID, PK)
- title (VARCHAR)
- description (TEXT)
- status (ENUM: pending, in_progress, completed)
- project_id (FK -> Projects)
- assignee_id (FK -> Users)
- due_date (TIMESTAMP)
- created_at (TIMESTAMP)

## API Endpoints

### Authentication
- POST /auth/register - Register new user
- POST /auth/login - Login and get JWT
- POST /auth/refresh - Refresh access token

### Projects
- GET /projects - List user's projects
- POST /projects - Create project
- GET /projects/{{id}} - Get project details
- PUT /projects/{{id}} - Update project
- DELETE /projects/{{id}} - Delete project

### Tasks
- GET /projects/{{project_id}}/tasks - List tasks
- POST /projects/{{project_id}}/tasks - Create task
- GET /tasks/{{id}} - Get task details
- PUT /tasks/{{id}} - Update task
- DELETE /tasks/{{id}} - Delete task

## Testing Strategy

### Unit Tests
- Model validation tests
- Service layer tests
- Utility function tests

### Integration Tests
- API endpoint tests with TestClient
- Database transaction tests
- Authentication flow tests

### E2E Tests
- Full user journey tests
- WebSocket notification tests

## Security Considerations
- JWT tokens with short expiry (15 min access, 7 day refresh)
- Password hashing with bcrypt
- Rate limiting per IP and per user
- Input validation with Pydantic
- SQL injection prevention via ORM
"""
    save_file("03_project_design.md", design_doc)
    print("  ✓ Design document generated")
    
    # =========================================================================
    # STAGE 3: Design Validation
    # =========================================================================
    print("\n" + "=" * 60)
    print("STAGE 3: Design Validation (Rule-Based)")
    print("=" * 60)
    
    validator = DesignValidator()
    validation_report = validator.validate(design_doc, complexity_profile=static_profile)
    
    validation_md = f"""# Design Validation Report

## Summary
- **Valid**: {'✅ Yes' if validation_report.is_valid else '❌ No'}
- **Auto-Correctable**: {'Yes' if validation_report.auto_correctable else 'No'}

## Check Results
| Check | Result |
|-------|--------|
| Completeness | {'✅' if validation_report.checks.get('completeness', False) else '❌'} |
| Consistency | {'✅' if validation_report.checks.get('consistency', False) else '❌'} |
| Scope Alignment | {'✅' if validation_report.checks.get('scope_alignment', False) else '❌'} |
| Hallucination | {'✅' if validation_report.checks.get('hallucination', False) else '❌'} |
| Over-Engineering | {'✅' if validation_report.checks.get('over_engineering', False) else '❌'} |

## Issues Found
"""
    if validation_report.issues:
        for issue in validation_report.issues:
            validation_md += f"""
### {issue.code}
- **Severity**: {issue.severity}
- **Message**: {issue.message}
- **Auto-Correctable**: {'Yes' if issue.auto_correctable else 'No'}
- **Suggestion**: {issue.suggestion}
"""
    else:
        validation_md += "\nNo issues found! Design passed all validation checks.\n"
    
    save_file("04_validation_report.md", validation_md)
    print(f"  Valid: {validation_report.is_valid}, Issues: {len(validation_report.issues)}")
    
    # =========================================================================
    # STAGE 4: LLM Sanity Review
    # =========================================================================
    print("\n" + "=" * 60)
    print("STAGE 4: LLM Sanity Review")
    print("=" * 60)
    
    llm_reviewer = LLMSanityReviewerWithLLM(client)
    sanity_result = await llm_reviewer.review_with_llm(design_doc, validation_report)
    
    sanity_md = f"""# LLM Sanity Review

## Overall Assessment
- **Confidence**: {sanity_result.confidence}%
- **Assessment**: {sanity_result.overall_assessment}
- **Coherence Score**: {sanity_result.coherence_score}%

## Hallucination Check
- **Result**: {'✅ Passed' if sanity_result.hallucination_passed else '❌ Failed'}

## Scope Alignment
"""
    if sanity_result.scope_alignment:
        sanity_md += f"""- **Score**: {sanity_result.scope_alignment.score}
- **Missing Requirements**: {', '.join(sanity_result.scope_alignment.missing_requirements) if sanity_result.scope_alignment.missing_requirements else 'None'}
- **Over-Engineered**: {', '.join(sanity_result.scope_alignment.over_engineered) if sanity_result.scope_alignment.over_engineered else 'None'}
- **Under-Engineered**: {', '.join(sanity_result.scope_alignment.under_engineered) if sanity_result.scope_alignment.under_engineered else 'None'}
"""
    else:
        sanity_md += "No scope alignment data available.\n"
    
    sanity_md += """
## Risks Identified
"""
    for risk in sanity_result.risks:
        sanity_md += f"- **{risk.severity.upper()}**: {risk.description}\n"
    
    sanity_md += f"""
## Suggestions
"""
    for suggestion in sanity_result.suggestions:
        sanity_md += f"- {suggestion}\n"
    
    sanity_md += f"""
## Hallucination Issues
"""
    if sanity_result.hallucination_issues:
        for issue in sanity_result.hallucination_issues:
            sanity_md += f"- **{issue.item}** ({issue.category}): {issue.details}\n"
    else:
        sanity_md += "No hallucination issues detected.\n"
    
    save_file("05_sanity_review.md", sanity_md)
    print(f"  Confidence: {sanity_result.confidence}%, Assessment: {sanity_result.overall_assessment}")
    
    # =========================================================================
    # STAGE 5: Correction Loop (if needed)
    # =========================================================================
    print("\n" + "=" * 60)
    print("STAGE 5: Correction Loop")
    print("=" * 60)
    
    corrected_design = design_doc
    correction_history = []
    correction_result = None  # Initialize to None
    
    if not validation_report.is_valid or sanity_result.overall_assessment == "problematic":
        print("  Running correction loop...")
        
        llm_corrector = LLMDesignCorrectionLoop(client)
        correction_result = await llm_corrector.run_with_llm(
            design_doc, 
            validation_report,
            max_iterations=3
        )
        
        corrected_design = correction_result.corrected_design
        
        correction_md = f"""# Correction Loop Results

## Summary
- **Iterations Used**: {correction_result.iterations_used}
- **Final Valid**: {'✅ Yes' if correction_result.is_valid else '❌ No'}
- **Requires Human Review**: {'Yes' if correction_result.requires_human_review else 'No'}
- **Max Iterations Reached**: {'Yes' if correction_result.max_iterations_reached else 'No'}

## Changes Made
"""
        for change in correction_result.changes:
            correction_md += f"""
### {change.issue_code}
- **Action**: {change.action}
- **Original**: {change.original_text[:100]}...
- **Corrected**: {change.corrected_text[:100]}...
"""
        
        save_file("06_correction_loop.md", correction_md)
        save_file("07_corrected_design.md", corrected_design)
        print(f"  Iterations: {correction_result.iterations_used}, Valid: {correction_result.is_valid}")
    else:
        print("  No correction needed - design passed validation")
        save_file("06_correction_loop.md", "# Correction Loop\n\nNo correction needed - design passed all validation checks.")
    
    # =========================================================================
    # STAGE 6: DevPlan Generation (REAL LLM)
    # =========================================================================
    print("\n" + "=" * 60)
    print("STAGE 6: DevPlan Generation (Real LLM)")
    print("=" * 60)
    
    from src.pipeline.basic_devplan import BasicDevPlanGenerator
    from src.pipeline.detailed_devplan import DetailedDevPlanGenerator
    from src.concurrency import ConcurrencyManager
    from src.models import ProjectDesign
    
    # Create project design from interview data
    project_design = ProjectDesign(
        project_name=interview_data["project_name"],
        objectives=[
            "Build a scalable task management API",
            "Implement secure user authentication",
            "Support real-time notifications",
            "Achieve high test coverage"
        ],
        tech_stack=interview_data.get("frameworks", []),
        architecture_overview=corrected_design if correction_result else design_doc,
        dependencies=["FastAPI", "SQLAlchemy", "Alembic", "Redis", "PostgreSQL"],
        challenges=["Real-time WebSocket scaling", "Secure auth implementation"],
        mitigations=["Use Redis pub/sub", "Follow OWASP guidelines"],
        complexity=llm_result.depth_level.capitalize(),
        estimated_phases=llm_result.estimated_phase_count,
    )
    
    print(f"  Generating {project_design.estimated_phases} phases (depth: {project_design.complexity})...")
    
    # Generate basic devplan with LLM
    basic_gen = BasicDevPlanGenerator(client)
    concurrency = ConcurrencyManager(max_concurrent=5)
    
    print("  Step 1: Generating basic devplan structure...")
    basic_devplan = await basic_gen.generate(project_design)
    print(f"    -> Got {len(basic_devplan.phases)} phases from basic devplan")
    
    # Generate detailed steps for each phase
    print("  Step 2: Generating detailed steps for each phase...")
    detailed_gen = DetailedDevPlanGenerator(client, concurrency)
    
    def on_phase_complete(result):
        print(f"    -> Phase {result.phase.number}: {len(result.phase.steps)} steps ({result.response_chars} chars)")
    
    detailed_devplan = await detailed_gen.generate(
        basic_devplan,
        project_name=interview_data["project_name"],
        tech_stack=interview_data.get("frameworks", []),
        on_phase_complete=on_phase_complete,
    )
    
    print(f"  Generated detailed devplan with {len(detailed_devplan.phases)} phases")
    
    # Generate devplan markdown
    phase_count = len(detailed_devplan.phases)
    depth = llm_result.depth_level
    
    devplan_md = f"""# Development Plan - {interview_data["project_name"]}

## Project Dashboard

| Metric | Value |
|--------|-------|
| Complexity Score | {llm_result.complexity_score} |
| Depth Level | {depth} |
| Estimated Phases | {phase_count} |
| Confidence | {llm_result.confidence} |

### Phase Overview

| Phase | Name | Steps | Status |
|-------|------|-------|--------|
"""
    
    for phase in detailed_devplan.phases:
        devplan_md += f"| {phase.number} | {phase.title} | {len(phase.steps)} | Not Started |\n"
    
    devplan_md += """
<!-- PROGRESS_LOG_START -->
## Progress Log

_No progress yet - project starting_

<!-- PROGRESS_LOG_END -->

<!-- NEXT_TASK_GROUP_START -->
## Next Tasks

"""
    # Add first 5 tasks from phase 1
    if detailed_devplan.phases and detailed_devplan.phases[0].steps:
        for i, step in enumerate(detailed_devplan.phases[0].steps[:5], 1):
            devplan_md += f"{i}. [ ] {step.number}: {step.description}\n"
    
    devplan_md += """
<!-- NEXT_TASK_GROUP_END -->
"""
    
    save_file("08_devplan.md", devplan_md)
    
    # Generate individual phase files with FULL DETAIL
    for phase in detailed_devplan.phases:
        phase_md = f"""# Phase {phase.number}: {phase.title}

**Project**: {interview_data["project_name"]}
**Total Steps**: {len(phase.steps)}
**Depth Level**: {depth}

## Tasks

<!-- PHASE_TASKS_START -->
"""
        for step in phase.steps:
            phase_md += f"\n### {step.number}: {step.description}\n"
            if step.details:
                for detail in step.details:
                    phase_md += f"- {detail}\n"
            else:
                phase_md += "- (No sub-details generated)\n"
        
        phase_md += """
<!-- PHASE_TASKS_END -->

## Context

<!-- PHASE_CONTEXT_START -->
This phase is part of the adaptive pipeline with complexity-aware generation.
<!-- PHASE_CONTEXT_END -->

## Outcomes

<!-- PHASE_OUTCOMES_START -->
<!-- Updates added as tasks complete -->
<!-- PHASE_OUTCOMES_END -->
"""
        save_file(f"phase{phase.number}.md", phase_md)
    
    print(f"  Generated {len(detailed_devplan.phases)} detailed phase files")
    
    # =========================================================================
    # STAGE 7: Handoff Prompt
    # =========================================================================
    print("\n" + "=" * 60)
    print("STAGE 7: Handoff Prompt")
    print("=" * 60)
    
    handoff_md = f"""# Handoff Prompt - TaskFlow API

## Project Context

**Project**: TaskFlow API
**Complexity**: {llm_result.depth_level.upper()} ({llm_result.complexity_score}/20)
**Phases**: {phase_count}

## Quick Status

<!-- QUICK_STATUS_START -->
- **Current Phase**: 1 - Project Setup
- **Completion**: 0%
- **Blockers**: None
- **Next Action**: Initialize repository
<!-- QUICK_STATUS_END -->

## Tech Stack Summary

- **Backend**: FastAPI + SQLAlchemy + PostgreSQL
- **Cache**: Redis
- **Auth**: JWT tokens
- **Testing**: pytest + TestClient

## Key Design Decisions

1. **Async-first**: All endpoints use async/await for performance
2. **Repository pattern**: Service layer between API and database
3. **Pydantic validation**: All inputs validated with Pydantic models
4. **Alembic migrations**: Database changes tracked in version control

## Validation Summary

- Rule-based validation: {'✅ Passed' if validation_report.is_valid else '⚠️ Issues found'}
- LLM sanity review: {sanity_result.overall_assessment} ({sanity_result.confidence}% confidence)

## Hidden Risks

{chr(10).join(f'- {risk}' for risk in llm_result.hidden_risks)}

<!-- HANDOFF_NOTES_START -->
## Handoff Notes

_No handoff notes yet - project starting_

<!-- HANDOFF_NOTES_END -->

## Files Generated

1. `01_static_complexity.md` - Static complexity analysis
2. `02_llm_complexity.md` - LLM-driven complexity analysis
3. `03_project_design.md` - Full project design document
4. `04_validation_report.md` - Rule-based validation results
5. `05_sanity_review.md` - LLM sanity review results
6. `06_correction_loop.md` - Correction loop summary
7. `07_corrected_design.md` - Corrected design (if applicable)
8. `08_devplan.md` - Development plan with phases
9. `phase1.md` - `phase{phase_count}.md` - Individual phase files
10. `09_handoff.md` - This handoff document
"""
    
    save_file("09_handoff.md", handoff_md)
    print("  ✓ Handoff prompt generated")
    
    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)
    print(f"\nAll outputs saved to: {OUTPUT_DIR.absolute()}")
    print("\nFiles generated:")
    for f in sorted(OUTPUT_DIR.glob("*.md")):
        print(f"  - {f.name}")


if __name__ == "__main__":
    asyncio.run(run_full_pipeline())
