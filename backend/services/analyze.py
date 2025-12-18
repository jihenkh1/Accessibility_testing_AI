from __future__ import annotations

import json
import re
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


def _extract_best_selector(elements: Any) -> Optional[str]:
    """
    Return a meaningful selector for UI.

    - Skips metadata-only dicts like {"occurrence_count": N}
    - Prefers string selectors
    - Falls back to common selector keys in dicts
    - Returns None if no meaningful selector is found (better than dumping JSON)
    """
    if not isinstance(elements, list) or not elements:
        return None

    for item in elements:
        # direct selector string
        if isinstance(item, str) and item.strip():
            return item.strip()

        # dict element: look for common selector keys
        if isinstance(item, dict):
            for key in ("selector", "css", "xpath", "id"):
                val = item.get(key)
                if isinstance(val, str) and val.strip():
                    return val.strip()

            # If it looks like ONLY metadata, skip it
            if set(item.keys()).issubset({"occurrence_count", "count", "occurrences"}):
                continue

    return None


def _sanitize_user_impact(text: Any) -> str:
    """
    Remove fake precision (e.g., 'Affects 2.2% ...') while keeping meaning.

    This is a lightweight demo-safe sanitizer: it removes sentences containing '%'.
    """
    if not isinstance(text, str):
        return ""
    if "%" not in text:
        return text.strip()

    # Remove any sentence fragments containing '%'
    parts = [p.strip() for p in text.split(".") if p.strip() and "%" not in p]
    cleaned = ". ".join(parts).strip()
    if cleaned and not cleaned.endswith("."):
        cleaned += "."
    return cleaned


def _sanitize_fix_suggestion(rule_id: str, text: Any, issue_description: str = "", elements: Any = None) -> str:
    """
    Make fix suggestions safer and less misleading for demo:
      - Avoid defaulting to aria-label='Search' unless context indicates search
      - Prefer <ACTION> placeholder when action is unknown
    """
    if not isinstance(text, str):
        return ""

    s = text.strip()
    if not s:
        return ""

    rid = (rule_id or "").lower()

    # Prevent misleading "Search" default for button-name unless context indicates it
    if rid == "button-name":
        evidence_blob = " ".join(
            [
                issue_description or "",
                json.dumps(elements, ensure_ascii=False) if elements is not None else "",
            ]
        ).lower()
        has_search_evidence = "search" in evidence_blob

        if re.search(r'aria-label\s*=\s*[\'"]search[\'"]', s, flags=re.IGNORECASE) and not has_search_evidence:
            return (
                "Add an accessible name that matches the button's action. "
                "Use visible text or aria-label/aria-labelledby (e.g., \"Previous slide\", \"Next slide\", \"Close\", \"Search\")."
            )

    return s


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
        url=url,
    )

    try:
        analyzer = AccessibilityAnalyzer(use_ai=use_ai, max_ai_issues=max_ai_issues)
        enhanced = analyzer.analyze_issues(raw_report=report, url=url, framework=framework)
    except Exception as e:
        logger.error(
            "analyzer_initialization_failed",
            error=str(e),
            error_type=type(e).__name__,
            framework=framework,
        )
        raise AIServiceError(
            f"Failed to initialize analyzer: {str(e)}",
            error_code="ANALYZER_INIT_FAILED",
            details={"framework": framework, "use_ai": use_ai},
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

            # Extract a meaningful selector for UI (skip occurrence_count dicts)
            selector = _extract_best_selector(elements)

            ai = getattr(ei, "ai_analysis", None)

            if getattr(ei, "analysis_source", "") == "ai_enhanced":
                ai_count += 1

            # Get priority value (handle both enum and string)
            priority = getattr(ei, "priority", "medium")
            priority_str = priority.value if hasattr(priority, "value") else str(priority)

            # Extract + sanitize user impact and fix suggestion
            user_impact_raw = getattr(ai, "user_impact", "") if ai else ""
            fix_suggestion_raw = getattr(ai, "fix_suggestion", "") if ai else ""

            user_impact = _sanitize_user_impact(user_impact_raw)
            fix_suggestion = _sanitize_fix_suggestion(
                rule_id=str(rid),
                text=fix_suggestion_raw,
                issue_description=str(getattr(oi, "description", "") if oi else ""),
                elements=elements,
            )

            issues.append(
                {
                    "rule_id": str(rid),
                    "priority": priority_str,
                    "user_impact": user_impact,
                    "fix_suggestion": fix_suggestion,
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
                issue_index=len(issues),
            )
            continue

    if parse_errors > 0:
        logger.warning(
            "report_parsing_completed_with_errors",
            total_issues=len(enhanced),
            parsed_issues=len(issues),
            parse_errors=parse_errors,
        )

    try:
        summary = analyzer.get_analysis_summary(enhanced)
        summary["ai_enhanced_issues"] = int(ai_count)
    except Exception as e:
        logger.error(
            "summary_generation_failed",
            error=str(e),
            error_type=type(e).__name__,
        )
        raise ReportParsingError(
            f"Failed to generate analysis summary: {str(e)}",
            error_code="SUMMARY_GENERATION_FAILED",
        ) from e

    logger.info(
        "report_analysis_completed",
        total_issues=len(issues),
        ai_enhanced=ai_count,
        parse_errors=parse_errors,
        url=url,
    )

    return {"summary": summary, "issues": issues}
