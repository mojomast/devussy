from src.interview.complexity_analyzer import ComplexityProfile
from src.pipeline.design_generator import AdaptiveDesignGenerator


def _profile(score: float, depth: str, phases: int) -> ComplexityProfile:
    return ComplexityProfile(
        project_type_bucket="web_app",
        technical_complexity_bucket="simple_crud",
        integration_bucket="standalone",
        team_size_bucket="solo",
        score=score,
        estimated_phase_count=phases,
        depth_level=depth,  # type: ignore[arg-type]
        confidence=0.9,
    )


def test_minimal_depth_has_core_sections_only():
    gen = AdaptiveDesignGenerator()
    profile = _profile(score=2.0, depth="minimal", phases=3)

    text = gen.generate(profile, project_label="CLI Tool")

    assert "# Adaptive Design for CLI Tool" in text
    assert "## Architecture" in text
    assert "## Data Model" in text
    assert "## Testing" in text
    # Minimal depth should not include advanced sections
    assert "## Security" not in text
    assert "## Scalability" not in text


def test_standard_depth_includes_deployment_and_dependencies():
    gen = AdaptiveDesignGenerator()
    profile = _profile(score=5.0, depth="standard", phases=5)

    text = gen.generate(profile, project_label="Web App")

    assert "## Deployment" in text
    assert "## Dependencies" in text


def test_detailed_depth_includes_security_and_scalability():
    gen = AdaptiveDesignGenerator()
    profile = _profile(score=10.0, depth="detailed", phases=7)

    text = gen.generate(profile, project_label="SaaS Platform")

    assert "## Security" in text
    assert "## Scalability & Reliability" in text
    # Footer should reflect profile values
    assert "Estimated phases: 7" in text
