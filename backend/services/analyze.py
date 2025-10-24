from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure repo root on path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.accessibility_ai.analyzer import AccessibilityAnalyzer  # type: ignore


def analyze_report(
    report: Dict[str, Any],
    framework: str = "html",
    use_ai: bool = True,
    max_ai_issues: Optional[int] = 50,
    url: str = "api_request",
) -> Dict[str, Any]:
    analyzer = AccessibilityAnalyzer(use_ai=use_ai, max_ai_issues=max_ai_issues)
    enhanced = analyzer.analyze_issues(raw_report=report, url=url, framework=framework)

    # Build UI-friendly issues payload
    issues: List[Dict[str, Any]] = []
    ai_count = 0
    for ei in enhanced:
        try:
            oi = getattr(ei, "original_issue", None)
            rid = getattr(oi, "id", None) or "unknown"
            elements = getattr(oi, "elements", []) if oi is not None else []
            selector = (elements[0] if isinstance(elements, list) and elements else None)
            ai = getattr(ei, "ai_analysis", None)
            if getattr(ei, "analysis_source", "") == "ai_enhanced":
                ai_count += 1
            issues.append(
                {
                    "rule_id": str(rid),
                    "priority": str(getattr(ei, "priority", "medium")),
                    "user_impact": (getattr(ai, "user_impact", "") if ai else ""),
                    "fix_suggestion": (getattr(ai, "fix_suggestion", "") if ai else ""),
                    "effort_minutes": int(getattr(ei, "effort_minutes", 15) or 15),
                    "wcag_refs": list(getattr(ai, "wcag_refs", []) or []) if ai else [],
                    "selector": selector,
                    "source": str(getattr(ei, "analysis_source", "")),
                }
            )
        except Exception:
            continue

    summary = analyzer.get_analysis_summary(enhanced)
    # Ensure ai_enhanced_issues is present for storage
    try:
        summary["ai_enhanced_issues"] = int(ai_count)
    except Exception:
        pass
    return {"summary": summary, "issues": issues}

