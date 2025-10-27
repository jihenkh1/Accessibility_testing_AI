from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    report: Dict[str, Any]
    framework: str = Field(default="html", description="html|react|vue|angular|svelte")
    use_ai: bool = True
    max_ai_issues: Optional[int] = 50
    url: Optional[str] = "api_request"


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
    # Additional computed fields for frontend
    name: Optional[str] = None
    most_violated_rule: Optional[str] = None
    most_violated_wcag: Optional[str] = None
    trend: Optional[float] = None


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


class ChecklistGenerateRequest(BaseModel):
    page_type: str = Field(description="landing, form, dashboard, or ecommerce")
    components: List[str] = Field(default=[], description="List of component names")
    run_id: Optional[int] = Field(default=None, description="Optional: link to existing scan run")


class ChecklistResponse(BaseModel):
    checklist_id: int
    page_type: str
    components: List[str]
    total_items: int
    categories: List[str]
    priority_counts: Dict[str, int]
    estimated_minutes: int
    items: List[ChecklistItem]
    created_at: str


class TestSessionCreate(BaseModel):
    checklist_id: int
    tester_name: str
    run_id: Optional[int] = None


class TestSessionResponse(BaseModel):
    id: int
    run_id: Optional[int]
    checklist_id: int
    tester_name: str
    started_at: str
    completed_at: Optional[str]
    status: str


class TestResultRecord(BaseModel):
    session_id: int
    item_id: str
    status: str = Field(description="passed, failed, needs_retest, skipped")
    notes: Optional[str] = None


class TestResultResponse(BaseModel):
    id: int
    session_id: int
    checklist_id: int
    item_id: str
    status: str
    notes: Optional[str]
    screenshot_path: Optional[str]
    created_at: str


class SessionResultsSummary(BaseModel):
    session: TestSessionResponse
    checklist: ChecklistResponse
    results: List[TestResultResponse]
    progress: Dict[str, int]  # passed, failed, needs_retest, skipped counts

