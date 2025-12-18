import json
import re
from typing import List, Dict, Any, Optional, Tuple

from ..models import AccessibilityIssue


def _map_htmlcs_code_to_rule_id(code: str, message: str) -> str:
    """Map HTMLCS/Pa11y WCAG code strings to canonical rule IDs used by our rule DB.

    Pa11y (runner=htmlcs) often reports rules with long WCAG2AA.* codes.
    Our internal rule database uses axe-style short IDs (e.g., 'button-name').
    """
    code = (code or "").strip()
    msg = (message or "").lower()

    # Button accessible name (WCAG 4.1.2 - H91 Button Name)
    if "h91.button.name" in code.lower() or ("button element does not have a name" in msg):
        return "button-name"

    # Contrast failures (WCAG 1.4.3 - G18 Fail)
    if "g18.fail" in code.lower() or ("insufficient contrast" in msg and "contrast ratio" in msg):
        return "color-contrast"

    # Iframe title (WCAG 2.4.1 / H64.1 iframe title)
    if "h64.1" in code.lower() or ("iframe element requires" in msg and "title attribute" in msg):
        return "iframe-title"

    # Fallback: keep original code
    return code or "unknown"


_CONTRAST_RE = re.compile(
    r"Expected a contrast ratio of at least\s+(?P<expected>[0-9]+(?:\.[0-9]+)?)\s*:\s*1.*?contrast ratio of\s+(?P<actual>[0-9]+(?:\.[0-9]+)?)\s*:\s*1",
    re.IGNORECASE,
)
_RECOMMEND_COLOR_RE = re.compile(r"Recommendation:\s*change text colour to\s*(?P<hex>#[0-9a-fA-F]{3,6})", re.IGNORECASE)


def _extract_contrast_evidence(message: str) -> Dict[str, Any]:
    """Extract measured/expected contrast ratios and any recommended color from HTMLCS message."""
    out: Dict[str, Any] = {}
    if not message:
        return out

    m = _CONTRAST_RE.search(message)
    if m:
        try:
            out["expected_ratio"] = float(m.group("expected"))
            out["contrast_ratio"] = float(m.group("actual"))
        except Exception:
            pass

    m2 = _RECOMMEND_COLOR_RE.search(message)
    if m2:
        out["recommended_text_color"] = m2.group("hex")

    return out


def parse_pa11y_report(report: Dict[str, Any]) -> List[AccessibilityIssue]:
    """Parse a Pa11y JSON report into a list of AccessibilityIssue.

    Expects a structure with a top-level "issues" list.
    Maps Pa11y severity types to standard impact levels.
    Also maps HTMLCS WCAG codes to canonical rule IDs used by our rule DB and
    enriches element metadata for better grouping and better developer guidance.
    """
    issues: List[AccessibilityIssue] = []
    items = report.get("issues") or []
    if not isinstance(items, list):
        return issues

    # Pa11y severity mapping to standard impact
    SEVERITY_MAP = {
        "error": "critical",
        "warning": "moderate",
        "notice": "low",
    }

    for item in items:
        if not isinstance(item, dict):
            continue

        raw_code = str(item.get("code", "unknown"))
        message = str(item.get("message", "") or "")
        selector = item.get("selector")
        context = item.get("context") or ""
        runner = item.get("runner") or "pa11y"

        rule_id = _map_htmlcs_code_to_rule_id(raw_code, message)

        pa11y_type = str(item.get("type", "moderate"))
        impact = SEVERITY_MAP.get(pa11y_type.lower(), pa11y_type)

        element: Dict[str, Any] = {
            "selector": str(selector) if selector else "unknown-selector",
            "html": str(context),
            "message": message,
            "runner": runner,
            "raw_code": raw_code,
        }

        # Add contrast evidence when applicable
        if rule_id == "color-contrast":
            element.update(_extract_contrast_evidence(message))

        issues.append(
            AccessibilityIssue(
                id=rule_id,
                description=message,
                impact=impact,
                elements=[element],
            )
        )

    return issues
