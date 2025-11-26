from src.pipeline.design_validator import DesignValidator, DesignValidationReport
from src.interview.complexity_analyzer import ComplexityProfile


def _simple_profile(score: float) -> ComplexityProfile:
    return ComplexityProfile(
        project_type_bucket="web_app",
        technical_complexity_bucket="simple_crud",
        integration_bucket="standalone",
        team_size_bucket="solo",
        score=score,
        estimated_phase_count=3,
        depth_level="minimal",
        confidence=1.0,
    )


def test_design_validator_completeness_and_consistency():
    validator = DesignValidator()
    design = """# Architecture\n\nThis is an architecture overview.\n\n## Data Model\nWe use a simple schema.\n\n## Testing\nUnit and integration tests."""

    report = validator.validate(design, complexity_profile=_simple_profile(2))

    assert isinstance(report, DesignValidationReport)
    assert report.is_valid
    assert report.auto_correctable
    assert not report.issues


def test_design_validator_flags_over_engineering_for_trivial_project():
    validator = DesignValidator()
    design = """Trivial CLI but implemented with microservices and CQRS and event sourcing.\nArchitecture: microservices.\nData model: simple.\nTesting: basic."""

    report = validator.validate(design, complexity_profile=_simple_profile(2))

    assert not report.is_valid
    codes = {issue.code for issue in report.issues}
    assert "over_engineering.complex_patterns_for_simple_project" in codes


def test_design_validator_scope_alignment_for_complex_project():
    validator = DesignValidator()
    # Design for complex project (score=10) that does NOT mention scalability
    # Note: "scalab" substring is checked, so avoid that word entirely
    design = """Complex SaaS platform.\nArchitecture: microservices.\nData model: relational.\nTesting: comprehensive.\n(No performance discussion here.)"""

    report = validator.validate(design, complexity_profile=_simple_profile(10))

    assert not report.is_valid
    codes = {issue.code for issue in report.issues}
    assert "scope_alignment.missing_scalability" in codes
