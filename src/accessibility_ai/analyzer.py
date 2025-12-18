from typing import List, Dict, Any, Optional, Union, Tuple
import logging
import re
import json
from pathlib import Path

from .models import (
    AccessibilityIssue,
    Priority,
    AIAnalysis,
    EnhancedIssue,
    AnalysisResult,
)
from .simple_ai import SimpleAIClient, PROMPT_VERSION
from .adapters.axe_adapter import parse_axe_report
from .adapters.pa11y_adapter import parse_pa11y_report
from .ai.cache import AICache
from .wcag import get_rule_database
from .prioritizer import IssuePrioritizer

logger = logging.getLogger(__name__)


class AccessibilityAnalyzer:
    """Main analysis engine for processing accessibility reports."""

    def __init__(
        self,
        use_ai: bool = True,
        max_ai_issues: Optional[int] = None,
        enable_persistent_cache: bool = True,
        cache_path: Optional[str] = None,
        cache_ttl_days: int = 30,
    ) -> None:
        self.use_ai = use_ai
        self.ai_client: Optional[SimpleAIClient] = None
        self._ai_initialized = False
        self._ai_cache: Dict[Any, Optional[AIAnalysis]] = {}
        self.max_ai_issues = max_ai_issues
        self._framework = "html"
        self._prioritizer = IssuePrioritizer()
        self._rule_db = get_rule_database()

        self._persistent_cache: Optional[AICache] = None
        self._ai_calls_used = 0
        self._rule_db_hits = 0

        if enable_persistent_cache:
            try:
                db = Path(cache_path) if cache_path else Path.cwd() / "ai_cache.sqlite"
                self._persistent_cache = AICache(db, ttl_days=cache_ttl_days)
                if self._persistent_cache:
                    self._persistent_cache.cleanup_expired()
            except Exception as e:
                logger.warning(f"Failed to initialize persistent cache: {e}")
                self._persistent_cache = None

        if use_ai:
            logger.info("Analyzer initialized (AI will be loaded on demand)")
        else:
            logger.info("Basic analyzer initialized (AI disabled)")

    def _ensure_ai_client(self) -> bool:
        """Lazy initialization of AI client for better startup performance"""
        if not self.use_ai:
            return False

        if not self._ai_initialized:
            try:
                self.ai_client = SimpleAIClient()
                self._ai_initialized = True
                if self.ai_client.is_available():
                    logger.info("AI client loaded successfully")
                    return True
                else:
                    logger.info("AI not available - using rule-based analysis")
                    return False
            except Exception as e:
                logger.warning(f"AI client initialization failed: {e}")
                self._ai_initialized = True
                return False

        return self.ai_client is not None and self.ai_client.is_available()

    # -------------------------------------------------------------------------
    # NEW: Better grouping helpers (industry standard)
    # -------------------------------------------------------------------------

    def _normalize_signature(self, text: str) -> str:
        """
        Normalize volatile parts so the same issue groups together.
        Removes numbers, repeated whitespace, and common unstable fragments.
        """
        s = (text or "").strip().lower()
        s = re.sub(r"\s+", " ", s)
        s = re.sub(r"\b\d+(\.\d+)?\b", "N", s)  # 4.48 -> N
        s = s[:250]
        return s

    def _group_key(self, item: AccessibilityIssue) -> Tuple[str, str, str]:
        """
        Group by RULE + normalized description + impact.
        IMPORTANT: do NOT include selectors here.
        """
        rid = (item.id or "").strip().lower()
        desc = self._normalize_signature(item.description or "")
        impact = (item.impact or "").strip().lower()
        return (rid, desc, impact)

    def _merge_group(self, group: List[AccessibilityIssue]) -> AccessibilityIssue:
        """
        Merge occurrences into one AccessibilityIssue:
        - Keep first issue fields (id/description/impact)
        - Merge all unique element selectors/entries
        - Add a metadata dict at the start with occurrence_count
        """
        first = group[0]
        merged: List[Any] = []
        seen: set = set()

        def _element_hash(el: Any) -> str:
            hashed = self._elements_to_hashable([el])
            return hashed[0] if hashed else str(el)

        for it in group:
            for el in (it.elements or []):
                h = _element_hash(el)
                if h not in seen:
                    seen.add(h)
                    merged.append(el)

        # prepend metadata (safe: your code handles dicts in _elements_to_hashable)
        merged = [{"occurrence_count": len(group)}] + merged

        return AccessibilityIssue(
            id=first.id,
            description=first.description,
            impact=first.impact,
            elements=merged,
        )

    def _group_issues(self, issues: List[AccessibilityIssue]) -> List[AccessibilityIssue]:
        """
        Group all issues and merge occurrences so UI does not get spammed.
        """
        buckets: Dict[Tuple[str, str, str], List[AccessibilityIssue]] = {}
        for it in issues:
            buckets.setdefault(self._group_key(it), []).append(it)

        grouped = [self._merge_group(g) for g in buckets.values()]

        if len(grouped) != len(issues):
            logger.info("Grouped %d issues into %d grouped issues", len(issues), len(grouped))

        return grouped

    def _extract_occurrence_count(self, elements: Optional[List[Any]]) -> int:
        """
        Read occurrence_count metadata if present.
        """
        if not elements:
            return 1
        first = elements[0]
        if isinstance(first, dict) and "occurrence_count" in first:
            raw = first.get("occurrence_count", 1)
            try:
                return int(raw) if raw is not None else 1
            except (TypeError, ValueError):
                return 1
        return 1

    # -------------------------------------------------------------------------
    # MAIN
    # -------------------------------------------------------------------------

    def analyze_issues(
        self,
        raw_report: Dict[str, Any],
        url: str = "unknown",
        framework: str = "html",
    ) -> List[EnhancedIssue]:
        logger.info(f"Starting analysis for {url}")
        try:
            self._framework = framework
        except Exception:
            self._framework = "html"

        issues = self._extract_issues(raw_report)
        logger.info(f"Extracted {len(issues)} issues from report")

        # NEW: group BEFORE enhancement so AI runs once per grouped issue
        issues = self._group_issues(issues)

        self._ai_calls_used = 0
        self._rule_db_hits = 0

        enhanced: List[EnhancedIssue] = []
        processed_groups = 0

        for issue in issues:
            # Cache key is now stable and does not include selectors
            key = self._group_key(issue)

            # In-run cache
            if key in self._ai_cache:
                cached_analysis = self._ai_cache[key]
                enhanced.append(
                    EnhancedIssue(
                        original_issue=issue,
                        ai_analysis=cached_analysis,
                        analysis_source="ai_enhanced" if cached_analysis else "rule_based",
                    )
                )
                continue

            # Persistent cache check
            if getattr(self, "_persistent_cache", None) is not None and self._persistent_cache is not None:
                try:
                    pkey = AICache.make_key(*(list(key) + [self._framework, PROMPT_VERSION]))
                    cached_json = self._persistent_cache.get(pkey)  # type: ignore[attr-defined]
                    if cached_json:
                        ai_raw = json.loads(cached_json)
                        cached_ai = self._build_ai_analysis_from_ai_raw(ai_raw)
                        self._ai_cache[key] = cached_ai
                        enhanced.append(
                            EnhancedIssue(
                                original_issue=issue,
                                ai_analysis=cached_ai,
                                analysis_source="ai_enhanced",
                            )
                        )
                        continue
                except Exception:
                    pass

            # Rule DB first
            rule_analysis = self._try_rule_database(issue)
            if rule_analysis is not None:
                self._rule_db_hits += 1
                self._ai_cache[key] = rule_analysis
                enhanced.append(
                    EnhancedIssue(
                        original_issue=issue,
                        ai_analysis=rule_analysis,
                        analysis_source="rule_database",
                    )
                )
                continue

            # Gate AI usage
            context = {
                "framework": self._framework,
                "ai_calls_used": self._ai_calls_used,
                "max_ai_calls": self.max_ai_issues or 5,
            }

            if self._prioritizer.should_enrich(issue, context):
                budget_ok = self.max_ai_issues is None or processed_groups < self.max_ai_issues
                if budget_ok:
                    ei = self._enhance_issue_with_ai(issue)
                    self._ai_cache[key] = ei.ai_analysis
                    self._ai_calls_used += 1
                    processed_groups += 1

                    # Persist AI payload if available
                    if (
                        getattr(self, "_persistent_cache", None) is not None
                        and ei.ai_analysis is not None
                        and getattr(ei, "analysis_source", "") == "ai_enhanced"
                    ):
                        try:
                            pkey = AICache.make_key(*(list(key) + [self._framework, PROMPT_VERSION]))
                            payload = self._ai_analysis_to_raw(ei.ai_analysis)
                            if self._persistent_cache is not None:
                                self._persistent_cache.set(pkey, json.dumps(payload, ensure_ascii=False))  # type: ignore[attr-defined]
                        except Exception:
                            pass

                    enhanced.append(ei)
                else:
                    enhanced.append(EnhancedIssue(original_issue=issue, ai_analysis=None, analysis_source="rule_based"))
            else:
                enhanced.append(EnhancedIssue(original_issue=issue, ai_analysis=None, analysis_source="rule_based"))

        logger.info(
            f"Analysis completed: {self._rule_db_hits} from rule DB, "
            f"{self._ai_calls_used} from AI, "
            f"{len(enhanced) - self._rule_db_hits - self._ai_calls_used} generic fallback"
        )
        return enhanced

    # -------------------------------------------------------------------------
    # Issue extraction (kept mostly unchanged, but remove selector-based dedupe)
    # -------------------------------------------------------------------------

    def _extract_issues(self, raw_report: Dict[str, Any]) -> List[AccessibilityIssue]:
        issues: List[AccessibilityIssue] = []

        if "axe-core" in raw_report and isinstance(raw_report["axe-core"], dict):
            axe_data = raw_report["axe-core"]
            if isinstance(axe_data.get("violations"), list):
                issues.extend(parse_axe_report(axe_data))
            if isinstance(axe_data.get("incomplete"), list) and axe_data["incomplete"]:
                incomplete_report = {"violations": axe_data["incomplete"]}
                issues.extend(parse_axe_report(incomplete_report))

        if isinstance(raw_report.get("violations"), list):
            issues.extend(parse_axe_report(raw_report))

        if isinstance(raw_report.get("incomplete"), list) and raw_report["incomplete"]:
            incomplete_report = {"violations": raw_report["incomplete"]}
            issues.extend(parse_axe_report(incomplete_report))

        if "pa11y" in raw_report:
            pa11y_data = raw_report["pa11y"]
            if isinstance(pa11y_data, dict) and isinstance(pa11y_data.get("issues"), list):
                issues.extend(parse_pa11y_report(pa11y_data))
            elif isinstance(pa11y_data, list):
                issues.extend(parse_pa11y_report({"issues": pa11y_data}))
        elif isinstance(raw_report.get("issues"), list):
            issues.extend(parse_pa11y_report(raw_report))

        if not issues:
            for _, value in raw_report.items():
                if isinstance(value, list) and value and isinstance(value[0], dict):
                    sample = value[0]
                    if any(k in sample for k in ("id", "description", "impact")):
                        for item in value:
                            els = item.get("elements", [])
                            if not isinstance(els, list):
                                els = [str(els)]
                            issues.append(
                                AccessibilityIssue(
                                    id=str(item.get("id", "unknown")),
                                    description=str(item.get("description", "")),
                                    impact=str(item.get("impact", "moderate")),
                                    elements=[str(e) for e in els],
                                )
                            )
                        break

        # NOTE: We intentionally do NOT “dedupe by selector” anymore.
        # Grouping is done later by rule+signature+impact.
        return issues

    # -------------------------------------------------------------------------
    # Rule database routing (unchanged)
    # -------------------------------------------------------------------------

    def _try_rule_database(self, issue: AccessibilityIssue) -> Optional[AIAnalysis]:
        rule_id = issue.id or ""

        # Deterministic contrast handling when evidence is present (avoid AI)
        if rule_id == "color-contrast":
            contrast_ai = self._build_contrast_from_evidence(issue)
            if contrast_ai:
                return contrast_ai
        # Deterministic landmark coverage handling when evidence is present (avoid AI)
        if rule_id == "region":
            region_ai = self._build_region_from_evidence(issue)
            if region_ai:
                return region_ai
        # Deterministic unique landmark naming when evidence is present (avoid AI)
        if rule_id == "landmark-unique":
            landmark_ai = self._build_landmark_unique_from_evidence(issue)
            if landmark_ai:
                return landmark_ai

        if not self._rule_db.has_rule(rule_id):
            return None
        if self._rule_db.requires_ai_enhancement(rule_id):
            return None

        try:
            fix_code = self._rule_db.get_fix_for_framework(rule_id, self._framework) or ""
            rule_data = self._rule_db.get_rule(rule_id)
            if not rule_data:
                return None

            severity_map = {
                "critical": Priority.CRITICAL,
                "serious": Priority.HIGH,
                "moderate": Priority.MEDIUM,
                "minor": Priority.LOW,
            }
            severity = rule_data.get("severity", "moderate")
            priority = severity_map.get(severity, Priority.MEDIUM)

            return AIAnalysis(
                priority=priority,
                user_impact=self._rule_db.get_user_impact(rule_id),
                fix_suggestion=fix_code,
                wcag_refs=self._rule_db.get_wcag_references(rule_id),
                effort_minutes=self._rule_db.get_effort_estimate(rule_id),
            )
        except Exception as e:
            logger.warning(f"Failed to build analysis from rule database for {rule_id}: {e}")
            return None

    # -------------------------------------------------------------------------
    # Element hashing (your safe version kept)
    # -------------------------------------------------------------------------

    def _elements_to_hashable(self, elements: Any) -> List[str]:
        out: List[str] = []
        if not elements:
            return out

        for el in elements:
            s: Optional[str]
            try:
                if isinstance(el, str):
                    s = el.strip() or "unknown-selector"
                elif isinstance(el, dict):
                    sel = el.get("selector") or el.get("xpath") or el.get("id")
                    if isinstance(sel, str) and sel.strip():
                        s = sel.strip()
                    elif sel is not None:
                        s = str(sel)
                    else:
                        try:
                            fp = {k: el.get(k) for k in ("selector", "tag", "role") if k in el}
                            s = json.dumps(fp, sort_keys=True, ensure_ascii=False) if fp else "unknown-selector"
                        except Exception:
                            s = "unknown-selector"
                else:
                    s = str(el)
            except Exception:
                s = "unknown-selector"

            if not s or str(s).strip().lower() in ("undefined", "none"):
                s = "unknown-selector"
            out.append(str(s))

        return out

    # -------------------------------------------------------------------------
    # AI enhancement (unchanged)
    # -------------------------------------------------------------------------

    def _build_contrast_from_evidence(self, issue: AccessibilityIssue) -> Optional[AIAnalysis]:
        """
        Build a deterministic color-contrast analysis from extracted evidence.
        Requires fg/bg/contrast_ratio/expected_ratio to be present on any element.
        """
        if not issue or issue.id != "color-contrast":
            return None

        elems = issue.elements or []
        evidence: Optional[Dict[str, Any]] = None
        for el in elems:
            if not isinstance(el, dict):
                continue
            fg = el.get("fg_color") or el.get("fgColor")
            bg = el.get("bg_color") or el.get("bgColor")
            ratio = el.get("contrast_ratio") or el.get("contrastRatio")
            expected = el.get("expected_ratio") or el.get("expectedContrastRatio")
            if fg and bg and ratio is not None and expected is not None:
                evidence = {
                    "fg": fg,
                    "bg": bg,
                    "ratio": ratio,
                    "expected": expected,
                    "recommended": el.get("recommended_text_color") or el.get("recommendedTextColor"),
                }
                break

        if not evidence:
            return None

        fg = evidence["fg"]
        bg = evidence["bg"]
        ratio = evidence["ratio"]
        expected = evidence["expected"]
        rec = evidence.get("recommended")

        evidence_line = f"Evidence: contrast {ratio} with foreground {fg} on background {bg}; required {expected}."
        steps = [
            "Fix steps:",
            "- Adjust the text color (preferred) or background color to meet the required ratio; update design tokens if used.",
            "- Re-check the specific element(s) with a contrast checker (axe/DevTools).",
        ]
        if rec:
            steps.append(f"- Pa11y recommendation: use text color {rec}.")
        verify = [
            "Verify:",
            "- Use a contrast checker in DevTools to confirm the ratio meets WCAG.",
            "- Rerun axe/pa11y to confirm the color-contrast issue is resolved.",
        ]

        fix_text = "\n".join([evidence_line, "", "\n".join(steps), "", "\n".join(verify)])

        return AIAnalysis(
            priority=Priority.HIGH,
            user_impact=self._rule_db.get_user_impact("color-contrast"),
            fix_suggestion=fix_text,
            wcag_refs=self._rule_db.get_wcag_references("color-contrast"),
            effort_minutes=self._rule_db.get_effort_estimate("color-contrast"),
        )

    def _is_vague_fix(self, text: str) -> bool:
        """Detect weak/vague fix suggestions."""
        if not text:
            return True
        lower = text.lower()
        weak_verbs = {"review", "ensure", "consider", "verify", "check"}
        action_verbs = {"add", "remove", "change", "replace", "update", "wrap", "move", "set", "provide", "use"}
        words = text.split()
        first = words[0].lower() if words else ""
        has_action = any(v in lower for v in action_verbs)
        if first in weak_verbs and not has_action:
            return True
        has_selector = any(ch in text for ch in [".", "#", "[", "<"])
        has_specifics = any(ch in text for ch in [":", "=", '"', "'"])
        if not (has_selector or has_specifics or has_action) and len(text) > 60:
            return True
        return False

    def _trim_html(self, html: str, max_len: int = 180) -> str:
        """Trim and normalize HTML snippets for evidence display."""
        if not html:
            return ""
        try:
            normalized = " ".join(html.split())
        except Exception:
            normalized = html
        if len(normalized) <= max_len:
            return normalized
        return normalized[:max_len].rstrip() + "..."

    def _build_region_from_evidence(self, issue: AccessibilityIssue) -> Optional[AIAnalysis]:
        """
        Build a deterministic guidance for region when axe evidence is available.
        Uses selectors/html from the elements list; does not invent labels or structure.
        """
        if not issue or issue.id != "region":
            return None

        elems = issue.elements or []
        occurrences: List[str] = []
        total_occurrences = 0

        def _selector_from_element(el: Any) -> str:
            if isinstance(el, dict):
                sel = el.get("selector")
                if not sel and isinstance(el.get("target"), list) and el.get("target"):
                    sel = el.get("target")[0]
                return str(sel) if sel else "unknown-selector"
            try:
                return str(el)
            except Exception:
                return "unknown-selector"

        def _html_from_element(el: Any) -> str:
            if isinstance(el, dict):
                html = el.get("html") or ""
                if html:
                    return self._trim_html(html, max_len=180)
            return ""

        for el in elems:
            if isinstance(el, dict) and "occurrence_count" in el and len(el.keys()) == 1:
                continue
            total_occurrences += 1
            sel = _selector_from_element(el)
            html_snip = _html_from_element(el)
            entry = f"- Selector: {sel}"
            if html_snip:
                entry += f" | HTML: {html_snip}"
            occurrences.append(entry)
            if len(occurrences) >= 3:
                break

        if not occurrences:
            return None

        if total_occurrences > len(occurrences):
            occurrences.append(f"(+{total_occurrences - len(occurrences)} more)")

        evidence_block = "\n".join(["Evidence (from axe):"] + occurrences)
        fixes = [
            "Fix steps:",
            "- Ensure the page has a single <main> landmark for primary content.",
            "- Wrap or move navigation, footer, and complementary sections into semantic landmarks (<nav>, <footer>, <aside>) or role equivalents.",
            "- If multiple landmarks of the same type exist, give each a unique accessible name via aria-label or aria-labelledby that matches its purpose (choose the label based on actual page content).",
        ]
        verify = [
            "Verify:",
            "- Rerun axe to confirm the region issue is resolved.",
            "- Use a screen reader's landmark navigation to ensure each landmark is present and uniquely named.",
        ]

        fix_text = "\n".join([evidence_block, "", "\n".join(fixes), "", "\n".join(verify)])

        return AIAnalysis(
            priority=Priority.MEDIUM,
            user_impact=self._rule_db.get_user_impact("region"),
            fix_suggestion=fix_text,
            wcag_refs=self._rule_db.get_wcag_references("region"),
            effort_minutes=self._rule_db.get_effort_estimate("region"),
        )

    def _build_landmark_unique_from_evidence(self, issue: AccessibilityIssue) -> Optional[AIAnalysis]:
        """
        Build deterministic guidance for landmark-unique when axe evidence is available.
        Uses selectors/html; does not guess labels or structure.
        """
        if not issue or issue.id != "landmark-unique":
            return None

        elems = issue.elements or []
        occurrences: List[str] = []
        total_occurrences = 0

        def _selector_from_element(el: Any) -> str:
            if isinstance(el, dict):
                sel = el.get("selector")
                if not sel and isinstance(el.get("target"), list) and el.get("target"):
                    sel = el.get("target")[0]
                return str(sel) if sel else "unknown-selector"
            try:
                return str(el)
            except Exception:
                return "unknown-selector"

        def _html_from_element(el: Any) -> str:
            if isinstance(el, dict):
                html = el.get("html") or ""
                if html:
                    return self._trim_html(html, max_len=180)
            return ""

        for el in elems:
            if isinstance(el, dict) and "occurrence_count" in el and len(el.keys()) == 1:
                continue
            total_occurrences += 1
            sel = _selector_from_element(el)
            html_snip = _html_from_element(el)
            entry = f"- Selector: {sel}"
            if html_snip:
                entry += f" | HTML: {html_snip}"
            occurrences.append(entry)
            if len(occurrences) >= 3:
                break

        if not occurrences:
            return None

        if total_occurrences > len(occurrences):
            occurrences.append(f"(+{total_occurrences - len(occurrences)} more)")

        evidence_block = "\n".join(["Evidence (from axe):"] + occurrences)
        fixes = [
            "Fix steps:",
            "- When multiple landmarks of the same type exist (e.g., multiple <nav>), give each a unique accessible name via aria-label or aria-labelledby.",
            "- Choose labels that reflect the actual purpose (e.g., \"Main navigation\", \"Footer links\", \"Breadcrumb\") without inventing content.",
            "- Keep one landmark per primary purpose; avoid duplicate unlabeled landmarks.",
        ]
        verify = [
            "Verify:",
            "- Rerun axe to confirm the landmark-unique issue is resolved.",
            "- Use a screen reader's landmark navigation to ensure each landmark is present and uniquely named.",
        ]

        fix_text = "\n".join([evidence_block, "", "\n".join(fixes), "", "\n".join(verify)])

        return AIAnalysis(
            priority=Priority.MEDIUM,
            user_impact=self._rule_db.get_user_impact("landmark-unique"),
            fix_suggestion=fix_text,
            wcag_refs=self._rule_db.get_wcag_references("landmark-unique"),
            effort_minutes=self._rule_db.get_effort_estimate("landmark-unique"),
        )

    def _vague_fix_templates(self) -> Dict[str, str]:
        """Deterministic templates for rules prone to vague guidance."""
        return {
            "landmark-unique": (
                "Give each landmark a unique accessible name: add aria-label or aria-labelledby so navigation, header, footer, and sidebars are distinguishable. "
                "Validate with a screen reader or axe to confirm no two landmarks share the same role+name."
            ),
            "region": (
                "Wrap page sections in landmarks: one <main> for primary content, <header>/<footer>/<nav>/aside where appropriate. "
                "Ensure all visible content is inside a landmark and rerun the accessibility scan."
            ),
            "page-has-heading-one": (
                "Add a single, descriptive <h1> near the top of the page that summarizes the page purpose. "
                "Keep only one <h1>; maintain correct heading order below it."
            ),
            "identical-links-same-purpose": (
                "Differentiate links with identical text: add context in the link text or aria-label so users can tell destinations apart. "
                "For repeated links to the same destination, keep text consistent; for different targets, add specific text (e.g., 'Pricing – Product A', 'Pricing – Product B')."
            ),
            "listitem": (
                "Ensure list content is inside semantic lists: wrap items in <li> within a parent <ul> or <ol>; do not leave standalone text or divs as list items. "
                "Confirm the DOM shows proper list and listitem roles."
            ),
        }

    def _enforce_vague_template(self, issue_id: str, ai_analysis: Optional[AIAnalysis]) -> Optional[AIAnalysis]:
        """Replace vague fixes with deterministic templates for specific rules."""
        if ai_analysis is None:
            return None
        templates = self._vague_fix_templates()
        if issue_id not in templates:
            return ai_analysis
        fix_text = ai_analysis.fix_suggestion or ""
        if self._is_vague_fix(fix_text):
            ai_analysis.fix_suggestion = templates[issue_id]
        return ai_analysis

    def _enhance_issue_with_ai(self, issue: AccessibilityIssue) -> EnhancedIssue:
        ai_analysis: Optional[AIAnalysis] = None
        analysis_source = "rule_based"

        if self.use_ai and not getattr(self, "_ai_disabled", False) and self._ensure_ai_client():
            try:
                ai_client = self.ai_client
                assert ai_client is not None, "AI client should be initialized when available"
                ai_raw = ai_client.analyze_accessibility_issue(
                    issue_description=issue.description,
                    elements=issue.elements,
                    impact=issue.impact,
                    rule_id=issue.id,
                    framework=getattr(self, "_framework", "html"),
                ) or {}
                fallback_used = bool(ai_raw.pop("__fallback__", False)) or not ai_raw
                if fallback_used:
                    logger.warning(f"AI returned empty/fallback response for {issue.id}")

                def as_text(v: Any) -> str:
                    if isinstance(v, list):
                        return "\n".join(str(x) for x in v)
                    return str(v)

                prio_raw = (ai_raw.get("priority") or "medium").lower()
                try:
                    prio = Priority(prio_raw)
                except ValueError:
                    prio = Priority.MEDIUM

                effort_raw = ai_raw.get("effort_minutes", 15)
                try:
                    effort_val = int(effort_raw)
                except (TypeError, ValueError):
                    effort_val = 15

                def as_list_str(v: Any) -> List[str]:
                    if isinstance(v, list):
                        return [str(x) for x in v]
                    if v is None:
                        return []
                    return [str(v)]

                def as_opt_dict(v: Any) -> Optional[Dict[str, Any]]:
                    return v if isinstance(v, dict) else None

                def as_opt_str(v: Any) -> Optional[str]:
                    return str(v) if v is not None else None

                def as_opt_int(v: Any) -> Optional[int]:
                    try:
                        return int(v) if v is not None else None
                    except (TypeError, ValueError):
                        return None

                ai_analysis = AIAnalysis(
                    priority=prio,
                    user_impact=str(ai_raw.get("user_impact", "")),
                    fix_suggestion=as_text(ai_raw.get("fix_suggestion", "")),
                    effort_minutes=effort_val,
                    code_example=as_opt_str(ai_raw.get("code_example")),
                    wcag_refs=as_list_str(ai_raw.get("wcag_refs")),
                    acceptance_criteria=as_list_str(ai_raw.get("acceptance_criteria")),
                    test_steps=as_list_str(ai_raw.get("test_steps")),
                    automation_hints=as_list_str(ai_raw.get("automation_hints")),
                    personas_impact=as_opt_dict(ai_raw.get("personas_impact")),
                    root_cause_hypothesis=as_opt_str(ai_raw.get("root_cause_hypothesis")),
                    component_guess=as_opt_str(ai_raw.get("component_guess")),
                    fix_plan=as_opt_dict(ai_raw.get("fix_plan")),
                    ticket_title=as_opt_str(ai_raw.get("ticket_title")),
                    ticket_body=as_opt_str(ai_raw.get("ticket_body")),
                    confidence=as_opt_int(ai_raw.get("confidence")),
                    risk_level=as_opt_str(ai_raw.get("risk_level")),
                )
                analysis_source = "ai_fallback" if fallback_used else "ai_enhanced"
            except Exception as e:
                logger.warning(f"AI enhancement failed for {issue.id}: {e}")
                fail_count = getattr(self, "_ai_failures", 0) + 1
                self._ai_failures = fail_count
                if fail_count >= 5:
                    self._ai_disabled = True
                    logger.info("AI disabled for this run due to repeated failures (circuit breaker)")

        # Enforce deterministic template when AI returns vague guidance for specific rules
        if ai_analysis:
            ai_analysis = self._enforce_vague_template(issue.id or "", ai_analysis)

        return EnhancedIssue(original_issue=issue, ai_analysis=ai_analysis, analysis_source=analysis_source)

    # -------------------------------------------------------------------------
    # Summary + cache conversion (unchanged)
    # -------------------------------------------------------------------------

    def get_analysis_summary(self, result: Union[AnalysisResult, List[EnhancedIssue]]) -> Dict[str, Union[int, str]]:
        if isinstance(result, AnalysisResult):
            return result.summary  # type: ignore[return-value]

        if not isinstance(result, list):
            raise ValueError("get_analysis_summary expects either an AnalysisResult or a list of EnhancedIssue instances")

        total = crit = high = med = low = ai_count = 0
        total_minutes = 0
        for issue in result:
            if not isinstance(issue, EnhancedIssue):
                raise ValueError("All items must be EnhancedIssue")
            total += 1
            pr = issue.priority
            if pr == Priority.CRITICAL:
                crit += 1
            elif pr == Priority.HIGH:
                high += 1
            elif pr == Priority.MEDIUM:
                med += 1
            else:
                low += 1
            total_minutes += issue.effort_minutes
            if issue.analysis_source == "ai_enhanced":
                ai_count += 1

        parts: List[str] = []
        if crit:
            parts.append(f"{crit} critical")
        if high:
            parts.append(f"{high} high")
        if med:
            parts.append(f"{med} medium")
        if low:
            parts.append(f"{low} low")
        summary_text = (", ".join(parts) + " issues detected") if parts else "No issues detected"

        return {
            "total_issues": total,
            "critical_issues": crit,
            "high_issues": high,
            "medium_issues": med,
            "low_issues": low,
            "estimated_total_time_minutes": total_minutes,
            "ai_enhanced_issues": ai_count,
            "summary": summary_text,
        }

    def _build_ai_analysis_from_ai_raw(self, ai_raw: Dict[str, Any]) -> AIAnalysis:
        prio_raw = (ai_raw.get("priority") or "medium").lower()
        try:
            prio = Priority(prio_raw)
        except ValueError:
            prio = Priority.MEDIUM

        effort_raw = ai_raw.get("effort_minutes", 15)
        try:
            effort_val = int(effort_raw)
        except (TypeError, ValueError):
            effort_val = 15

        def as_list_str(v: Any) -> List[str]:
            if isinstance(v, list):
                return [str(x) for x in v]
            if v is None:
                return []
            return [str(v)]

        def as_opt_dict(v: Any) -> Optional[Dict[str, Any]]:
            return v if isinstance(v, dict) else None

        def as_opt_str(v: Any) -> Optional[str]:
            return str(v) if v is not None else None

        def as_opt_int(v: Any) -> Optional[int]:
            try:
                return int(v) if v is not None else None
            except (TypeError, ValueError):
                return None

        return AIAnalysis(
            priority=prio,
            user_impact=str(ai_raw.get("user_impact", "")),
            fix_suggestion=str(ai_raw.get("fix_suggestion", "")),
            effort_minutes=effort_val,
            code_example=as_opt_str(ai_raw.get("code_example")),
            wcag_refs=as_list_str(ai_raw.get("wcag_refs")),
            acceptance_criteria=as_list_str(ai_raw.get("acceptance_criteria")),
            test_steps=as_list_str(ai_raw.get("test_steps")),
            automation_hints=as_list_str(ai_raw.get("automation_hints")),
            personas_impact=as_opt_dict(ai_raw.get("personas_impact")),
            root_cause_hypothesis=as_opt_str(ai_raw.get("root_cause_hypothesis")),
            component_guess=as_opt_str(ai_raw.get("component_guess")),
            fix_plan=as_opt_dict(ai_raw.get("fix_plan")),
            ticket_title=as_opt_str(ai_raw.get("ticket_title")),
            ticket_body=as_opt_str(ai_raw.get("ticket_body")),
            confidence=as_opt_int(ai_raw.get("confidence")),
            risk_level=as_opt_str(ai_raw.get("risk_level")),
        )

    def _ai_analysis_to_raw(self, ai: AIAnalysis) -> Dict[str, Any]:
        return {
            "priority": ai.priority.value if isinstance(ai.priority, Priority) else str(ai.priority),
            "user_impact": ai.user_impact,
            "fix_suggestion": ai.fix_suggestion,
            "effort_minutes": ai.effort_minutes,
            "code_example": ai.code_example,
            "wcag_refs": list(ai.wcag_refs or []),
            "acceptance_criteria": list(ai.acceptance_criteria or []),
            "test_steps": list(ai.test_steps or []),
            "automation_hints": list(ai.automation_hints or []),
            "personas_impact": ai.personas_impact,
            "root_cause_hypothesis": ai.root_cause_hypothesis,
            "component_guess": ai.component_guess,
            "fix_plan": ai.fix_plan,
            "ticket_title": ai.ticket_title,
            "ticket_body": ai.ticket_body,
            "confidence": ai.confidence,
            "risk_level": ai.risk_level,
        }

    def get_ai_usage_stats(self) -> Dict[str, Any]:
        total_issues = self._ai_calls_used + self._rule_db_hits
        return {
            "total_issues_analyzed": total_issues,
            "ai_calls_used": self._ai_calls_used,
            "rule_database_hits": self._rule_db_hits,
            "generic_fallback": max(0, total_issues - self._ai_calls_used - self._rule_db_hits),
            "ai_usage_percentage": round((self._ai_calls_used / total_issues * 100) if total_issues > 0 else 0, 1),
            "rule_db_coverage": round((self._rule_db_hits / total_issues * 100) if total_issues > 0 else 0, 1),
            "max_ai_budget": self.max_ai_issues or 5,
            "budget_remaining": max(0, (self.max_ai_issues or 5) - self._ai_calls_used),
        }
