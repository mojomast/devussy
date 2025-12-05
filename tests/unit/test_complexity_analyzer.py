from src.interview.complexity_analyzer import (
    ComplexityAnalyzer,
    estimate_phase_count,
    ComplexityProfile,
)


def test_estimate_phase_count_thresholds():
    # Test boundary conditions for phase count estimation
    # Formula: score <= 3 -> 3, <= 7 -> 5, <= 12 -> 7, else min(9 + (score-12)//2, 15)
    assert estimate_phase_count(0) == 3
    assert estimate_phase_count(3) == 3
    assert estimate_phase_count(4) == 5
    assert estimate_phase_count(7) == 5
    assert estimate_phase_count(8) == 7
    assert estimate_phase_count(12) == 7
    assert estimate_phase_count(13) == 9
    # At score=20: 9 + (20-12)//2 = 9 + 4 = 13
    assert estimate_phase_count(20) == 13
    # At score=24: 9 + (24-12)//2 = 9 + 6 = 15 (capped)
    assert estimate_phase_count(24) == 15
    # At score=30: 9 + (30-12)//2 = 9 + 9 = 18, but capped at 15
    assert estimate_phase_count(30) == 15


def test_analyze_trivial_cli_solo():
    analyzer = ComplexityAnalyzer()
    data = {
        "project_type": "CLI Tool",
        "requirements": "Simple CRUD over a local file",
        "team_size": "1",
    }

    profile = analyzer.analyze(data)

    assert isinstance(profile, ComplexityProfile)
    assert profile.project_type_bucket == "cli_tool"
    assert profile.technical_complexity_bucket == "simple_crud"
    assert profile.integration_bucket == "standalone"
    assert profile.team_size_bucket == "solo"
    assert profile.score <= 3
    assert profile.estimated_phase_count == 3
    assert profile.depth_level == "minimal"


def test_analyze_standard_web_app_small_team():
    analyzer = ComplexityAnalyzer()
    data = {
        "project_type": "Web App",
        "requirements": "Web app with auth and database-backed CRUD UI.",
        "frameworks": "Django",
        "apis": ["payments"],
        "team_size": "3",
    }

    profile = analyzer.analyze(data)

    assert profile.project_type_bucket == "web_app"
    assert profile.technical_complexity_bucket in {"auth_db", "simple_crud"}
    assert profile.integration_bucket == "1_2_services"
    assert profile.team_size_bucket == "2_3"
    assert 3 < profile.score <= 12
    assert profile.estimated_phase_count in {5, 7}
    assert profile.depth_level in {"standard", "detailed"}


def test_analyze_complex_saas_multi_region():
    analyzer = ComplexityAnalyzer()
    data = {
        "project_type": "SaaS Platform",
        "requirements": "Multi-region SaaS with realtime collaboration and ML-based recommendations.",
        "apis": ["billing", "email", "analytics", "crm", "support", "search"],
        "team_size": "10",
    }

    profile = analyzer.analyze(data)

    assert profile.project_type_bucket == "saas"
    assert profile.technical_complexity_bucket in {"realtime", "ml_ai", "multi_region"}
    assert profile.integration_bucket == "6_plus_services"
    assert profile.team_size_bucket == "7_plus"
    assert profile.score >= 7
    assert profile.estimated_phase_count >= 7
    assert profile.depth_level == "detailed"
    assert 0.5 <= profile.confidence <= 1.0
