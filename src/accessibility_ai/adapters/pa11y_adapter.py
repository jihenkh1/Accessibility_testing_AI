import json
from typing import List, Dict, Any

from ..models import AccessibilityIssue


def parse_pa11y_report(report: Dict[str, Any]) -> List[AccessibilityIssue]:
    """Parse a Pa11y JSON report into a list of AccessibilityIssue.

    Expects a structure with a top-level "issues" list.
    Maps Pa11y severity types to standard impact levels.
    """
    # Pa11y severity mapping to standard impact
    SEVERITY_MAP = {
        "error": "critical",
        "warning": "moderate",
        "notice": "minor"
    }
    
    issues: List[AccessibilityIssue] = []
    raw_issues = report.get("issues")
    if not isinstance(raw_issues, list):
        return issues

    for item in raw_issues:
        # Accept strings by attempting to coerce to dict; otherwise store as plain description
        if isinstance(item, str):
            try:
                parsed = json.loads(item)
                if isinstance(parsed, dict):
                    item = parsed
                else:
                    issues.append(
                        AccessibilityIssue(
                            id="pa11y:string",
                            description=item,
                            impact="moderate",
                            elements=[],
                        )
                    )
                    continue
            except Exception:
                issues.append(
                    AccessibilityIssue(
                        id="pa11y:string",
                        description=item,
                        impact="moderate",
                        elements=[],
                    )
                )
                continue

        if not isinstance(item, dict):
            # Unknown shape; skip instead of crashing
            continue

        selector = item.get("selector", "")
        elements = [selector] if selector else []
        
        # Map Pa11y type to standard impact level
        pa11y_type = str(item.get("type", "moderate"))
        impact = SEVERITY_MAP.get(pa11y_type.lower(), pa11y_type)
        
        issues.append(
            AccessibilityIssue(
                id=str(item.get("code", "unknown")),
                description=str(item.get("message", "")),
                impact=impact,
                elements=elements,
            )
        )

    return issues
