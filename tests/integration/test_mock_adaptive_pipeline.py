from src.pipeline.mock_adaptive_pipeline import MockAdaptivePipeline, MockAdaptivePipelineResult


def test_mock_adaptive_pipeline_trivial_project():
    pipeline = MockAdaptivePipeline()

    interview_data = {
        "project_type": "CLI Tool",
        "requirements": "Simple local CLI helper.",
        "team_size": "1",
    }

    result = pipeline.run(interview_data)

    assert isinstance(result, MockAdaptivePipelineResult)
    assert result.devplan.phases
    assert result.interview.complexity_profile.estimated_phase_count == 3
    assert len(result.devplan.phases) == 3


def test_mock_adaptive_pipeline_more_complex_project():
    pipeline = MockAdaptivePipeline()

    interview_data = {
        "project_type": "Web App",
        "requirements": "Complex SaaS platform with realtime collab and ML.",
        "apis": ["billing", "auth", "analytics", "crm"],
        "team_size": "7+",
    }

    result = pipeline.run(interview_data)

    assert result.interview.complexity_profile.estimated_phase_count >= 5
    assert len(result.devplan.phases) == result.interview.complexity_profile.estimated_phase_count
