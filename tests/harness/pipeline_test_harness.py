from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Mapping

from src.pipeline.mock_adaptive_pipeline import MockAdaptivePipeline, MockAdaptivePipelineResult


@dataclass
class TestScenario:
    name: str
    interview_data: Mapping[str, Any]
    min_phases: int
    max_phases: int


@dataclass
class ScenarioResult:
    scenario_name: str
    passed: bool
    messages: List[str]


@dataclass
class TestReport:
    results: List[ScenarioResult]

    @property
    def all_passed(self) -> bool:
        return all(r.passed for r in self.results)


class PipelineTestHarness:
    def run_scenario(self, scenario: TestScenario) -> ScenarioResult:
        pipeline = MockAdaptivePipeline()
        result: MockAdaptivePipelineResult = pipeline.run(scenario.interview_data)

        profile = result.interview.complexity_profile
        devplan = result.devplan

        phase_count = len(devplan.phases)
        messages: List[str] = []
        passed = True

        if not (scenario.min_phases <= phase_count <= scenario.max_phases):
            passed = False
            messages.append(
                f"Phase count {phase_count} outside expected range "
                f"[{scenario.min_phases}, {scenario.max_phases}]"
            )

        if phase_count != profile.estimated_phase_count:
            passed = False
            messages.append(
                "Devplan phase count does not match estimated_phase_count "
                f"({phase_count} != {profile.estimated_phase_count})"
            )

        if not devplan.summary:
            passed = False
            messages.append("Devplan summary is empty")

        if not messages:
            messages.append("OK")

        return ScenarioResult(
            scenario_name=scenario.name,
            passed=passed,
            messages=messages,
        )

    def run_test_suite(self, scenarios: List[TestScenario]) -> TestReport:
        results = [self.run_scenario(s) for s in scenarios]
        return TestReport(results=results)
