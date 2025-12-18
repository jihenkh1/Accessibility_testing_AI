from typing import List, Dict, Any
import re

from ..models import AccessibilityIssue


def _extract_tag_from_html(html: str) -> str:
    if not html:
        return 'unknown'
    m = re.match(r"\s*<\s*(\w+)", html)
    return m.group(1).lower() if m else 'unknown'


def _extract_color_info_from_node(node: Dict[str, Any]) -> Dict[str, Any]:
    """Extract contrast/color info if present in axe node checks."""
    data = {}
    checks = list(node.get('any', [])) + list(node.get('all', []))
    for check in checks:
        cid = str(check.get('id', '')).lower()
        if 'color-contrast' in cid:
            d = check.get('data', {}) or {}
            data.update({
                'fg_color': d.get('fgColor') or d.get('fg_color'),
                'bg_color': d.get('bgColor') or d.get('bg_color'),
                'contrast_ratio': d.get('contrastRatio') or d.get('contrast_ratio'),
                'expected_ratio': d.get('expectedContrastRatio') or d.get('expected_contrast_ratio'),
                'font_size': d.get('fontSize'),
                'font_weight': d.get('fontWeight'),
            })
            break
    return data


def parse_axe_report(report: Dict[str, Any]) -> List[AccessibilityIssue]:
    """Parse an axe-core JSON report into a list of AccessibilityIssue.

    This enhanced parser extracts structured element information (selector, html, tag,
    role, aria-label, colors) and returns that as the `elements` field on
    `AccessibilityIssue`. It falls back to selector strings if richer data is
    unavailable, and avoids returning 'None' or 'undefined' selectors.
    """
    issues: List[AccessibilityIssue] = []
    violations = report.get('violations')
    if not isinstance(violations, list):
        return issues

    for violation in violations:
        enhanced_elements: List[Dict[str, Any]] = []

        for node in (violation.get('nodes') or []):
            # Prefer node.target (list) but filter invalid entries
            raw_targets = node.get('target') or []
            targets = []
            if isinstance(raw_targets, list):
                for t in raw_targets:
                    if t and str(t).strip() and str(t).strip().lower() not in ('undefined', 'none'):
                        targets.append(str(t).strip())
            elif raw_targets:
                if str(raw_targets).strip().lower() not in ('undefined', 'none'):
                    targets.append(str(raw_targets).strip())

            # Fallback selector
            selector = targets[0] if targets else (node.get('selector') or node.get('xpath') or 'unknown-selector')

            # Defensive cleanup for selector
            if not selector or str(selector).strip().lower() in ('undefined', 'none'):
                selector = node.get('xpath') or 'unknown-selector'

            html = node.get('html') or ''
            tag = _extract_tag_from_html(html)
            role = node.get('role')
            aria_label = node.get('aria-label') or node.get('aria_label')

            # Extract color/contrast info when present
            color_info = _extract_color_info_from_node(node)

            elem = {
                'selector': selector,
                'html': html,
                'tag': tag,
                'role': role,
                'aria_label': aria_label,
            }
            elem.update(color_info)

            enhanced_elements.append(elem)

        issues.append(
            AccessibilityIssue(
                id=str(violation.get('id', 'unknown')),
                description=str(violation.get('description', '')),
                impact=str(violation.get('impact', 'moderate')),
                elements=enhanced_elements,
            )
        )

    return issues

