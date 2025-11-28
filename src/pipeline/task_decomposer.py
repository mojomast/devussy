"""Task decomposition and phase planning module.

This module provides a pre-phase-generation step that:
1. Extracts all discrete tasks from the project design
2. Validates coverage against requirements
3. Groups tasks into logical phases with explicit reasoning
4. Identifies dependencies and ordering constraints

This intermediate step ensures phase generation is grounded in
explicit task analysis rather than ad-hoc LLM decisions.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Mapping

from ..llm_client import LLMClient
from ..logger import get_logger
from ..models import ProjectDesign

logger = get_logger(__name__)


@dataclass
class Task:
    """A discrete unit of work extracted from the project design."""
    id: str
    title: str
    description: str
    category: str  # e.g., "setup", "core", "integration", "testing", "docs", "deployment"
    complexity: str  # "trivial", "simple", "moderate", "complex"
    estimated_effort: str  # "hours", "day", "days", "week"
    dependencies: List[str] = field(default_factory=list)  # Task IDs this depends on
    required_for: List[str] = field(default_factory=list)  # Requirement IDs this addresses
    

@dataclass
class PhaseAssignment:
    """A task assigned to a specific phase with justification."""
    task_id: str
    phase_number: int
    justification: str  # Why this task belongs in this phase


@dataclass
class ProposedPhase:
    """A proposed phase with its tasks and rationale."""
    number: int
    title: str
    objective: str  # What this phase achieves
    tasks: List[str]  # Task IDs
    entry_criteria: List[str]  # What must be true before starting
    exit_criteria: List[str]  # What must be true to complete
    risks: List[str]  # Potential issues in this phase


@dataclass
class TaskDecompositionResult:
    """Complete result of task decomposition and phase planning."""
    tasks: List[Task]
    phases: List[ProposedPhase]
    coverage_analysis: Dict[str, Any]  # Requirement -> tasks mapping
    dependency_graph: Dict[str, List[str]]  # Task -> dependencies
    uncovered_requirements: List[str]  # Requirements without tasks
    phase_rationale: str  # Overall reasoning for phase structure


TASK_EXTRACTION_PROMPT = """You are an expert software architect breaking down a project into discrete tasks.

## Your Role
Analyze the project design and extract EVERY discrete task needed to complete the project.
Be exhaustive - missing tasks leads to incomplete phases later.

## Project Design
{design_json}

## Complexity Assessment
{complexity_json}

## Task Extraction Rules

1. **Granularity**: Each task should be completable in hours to a few days, not weeks.
2. **Atomicity**: Each task should have a single clear outcome.
3. **Traceability**: Link tasks to the requirements they address.
4. **Categories**: Assign each task to exactly one category:
   - "setup": Environment, tooling, project structure
   - "core": Main business logic and features
   - "data": Database, models, data layer
   - "integration": External APIs, services
   - "ui": User interface components
   - "testing": Tests, QA, validation
   - "docs": Documentation, help text
   - "deployment": Build, deploy, release
   - "security": Auth, permissions, encryption

5. **Dependencies**: Identify which tasks depend on others.

## Output Format (STRICT JSON)

{{
  "tasks": [
    {{
      "id": "T001",
      "title": "Short descriptive title",
      "description": "What specifically needs to be done",
      "category": "core|setup|data|integration|ui|testing|docs|deployment|security",
      "complexity": "trivial|simple|moderate|complex",
      "estimated_effort": "hours|day|days|week",
      "dependencies": ["T000"],
      "required_for": ["R001", "R002"]
    }}
  ],
  "requirements_mapping": {{
    "R001": {{
      "text": "The requirement text",
      "tasks": ["T001", "T002"]
    }}
  }},
  "extraction_notes": "Brief notes on any ambiguities or assumptions made"
}}

## Critical Rules
- Output ONLY valid JSON, no prose
- Extract at least 10 tasks for any real project
- Every feature from objectives/requirements must have tasks
- Don't skip "obvious" tasks - be explicit
- Dependencies should form a DAG (no cycles)

BEGIN NOW."""


PHASE_PLANNING_PROMPT = """You are an expert project manager organizing tasks into development phases.

