from typing import List, Dict, Any

from ..models import AccessibilityIssue


def parse_pa11y_report(report: Dict[str, Any]) -> List[AccessibilityIssue]:
    """Parse a Pa11y JSON report into a list of AccessibilityIssue.

    Expects a structure with a top-level "issues" list.
    """
    issues: List[AccessibilityIssue] = []
    raw_issues = report.get("issues")
    if not isinstance(raw_issues, list):
        return issues

    for item in raw_issues:
        selector = item.get("selector", "")
        elements = [selector] if selector else []
        issues.append(
            AccessibilityIssue(
                id=str(item.get("code", "unknown")),
                description=str(item.get("message", "")),
                impact=str(item.get("type", "moderate")),
                elements=elements,
            )
        )

    return issues

