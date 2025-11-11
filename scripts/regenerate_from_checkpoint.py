"""Regenerate detailed devplan and docs from an existing checkpoint, writing v2 files.

Usage (PowerShell):
  python scripts/regenerate_from_checkpoint.py "Potato Hopping Game_pipeline" "docs/potato-hopping-game_20251107_011551"

This will:
- Load the saved project_design and basic_devplan from the checkpoint
- Re-run detailed phase generation with current templates and settings
- Write richer outputs to devplan2.md, phase{N}_v2.md, and handoff_prompt_v2.md in the output folder
"""
from __future__ import annotations

import sys
from pathlib import Path

from src.config import load_config
from src.state_manager import StateManager
from src.pipeline.compose import PipelineOrchestrator
from src.clients.factory import create_llm_client
from src.concurrency import ConcurrencyManager
from src.file_manager import FileManager
from src.models import DevPlan, ProjectDesign


def main() -> int:
    if len(sys.argv) < 3:
        print("Usage: python scripts/regenerate_from_checkpoint.py <checkpoint_key> <output_dir>")
        return 2

    checkpoint_key = sys.argv[1]
    output_dir = Path(sys.argv[2])
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load config and components
    config = load_config()
    llm_client = create_llm_client(config)
    conc = ConcurrencyManager(config.max_concurrent_requests)
    file_mgr = FileManager()
    orch = PipelineOrchestrator(
        llm_client=llm_client,
        concurrency_manager=conc,
        file_manager=file_mgr,
        git_config=config.git,
        config=config,
    )

    # Load checkpoint data
    sm = StateManager()
    ckpt = sm.load_checkpoint(checkpoint_key)
    if not ckpt:
        print(f"Checkpoint not found: {checkpoint_key}")
        return 1

    data = ckpt.get("data", {})
    design = ProjectDesign.model_validate(data["project_design"])  # type: ignore[index]
    basic_devplan = DevPlan.model_validate(data["basic_devplan"])  # type: ignore[index]

    # Re-run detailed phase generation
    print("🔄 Regenerating detailed phase steps with current templates and settings...")
    import asyncio
    detailed = asyncio.run(
        orch.detailed_devplan_gen.generate(
            basic_devplan,
            project_name=design.project_name,
            tech_stack=design.tech_stack,
        )
    )

    # Write v2 outputs
    devplan_path = output_dir / "devplan2.md"
    devplan_md = orch._devplan_to_markdown(detailed)
    file_mgr.write_markdown(str(devplan_path), devplan_md)

    # Phase files (suffix _v2)
    print("📝 Writing v2 phase files...")
    for phase in detailed.phases:
        phase_md = orch._phase_to_markdown(phase, detailed)
        file_mgr.write_markdown(str(output_dir / f"phase{phase.number}_v2.md"), phase_md)

    # Create a v2 handoff prompt
    handoff = orch.handoff_gen.generate(
        devplan=detailed,
        project_name=design.project_name,
        project_summary=detailed.summary or "",
        architecture_notes=design.architecture_overview or "",
    )
    file_mgr.write_markdown(str(output_dir / "handoff_prompt_v2.md"), handoff.content)

    print("✅ Regeneration complete:")
    print(f" - {devplan_path}")
    for phase in detailed.phases:
        print(f" - {output_dir / f'phase{phase.number}_v2.md'}")
    print(f" - {output_dir / 'handoff_prompt_v2.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
