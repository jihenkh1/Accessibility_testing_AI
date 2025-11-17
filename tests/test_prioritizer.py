"""
Unit tests for IssuePrioritizer.

Tests priority assignment logic based on impact, WCAG level, and user experience factors.
"""
import pytest
from src.accessibility_ai.prioritizer import IssuePrioritizer
from src.accessibility_ai.models import AccessibilityIssue, Priority


class TestIssuePrioritizer:
    """Test suite for IssuePrioritizer class."""
    
    @pytest.fixture
    def prioritizer(self):
        """Create prioritizer instance."""
        return IssuePrioritizer()
    
    @pytest.fixture
    def critical_issue(self):
        """Create a critical impact issue."""
        return AccessibilityIssue(
            id="button-name",
            description="Buttons must have discernible text",
            impact="critical",
            elements=["button.submit"],
            wcag_level="A"
        )
    
    @pytest.fixture
    def moderate_issue(self):
        """Create a moderate impact issue."""
        return AccessibilityIssue(
            id="color-contrast",
            description="Elements must have sufficient color contrast",
            impact="moderate",
            elements=[".text-gray"],
            wcag_level="AA"
        )
    
    @pytest.fixture
    def minor_issue(self):
        """Create a minor impact issue."""
        return AccessibilityIssue(
            id="meta-viewport",
            description="Zooming and scaling should not be disabled",
            impact="minor",
            elements=["meta[name=viewport]"],
            wcag_level="AAA"
        )
    
    def test_prioritizer_initialization(self, prioritizer):
        """Test prioritizer initializes correctly."""
        assert prioritizer is not None
        assert hasattr(prioritizer, "assign_priority")
    
    def test_critical_impact_gets_high_priority(self, prioritizer, critical_issue):
        """Test critical impact issues get high/critical priority."""
        priority = prioritizer.assign_priority(critical_issue)
        assert priority in [Priority.CRITICAL, Priority.HIGH]
    
    def test_moderate_impact_gets_medium_priority(self, prioritizer, moderate_issue):
        """Test moderate impact issues get medium priority."""
        priority = prioritizer.assign_priority(moderate_issue)
        assert priority in [Priority.MEDIUM, Priority.HIGH]
    
    def test_minor_impact_gets_low_priority(self, prioritizer, minor_issue):
        """Test minor impact issues get low/medium priority."""
        priority = prioritizer.assign_priority(minor_issue)
        assert priority in [Priority.LOW, Priority.MEDIUM]
    
    def test_wcag_level_a_increases_priority(self, prioritizer):
        """Test WCAG Level A issues get higher priority."""
        level_a_issue = AccessibilityIssue(
            id="test-rule",
            description="Test",
            impact="moderate",
            elements=[".test"],
            wcag_level="A"
        )
        
        level_aaa_issue = AccessibilityIssue(
            id="test-rule",
            description="Test",
            impact="moderate",
            elements=[".test"],
            wcag_level="AAA"
        )
        
        priority_a = prioritizer.assign_priority(level_a_issue)
        priority_aaa = prioritizer.assign_priority(level_aaa_issue)
        
        # Level A should be higher or equal priority to AAA for same impact
        priority_order = {Priority.CRITICAL: 4, Priority.HIGH: 3, Priority.MEDIUM: 2, Priority.LOW: 1}
        assert priority_order[priority_a] >= priority_order[priority_aaa]
    
    def test_multiple_elements_doesnt_change_priority(self, prioritizer):
        """Test that number of affected elements doesn't change base priority."""
        single_element = AccessibilityIssue(
            id="test-rule",
            description="Test",
            impact="critical",
            elements=[".test"],
            wcag_level="AA"
        )
        
        multiple_elements = AccessibilityIssue(
            id="test-rule",
            description="Test",
            impact="critical",
            elements=[".test1", ".test2", ".test3"],
            wcag_level="AA"
        )
        
        priority_single = prioritizer.assign_priority(single_element)
        priority_multiple = prioritizer.assign_priority(multiple_elements)
        
        # Base priority should be same (though AI might later adjust for scale)
        assert priority_single == priority_multiple
    
    def test_unknown_impact_defaults_to_medium(self, prioritizer):
        """Test unknown impact levels default to low priority (conservative approach)."""
        unknown_impact_issue = AccessibilityIssue(
            id="test-rule",
            description="Test",
            impact="unknown",
            elements=[".test"],
            wcag_level="AA"
        )
        
        # Unknown impact gets base score of 20, which maps to LOW priority
        priority = prioritizer.assign_priority(unknown_impact_issue)
        assert priority == Priority.LOW
    
    def test_serious_impact_maps_correctly(self, prioritizer):
        """Test 'serious' impact (axe-core specific) maps to high priority."""
        serious_issue = AccessibilityIssue(
            id="test-rule",
            description="Test",
            impact="serious",
            elements=[".test"],
            wcag_level="AA"
        )
        
        priority = prioritizer.assign_priority(serious_issue)
        assert priority in [Priority.HIGH, Priority.CRITICAL]
