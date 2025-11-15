"""Anchor validation CLI for Devussy markdown artifacts.

Usage (from repo root):

    python -m src.utils.validate_anchors docs/

This checks that key markdown files (devplan.md, phaseN.md, handoff_prompt.md)
contain the expected START/END anchor pairs used by agents for efficient
context reading.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, Iterable, List

from .anchor_utils import _anchor_pair

# Logical anchors expected per filename pattern
REQUIRED_ANCHORS: Dict[str, List[str]] = {
    "devplan.md": ["PROGRESS_LOG", "NEXT_TASK_GROUP"],
    "handoff_prompt.md": ["QUICK_STATUS", "DEV_INSTRUCTIONS", "TOKEN_RULES", "HANDOFF_NOTES"],
}


def _required_for_path(path: Path) -> List[str]:
    """Return the list of required anchors for a given file.

    - devplan.md → PROGRESS_LOG, NEXT_TASK_GROUP
    - handoff_prompt.md → QUICK_STATUS, DEV_INSTRUCTIONS, TOKEN_RULES, HANDOFF_NOTES
    - phase*.md → PHASE_TASKS, PHASE_OUTCOMES (and legacy PHASE_PROGRESS)
    """

    name = path.name
    if name in REQUIRED_ANCHORS:
        return REQUIRED_ANCHORS[name]
    if name.startswith("phase") and name.endswith(".md"):
        return ["PHASE_TASKS", "PHASE_OUTCOMES", "PHASE_PROGRESS"]
    return []


def validate_file(path: Path) -> bool:
    """Validate that required anchors exist in the given file.

    Returns True if all required anchors are present, False otherwise.
    """

    required = _required_for_path(path)
    if not required:
        return True

    text = path.read_text(encoding="utf-8")
    missing: List[str] = []

    for logical in required:
        start, end = _anchor_pair(logical)
        if start not in text or end not in text:
            missing.append(logical)

    if missing:
        print(f"[ERROR] {path}: missing anchors {', '.join(missing)}")
        return False

    print(f"[OK] {path}: all required anchors present")
    return True


def iter_markdown_files(root: Path) -> Iterable[Path]:
    """Yield markdown files under root that we care about.

    We only check:
    - devplan.md
    - handoff_prompt.md
    - phase*.md
    """

    for p in root.rglob("*.md"):
        if _required_for_path(p):
            yield p


def main(argv: List[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print("Usage: python -m src.utils.validate_anchors <docs_root>")
        return 1

    root = Path(argv[0]).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        print(f"Error: {root} is not a directory")
        return 1

    print(f"Validating anchors under {root}...\n")
    ok = True
    for md in iter_markdown_files(root):
        if not validate_file(md):
            ok = False

    if ok:
        print("\nAll checked markdown files have required anchors.")
        return 0

    print("\nSome markdown files are missing required anchors.")
    return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
