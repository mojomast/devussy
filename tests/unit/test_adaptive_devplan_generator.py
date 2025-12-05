from src.interview.complexity_analyzer import ComplexityProfile
from src.pipeline.devplan_generator import AdaptiveDevPlanGenerator


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


def test_devplan_phase_count_matches_estimated_phases():
    gen = AdaptiveDevPlanGenerator()
    profile = _profile(score=2.0, depth="minimal", phases=3)

    devplan = gen.generate(profile, project_label="CLI Tool")

    assert len(devplan.phases) == 3
    assert devplan.summary.startswith("Adaptive devplan for CLI Tool")


def test_devplan_uses_canonical_names_for_common_counts():
    gen = AdaptiveDevPlanGenerator()
    profile = _profile(score=6.0, depth="standard", phases=5)

    devplan = gen.generate(profile, project_label="Web App")

    titles = [p.title for p in devplan.phases]
    assert "Foundation" in titles[0]
    assert "Deployment" in titles[-1]


def test_devplan_handles_larger_phase_counts():
    gen = AdaptiveDevPlanGenerator()
    profile = _profile(score=15.0, depth="detailed", phases=10)

    devplan = gen.generate(profile, project_label="SaaS")

    assert len(devplan.phases) == 10
    # Ensure we at least have some of the extended names present
    titles = [p.title for p in devplan.phases]
    assert any("Auth & Security" in t for t in titles)
    assert any("Deployment" in t for t in titles)
