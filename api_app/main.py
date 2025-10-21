from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from pydantic import BaseModel


# Ensure the repo root is importable
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class AnalyzeRequest(BaseModel):
    report: Dict[str, Any]
    framework: str = "html"
    use_ai: bool = True
    max_ai_issues: Optional[int] = 50
    url: Optional[str] = "api_request"


class IssueOut(BaseModel):
    rule_id: str
    priority: str
    user_impact: str = ""
    fix_suggestion: str = ""
    effort_minutes: int = 15
    wcag_refs: List[str] = []
    selector: Optional[str] = None
    source: str = ""


class AnalyzeResponse(BaseModel):
    summary: Dict[str, Any]
    issues: List[IssueOut]


app = FastAPI(title="Accessibility AI API", version="0.1.0")


@app.get("/health")
def health() -> Dict[str, Any]:
    try:
        from src.accessibility_ai.simple_ai import SimpleAIClient  # type: ignore

        ai_ok = SimpleAIClient().is_available()
    except Exception:
        ai_ok = False
    return {"status": "ok", "ai_configured": ai_ok}


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    from src.accessibility_ai.analyzer import AccessibilityAnalyzer  # type: ignore

    analyzer = AccessibilityAnalyzer(use_ai=req.use_ai, max_ai_issues=req.max_ai_issues)
    enhanced = analyzer.analyze_issues(
        raw_report=req.report,
        url=req.url or "api_request",
        framework=req.framework,
    )

    # Build UI-friendly issues payload
    issues: List[IssueOut] = []
    for ei in enhanced:
        try:
            oi = getattr(ei, "original_issue", None)
            rid = getattr(oi, "id", None) or "unknown"
            elements = getattr(oi, "elements", []) if oi is not None else []
            selector = (elements[0] if isinstance(elements, list) and elements else None)
            ai = getattr(ei, "ai_analysis", None)
            issues.append(
                IssueOut(
                    rule_id=str(rid),
                    priority=str(getattr(ei, "priority", "medium")),
                    user_impact=(getattr(ai, "user_impact", "") if ai else ""),
                    fix_suggestion=(getattr(ai, "fix_suggestion", "") if ai else ""),
                    effort_minutes=int(getattr(ei, "effort_minutes", 15) or 15),
                    wcag_refs=list(getattr(ai, "wcag_refs", []) or []) if ai else [],
                    selector=selector,
                    source=str(getattr(ei, "analysis_source", "")),
                )
            )
        except Exception:
            continue

    summary = analyzer.get_analysis_summary(enhanced)
    return AnalyzeResponse(summary=summary, issues=issues)

