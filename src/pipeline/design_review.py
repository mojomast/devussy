"""Design review/refinement using the DevPlan (phase 2) model.

This optional step asks the devplan model to review the freshly generated
project design for compatibility/workflow/backend/efficiency issues and
return a strict JSON including a potentially updated ProjectDesign.
"""

from __future__ import annotations

import json
import re
from typing import Any, Tuple

from ..llm_client import LLMClient
from ..logger import get_logger
from ..models import ProjectDesign
from ..templates import render_template

logger = get_logger(__name__)


class DesignReviewRefiner:
    """Use the devplan model to sanity-check and refine a ProjectDesign."""

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    async def refine(
        self,
        project_design: ProjectDesign,
        **llm_kwargs: Any,
    ) -> Tuple[ProjectDesign, str, bool]:
        """Run a review with the devplan model and return an updated design.

        Returns:
            (updated_design, review_report_markdown, changed)
        """
        # Render prompt for review
        prompt = render_template("design_review.jinja", {"project_design": project_design})
        logger.debug(f"Design review prompt length: {len(prompt)} chars")

        # Use conservative decoding for reliability
        kw = dict(llm_kwargs)
        kw.setdefault("temperature", 0.3)
        kw.setdefault("max_tokens", 1200)

        response = await self.llm_client.generate_completion(prompt, **kw)
        logger.info(f"Received design review response ({len(response)} chars)")

        # Extract JSON from response
        data = self._extract_json(response)
        if not data:
            logger.warning("Design review did not return parseable JSON; keeping original design")
            return project_design, self._as_markdown_fallback(response), False

        status = (data.get("status") or "ok").lower()
        summary = data.get("summary") or ""
        issues = data.get("issues") or []
        proj_dict = data.get("project_design") or {}

        # Build updated ProjectDesign if provided
        updated = project_design
        changed = False
        try:
            if proj_dict:
                updated = ProjectDesign.model_validate(proj_dict)
                # Detect change heuristically
                changed = updated.model_dump() != project_design.model_dump()
        except Exception as e:
            logger.warning(f"Invalid project_design in review JSON: {e}; keeping original")
            updated = project_design
            changed = False

        # Compose a human-friendly report we can save
        report_md = self._build_report_md(status, summary, issues, original=project_design, updated=updated)
        return updated, report_md, changed

    def _extract_json(self, text: str) -> dict | None:
        """Find and parse a JSON object, preferring fenced ```json blocks."""
        if not text:
            return None
        # Prefer fenced json block
        m = re.search(r"```json\s*(\{[\s\S]*?\})\s*```", text, flags=re.IGNORECASE)
        candidate = None
        if m:
            candidate = m.group(1)
        else:
            # Try any JSON object in the text
            m2 = re.search(r"(\{[\s\S]*\})", text)
            if m2:
                candidate = m2.group(1)
        if not candidate:
            # Might already be raw JSON
            candidate = text.strip()
        try:
            return json.loads(candidate)
        except Exception:
            return None

    def _as_markdown_fallback(self, response: str) -> str:
        preview = (response or "").strip()
        if len(preview) > 1200:
            preview = preview[:1200] + "\n..."
        return f"# Design Review (Unstructured)\n\n````\n{preview}\n````\n"

    def _build_report_md(
        self,
        status: str,
        summary: str,
        issues: list,
        original: ProjectDesign,
        updated: ProjectDesign,
    ) -> str:
        lines = [
            "# Design Review by DevPlan Model\n",
            f"**Status:** {status}\n",
            f"**Summary:** {summary}\n\n",
            "## Issues\n",
        ]
        if not issues:
            lines.append("- No material issues found.\n\n")
        else:
            for issue in issues:
                itype = issue.get("type", "unknown")
                sev = issue.get("severity", "-")
                detail = issue.get("detail", "")
                fix = issue.get("fix", "")
                lines.append(f"- [{sev}] ({itype}) {detail}\n  - Fix: {fix}\n")
            lines.append("\n")

        lines.extend([
            "## Original Design (summary)\n",
            f"- Objectives: {len(original.objectives)}\n",
            f"- Tech Stack: {', '.join(original.tech_stack)}\n",
            f"- Dependencies: {', '.join(original.dependencies)}\n\n",
            "## Updated Design (summary)\n",
            f"- Objectives: {len(updated.objectives)}\n",
            f"- Tech Stack: {', '.join(updated.tech_stack)}\n",
            f"- Dependencies: {', '.join(updated.dependencies)}\n",
        ])
        return "".join(lines)
