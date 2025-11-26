from src.interview.interview_pipeline import InterviewPipeline, InterviewPipelineResult
from src.interview.complexity_analyzer import ComplexityProfile


def test_interview_pipeline_trivial_project():
    pipeline = InterviewPipeline()

    interview_data = {
        "project_type": "CLI Tool",
        "requirements": "Tiny helper to manage local text files.",
        "team_size": "1",
    }

    result = pipeline.run(interview_data)

    assert isinstance(result, InterviewPipelineResult)
    assert isinstance(result.complexity_profile, ComplexityProfile)
    assert result.inputs["project_type"] == "CLI Tool"
    assert result.complexity_profile.estimated_phase_count == 3


def test_interview_pipeline_more_complex_web_app():
    pipeline = InterviewPipeline()

    interview_data = {
        "project_type": "Web App",
        "requirements": "Realtime collaborative editor with authentication and database-backed storage.",
        "frameworks": "Next.js, FastAPI",
        "apis": ["auth0", "payments", "analytics"],
        "team_size": "4-6",
    }

    result = pipeline.run(interview_data)

    assert isinstance(result, InterviewPipelineResult)
    assert isinstance(result.complexity_profile, ComplexityProfile)
    assert result.complexity_profile.score > 3
    assert result.complexity_profile.estimated_phase_count >= 5
