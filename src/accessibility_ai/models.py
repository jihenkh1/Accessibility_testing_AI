from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Union
from enum import Enum

class Priority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AccessibilityIssue(BaseModel):
    id: str
    description: str
    impact: str
    elements: List[str] = Field(default_factory=list)  # safe mutable default


class FixSuggestion(BaseModel):
    title: str
    description: str
    code_before: Optional[str] = None
    code_after: Optional[str] = None
    effort_minutes: int


class AIAnalysis(BaseModel):
    priority: Priority = Priority.MEDIUM
    user_impact: str = ""
    fix_suggestion: str = ""
    effort_minutes: int = 15
    # Rich optional fields
    code_example: Optional[str] = None
    wcag_refs: List[str] = Field(default_factory=list)
    acceptance_criteria: List[str] = Field(default_factory=list)
    test_steps: List[str] = Field(default_factory=list)
    automation_hints: List[str] = Field(default_factory=list)
    personas_impact: Optional[Dict[str, str]] = None
    root_cause_hypothesis: Optional[str] = None
    component_guess: Optional[str] = None
    fix_plan: Optional[Dict[str, List[str]]] = None
    ticket_title: Optional[str] = None
    ticket_body: Optional[str] = None
    confidence: Optional[int] = None
    risk_level: Optional[str] = None

    def to_fix_suggestion(self) -> FixSuggestion:
        """Convert AI analysis to a FixSuggestion object"""
        title = (self.fix_suggestion or "").strip()
        if len(title.split()) > 8:
            title = " ".join(title.split()[:8]) + "..."
        return FixSuggestion(
            title=title or "Accessibility Fix",
            description=self.fix_suggestion or "Review the issue and apply an appropriate fix.",
            code_before=None,
            code_after=None,
            effort_minutes=self.effort_minutes,
        )



class EnhancedIssue(BaseModel):
    original_issue: AccessibilityIssue
    ai_analysis: Optional[AIAnalysis] = None
    analysis_source: str = "rule_based"

    class Config:
        arbitrary_types_allowed = True  # keep if you pass non-pydantic types around

    @property
    def priority(self) -> Priority:
        if self.ai_analysis and self.ai_analysis.priority:
            return self.ai_analysis.priority
        impact = (self.original_issue.impact or "").lower()
        if impact == "critical":
            return Priority.CRITICAL
        if impact in ("serious", "high"):
            return Priority.HIGH
        if impact in ("moderate", "medium"):
            return Priority.MEDIUM
        if impact in ("minor", "low"):
            return Priority.LOW
        return Priority.MEDIUM

    @property
    def user_impact(self) -> str:
        if self.ai_analysis and self.ai_analysis.user_impact:
            return self.ai_analysis.user_impact
        return "This accessibility issue may affect users with disabilities."

    @property
    def effort_minutes(self) -> int:
        if self.ai_analysis and isinstance(self.ai_analysis.effort_minutes, int):
            return self.ai_analysis.effort_minutes
        # Default effort estimate by priority
        return {
            Priority.CRITICAL: 45,
            Priority.HIGH: 25,
            Priority.MEDIUM: 15,
            Priority.LOW: 5,
        }[self.priority]

    @property
    def fix_suggestions(self) -> List[FixSuggestion]:
        if self.ai_analysis:
            return [self.ai_analysis.to_fix_suggestion()]
        # Fallback generic suggestion
        return [
            FixSuggestion(
                title="Review and fix issue",
                description="Follow accessibility guidelines (WCAG) to address this issue.",
                code_before=None,
                code_after=None,
                effort_minutes=self.effort_minutes,
            )
        ]

    def to_ui_dict(self) -> dict:
        return {
            "priority": self.priority.value,
            "original_issue": self.original_issue,
            "user_impact": self.user_impact,
            "analysis_source": self.analysis_source,
            "fix_suggestions": self.fix_suggestions,
        }


class AnalysisResult(BaseModel):
    url: str
    enhanced_issues: List[EnhancedIssue]
    framework: str = "html"

    class Config:
        arbitrary_types_allowed = True

    @property
    def summary(self) -> Dict[str, Union[int, str]]:
        counts: Dict[str, Union[int, str]] = {
            "total_issues": 0,
            "critical_issues": 0,
            "high_issues": 0,
            "medium_issues": 0,
            "low_issues": 0,
        }
        total_minutes = 0
        ai_count = 0
        for e in self.enhanced_issues:
            counts["total_issues"] = int(counts["total_issues"]) + 1
            pr = e.priority
            if pr == Priority.CRITICAL:
                counts["critical_issues"] = int(counts["critical_issues"]) + 1
            elif pr == Priority.HIGH:
                counts["high_issues"] = int(counts["high_issues"]) + 1
            elif pr == Priority.MEDIUM:
                counts["medium_issues"] = int(counts["medium_issues"]) + 1
            else:
                counts["low_issues"] = int(counts["low_issues"]) + 1

            total_minutes += e.effort_minutes
            if e.analysis_source == "ai_enhanced":
                ai_count += 1

        parts: List[str] = []
        if counts["critical_issues"]:
            parts.append(f"{counts['critical_issues']} critical")
        if counts["high_issues"]:
            parts.append(f"{counts['high_issues']} high")
        if counts["medium_issues"]:
            parts.append(f"{counts['medium_issues']} medium")
        if counts["low_issues"]:
            parts.append(f"{counts['low_issues']} low")
        summary_text = (", ".join(parts) + " issues detected") if parts else "No issues detected"

        counts["estimated_total_time_minutes"] = total_minutes
        counts["ai_enhanced_issues"] = ai_count
        counts["summary"] = summary_text
        return counts
