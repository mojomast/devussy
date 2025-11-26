from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from src.interview.interview_pipeline import InterviewPipeline, InterviewPipelineResult
from src.pipeline.design_correction_loop import DesignCorrectionLoop, DesignCorrectionResult
from src.pipeline.design_generator import AdaptiveDesignGenerator
from src.pipeline.devplan_generator import AdaptiveDevPlanGenerator
from src.models import DevPlan


@dataclass
class MockAdaptivePipelineResult:
    interview: InterviewPipelineResult
    devplan: DevPlan
    correction: DesignCorrectionResult


class MockAdaptivePipeline:
    """End-to-end adaptive pipeline using only mock components.

    This does NOT call any real LLM generators. It is intended for local
    testing of control flow: interview → complexity → validation/correction →
    synthetic devplan, all deterministic.
    """

    def __init__(self) -> None:
        self._interview_pipeline = InterviewPipeline()
        self._correction_loop = DesignCorrectionLoop()
        self._design_generator = AdaptiveDesignGenerator()
        self._devplan_generator = AdaptiveDevPlanGenerator()

    def run(self, interview_data: Mapping[str, Any]) -> MockAdaptivePipelineResult:
        interview_result = self._interview_pipeline.run(interview_data)
        profile = interview_result.complexity_profile
        project_label = str(interview_result.inputs.get("project_type") or "project")

        design_text = self._design_generator.generate(profile, project_label=project_label)

        devplan = self._devplan_generator.generate(profile, project_label=project_label)

        correction = self._correction_loop.run(design_text, complexity_profile=profile)

        return MockAdaptivePipelineResult(
            interview=interview_result,
            devplan=devplan,
            correction=correction,
        )
