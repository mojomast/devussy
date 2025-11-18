"""Pydantic models used across the pipeline stages."""

from __future__ import annotations

from typing import List, Optional, Dict

from pydantic import BaseModel, Field


class ProjectDesign(BaseModel):
    """Structured representation of a project design document."""

    project_name: str
    objectives: List[str] = Field(default_factory=list)
    tech_stack: List[str] = Field(default_factory=list)
    architecture_overview: Optional[str] = None
    dependencies: List[str] = Field(default_factory=list)
    challenges: List[str] = Field(default_factory=list)
    mitigations: List[str] = Field(default_factory=list)
    raw_llm_response: Optional[str] = Field(default=None, description="Full raw markdown response from LLM")

    def to_json(self) -> str:
        return self.model_dump_json(indent=2)

    @classmethod
    def from_json(cls, data: str) -> "ProjectDesign":
        return cls.model_validate_json(data)


class DevPlanStep(BaseModel):
    """An actionable, numbered step within a phase.

    Now supports optional sub-bullets ("details") to capture rich guidance the
    model may emit as list items under each step.
    """

    number: str  # e.g., "2.7"
    description: str
    details: list[str] = Field(default_factory=list)
    done: bool = False


class DevPlanPhase(BaseModel):
    """A development plan phase containing multiple steps."""

    number: int
    title: str
    description: Optional[str] = None
    steps: List[DevPlanStep] = Field(default_factory=list)


class DevPlan(BaseModel):
    """The complete development plan made of multiple phases."""

    phases: List[DevPlanPhase] = Field(default_factory=list)
    summary: Optional[str] = None
    raw_basic_response: Optional[str] = Field(default=None, description="Full raw markdown from basic devplan generation")
    raw_detailed_responses: Optional[Dict[int, str]] = Field(default=None, description="Raw markdown for each phase detail")

    def to_json(self) -> str:
        return self.model_dump_json(indent=2)

    @classmethod
    def from_json(cls, data: str) -> "DevPlan":
        return cls.model_validate_json(data)


class HandoffPrompt(BaseModel):
    """The final handoff prompt document and metadata."""

    content: str
    next_steps: List[str] = Field(default_factory=list)

    def to_json(self) -> str:
        return self.model_dump_json(indent=2)

    @classmethod
    def from_json(cls, data: str) -> "HandoffPrompt":
        return cls.model_validate_json(data)
