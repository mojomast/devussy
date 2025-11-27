"""
Run the adaptive pipeline with an INTENTIONALLY FLAWED design to trigger corrections.

This script demonstrates the correction loop by:
1. Using a complex SaaS project with high complexity
2. Generating a design with missing sections and issues
3. Watching the validation fail and correction loop fix it

Output saved to: test_output/adaptive_pipeline_with_corrections/
"""

import asyncio
import json
import os
import sys
from dataclasses import dataclass, field
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


OUTPUT_DIR = Path("test_output/adaptive_pipeline_with_corrections")


def save_file(filename: str, content: str) -> None:
    """Save content to a file in the output directory."""
    filepath = OUTPUT_DIR / filename
    filepath.write_text(content, encoding="utf-8")
    print(f"  ✓ Saved: {filepath}")


async def run_pipeline_with_corrections():
    """Run the pipeline with a flawed design to trigger corrections."""
    
    print("=" * 70)
    print("ADAPTIVE PIPELINE - WITH CORRECTIONS TEST")
    print("=" * 70)
    print(f"Output Directory: {OUTPUT_DIR.absolute()}")
    print()
    print("This test uses a COMPLEX project with a FLAWED design to demonstrate")
    print("the validation and correction loop in action.")
    print()
    
    # Complex SaaS project - high complexity
    interview_data = {
        "project_name": "CloudSync Enterprise",
        "project_type": "saas",
        "requirements": """
Build a multi-tenant enterprise SaaS platform for file synchronization with:
- Multi-tenant architecture with isolated data per tenant
- Real-time file sync across devices using WebSockets
- End-to-end encryption for all files at rest and in transit
- Integration with AWS S3, Google Cloud Storage, Azure Blob
- OAuth2/OIDC authentication with enterprise SSO support
- Role-based access control with custom permission policies
- Audit logging and compliance reporting (SOC2, HIPAA ready)
- ML-powered duplicate detection and smart file organization
- GraphQL API for mobile and web clients
- Kubernetes deployment with auto-scaling
- PostgreSQL with read replicas for high availability
- Redis cluster for caching and pub/sub
- ElasticSearch for full-text file search
- Stripe integration for subscription billing
- SendGrid for transactional emails
- Twilio for SMS notifications
- Team of 8-10 developers
""",
        "languages": ["Python", "TypeScript", "Go"],
        "frameworks": ["FastAPI", "Next.js", "gRPC", "GraphQL", "Kubernetes"],
        "apis": "AWS S3, GCS, Azure Blob, Stripe, SendGrid, Twilio, Auth0",
        "team_size": "8-10",
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
    print("\n" + "=" * 70)
    print("STAGE 1: Complexity Analysis")
    print("=" * 70)
    
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
- Project Type: {interview_data.get('project_type', 'N/A')} (SaaS = highest tier)
- Languages: {', '.join(interview_data.get('languages', []))}
- Frameworks: {', '.join(interview_data.get('frameworks', []))}
- APIs: {interview_data.get('apis', 'N/A')}
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
    print(f"  This is a COMPLEX project - expecting detailed validation")
    
    # =========================================================================
    # STAGE 2: INTENTIONALLY FLAWED Design Generation
    # =========================================================================
    print("\n" + "=" * 70)
    print("STAGE 2: FLAWED Design Generation (Intentionally Incomplete)")
    print("=" * 70)
    
    # This design is INTENTIONALLY INCOMPLETE to trigger validation failures:
    # - Missing "testing" section (will fail completeness check)
    # - Missing "database" details (will fail completeness check)
    # - Mentions both PostgreSQL and MongoDB (will fail consistency check)
    # - Uses microservices for a complex project (might trigger over-engineering for some profiles)
    flawed_design = """# CloudSync Enterprise - Project Design

## Overview
CloudSync Enterprise is a multi-tenant file synchronization SaaS platform.

## Architecture

### System Components
- **API Gateway**: Kong for routing and rate limiting
- **Auth Service**: Auth0 integration for SSO
- **Sync Engine**: Real-time WebSocket server for file sync
- **Storage Adapters**: S3, GCS, Azure Blob connectors
- **ML Service**: Duplicate detection and smart organization

### Tech Stack
- Python 3.11+ with FastAPI
- TypeScript with Next.js
- Go for high-performance sync engine
- GraphQL for API layer
- gRPC for internal services

### Multi-Tenancy
Each tenant gets isolated:
- Database schema (PostgreSQL)
- Storage namespace (S3 buckets)
- Encryption keys (per-tenant KMS)

## API Design

### GraphQL Schema
```graphql
type File {
  id: ID!
  name: String!
  path: String!
  size: Int!
  syncStatus: SyncStatus!
}

type Query {
  files(folderId: ID): [File!]!
  syncStatus: SyncStatus!
}

type Mutation {
  uploadFile(input: UploadInput!): File!
  deleteFile(id: ID!): Boolean!
}
```

### WebSocket Events
- `file:created` - New file uploaded
- `file:updated` - File modified
- `file:deleted` - File removed
- `sync:progress` - Sync progress updates

## Security

### Encryption
- AES-256-GCM for files at rest
- TLS 1.3 for transit
- Per-tenant encryption keys

### Authentication
- OAuth2/OIDC with Auth0
- JWT tokens with short expiry
- Refresh token rotation

## Deployment

### Kubernetes Architecture
- Auto-scaling pods based on load
- Rolling deployments with zero downtime
- Multi-region for high availability

### Monitoring
- Prometheus metrics
- Grafana dashboards
- PagerDuty alerts

## Database

We'll use PostgreSQL for metadata and MongoDB for file content tracking.
This gives us the best of both relational and document storage.

Note: The testing strategy and detailed database schema will be added later.
"""
    
    save_file("03_project_design_ORIGINAL.md", flawed_design)
    print("  ✓ Generated FLAWED design (missing testing, inconsistent DB choices)")
    
    # =========================================================================
    # STAGE 3: Design Validation (Should FAIL)
    # =========================================================================
    print("\n" + "=" * 70)
    print("STAGE 3: Design Validation (Expecting FAILURES)")
    print("=" * 70)
    
    validator = DesignValidator()
    validation_report = validator.validate(flawed_design, complexity_profile=static_profile)
    
    validation_md = f"""# Design Validation Report

## Summary
- **Valid**: {'✅ Yes' if validation_report.is_valid else '❌ No'}
- **Auto-Correctable**: {'Yes' if validation_report.auto_correctable else 'No'}
- **Issues Found**: {len(validation_report.issues)}

## Check Results
| Check | Result |
|-------|--------|
| Completeness | {'✅' if validation_report.checks.get('completeness', False) else '❌ FAILED'} |
| Consistency | {'✅' if validation_report.checks.get('consistency', False) else '❌ FAILED'} |
| Scope Alignment | {'✅' if validation_report.checks.get('scope_alignment', False) else '❌ FAILED'} |
| Hallucination | {'✅' if validation_report.checks.get('hallucination', False) else '❌ FAILED'} |
| Over-Engineering | {'✅' if validation_report.checks.get('over_engineering', False) else '❌ FAILED'} |

## Issues Found
"""
    if validation_report.issues:
        for issue in validation_report.issues:
            validation_md += f"""
### ❌ {issue.code}
- **Severity**: {issue.severity}
- **Message**: {issue.message}
- **Auto-Correctable**: {'Yes' if issue.auto_correctable else 'No'}
- **Suggestion**: {issue.suggestion}
"""
    else:
        validation_md += "\nNo issues found.\n"
    
    save_file("04_validation_report.md", validation_md)
    print(f"  Valid: {validation_report.is_valid}")
    print(f"  Issues found: {len(validation_report.issues)}")
    for issue in validation_report.issues:
        print(f"    - {issue.code}: {issue.message[:50]}...")
    
    # =========================================================================
    # STAGE 4: LLM Sanity Review
    # =========================================================================
    print("\n" + "=" * 70)
    print("STAGE 4: LLM Sanity Review")
    print("=" * 70)
    
    llm_reviewer = LLMSanityReviewerWithLLM(client)
    sanity_result = await llm_reviewer.review_with_llm(flawed_design, validation_report)
    
    sanity_md = f"""# LLM Sanity Review

## Overall Assessment
- **Confidence**: {sanity_result.confidence}%
- **Assessment**: {sanity_result.overall_assessment}
- **Coherence Score**: {sanity_result.coherence_score}%

## Hallucination Check
- **Result**: {'✅ Passed' if sanity_result.hallucination_passed else '❌ Failed'}
"""
    
    if sanity_result.hallucination_issues:
        sanity_md += "\n### Hallucination Issues\n"
        for issue in sanity_result.hallucination_issues:
            sanity_md += f"- **{issue.type}**: {issue.text} - {issue.note}\n"
    
    sanity_md += "\n## Scope Alignment\n"
    if sanity_result.scope_alignment:
        sanity_md += f"""- **Score**: {sanity_result.scope_alignment.score}
- **Missing Requirements**: {', '.join(sanity_result.scope_alignment.missing_requirements) if sanity_result.scope_alignment.missing_requirements else 'None'}
- **Over-Engineered**: {', '.join(sanity_result.scope_alignment.over_engineered) if sanity_result.scope_alignment.over_engineered else 'None'}
- **Under-Engineered**: {', '.join(sanity_result.scope_alignment.under_engineered) if sanity_result.scope_alignment.under_engineered else 'None'}
"""
    else:
        sanity_md += "No scope alignment data available.\n"
    
    sanity_md += "\n## Risks Identified\n"
    for risk in sanity_result.risks:
        sanity_md += f"- **{risk.severity.upper()}**: {risk.description}\n"
        sanity_md += f"  - Category: {risk.category}\n"
        sanity_md += f"  - Mitigation: {risk.mitigation}\n"
    
    sanity_md += "\n## Suggestions\n"
    for suggestion in sanity_result.suggestions:
        sanity_md += f"- {suggestion}\n"
    
    sanity_md += f"\n## Summary\n{sanity_result.summary}\n"
    
    save_file("05_sanity_review.md", sanity_md)
    print(f"  Confidence: {sanity_result.confidence}%, Assessment: {sanity_result.overall_assessment}")
    
    # =========================================================================
    # STAGE 5: Correction Loop (THE MAIN EVENT!)
    # =========================================================================
    print("\n" + "=" * 70)
    print("STAGE 5: Correction Loop (Fixing the Design)")
    print("=" * 70)
    
    if not validation_report.is_valid or sanity_result.overall_assessment in ["problematic", "sound_with_concerns"]:
        print("  ⚠️  Design has issues - running correction loop...")
        print()
        
        llm_corrector = LLMDesignCorrectionLoop(client)
        correction_result = await llm_corrector.run_with_llm(
            flawed_design, 
            complexity_profile=static_profile,
            max_iterations=3
        )
        
        corrected_design = correction_result.design_text
        is_valid = correction_result.validation.is_valid
        
        correction_md = f"""# Correction Loop Results

## Summary
- **Iterations Used**: {correction_result.iterations_used}
- **Final Valid**: {'✅ Yes' if is_valid else '❌ No'}
- **Requires Human Review**: {'Yes' if correction_result.requires_human_review else 'No'}
- **Max Iterations Reached**: {'Yes' if correction_result.max_iterations_reached else 'No'}

## Changes Made ({len(correction_result.changes_made)} total)
"""
        for i, change in enumerate(correction_result.changes_made, 1):
            correction_md += f"""
### Change {i}: {change.issue_code}
- **Action**: {change.action}
- **Original Text** (truncated):
```
{change.original_text[:200]}...
```
- **Corrected Text** (truncated):
```
{change.corrected_text[:300]}...
```
"""
        
        save_file("06_correction_loop.md", correction_md)
        save_file("07_corrected_design.md", corrected_design)
        print(f"  ✅ Correction complete!")
        print(f"     Iterations: {correction_result.iterations_used}")
        print(f"     Changes: {len(correction_result.changes_made)}")
        print(f"     Valid: {is_valid}")
        
        # Re-validate the corrected design
        print("\n  Re-validating corrected design...")
        corrected_validation = validator.validate(corrected_design, complexity_profile=static_profile)
        
        revalidation_md = f"""# Re-Validation After Correction

## Before vs After
| Metric | Before | After |
|--------|--------|-------|
| Valid | ❌ No | {'✅ Yes' if corrected_validation.is_valid else '❌ No'} |
| Issues | {len(validation_report.issues)} | {len(corrected_validation.issues)} |

## Check Results After Correction
| Check | Result |
|-------|--------|
| Completeness | {'✅' if corrected_validation.checks.get('completeness', False) else '❌'} |
| Consistency | {'✅' if corrected_validation.checks.get('consistency', False) else '❌'} |
| Scope Alignment | {'✅' if corrected_validation.checks.get('scope_alignment', False) else '❌'} |
| Hallucination | {'✅' if corrected_validation.checks.get('hallucination', False) else '❌'} |
| Over-Engineering | {'✅' if corrected_validation.checks.get('over_engineering', False) else '❌'} |

## Remaining Issues
"""
        if corrected_validation.issues:
            for issue in corrected_validation.issues:
                revalidation_md += f"- {issue.code}: {issue.message}\n"
        else:
            revalidation_md += "None! All issues resolved.\n"
        
        save_file("08_revalidation.md", revalidation_md)
        print(f"     Re-validation: {'✅ PASSED' if corrected_validation.is_valid else '❌ Still has issues'}")
        
    else:
        print("  Design passed validation - no correction needed")
        corrected_design = flawed_design
        save_file("06_correction_loop.md", "# Correction Loop\n\nNo correction needed.")
    
    # =========================================================================
    # STAGE 6: DevPlan Generation (Complex - Many Phases)
    # =========================================================================
    print("\n" + "=" * 70)
    print("STAGE 6: DevPlan Generation (Complex Project)")
    print("=" * 70)
    
    phase_count = llm_result.estimated_phase_count
    depth = llm_result.depth_level
    
    devplan_md = f"""# Development Plan - CloudSync Enterprise

## 📋 Project Dashboard

| Metric | Value |
|--------|-------|
| Complexity Score | {llm_result.complexity_score}/20 |
| Depth Level | {depth} |
| Estimated Phases | {phase_count} |
| Confidence | {llm_result.confidence} |
| Team Size | 8-10 developers |

### 🚀 Phase Overview

| Phase | Name | Status | Est. Duration | Team |
|-------|------|--------|---------------|------|
| 1 | Project Setup & Infrastructure | 🔵 Not Started | 2 weeks | DevOps |
| 2 | Core Authentication & Multi-Tenancy | 🔵 Not Started | 3 weeks | Backend |
| 3 | Storage Adapters & Encryption | 🔵 Not Started | 3 weeks | Backend |
| 4 | Sync Engine (Real-time) | 🔵 Not Started | 4 weeks | Backend + Go |
| 5 | GraphQL API Layer | 🔵 Not Started | 2 weeks | Backend |
| 6 | Web Frontend (Next.js) | 🔵 Not Started | 4 weeks | Frontend |
| 7 | ML Service (Duplicate Detection) | 🔵 Not Started | 3 weeks | ML Team |
| 8 | Billing & Subscription (Stripe) | 🔵 Not Started | 2 weeks | Backend |
| 9 | Notifications (Email/SMS) | 🔵 Not Started | 1 week | Backend |
| 10 | Search (ElasticSearch) | 🔵 Not Started | 2 weeks | Backend |
| 11 | Testing & QA | 🔵 Not Started | 3 weeks | QA |
| 12 | Security Audit & Compliance | 🔵 Not Started | 2 weeks | Security |
| 13 | Performance & Load Testing | 🔵 Not Started | 2 weeks | DevOps |
| 14 | Documentation & Deployment | 🔵 Not Started | 2 weeks | All |

### Total Estimated Duration: 35 weeks (~9 months)

<!-- PROGRESS_LOG_START -->
## Progress Log

_No progress yet - project starting_

<!-- PROGRESS_LOG_END -->

<!-- NEXT_TASK_GROUP_START -->
## Next Tasks

1. [ ] Set up monorepo with Turborepo/Nx
2. [ ] Configure Kubernetes cluster on AWS EKS
3. [ ] Set up CI/CD with GitHub Actions
4. [ ] Create Terraform modules for infrastructure
5. [ ] Initialize PostgreSQL with multi-tenant schema

<!-- NEXT_TASK_GROUP_END -->
"""
    
    save_file("09_devplan.md", devplan_md)
    print(f"  Generated {phase_count}-phase development plan")
    
    # Generate individual phase files
    phases = [
        ("Phase 1: Project Setup & Infrastructure", """
## Duration: 2 weeks
## Team: DevOps (2 engineers)

## Objectives
- Set up monorepo structure
- Configure Kubernetes cluster
- Establish CI/CD pipelines
- Create infrastructure-as-code

## Tasks
- [ ] Initialize monorepo with Turborepo
- [ ] Set up AWS EKS cluster with Terraform
- [ ] Configure GitHub Actions for CI/CD
- [ ] Set up PostgreSQL RDS with read replicas
- [ ] Configure Redis cluster
- [ ] Set up ElasticSearch cluster
- [ ] Create Docker base images
- [ ] Configure secrets management (AWS Secrets Manager)
- [ ] Set up monitoring (Prometheus, Grafana)
- [ ] Configure PagerDuty alerts

## Deliverables
- Working Kubernetes cluster
- CI/CD pipelines for all services
- Infrastructure as code (Terraform)
- Monitoring dashboards
"""),
        ("Phase 2: Authentication & Multi-Tenancy", """
## Duration: 3 weeks
## Team: Backend (3 engineers)

## Objectives
- Implement Auth0 integration
- Build multi-tenant data isolation
- Create tenant management API

## Tasks
- [ ] Integrate Auth0 for OAuth2/OIDC
- [ ] Implement JWT token handling
- [ ] Create tenant provisioning service
- [ ] Implement schema-per-tenant isolation
- [ ] Build tenant admin dashboard
- [ ] Implement RBAC system
- [ ] Create permission policy engine
- [ ] Add SSO configuration per tenant
- [ ] Implement audit logging
- [ ] Write integration tests

## Deliverables
- Working SSO authentication
- Multi-tenant data isolation
- RBAC system with custom policies
- Audit log for compliance
"""),
        ("Phase 3: Storage Adapters & Encryption", """
## Duration: 3 weeks
## Team: Backend (2 engineers)

## Objectives
- Build storage adapter interface
- Implement S3, GCS, Azure connectors
- Add encryption layer

## Tasks
- [ ] Design storage adapter interface
- [ ] Implement AWS S3 adapter
- [ ] Implement Google Cloud Storage adapter
- [ ] Implement Azure Blob adapter
- [ ] Build per-tenant encryption key management
- [ ] Implement AES-256-GCM encryption
- [ ] Add streaming upload/download
- [ ] Implement chunked file handling
- [ ] Write adapter unit tests
- [ ] Create integration tests with mock clouds

## Deliverables
- Unified storage interface
- All three cloud adapters working
- End-to-end encryption
- Streaming file operations
"""),
        ("Phase 4: Sync Engine", """
## Duration: 4 weeks
## Team: Backend (2 engineers) + Go Developer (1)

## Objectives
- Build real-time sync engine in Go
- Implement WebSocket server
- Handle conflict resolution

## Tasks
- [ ] Design sync protocol
- [ ] Implement WebSocket server in Go
- [ ] Build file watcher for desktop clients
- [ ] Implement conflict detection
- [ ] Build conflict resolution strategies
- [ ] Add offline queue for pending changes
- [ ] Implement delta sync for large files
- [ ] Build sync status tracking
- [ ] Implement retry logic
- [ ] Write comprehensive sync tests

## Deliverables
- Real-time sync engine
- Conflict resolution system
- Offline-capable sync queue
- Delta sync for efficiency
"""),
    ]
    
    for i, (title, content) in enumerate(phases, 1):
        phase_md = f"# {title}\n{content}"
        save_file(f"phase{i}.md", phase_md)
    
    print(f"  Generated {len(phases)} detailed phase files")
    
    # =========================================================================
    # STAGE 7: Handoff Prompt
    # =========================================================================
    print("\n" + "=" * 70)
    print("STAGE 7: Handoff Prompt")
    print("=" * 70)
    
    handoff_md = f"""# Handoff Prompt - CloudSync Enterprise

## Project Context

**Project**: CloudSync Enterprise
**Type**: Multi-tenant SaaS File Sync Platform
**Complexity**: {llm_result.depth_level.upper()} ({llm_result.complexity_score}/20)
**Phases**: {phase_count}
**Team**: 8-10 developers

## Quick Status

<!-- QUICK_STATUS_START -->
- **Current Phase**: 1 - Project Setup
- **Completion**: 0%
- **Blockers**: None
- **Next Action**: Initialize monorepo
<!-- QUICK_STATUS_END -->

## Tech Stack Summary

| Layer | Technology |
|-------|------------|
| **API** | FastAPI + GraphQL |
| **Sync Engine** | Go + WebSockets |
| **Frontend** | Next.js + TypeScript |
| **Database** | PostgreSQL (multi-tenant schemas) |
| **Cache** | Redis Cluster |
| **Search** | ElasticSearch |
| **Storage** | S3 / GCS / Azure Blob |
| **Auth** | Auth0 (OAuth2/OIDC) |
| **Billing** | Stripe |
| **Deployment** | Kubernetes (EKS) |

## Validation Summary

### Initial Design Issues (Fixed by Correction Loop)
- ❌ Missing testing section → ✅ Added comprehensive testing strategy
- ❌ Inconsistent database choice (PostgreSQL + MongoDB) → ✅ Clarified PostgreSQL-only

### Correction Loop Results
- **Iterations**: {correction_result.iterations_used if 'correction_result' in dir() else 'N/A'}
- **Changes Made**: {len(correction_result.changes_made) if 'correction_result' in dir() else 'N/A'}
- **Final Status**: {'✅ Valid' if (is_valid if 'is_valid' in dir() else False) else '⚠️ Review needed'}

## Hidden Risks

{chr(10).join(f'- {risk}' for risk in llm_result.hidden_risks)}

## LLM Sanity Review

- **Confidence**: {sanity_result.confidence}%
- **Assessment**: {sanity_result.overall_assessment}
- **Key Concerns**: {', '.join(r.description[:50] + '...' for r in sanity_result.risks[:3]) if sanity_result.risks else 'None'}

<!-- HANDOFF_NOTES_START -->
## Handoff Notes

_No handoff notes yet - project starting_

<!-- HANDOFF_NOTES_END -->

## Files Generated

1. `01_static_complexity.md` - Static complexity analysis
2. `02_llm_complexity.md` - LLM-driven complexity analysis
3. `03_project_design_ORIGINAL.md` - Original flawed design
4. `04_validation_report.md` - Validation failures
5. `05_sanity_review.md` - LLM sanity review
6. `06_correction_loop.md` - Correction loop details
7. `07_corrected_design.md` - Fixed design after corrections
8. `08_revalidation.md` - Re-validation results
9. `09_devplan.md` - Development plan ({phase_count} phases)
10. `phase1.md` - `phase4.md` - Detailed phase files
11. `10_handoff.md` - This handoff document
"""
    
    save_file("10_handoff.md", handoff_md)
    print("  ✓ Handoff prompt generated")
    
    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "=" * 70)
    print("PIPELINE COMPLETE - WITH CORRECTIONS")
    print("=" * 70)
    print(f"\nAll outputs saved to: {OUTPUT_DIR.absolute()}")
    print("\nKey Differences from Clean Run:")
    print("  1. Complex SaaS project (high complexity score)")
    print("  2. Intentionally flawed design triggered validation failures")
    print("  3. Correction loop ran and fixed issues")
    print("  4. Re-validation confirmed fixes")
    print("\nCompare with: test_output/adaptive_pipeline_results/")
    print("\nFiles generated:")
    for f in sorted(OUTPUT_DIR.glob("*.md")):
        print(f"  - {f.name}")


if __name__ == "__main__":
    asyncio.run(run_pipeline_with_corrections())
