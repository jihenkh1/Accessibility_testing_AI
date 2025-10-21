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


class ScanUrlRequest(BaseModel):
    url: str
    framework: str = Field(default="html")
    use_ai: bool = True
    max_ai_issues: Optional[int] = 50
    max_pages: int = 20
    same_origin_only: bool = True
    scanner: str = Field(default="axe", description="axe|pa11y")  # NEW: Choose scanning engine


class IssuesPage(BaseModel):
    items: List[IssueOut]
    total: int
