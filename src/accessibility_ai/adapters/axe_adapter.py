from typing import List, Dict, Any

from ..models import AccessibilityIssue


def parse_axe_report(report: Dict[str, Any]) -> List[AccessibilityIssue]:
    """Parse an axe-core JSON report into a list of AccessibilityIssue.

    Expects a structure with a top-level "violations" list.
    Safely handles missing fields and varied node target shapes.
    """
    issues: List[AccessibilityIssue] = []
    violations = report.get("violations")
    if not isinstance(violations, list):
        return issues

    for violation in violations:
        elements: List[str] = []
        for node in (violation.get("nodes") or []):
            target = node.get("target", [])
            if isinstance(target, list):
                elements.extend([str(t) for t in target])
            elif target:
                elements.append(str(target))

        issues.append(
            AccessibilityIssue(
                id=str(violation.get("id", "unknown")),
                description=str(violation.get("description", "")),
                impact=str(violation.get("impact", "moderate")),
                elements=elements,
            )
        )

    return issues

