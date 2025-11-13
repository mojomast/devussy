"""Utilities for working with markdown anchor sections.

These helpers are used to read and update specific regions of markdown
files that are delimited with HTML-style comment anchors, e.g.::

    <!-- PROGRESS_LOG_START -->
    ... content ...
    <!-- PROGRESS_LOG_END -->

They are intentionally simple and safe to use from agents or scripts
that need deterministic, token-efficient updates.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, Optional


def _anchor_pair(anchor_name: str) -> tuple[str, str]:
    """Return the START/END markers for a logical anchor name.

    Example: ``_anchor_pair("PROGRESS_LOG")`` ->
    ("<!-- PROGRESS_LOG_START -->", "<!-- PROGRESS_LOG_END -->").
    """

    anchor_name = anchor_name.strip().upper()
    start = f"<!-- {anchor_name}_START -->"
    end = f"<!-- {anchor_name}_END -->"
    return start, end


def extract_between_anchors(
    content: str,
    anchor_name: str,
    *,
    raise_on_missing: bool = False,
) -> Optional[str]:
    """Extract content between START and END anchors.

    Returns the inner text without the anchors themselves, stripped of
    leading/trailing whitespace. If anchors are missing and
    ``raise_on_missing`` is False, returns ``None``.
    """

    start, end = _anchor_pair(anchor_name)
    pattern = f"{re.escape(start)}(.*?){re.escape(end)}"
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        if raise_on_missing:
            raise ValueError(f"Anchors for {anchor_name!r} not found")
        return None
    return match.group(1).strip()


def replace_anchor_content(content: str, anchor_name: str, new_content: str) -> str:
    """Replace the content between START and END anchors.

    If the anchors are missing, they are appended to the end of the
    document with ``new_content`` in between.
    """

    start, end = _anchor_pair(anchor_name)
    new_section = f"{start}\n{new_content}\n{end}"

    pattern = f"{re.escape(start)}.*?{re.escape(end)}"
    if re.search(pattern, content, re.DOTALL):
        return re.sub(pattern, new_section, content, flags=re.DOTALL)

    # If anchors did not exist, append them at the end on a new block
    sep = "\n\n" if not content.endswith("\n") else "\n"
    return f"{content}{sep}{new_section}\n"


def ensure_anchors_exist(content: str, anchor_names: Iterable[str]) -> str:
    """Ensure each logical anchor has START/END markers in the document.

    Anchors that are already present are left unchanged; missing ones
    are appended at the end in the order provided.
    """

    for name in anchor_names:
        start, end = _anchor_pair(name)
        if start in content and end in content:
            continue
        block = f"{start}\n{end}\n"
        if not content.endswith("\n"):
            content += "\n"
        content += "\n" + block
    return content


def get_anchor_token_estimate(content: str, anchor_name: str) -> int:
    """Very rough estimate of token count for an anchor section.

    This uses a naive heuristic of ~4 characters per token, which is
    good enough for budgeting relative section sizes.
    """

    section = extract_between_anchors(content, anchor_name)
    if section is None:
        return 0
    # 4 chars per token is a common rough approximation.
    return max(1, len(section) // 4)


def load_and_replace_anchor(
    path: Path,
    anchor_name: str,
    new_content: str,
    *,
    encoding: str = "utf-8",
) -> None:
    """Convenience helper to update a single anchor in a file on disk."""

    text = path.read_text(encoding=encoding)
    updated = replace_anchor_content(text, anchor_name, new_content)
    if updated != text:
        path.write_text(updated, encoding=encoding)
