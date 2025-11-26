"""Design validator for rule-based validation checks.

This module provides deterministic validation of design documents
before proceeding to devplan generation. Used in conjunction with
LLMSanityReviewer for comprehensive design review.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from src.interview.complexity_analyzer import ComplexityProfile


@dataclass
class DesignValidationIssue:
    """A single validation issue found in the design."""
    
    code: str
    message: str
    auto_correctable: bool = True
    severity: str = "warning"  # warning, error, info
    suggestion: str = ""


@dataclass
class DesignValidationReport:
    """Complete validation report for a design document."""
    
    is_valid: bool
    auto_correctable: bool
    issues: List[DesignValidationIssue] = field(default_factory=list)
    checks: Dict[str, bool] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        # Ensure is_valid is consistent with issues
        if self.issues and any(i.severity == "error" for i in self.issues):
            self.is_valid = False


class DesignValidator:
    """Rule-based design validator.
    
    Performs automated sanity checks on generated designs:
    - Consistency: tech stack matches, no contradictions
    - Completeness: required sections present
    - Scope alignment: complexity matches profile
    - Hallucination detection: no invented libraries
    - Over-engineering detection: appropriate for scale
    
    This is a mock/testing implementation using keyword matching.
    For production, integrate with LLMSanityReviewer for semantic analysis.
    """
    
    # Required sections for a valid design
    REQUIRED_SECTIONS = [
        "architecture",
        "database",
        "testing",
    ]
    
    # Keywords that suggest over-engineering for simple projects
    OVER_ENGINEERING_KEYWORDS = [
        "microservice",
        "kubernetes",
        "distributed",
        "event sourcing",
        "cqrs",
    ]
    
    def validate(
        self,
        design_text: str,
        complexity_profile: ComplexityProfile | None = None,
    ) -> DesignValidationReport:
        """Validate a design document.
        
        Args:
            design_text: The design document to validate
            complexity_profile: Optional complexity profile for scope alignment
            
        Returns:
            DesignValidationReport with all check results
        """
        issues: List[DesignValidationIssue] = []
        checks: Dict[str, bool] = {}
        
        # Run all validation checks
        checks["completeness"] = self._check_completeness(design_text, issues)
        checks["consistency"] = self._check_consistency(design_text, issues)
        checks["scope_alignment"] = self._check_scope_alignment(
            design_text, complexity_profile, issues
        )
        checks["hallucination"] = self._check_hallucinations(design_text, issues)
        checks["over_engineering"] = self._check_over_engineering(
            design_text, complexity_profile, issues
        )
        
        # Determine overall validity
        is_valid = all(checks.values())
        auto_correctable = all(issue.auto_correctable for issue in issues)
        
        return DesignValidationReport(
            is_valid=is_valid,
            auto_correctable=auto_correctable,
            issues=issues,
            checks=checks,
        )
    
    def _check_completeness(
        self,
        design_text: str,
        issues: List[DesignValidationIssue],
    ) -> bool:
        """Check that all required sections are present."""
        design_lower = design_text.lower()
        missing = []
        
        for section in self.REQUIRED_SECTIONS:
            if section not in design_lower:
                missing.append(section)
        
        if missing:
            issues.append(
                DesignValidationIssue(
                    code="completeness.missing_sections",
                    message=f"Missing required sections: {', '.join(missing)}",
                    auto_correctable=True,
                    severity="warning",
                    suggestion=f"Add sections for: {', '.join(missing)}",
                )
            )
            return False
        
        return True
    
    def _check_consistency(
        self,
        design_text: str,
        issues: List[DesignValidationIssue],
    ) -> bool:
        """Check for internal consistency."""
        design_lower = design_text.lower()
        
        # Check for contradicting database choices
        db_choices = []
        for db in ["postgresql", "mysql", "mongodb", "sqlite"]:
            if db in design_lower:
                db_choices.append(db)
        
        if len(db_choices) > 1:
            issues.append(
                DesignValidationIssue(
                    code="consistency.multiple_databases",
                    message=f"Multiple databases mentioned: {', '.join(db_choices)}",
                    auto_correctable=False,
                    severity="warning",
                    suggestion="Clarify primary database choice",
                )
            )
            return False
        
        return True
    
    def _check_scope_alignment(
        self,
        design_text: str,
        complexity_profile: ComplexityProfile | None,
        issues: List[DesignValidationIssue],
    ) -> bool:
        """Check that design complexity matches profile."""
        if complexity_profile is None:
            return True
        
        design_lower = design_text.lower()
        
        # Simple heuristic: count complexity indicators
        complexity_keywords = [
            "microservice", "distributed", "kubernetes", "redis",
            "elasticsearch", "kafka", "rabbitmq", "graphql",
        ]
        found_keywords = sum(1 for kw in complexity_keywords if kw in design_lower)
        
        # Compare against expected depth
        if complexity_profile.depth_level == "minimal" and found_keywords > 2:
            issues.append(
                DesignValidationIssue(
                    code="scope_alignment.over_scoped",
                    message="Design complexity exceeds minimal profile",
                    auto_correctable=True,
                    severity="warning",
                    suggestion="Simplify architecture for minimal scope",
                )
            )
            return False
        
        return True
    
    def _check_hallucinations(
        self,
        design_text: str,
        issues: List[DesignValidationIssue],
    ) -> bool:
        """Check for invented/hallucinated libraries or frameworks.
        
        This is a simple mock that always passes. Real implementation
        would cross-reference against package registries.
        """
        # Mock: always passes - real impl would check package registries
        return True
    
    def _check_over_engineering(
        self,
        design_text: str,
        complexity_profile: ComplexityProfile | None,
        issues: List[DesignValidationIssue],
    ) -> bool:
        """Check for over-engineering relative to project scope."""
        if complexity_profile is None:
            return True
        
        design_lower = design_text.lower()
        
        # Only flag for simple projects
        if complexity_profile.depth_level != "minimal":
            return True
        
        found_over_engineering = []
        for keyword in self.OVER_ENGINEERING_KEYWORDS:
            if keyword in design_lower:
                found_over_engineering.append(keyword)
        
        if found_over_engineering:
            issues.append(
                DesignValidationIssue(
                    code="over_engineering.complex_for_simple",
                    message=f"Over-engineered patterns for minimal project: {', '.join(found_over_engineering)}",
                    auto_correctable=True,
                    severity="warning",
                    suggestion="Simplify architecture for project scale",
                )
            )
            return False
        
        return True
