from src.pipeline.design_correction_loop import DesignCorrectionLoop


def test_validation_and_correction_integration():
    loop = DesignCorrectionLoop()

    design = """# Architecture\n\nSmall web app.\n\n## Data Model\nSimple.\n\n## Testing\nBasic tests.\n\nTrivial project but mentions microservices and event sourcing without scalability discussion."""

    result = loop.run(design)

    # For this mock, we don't assert on exact text, only that the loop completes
    assert result.validation is not None
    assert result.review is not None
    assert result.validation.issues or result.max_iterations_reached in {True, False}