## Your Role
Given a list of extracted tasks, organize them into logical phases that:
1. Respect dependencies (can't start B before A if B depends on A)
2. Group related work together
3. Create meaningful milestones
4. Enable incremental delivery

## Extracted Tasks
{tasks_json}

## Complexity Profile
- Target Phase Count: {target_phases}
- Depth Level: {depth_level}

## Phase Planning Rules

1. **Dependency Respect**: No phase can contain a task whose dependencies are in a later phase.

2. **Cohesion**: Tasks in a phase should be related (same feature, same layer, same category).

3. **Entry/Exit Criteria**: Each phase needs clear start and completion conditions.

4. **Risk Awareness**: Identify what could go wrong in each phase.

5. **Phase Sizing**: Phases should be roughly balanced, but some variation is OK.

6. **Standard Phase Pattern** (adapt as needed):
   - Phase 1: Always setup/foundation
   - Middle phases: Core features, data layer, integrations
   - Late phases: Polish, testing, docs
   - Final phase: Deployment, release

## Output Format (STRICT JSON)

{{
  "phases": [
    {{
      "number": 1,
      "title": "Clear phase title",
      "objective": "What this phase achieves overall",
      "tasks": ["T001", "T002", "T003"],
      "entry_criteria": [
        "Repo created",
        "Dev environment set up"
      ],
      "exit_criteria": [
        "All tasks complete",
        "Basic CI passing"
      ],
      "risks": [
        "Dependency conflicts",
        "Tool version issues"
      ]
    }}
  ],
  "phase_rationale": "Explanation of why phases are structured this way",
  "dependency_validation": {{
    "valid": true,
    "violations": []
  }},
  "coverage_check": {{
    "all_tasks_assigned": true,
    "unassigned_tasks": []
  }}
}}

## Critical Rules
- Output ONLY valid JSON, no prose
- Every task must be assigned to exactly one phase
- Phases must be numbered sequentially starting from 1
- Dependencies MUST be in earlier or same phase, never later
- Include {target_phases} phases (±1 is OK if justified)

BEGIN NOW."""


class TaskDecomposer:
    """Decomposes project design into tasks and plans phases."""
    
    def __init__(self, llm_client: LLMClient) -> None:
        self._llm_client = llm_client
    
    async def decompose_and_plan(
        self,
        project_design: ProjectDesign,
        complexity_profile: Optional[Mapping[str, Any]] = None,
    ) -> TaskDecompositionResult:
        """Extract tasks from design and plan phases.
        
        This is a two-step process:
        1. Extract all discrete tasks from the design
        2. Organize tasks into phases with dependency awareness
        
        Args:
            project_design: The project design to decompose
            complexity_profile: Optional complexity analysis result
            
        Returns:
            TaskDecompositionResult with tasks, phases, and coverage analysis
        """
        # Step 1: Extract tasks
        logger.info("Extracting tasks from project design...")
        tasks = await self._extract_tasks(project_design, complexity_profile)
        logger.info(f"Extracted {len(tasks)} tasks")
        
        # Step 2: Plan phases
        target_phases = 5  # Default
        depth_level = "standard"
        
        if complexity_profile:
            target_phases = complexity_profile.get("estimated_phase_count", 5)
            depth_level = complexity_profile.get("depth_level", "standard")
        
        logger.info(f"Planning {target_phases} phases at {depth_level} depth...")
        phases, phase_rationale = await self._plan_phases(
            tasks, target_phases, depth_level
        )
        logger.info(f"Created {len(phases)} phases")
        
        # Build coverage analysis
        coverage = self._analyze_coverage(tasks, phases)
        
        # Build dependency graph
        dep_graph = {t.id: t.dependencies for t in tasks}
        
        return TaskDecompositionResult(
            tasks=tasks,
            phases=phases,
            coverage_analysis=coverage,
            dependency_graph=dep_graph,
            uncovered_requirements=coverage.get("uncovered", []),
            phase_rationale=phase_rationale,
        )
    
    async def _extract_tasks(
        self,
        project_design: ProjectDesign,
        complexity_profile: Optional[Mapping[str, Any]],
    ) -> List[Task]:
        """Extract discrete tasks from project design using LLM."""
        
        # Build design JSON for prompt
        design_data = {
            "project_name": project_design.project_name,
            "objectives": project_design.objectives,
            "tech_stack": project_design.tech_stack,
            "architecture_overview": project_design.architecture_overview,
            "dependencies": project_design.dependencies,
            "challenges": project_design.challenges,
            "mitigations": project_design.mitigations,
        }
        
        # Add optional fields
        if project_design.database:
            design_data["database"] = project_design.database
        if project_design.deployment_platform:
            design_data["deployment_platform"] = project_design.deployment_platform
        if project_design.apis:
            design_data["apis"] = project_design.apis
        if project_design.authentication:
            design_data["authentication"] = True
        if project_design.user_emphasis:
            design_data["user_emphasis"] = project_design.user_emphasis
        
        complexity_data = complexity_profile or {}
        
        prompt = TASK_EXTRACTION_PROMPT.format(
            design_json=json.dumps(design_data, indent=2),
            complexity_json=json.dumps(complexity_data, indent=2),
        )
        
        response = await self._llm_client.generate_completion(prompt)
        return self._parse_tasks(response)
    
    def _parse_tasks(self, response: str) -> List[Task]:
        """Parse LLM response into Task objects."""
        cleaned = self._clean_json_response(response)
        
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse task extraction response: {e}")
            raise ValueError(f"Failed to parse task extraction: {e}")
        
        tasks = []
        for t in data.get("tasks", []):
            tasks.append(Task(
                id=t.get("id", f"T{len(tasks)+1:03d}"),
                title=t.get("title", ""),
                description=t.get("description", ""),
                category=t.get("category", "core"),
                complexity=t.get("complexity", "moderate"),
                estimated_effort=t.get("estimated_effort", "day"),
                dependencies=t.get("dependencies", []),
                required_for=t.get("required_for", []),
            ))
        
        return tasks
    
    async def _plan_phases(
        self,
        tasks: List[Task],
        target_phases: int,
        depth_level: str,
    ) -> tuple[List[ProposedPhase], str]:
        """Organize tasks into phases using LLM."""
        
        tasks_data = [
            {
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "category": t.category,
                "complexity": t.complexity,
                "dependencies": t.dependencies,
            }
            for t in tasks
        ]
        
        prompt = PHASE_PLANNING_PROMPT.format(
            tasks_json=json.dumps(tasks_data, indent=2),
            target_phases=target_phases,
            depth_level=depth_level,
        )
        
        response = await self._llm_client.generate_completion(prompt)
        return self._parse_phases(response)
    
    def _parse_phases(self, response: str) -> tuple[List[ProposedPhase], str]:
        """Parse LLM response into ProposedPhase objects."""
        cleaned = self._clean_json_response(response)
        
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse phase planning response: {e}")
            raise ValueError(f"Failed to parse phase planning: {e}")
        
        phases = []
        for p in data.get("phases", []):
            phases.append(ProposedPhase(
                number=p.get("number", len(phases) + 1),
                title=p.get("title", ""),
                objective=p.get("objective", ""),
                tasks=p.get("tasks", []),
                entry_criteria=p.get("entry_criteria", []),
                exit_criteria=p.get("exit_criteria", []),
                risks=p.get("risks", []),
            ))
        
        rationale = data.get("phase_rationale", "")
        
        return phases, rationale
    
    def _analyze_coverage(
        self,
        tasks: List[Task],
        phases: List[ProposedPhase],
    ) -> Dict[str, Any]:
        """Analyze coverage of requirements by tasks and phases."""
        
        # Collect all task IDs
        all_task_ids = {t.id for t in tasks}
        
        # Collect assigned task IDs
        assigned_task_ids = set()
        for phase in phases:
            assigned_task_ids.update(phase.tasks)
        
        # Find unassigned tasks
        unassigned = all_task_ids - assigned_task_ids
        
        # Build requirement coverage
        req_coverage = {}
        for task in tasks:
            for req_id in task.required_for:
                if req_id not in req_coverage:
                    req_coverage[req_id] = []
                req_coverage[req_id].append(task.id)
        
        return {
            "total_tasks": len(tasks),
            "assigned_tasks": len(assigned_task_ids),
            "unassigned_tasks": list(unassigned),
            "requirement_coverage": req_coverage,
            "uncovered": [],  # Would need requirements list to compute
        }
    
    def _clean_json_response(self, response: str) -> str:
        """Clean potential markdown/code fences from JSON response."""
        cleaned = response.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned = "\n".join(lines)
        return cleaned
