#!/usr/bin/env python3
"""
End-to-end test script for Adaptive LLM Pipeline Integration.

Tests the full adaptive pipeline with real LLM calls using:
- Provider: requesty
- Model: openai/gpt-4.1-nano (fast/cheap for testing)

Usage:
    python test_adaptive_llm_integration.py

Prerequisites:
    - REQUESTY_API_KEY environment variable set
    - Virtual environment activated
"""

import asyncio
import json
import os
import sys

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config import load_config
from src.clients.factory import create_llm_client
from src.interview.complexity_analyzer import LLMComplexityAnalyzer, ComplexityAnalyzer
from src.pipeline.design_validator import DesignValidator
from src.pipeline.llm_sanity_reviewer import LLMSanityReviewerWithLLM
from src.pipeline.design_correction_loop import LLMDesignCorrectionLoop


def create_test_config():
    """Create config with requesty/gpt-4.1-nano for testing."""
    config = load_config()
    config.llm.provider = "requesty"
    config.llm.model = "openai/gpt-4.1-nano"
    config.llm.temperature = 0.3  # Lower for more deterministic output
    return config


# =============================================================================
# Test Data
# =============================================================================

SIMPLE_INTERVIEW = {
    "project_type": "CLI tool",
    "requirements": "A simple command-line tool to convert JSON to YAML",
    "team_size": "1",
    "apis": [],
    "frameworks": "click",
}

MEDIUM_INTERVIEW = {
    "project_type": "Web API",
    "requirements": "REST API with authentication, database, and real-time notifications",
    "team_size": "3",
    "apis": ["Stripe", "SendGrid"],
    "frameworks": "FastAPI, SQLAlchemy",
}

COMPLEX_INTERVIEW = {
    "project_type": "SaaS platform",
    "requirements": "Multi-tenant SaaS with ML-powered analytics, real-time dashboards, payments, and enterprise SSO",
    "team_size": "8",
    "apis": ["Stripe", "Auth0", "Twilio", "AWS", "OpenAI", "Mixpanel"],
    "frameworks": "Next.js, FastAPI, PostgreSQL, Redis, Kubernetes",
}

SAMPLE_DESIGN = """
# Project Design: Task Manager API

## Overview
A REST API for managing tasks and projects.

## Tech Stack
- Python 3.11+
- FastAPI
- PostgreSQL
- Redis for caching

## Architecture
- RESTful API design
- JWT authentication
- Repository pattern for data access

## Endpoints
- POST /tasks - Create task
- GET /tasks - List tasks
- PUT /tasks/{id} - Update task
- DELETE /tasks/{id} - Delete task

## Testing Strategy
- Unit tests with pytest
- Integration tests with TestClient
"""


# =============================================================================
# Tests
# =============================================================================

