from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, ValidationInfo
from pydantic_core import PydanticCustomError


class AnalyzeRequest(BaseModel):
    report: Dict[str, Any]
    framework: str = Field(default="html", description="html|react|vue|angular|svelte")
    use_ai: bool = True
    max_ai_issues: Optional[int] = 50
    url: Optional[str] = "api_request"
    project_name: Optional[str] = "Default Project"
    
    @field_validator("framework")
    @classmethod
    def validate_framework(cls, v: str) -> str:
        """Validate framework is one of the supported types."""
        allowed = {"html", "react", "vue", "angular", "svelte"}
        if v.lower() not in allowed:
            raise ValueError(
                f"Invalid framework '{v}'. Must be one of: {', '.join(allowed)}"
            )
        return v.lower()
    
    @field_validator("max_ai_issues")
    @classmethod
    def validate_max_ai_issues(cls, v: Optional[int]) -> Optional[int]:
        """Validate max_ai_issues is reasonable."""
        if v is not None:
            if v < 0:
                raise ValueError("max_ai_issues must be non-negative")
            if v > 1000:
                raise ValueError("max_ai_issues cannot exceed 1000")
        return v
    
    @field_validator("report")
    @classmethod
    def validate_report_not_empty(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate report is not empty."""
        if not v:
            raise ValueError("Report cannot be empty")
        return v
    
    @field_validator("project_name")
    @classmethod
    def validate_project_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate project name length."""
        if v and len(v) > 200:
            raise ValueError("Project name cannot exceed 200 characters")
        return v


class IssueOut(BaseModel):
    id: Optional[int] = None
    rule_id: str
    priority: str
    user_impact: str = ""
    fix_suggestion: str = ""
    effort_minutes: int = 15
    wcag_refs: List[str] = []
    selector: Optional[str] = None
    source: str = ""
    status: str = "todo"


class AnalyzeResponse(BaseModel):
    scan_id: Optional[int] = None
    summary: Dict[str, Any]
    issues: List[IssueOut]


class ScanSummary(BaseModel):
    id: int
    ts: str
    url: str
    framework: str
    total_issues: int
    critical_issues: int
    high_issues: int
    medium_issues: int
    low_issues: int
    estimated_total_time_minutes: int
    ai_enhanced_issues: int
    project_name: Optional[str] = "Default Project"
    # Additional computed fields for frontend
    name: Optional[str] = None
    most_violated_rule: Optional[str] = None
    most_violated_wcag: Optional[str] = None
    trend: Optional[float] = None
    # Raw report artifacts
    pdf_report_path: Optional[str] = None
    html_report_path: Optional[str] = None
    raw_report_json: Optional[str] = None
    screenshots_dir: Optional[str] = None


class IssuesPage(BaseModel):
    items: List[IssueOut]
    total: int


# Manual Testing Schemas

class ChecklistItem(BaseModel):
    id: str
    category: str
    # Legacy fields (for backward compatibility)
    title: Optional[str] = None
    description: Optional[str] = None
    wcag: Optional[str] = None
    # New actionable fields
    test_item: Optional[str] = None  # Specific action to perform
    how_to_test: Optional[str] = None  # Step-by-step instructions
    what_to_look_for: Optional[str] = None  # Success criteria
    wcag_reference: Optional[str] = None  # WCAG guideline reference
    priority: str
    estimated_time: Optional[int] = None  # Time estimate in minutes


# ============================================================================
# MANUAL BUG TRACKING SCHEMAS (V2)
# ============================================================================

class ManualBugCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500, description="One-line bug summary")
    wcag_criterion: str = Field(description="WCAG success criterion (e.g., 2.1.1, 1.4.3)")
    severity: str = Field(description="Critical, High, Medium, or Low")
    testing_tool: str = Field(description="NVDA, Keyboard, Zoom, or Other")
    description: str = Field(min_length=1, description="What is broken")
    expected_behavior: str = Field(min_length=1, description="What should happen")
    actual_behavior: str = Field(min_length=1, description="What actually happens")
    steps_to_reproduce: Optional[str] = None
    affected_user_groups: Optional[str] = None
    notes: Optional[str] = None
    project_name: str = "Default Project"
    run_id: Optional[int] = None
    created_by: Optional[str] = None

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        allowed = ["Critical", "High", "Medium", "Low"]
        if v not in allowed:
            raise ValueError(f"Severity must be one of: {', '.join(allowed)}")
        return v

    @field_validator("testing_tool")
    @classmethod
    def validate_testing_tool(cls, v: str) -> str:
        allowed = ["NVDA", "Keyboard", "Zoom", "Other"]
        if v not in allowed:
            raise ValueError(f"Testing tool must be one of: {', '.join(allowed)}")
        return v


class ManualBugResponse(BaseModel):
    id: int
    title: str
    wcag_criterion: str
    severity: str
    testing_tool: str
    description: str
    expected_behavior: str
    actual_behavior: str
    steps_to_reproduce: Optional[str]
    affected_user_groups: Optional[str]
    notes: Optional[str]
    project_name: str
    run_id: Optional[int]
    created_at: str
    created_by: Optional[str]
    evidence_count: int = 0


class ManualBugDetail(ManualBugResponse):
    evidence: List[Dict[str, Any]] = []


class BugEvidenceResponse(BaseModel):
    id: int
    bug_id: int
    file_path: str
    file_type: str
    file_size: int
    uploaded_at: str


class TestingMethodStats(BaseModel):
    tool: str
    bug_count: int
    last_tested: Optional[str]
