
from .models import Priority, AccessibilityIssue
from .wcag import get_rule_database
from typing import List, Dict, Any, Optional
import re
import logging

logger = logging.getLogger(__name__)


class IssuePrioritizer:
    """
    Smart prioritization engine that ranks accessibility issues
    by user impact, business risk, and fix effort.
    
    Uses rule database for instant lookups and intelligent AI gating.
    """
    
    def __init__(self):
        self.rule_db = get_rule_database()

        self.critical_blockers = [
            "keyboard trap", "focus management", "modal dialog",
            "form submission", "navigation", "skip link", "timeout"
        ]
        
        # High impact patterns affecting core functionality
        self.high_impact = [
            "form label", "button name", "link purpose", 
            "image alt", "headings", "landmarks", "aria"
        ]
        
        # Common but less critical patterns
        self.medium_impact = [
            "color contrast", "text spacing", "resize text",
            "multiple ways", "consistent navigation"
        ]

    def calculate_priority_score(self, issue: AccessibilityIssue, context: Optional[Dict[str, Any]] = None) -> int:
        """Calculate priority score (0-100) for an issue"""
        if context is None:
            context = {}
        
        score = 0
        
        # Base impact score
        impact_scores = {
            "critical": 80, 
            "serious": 60, 
            "moderate": 30, 
            "minor": 10
        }
        score += impact_scores.get(issue.impact.lower(), 20)
        
        # Critical blocker patterns
        description_lower = issue.description.lower()
        for pattern in self.critical_blockers:
            if pattern in description_lower:
                score += 40
                break
                
        # High impact patterns
        for pattern in self.high_impact:
            if pattern in description_lower:
                score += 25
                break
        
        # User flow importance
        if self._is_in_critical_flow(issue, context):
            score += 20
            
        # Affected elements count
        element_count = len(issue.elements)
        if element_count > 10:
            score += 15
        elif element_count > 5:
            score += 10
        elif element_count > 1:
            score += 5
            
        return min(score, 100)  # Cap at 100
    
    def _is_in_critical_flow(self, issue: AccessibilityIssue, context: Dict[str, Any]) -> bool:
        """Check if issue is in critical user flow (login, checkout, etc.)"""
        critical_selectors = [
            "login", "signin", "checkout", "payment", "submit", "buy", "purchase",
            "register", "signup", "contact", "search", "nav", "menu"
        ]
        
        for element in issue.elements:
            element_lower = element.lower()
            if any(selector in element_lower for selector in critical_selectors):
                return True
        return False
    
    def score_to_priority(self, score: int) -> Priority:
        """Convert numerical score to priority level"""
        if score >= 80:
            return Priority.CRITICAL
        elif score >= 60:
            return Priority.HIGH
        elif score >= 30:
            return Priority.MEDIUM
        else:
            return Priority.LOW
    
    def estimate_fix_time(self, issue: AccessibilityIssue, priority: Priority) -> int:
        """Estimate fix time in minutes based on issue complexity"""
        base_times = {
            Priority.CRITICAL: 45,
            Priority.HIGH: 25,
            Priority.MEDIUM: 15,
            Priority.LOW: 5
        }
        
        # Adjust for complexity
        complexity_multiplier = 1.0
        if len(issue.elements) > 10:
            complexity_multiplier = 2.0
        elif len(issue.elements) > 5:
            complexity_multiplier = 1.5
            
        return int(base_times[priority] * complexity_multiplier)
    
    def generate_user_impact(self, issue: AccessibilityIssue, priority: Priority) -> str:
        """Generate human-readable user impact description"""
        impact_templates = {
            Priority.CRITICAL: [
                "Completely blocks users with disabilities from completing tasks",
                "Prevents access to core functionality for assistive technology users",
                "Makes the application unusable for keyboard-only or screen reader users"
            ],
            Priority.HIGH: [
                "Significantly hinders user experience for people with disabilities",
                "Causes major difficulties in completing important tasks",
                "Creates substantial barriers for users with specific needs"
            ],
            Priority.MEDIUM: [
                "Causes inconvenience and extra effort for some users",
                "Makes certain tasks more difficult than necessary",
                "Affects user experience but doesn't block core functionality"
            ],
            Priority.LOW: [
                "Minor usability issue that could be improved",
                "Enhancement that would benefit some users",
                "Cosmetic or minor functional improvement"
            ]
        }
        
        import random
        templates = impact_templates[priority]
        return random.choice(templates)

    def should_enrich(self, issue: AccessibilityIssue, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Smart AI gating: Decide whether to use AI for this issue.
        
        Strategy:
        1. Check if rule exists in database
        2. If rule database has complete guidance (requires_ai=False), skip AI
        3. If rule requires contextual analysis (requires_ai=True), use AI
        4. If unknown rule, use AI
        5. Respect AI budget limits from context
        
        This minimizes AI usage for free tier API keys while maintaining quality.
        """
        ctx = context or {}
        
        # Check AI budget first (hard limit)
        ai_calls_used = ctx.get('ai_calls_used', 0)
        max_ai_calls = ctx.get('max_ai_calls', 5)  # Default: max 5 AI calls per scan
        
        if ai_calls_used >= max_ai_calls:
            logger.info(f"AI budget exhausted ({ai_calls_used}/{max_ai_calls}), using rule database")
            return False
        
        # Check if rule exists in database
        rule_id = issue.id or ""
        has_rule = self.rule_db.has_rule(rule_id)
        
        if not has_rule:
            # Unknown rule - use AI to analyze
            logger.info(f"Unknown rule '{rule_id}', will use AI")
            return True
        
        # Check if rule requires AI enhancement
        requires_ai = self.rule_db.requires_ai_enhancement(rule_id)
        
        if requires_ai:
            # Rule explicitly needs AI (e.g., color-contrast needs specific color suggestions)
            logger.info(f"Rule '{rule_id}' requires AI for context-specific analysis")
            return True
        
        # Rule database has complete guidance - no AI needed!
        logger.info(f"Rule '{rule_id}' has complete guidance in database, skipping AI")
        return False
