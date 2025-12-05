from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .complexity_analyzer import ComplexityAnalyzer, ComplexityProfile


@dataclass
class InterviewPipelineResult:
    """Result of running the interview → complexity pipeline.

    This is intentionally LLM-free and works purely on structured interview
    data so that it can be fully tested with mocks.
    """

    inputs: dict[str, Any]
    complexity_profile: ComplexityProfile


class InterviewPipeline:
    """Pure-Python adapter around the complexity analyzer.

    In the current mock-first implementation this takes the structured
    interview data (already extracted) and produces a `ComplexityProfile`.
    Later, additional steps (follow-up questions, LLM-based normalization)
    can be layered on top without changing this contract.
    """

    def __init__(self) -> None:
        self._analyzer = ComplexityAnalyzer()

    def run(self, interview_data: Mapping[str, Any]) -> InterviewPipelineResult:
        """Run the interview → complexity pipeline on provided data.

        Args:
            interview_data: Mapping of fields gathered from the interview
                step. This is expected to be compatible with the keys used
                by `ComplexityAnalyzer` (e.g. project_type, requirements,
                frameworks, apis, team_size).
        """

        normalized_inputs: dict[str, Any] = dict(interview_data)

        profile = self._analyzer.analyze(normalized_inputs)

        return InterviewPipelineResult(inputs=normalized_inputs, complexity_profile=profile)
