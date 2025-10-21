from typing import List, Dict, Any, Optional, Union
import logging

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
from pathlib import Path
import json
from .prioritizer import IssuePrioritizer

logger = logging.getLogger(__name__)


class AccessibilityAnalyzer:
    """Main analysis engine for processing accessibility reports."""

    def __init__(self, use_ai: bool = True, max_ai_issues: Optional[int] = None, enable_persistent_cache: bool = True, cache_path: Optional[str] = None, cache_ttl_days: int = 30) -> None:
        """
        Initialize the analyzer with lazy AI client loading for better performance.

        Parameters
        ----------
        use_ai: bool
            If True, the analyzer will attempt to enhance issues via the AI service.
            If the service is unavailable or an API key is missing, it will fall
            back to rule-based heuristics. When False, AI will never be used.
        enable_persistent_cache: bool
            If True, cache AI results in SQLite database
        cache_path: Optional[str]
            Custom path for cache database (default: ./ai_cache.sqlite)
        cache_ttl_days: int
            Cache time-to-live in days (default: 30 days)
        """
        self.use_ai = use_ai
        self.ai_client: Optional[SimpleAIClient] = None
        self._ai_initialized = False
        self._ai_cache: Dict[Any, Optional[AIAnalysis]] = {}
        self.max_ai_issues = max_ai_issues
        self._framework = "html"
        self._prioritizer = IssuePrioritizer()
        self._rule_db = get_rule_database()
        # Persistent cache across runs with expiration
        self._persistent_cache: Optional[AICache] = None
        # Track AI usage statistics
        self._ai_calls_used = 0
        self._rule_db_hits = 0
        if enable_persistent_cache:
            try:
                db = Path(cache_path) if cache_path else Path.cwd() / "ai_cache.sqlite"
                self._persistent_cache = AICache(db, ttl_days=cache_ttl_days)
                # Clean up expired entries on startup
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
                self._ai_initialized = True  # Don't retry
                return False

        return self.ai_client is not None and self.ai_client.is_available()

    def analyze_issues(
        self,
        raw_report: Dict[str, Any],
        url: str = "unknown",
        framework: str = "html",
    ) -> List[EnhancedIssue]:
        """
        Parse the raw report and return a list of EnhancedIssue objects.
        """
        logger.info(f"Starting analysis for {url}")
        # Persist the framework for AI prompts
        try:
            self._framework = framework
        except Exception:
            self._framework = "html"

        # Extract normalized issues
        issues = self._extract_issues(raw_report)
        logger.info(f"Extracted {len(issues)} issues from report")

        # Reset AI usage tracking
        self._ai_calls_used = 0
        self._rule_db_hits = 0

        # Enhance with grouping and in-run cache.
        enhanced: List[EnhancedIssue] = []
        processed_groups = 0

        def _group_key(item: AccessibilityIssue) -> Any:
            # Group by rule/description and first few selectors
            desc = (item.description or "").strip().lower()[:200]
            impact = (item.impact or "").strip().lower()
            top_elems = tuple((item.elements or [])[:3])
            return (item.id, desc, impact, top_elems)

        for issue in issues:
            key = _group_key(issue)
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
                    # Include framework and prompt version to fingerprint cache entries
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

            # SMART ROUTING: Rule Database → AI (budget-limited)
            # Try rule database first
            rule_analysis = self._try_rule_database(issue)
            
            if rule_analysis is not None:
                # Rule database provided complete guidance!
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

            # Gate by heuristics (only trigger AI for valuable cases)
            context = {
                "framework": self._framework,
                "ai_calls_used": self._ai_calls_used,
                "max_ai_calls": self.max_ai_issues or 5,
            }
            
            if self._prioritizer.should_enrich(issue, context):
                # Budget check: only call AI for up to max_ai_issues unique groups
                budget_ok = self.max_ai_issues is None or processed_groups < self.max_ai_issues
                if budget_ok:
                    ei = self._enhance_issue_with_ai(issue)
                    self._ai_cache[key] = ei.ai_analysis
                    self._ai_calls_used += 1
                    processed_groups += 1  # Count attempted group to enforce budget
                    # Persist if AI provided data - store full payload from ai_analysis
                    if getattr(self, "_persistent_cache", None) is not None and ei.ai_analysis is not None:
                        try:
                            pkey = AICache.make_key(*(list(key) + [self._framework, PROMPT_VERSION]))
                            payload = self._ai_analysis_to_raw(ei.ai_analysis)
                            if self._persistent_cache is not None:
                                self._persistent_cache.set(pkey, json.dumps(payload, ensure_ascii=False))  # type: ignore[attr-defined]
                        except Exception:
                            pass
                    enhanced.append(ei)
                else:
                    # No budget: fallback rule-based
                    enhanced.append(
                        EnhancedIssue(
                            original_issue=issue,
                            ai_analysis=None,
                            analysis_source="rule_based",
                        )
                    )
            else:
                # Gating skipped AI: keep rule-based
                enhanced.append(
                    EnhancedIssue(
                        original_issue=issue,
                        ai_analysis=None,
                        analysis_source="rule_based",
                    )
                )

        logger.info(f"Analysis completed: {self._rule_db_hits} from rule DB, {self._ai_calls_used} from AI, {len(enhanced) - self._rule_db_hits - self._ai_calls_used} generic fallback")
        return enhanced

    def _extract_issues(self, raw_report: Dict[str, Any]) -> List[AccessibilityIssue]:
        """
        Extract standardized `AccessibilityIssue` objects from various report formats.
        Supports axe-core (`violations`) and Pa11y (`issues`) formats.
        """
        issues: List[AccessibilityIssue] = []

        # Axe-core format (use adapter)
        if isinstance(raw_report.get("violations"), list):
            issues.extend(parse_axe_report(raw_report))

        # Pa11y format
        elif isinstance(raw_report.get("issues"), list):
            issues.extend(parse_pa11y_report(raw_report))

        # Generic fallback: detect lists of dicts with id/description/impact
        else:
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
        return issues

    def _try_rule_database(self, issue: AccessibilityIssue) -> Optional[AIAnalysis]:
        """
        Try to get complete guidance from rule database without using AI.
        
        Returns AIAnalysis populated from rule database, or None if AI is needed.
        """
        rule_id = issue.id or ""
        
        # Check if rule exists
        if not self._rule_db.has_rule(rule_id):
            return None
        
        # Check if rule requires AI (e.g., color-contrast needs specific calculations)
        if self._rule_db.requires_ai_enhancement(rule_id):
            return None
        
        # Build AIAnalysis from rule database
        try:
            fix_code = self._rule_db.get_fix_for_framework(rule_id, self._framework) or ""
            rule_data = self._rule_db.get_rule(rule_id)
            
            if not rule_data:
                return None
            
            # Map severity to priority
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

    def _enhance_issue_with_ai(self, issue: AccessibilityIssue) -> EnhancedIssue:
        """
        Enhance a single issue with AI analysis if available.
        """
        ai_analysis: Optional[AIAnalysis] = None
        analysis_source = "rule_based"

        # Circuit breaker: if AI had too many failures in this run, skip AI
        if self.use_ai and not getattr(self, "_ai_disabled", False) and self._ensure_ai_client():
            try:
                # Ensure AI client is non-None after _ensure_ai_client()
                ai_client = self.ai_client
                assert ai_client is not None, "AI client should be initialized when available"
                ai_raw = ai_client.analyze_accessibility_issue(
                    issue_description=issue.description,
                    elements=issue.elements,
                    impact=issue.impact,
                    rule_id=issue.id,
                    framework=getattr(self, "_framework", "html"),
                ) or {}
                # Coerce/validate AI fields defensively
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

                # Safely coerce optional list/dict fields
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
                analysis_source = "ai_enhanced"
            except Exception as e:
                logger.warning(f"AI enhancement failed for {issue.id}: {e}")
                # Increment failure count and possibly disable AI for the rest of the run
                fail_count = getattr(self, "_ai_failures", 0) + 1
                self._ai_failures = fail_count
                if fail_count >= 5:
                    self._ai_disabled = True
                    logger.info("AI disabled for this run due to repeated failures (circuit breaker)")

        return EnhancedIssue(
            original_issue=issue,
            ai_analysis=ai_analysis,
            analysis_source=analysis_source,
        )

    def get_analysis_summary(
        self,
        result: Union[AnalysisResult, List[EnhancedIssue]],
    ) -> Dict[str, Union[int, str]]:
        """
        Compute summary statistics (including estimated_total_time_minutes and a text summary).

        Returns a dict with ints for counts/time and a string for 'summary'.
        This fixes mypy issues where a Dict[str, int] was used but a string
        key ('summary') was inserted.
        """
        # If an AnalysisResult was provided, leverage its built-in summary
        if isinstance(result, AnalysisResult):
            # result.summary already includes the string 'summary' key
            return result.summary  # type: ignore[return-value]

        # Otherwise assume it's an iterable of EnhancedIssue objects
        if not isinstance(result, list):
            raise ValueError(
                "get_analysis_summary expects either an AnalysisResult or a list of EnhancedIssue instances",
            )

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

        # Return type allows both ints and a string
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
        """Build full AIAnalysis from cached/raw dict (persistent cache)."""
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
        """Convert AIAnalysis back to a raw dict to persist full payload."""
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
        """
        Get statistics about AI usage in the last analysis.
        
        Useful for monitoring free tier API usage and optimization.
        """
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