async def test_complexity_analysis():
    """Test LLM-powered complexity analysis."""
    print("\n" + "="*60)
    print("TEST: LLM Complexity Analysis")
    print("="*60)
    
    config = create_test_config()
    llm_client = create_llm_client(config)
    analyzer = LLMComplexityAnalyzer(llm_client)
    
    test_cases = [
        ("Simple CLI", SIMPLE_INTERVIEW),
        ("Medium Web API", MEDIUM_INTERVIEW),
        ("Complex SaaS", COMPLEX_INTERVIEW),
    ]
    
    for name, interview in test_cases:
        print(f"\n--- {name} ---")
        try:
            result = await analyzer.analyze_with_llm(interview)
            print(f"  Score: {result.complexity_score}")
            print(f"  Phases: {result.estimated_phase_count}")
            print(f"  Depth: {result.depth_level}")
            print(f"  Confidence: {result.confidence}")
            print(f"  Rationale: {result.rationale[:100]}..." if result.rationale else "  (no rationale)")
            if result.hidden_risks:
                print(f"  Hidden Risks: {result.hidden_risks[:2]}")
            print("  ✅ PASSED")
        except Exception as e:
            print(f"  ❌ FAILED: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    return True


async def test_sanity_review():
    """Test LLM-powered sanity review."""
    print("\n" + "="*60)
    print("TEST: LLM Sanity Review")
    print("="*60)
    
    config = create_test_config()
    llm_client = create_llm_client(config)
    
    # First validate with rule-based validator
    validator = DesignValidator()
    
    # Create a profile for validation context
    from src.interview.complexity_analyzer import ComplexityProfile
    profile = ComplexityProfile(
        project_type_bucket="api",
        technical_complexity_bucket="auth_db",
        integration_bucket="standalone",
        team_size_bucket="2_3",
        score=5.0,
        estimated_phase_count=5,
        depth_level="standard",
        confidence=0.8,
    )
    
    report = validator.validate(SAMPLE_DESIGN, complexity_profile=profile)
    print(f"Rule-based validation: is_valid={report.is_valid}")
    
    # Now run LLM review
    reviewer = LLMSanityReviewerWithLLM(llm_client)
    try:
        result = await reviewer.review_with_llm(SAMPLE_DESIGN, report)
        print(f"  Confidence: {result.confidence}")
        print(f"  Overall: {result.overall_assessment}")
        print(f"  Coherence: {result.coherence_score}")
        print(f"  Hallucination Check: {'PASSED' if result.hallucination_passed else 'FAILED'}")
        if result.risks:
            print(f"  Risks ({len(result.risks)}):")
            for risk in result.risks[:2]:
                print(f"    - {risk.severity}: {risk.description[:50]}...")
        if result.suggestions:
            print(f"  Suggestions: {result.suggestions[:2]}")
        print("  ✅ PASSED")
        return True
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_design_correction():
    """Test LLM-powered design correction loop."""
    print("\n" + "="*60)
    print("TEST: LLM Design Correction Loop")
    print("="*60)
    
    config = create_test_config()
    llm_client = create_llm_client(config)
    
    # Create a design with intentional issues
    design_with_issues = """
# Project Design: Todo App

## Overview
A simple todo application.

## Tech Stack
- Python
- Flask
- MongoDB

## Architecture
Basic MVC pattern.
"""
    
    correction_loop = LLMDesignCorrectionLoop(llm_client)
    
    try:
        result = await correction_loop.run_with_llm(design_with_issues, max_iterations=2)
        print(f"  Iterations used: {result.iterations_used}")
        print(f"  Is valid: {result.validation.is_valid}")
        print(f"  Requires human review: {result.requires_human_review}")
        print(f"  Max iterations reached: {result.max_iterations_reached}")
        print(f"  Changes made: {len(result.changes_made)}")
        if result.changes_made:
            for change in result.changes_made[:2]:
                print(f"    - {change.issue_code}: {change.action}")
        print("  ✅ PASSED")
        return True
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_full_pipeline():
    """Test the full adaptive pipeline end-to-end."""
    print("\n" + "="*60)
    print("TEST: Full Adaptive Pipeline E2E")
    print("="*60)
    
    config = create_test_config()
    llm_client = create_llm_client(config)
    
    print("\n1. Complexity Analysis...")
    analyzer = LLMComplexityAnalyzer(llm_client)
    try:
        complexity = await analyzer.analyze_with_llm(MEDIUM_INTERVIEW)
        print(f"   Score: {complexity.complexity_score}, Depth: {complexity.depth_level}")
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        return False
    
    print("\n2. Design Validation...")
    from src.interview.complexity_analyzer import ComplexityProfile
    profile = ComplexityProfile(
        project_type_bucket="api",
        technical_complexity_bucket="auth_db",
        integration_bucket="1_2_services",
        team_size_bucket="2_3",
        score=complexity.complexity_score,
        estimated_phase_count=complexity.estimated_phase_count,
        depth_level=complexity.depth_level,
        confidence=complexity.confidence,
    )
    
    validator = DesignValidator()
    report = validator.validate(SAMPLE_DESIGN, complexity_profile=profile)
    print(f"   Valid: {report.is_valid}, Issues: {len(report.issues)}")
    
    print("\n3. Sanity Review...")
    reviewer = LLMSanityReviewerWithLLM(llm_client)
    try:
        review = await reviewer.review_with_llm(SAMPLE_DESIGN, report)
        print(f"   Confidence: {review.confidence}, Assessment: {review.overall_assessment}")
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        return False
    
    print("\n4. Correction Loop...")
    correction_loop = LLMDesignCorrectionLoop(llm_client)
    try:
        result = await correction_loop.run_with_llm(SAMPLE_DESIGN, complexity_profile=profile, max_iterations=2)
        print(f"   Iterations: {result.iterations_used}, Valid: {result.validation.is_valid}")
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        return False
    
    print("\n✅ FULL PIPELINE PASSED")
    return True


async def main():
    """Run all tests."""
    print("="*60)
    print("ADAPTIVE LLM PIPELINE INTEGRATION TESTS")
    print("="*60)
    print(f"Provider: requesty")
    print(f"Model: openai/gpt-4.1-nano")
    
    # Check for API key
    if not os.getenv("REQUESTY_API_KEY"):
        print("\n⚠️  WARNING: REQUESTY_API_KEY not set!")
        print("   Tests will fail without API key.")
        print("   Set it with: $env:REQUESTY_API_KEY='your-key'")
        return
    
    results = []
    
    # Run individual tests
    results.append(("Complexity Analysis", await test_complexity_analysis()))
    results.append(("Sanity Review", await test_sanity_review()))
    results.append(("Design Correction", await test_design_correction()))
    results.append(("Full Pipeline", await test_full_pipeline()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    passed = sum(1 for _, r in results if r)
    total = len(results)
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {name}: {status}")
    print(f"\nTotal: {passed}/{total} passed")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
