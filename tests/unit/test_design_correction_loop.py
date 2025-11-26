from src.pipeline.design_correction_loop import DesignCorrectionLoop


def test_correction_loop_converges_for_fixable_issues():
    loop = DesignCorrectionLoop()

    design = """# Architecture\n\nMinimal design.\n\n## Data Model\nSimple.\n\n## Testing\nBasic tests.\n\nTrivial CLI implemented with microservices and CQRS and event sourcing."""

    result = loop.run(design)

    assert not result.requires_human_review
    assert result.validation is not None


def test_correction_loop_flags_non_auto_correctable():
    loop = DesignCorrectionLoop()

    # This design will trigger a non-auto-correctable consistency issue
    design = """Architecture: must be monolith.\nAlso using microservices everywhere.\n\n## Data Model\nSimple.\n\n## Testing\nBasic tests."""

    result = loop.run(design)

    assert result.requires_human_review
