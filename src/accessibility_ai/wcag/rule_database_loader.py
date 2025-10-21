"""
WCAG Rules Database Loader

Loads and caches accessibility rule guidance from JSON database.
Provides instant lookups for common WCAG issues without AI calls.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class RuleDatabaseLoader:
    """Loads and provides access to WCAG rules database"""
    
    def __init__(self, database_path: Optional[str] = None):
        """
        Initialize the rule database loader
        
        Parameters
        ----------
        database_path : Optional[str]
            Path to rules_database.json. If None, uses default location.
        """
        if database_path is None:
            # Default to same directory as this file
            self.database_path = Path(__file__).parent / "rules_database.json"
        else:
            self.database_path = Path(database_path)
        self._rules_cache: Optional[Dict[str, Any]] = None
        self._load_database()
    
    def _load_database(self) -> None:
        """Load rules database from JSON file into memory"""
        try:
            with open(self.database_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._rules_cache = data if isinstance(data, dict) else {}
            logger.info(f"Loaded {len(self._rules_cache)} rules from database")
        except FileNotFoundError:
            logger.warning(f"Rules database not found at {self.database_path}")
            self._rules_cache = {}
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse rules database: {e}")
            self._rules_cache = {}
    
    def get_rule(self, rule_id: str) -> Optional[Dict[str, Any]]:
        """
        Get rule data for a specific rule ID
        
        Parameters
        ----------
        rule_id : str
            The rule identifier (e.g., 'button-name', 'image-alt')
        
        Returns
        -------
        Optional[Dict[str, Any]]
            Rule data dictionary or None if not found
        """
        if self._rules_cache is None:
            return None
        
        # Normalize rule ID (lowercase, handle variations)
        normalized_id = rule_id.lower().strip()
        return self._rules_cache.get(normalized_id)
    
    def has_rule(self, rule_id: str) -> bool:
        """Check if rule exists in database"""
        return self.get_rule(rule_id) is not None
    
    def get_fix_for_framework(self, rule_id: str, framework: str = "html") -> Optional[str]:
        """
        Get framework-specific fix suggestion
        
        Parameters
        ----------
        rule_id : str
            The rule identifier
        framework : str
            Framework name ('html', 'react', 'vue', 'angular', 'svelte')
        
        Returns
        -------
        Optional[str]
            Framework-specific code example or None
        """
        rule_data = self.get_rule(rule_id)
        if not rule_data:
            return None
        
        fixes = rule_data.get('fix_by_framework', {})
        framework_normalized = framework.lower().strip()
        
        # Try exact match first
        if framework_normalized in fixes:
            return fixes[framework_normalized]
        
        # Fallback to html if framework not found
        return fixes.get('html')
    
    def get_effort_estimate(self, rule_id: str) -> int:
        """Get estimated effort in minutes to fix this issue"""
        rule_data = self.get_rule(rule_id)
        if not rule_data:
            return 5  # Default estimate
        return rule_data.get('effort_minutes', 5)
    
    def requires_ai_enhancement(self, rule_id: str) -> bool:
        """
        Check if this rule requires AI enhancement
        
        Some rules (like color-contrast) need context-specific AI analysis,
        while others (like button-name) have complete guidance in database.
        
        Parameters
        ----------
        rule_id : str
            The rule identifier
        
        Returns
        -------
        bool
            True if AI enhancement recommended, False if rule DB is sufficient
        """
        rule_data = self.get_rule(rule_id)
        if not rule_data:
            return True  # Unknown rules should use AI
        return rule_data.get('requires_ai', False)
    
    def get_wcag_references(self, rule_id: str) -> list:
        """Get WCAG success criteria references for this rule"""
        rule_data = self.get_rule(rule_id)
        if not rule_data:
            return []
        return rule_data.get('wcag', [])
    
    def get_user_impact(self, rule_id: str) -> str:
        """Get description of user impact for this issue"""
        rule_data = self.get_rule(rule_id)
        if not rule_data:
            return "This issue may affect users with disabilities."
        return rule_data.get('user_impact', "This issue may affect users with disabilities.")
    
    def get_all_rule_ids(self) -> list:
        """Get list of all rule IDs in database"""
        if self._rules_cache is None:
            return []
        return list(self._rules_cache.keys())
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the rules database"""
        if self._rules_cache is None:
            return {'total_rules': 0, 'requires_ai': 0, 'rule_based': 0}
        
        total = len(self._rules_cache)
        requires_ai = sum(1 for rule in self._rules_cache.values() if rule.get('requires_ai', False))
        
        return {
            'total_rules': total,
            'requires_ai': requires_ai,
            'rule_based': total - requires_ai,
            'coverage_percentage': round((total - requires_ai) / total * 100, 1) if total > 0 else 0
        }


# Global instance for easy access
_global_loader: Optional[RuleDatabaseLoader] = None


def get_rule_database() -> RuleDatabaseLoader:
    """Get the global rule database loader instance"""
    global _global_loader
    if _global_loader is None:
        _global_loader = RuleDatabaseLoader()
    return _global_loader
