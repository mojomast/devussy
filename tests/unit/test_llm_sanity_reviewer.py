from src.pipeline.design_validator import DesignValidationReport, DesignValidationIssue
from src.pipeline.llm_sanity_reviewer import LLMSanityReviewer, LLMSanityReviewResult


def test_sanity_reviewer_confident_when_valid():
    reviewer = LLMSanityReviewer()
    report = DesignValidationReport(is_valid=True, auto_correctable=True, issues=[], checks={})

    result = reviewer.review("ok", report)

    assert isinstance(result, LLMSanityReviewResult)
    assert result.confidence > 0.8
    assert not result.risks


def test_sanity_reviewer_reduces_confidence_on_issues():
    reviewer = LLMSanityReviewer()
    issue = DesignValidationIssue(code="x", message="", auto_correctable=False)
    report = DesignValidationReport(is_valid=False, auto_correctable=False, issues=[issue], checks={})

    result = reviewer.review("not ok", report)

    assert result.confidence <= 0.7
    assert "x" in result.risks
