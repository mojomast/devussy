from tests.harness.pipeline_test_harness import (
    PipelineTestHarness,
    TestScenario,
)


def _trivial_cli_scenario(min_phases: int, max_phases: int) -> TestScenario:
    return TestScenario(
        name="trivial_cli",
        interview_data={
            "project_type": "CLI Tool",
            "requirements": "Tiny helper to manage local text files.",
            "team_size": "1",
        },
        min_phases=min_phases,
        max_phases=max_phases,
    )


def test_trivial_cli_with_wide_bounds_passes():
    harness = PipelineTestHarness()
    scenario = _trivial_cli_scenario(min_phases=1, max_phases=5)

    report = harness.run_test_suite([scenario])

    assert report.all_passed
    assert len(report.results) == 1
    assert report.results[0].passed


def test_trivial_cli_with_too_strict_bounds_fails():
    harness = PipelineTestHarness()
    scenario = _trivial_cli_scenario(min_phases=5, max_phases=10)

    report = harness.run_test_suite([scenario])

    assert not report.all_passed
    assert len(report.results) == 1
    assert not report.results[0].passed
    assert any("outside expected range" in msg for msg in report.results[0].messages)
