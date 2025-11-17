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
from backend.logging_config import get_logger
from backend.exceptions import ReportParsingError, AIServiceError

logger = get_logger(__name__)


def analyze_report(
    report: Dict[str, Any],
    framework: str = "html",
    use_ai: bool = True,
    max_ai_issues: Optional[int] = 50,
    url: str = "api_request",
) -> Dict[str, Any]:
    """
    Analyze an accessibility report and enhance with AI insights.
    
    Args:
        report: Raw accessibility report data
        framework: Framework type (html, react, etc.)
        use_ai: Whether to use AI enhancement
        max_ai_issues: Maximum number of issues to enhance with AI
        url: URL being tested
        
    Returns:
        Dictionary with summary and issues
        
    Raises:
        ReportParsingError: If report parsing fails
        AIServiceError: If AI service encounters an error
    """
    logger.info(
        "analyzing_report",
        framework=framework,
        use_ai=use_ai,
        max_ai_issues=max_ai_issues,
        url=url
    )
    
    try:
        analyzer = AccessibilityAnalyzer(use_ai=use_ai, max_ai_issues=max_ai_issues)
        enhanced = analyzer.analyze_issues(raw_report=report, url=url, framework=framework)
    except Exception as e:
        logger.error(
            "analyzer_initialization_failed",
            error=str(e),
            error_type=type(e).__name__,
            framework=framework
        )
        raise AIServiceError(
            f"Failed to initialize analyzer: {str(e)}",
            error_code="ANALYZER_INIT_FAILED",
            details={"framework": framework, "use_ai": use_ai}
        ) from e

    # Build UI-friendly issues payload
    issues: List[Dict[str, Any]] = []
    ai_count = 0
    parse_errors = 0
    
    for ei in enhanced:
        try:
            oi = getattr(ei, "original_issue", None)
            rid = getattr(oi, "id", None) or "unknown"
            elements = getattr(oi, "elements", []) if oi is not None else []
            selector = (elements[0] if isinstance(elements, list) and elements else None)
            ai = getattr(ei, "ai_analysis", None)
            if getattr(ei, "analysis_source", "") == "ai_enhanced":
                ai_count += 1
            # Get priority value (handle both enum and string)
            priority = getattr(ei, "priority", "medium")
            priority_str = priority.value if hasattr(priority, "value") else str(priority)
            issues.append(
                {
                    "rule_id": str(rid),
                    "priority": priority_str,
                    "user_impact": (getattr(ai, "user_impact", "") if ai else ""),
                    "fix_suggestion": (getattr(ai, "fix_suggestion", "") if ai else ""),
                    "effort_minutes": int(getattr(ei, "effort_minutes", 15) or 15),
                    "wcag_refs": list(getattr(ai, "wcag_refs", []) or []) if ai else [],
                    "selector": selector,
                    "source": str(getattr(ei, "analysis_source", "")),
                }
            )
        except (AttributeError, ValueError, TypeError) as e:
            parse_errors += 1
            logger.warning(
                "issue_parsing_failed",
                error=str(e),
                error_type=type(e).__name__,
                issue_index=len(issues)
            )
            continue

    if parse_errors > 0:
        logger.warning(
            "report_parsing_completed_with_errors",
            total_issues=len(enhanced),
            parsed_issues=len(issues),
            parse_errors=parse_errors
        )

    try:
        summary = analyzer.get_analysis_summary(enhanced)
        summary["ai_enhanced_issues"] = int(ai_count)
    except Exception as e:
        logger.error(
            "summary_generation_failed",
            error=str(e),
            error_type=type(e).__name__
        )
        raise ReportParsingError(
            f"Failed to generate analysis summary: {str(e)}",
            error_code="SUMMARY_GENERATION_FAILED"
        ) from e
    
    logger.info(
        "report_analysis_completed",
        total_issues=len(issues),
        ai_enhanced=ai_count,
        parse_errors=parse_errors,
        url=url
    )
    
    return {"summary": summary, "issues": issues}

