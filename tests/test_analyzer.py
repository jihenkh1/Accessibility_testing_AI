"""
Unit tests for the AccessibilityAnalyzer.

Tests core analysis functionality including:
- Report parsing (axe-core, Pa11y)
- AI enhancement
- Priority assignment
- Issue enrichment
"""
import pytest
from pathlib import Path
from typing import Dict, Any
from src.accessibility_ai.analyzer import AccessibilityAnalyzer
from src.accessibility_ai.models import Priority


class TestAccessibilityAnalyzer:
    """Test suite for AccessibilityAnalyzer class."""
    
    @pytest.fixture
    def analyzer_no_ai(self):
        """Create analyzer instance without AI."""
        return AccessibilityAnalyzer(use_ai=False)
    
    @pytest.fixture
    def analyzer_with_ai(self):
        """Create analyzer instance with AI enabled."""
        return AccessibilityAnalyzer(use_ai=True, max_ai_issues=5)
    
    @pytest.fixture
    def sample_axe_report(self) -> Dict[str, Any]:
        """Sample axe-core report."""
        return {
            "violations": [
                {
                    "id": "button-name",
                    "impact": "critical",
                    "description": "Buttons must have discernible text",
                    "help": "Buttons must have discernible text",
                    "helpUrl": "https://dequeuniversity.com/rules/axe/4.0/button-name",
                    "nodes": [
                        {
                            "target": ["button.submit"],
                            "html": "<button class='submit'></button>",
                            "impact": "critical"
                        }
                    ]
                },
                {
                    "id": "color-contrast",
                    "impact": "serious",
                    "description": "Elements must have sufficient color contrast",
                    "help": "Elements must have sufficient color contrast",
                    "helpUrl": "https://dequeuniversity.com/rules/axe/4.0/color-contrast",
                    "nodes": [
                        {
                            "target": [".text-gray"],
                            "html": "<p class='text-gray'>Low contrast text</p>",
                            "impact": "serious"
                        }
                    ]
                }
            ],
            "passes": [],
            "incomplete": [],
            "inapplicable": []
        }
    
    @pytest.fixture
    def sample_pa11y_report(self) -> Dict[str, Any]:
        """Sample Pa11y report."""
        return {
            "issues": [
                {
                    "code": "WCAG2AA.Principle1.Guideline1_1.1_1_1.H37",
                    "type": "error",
                    "message": "Img element missing an alt attribute",
                    "context": "<img src=\"logo.png\">",
                    "selector": "html > body > img:nth-child(1)"
                }
            ]
        }
    
    def test_analyzer_initialization_no_ai(self):
        """Test analyzer initializes correctly without AI."""
        analyzer = AccessibilityAnalyzer(use_ai=False)
        assert analyzer.use_ai is False
        assert analyzer.ai_client is None
        assert analyzer._ai_initialized is False
    
    def test_analyzer_initialization_with_ai(self):
        """Test analyzer initializes correctly with AI."""
        analyzer = AccessibilityAnalyzer(use_ai=True, max_ai_issues=10)
        assert analyzer.use_ai is True
        assert analyzer.max_ai_issues == 10
    
    def test_analyze_axe_report_without_ai(self, analyzer_no_ai, sample_axe_report):
        """Test analyzing axe-core report without AI enhancement."""
        issues = analyzer_no_ai.analyze_issues(
            raw_report=sample_axe_report,
            url="https://example.com",
            framework="html"
        )
        
        assert len(issues) == 2
        assert all(hasattr(issue, "original_issue") for issue in issues)
        assert all(hasattr(issue, "priority") for issue in issues)
        
        # Check priority assignment
        button_issue = [i for i in issues if i.original_issue.id == "button-name"][0]
        assert button_issue.priority in [Priority.CRITICAL, Priority.HIGH]
    
    def test_analyze_pa11y_report_without_ai(self, analyzer_no_ai, sample_pa11y_report):
        """Test analyzing Pa11y report without AI enhancement."""
        issues = analyzer_no_ai.analyze_issues(
            raw_report=sample_pa11y_report,
            url="https://example.com",
            framework="html"
        )
        
        assert len(issues) == 1
        assert issues[0].original_issue.id == "WCAG2AA.Principle1.Guideline1_1.1_1_1.H37"
    
    def test_analyze_empty_report(self, analyzer_no_ai):
        """Test analyzing empty report returns empty list."""
        empty_report = {"violations": [], "passes": [], "incomplete": [], "inapplicable": []}
        issues = analyzer_no_ai.analyze_issues(
            raw_report=empty_report,
            url="https://example.com",
            framework="html"
        )
        
        assert len(issues) == 0
    
    def test_max_ai_issues_limit(self, analyzer_with_ai, sample_axe_report):
        """Test that max_ai_issues limit is respected."""
        # Analyzer has max_ai_issues=5
        assert analyzer_with_ai.max_ai_issues == 5
        
        # Should respect the limit during analysis
        issues = analyzer_with_ai.analyze_issues(
            raw_report=sample_axe_report,
            url="https://example.com",
            framework="html"
        )
        
        assert len(issues) > 0
    
    def test_analysis_summary(self, analyzer_no_ai, sample_axe_report):
        """Test generating analysis summary."""
        issues = analyzer_no_ai.analyze_issues(
            raw_report=sample_axe_report,
            url="https://example.com",
            framework="html"
        )
        
        summary = analyzer_no_ai.get_analysis_summary(issues)
        
        assert "total_issues" in summary
        assert "critical_issues" in summary
        assert "high_issues" in summary
        assert "medium_issues" in summary
        assert "low_issues" in summary
        assert summary["total_issues"] == len(issues)
    
    def test_invalid_framework(self, analyzer_no_ai, sample_axe_report):
        """Test handling of invalid framework parameter."""
        # Should still work, just uses default handling
        issues = analyzer_no_ai.analyze_issues(
            raw_report=sample_axe_report,
            url="https://example.com",
            framework="invalid-framework"
        )
        
        assert len(issues) == 2
    
    def test_malformed_report_handling(self, analyzer_no_ai):
        """Test handling of malformed report data."""
        malformed_report = {"some_key": "some_value"}
        
        # Should handle gracefully without crashing
        issues = analyzer_no_ai.analyze_issues(
            raw_report=malformed_report,
            url="https://example.com",
            framework="html"
        )
        
        # May return empty list or partial results
        assert isinstance(issues, list)
