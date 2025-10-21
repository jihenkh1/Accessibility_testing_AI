from typing import List

from .models import EnhancedIssue


def detect_patterns(issues: List[EnhancedIssue]) -> List[str]:
    """Very simple pattern detector to augment the UI.

    - Flags systemic rule ids (5+ instances)
    - Flags repeated selectors (exact string match appearing 5+ times)
    """
    patterns: List[str] = []

    # Count by rule id
    by_rule = {}
    for ei in issues:
        rid = ei.original_issue.id
        by_rule[rid] = by_rule.get(rid, 0) + 1
    for rid, count in by_rule.items():
        if count >= 10:
            patterns.append(f"Systemic {rid} issue ({count} instances)")
        elif count >= 5:
            patterns.append(f"Recurring {rid} issue ({count} instances)")

    # Count by exact selector
    by_selector = {}
    for ei in issues:
        for sel in ei.original_issue.elements or []:
            by_selector[sel] = by_selector.get(sel, 0) + 1
    frequent_selectors = [s for s, c in by_selector.items() if c >= 5]
    if frequent_selectors:
        top = ", ".join(frequent_selectors[:5])
        patterns.append(f"Frequently affected selectors: {top}")

    return patterns

