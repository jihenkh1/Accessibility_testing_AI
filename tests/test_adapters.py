"""
Unit tests for report adapters (axe-core and Pa11y).

Tests parsing and normalization of different accessibility report formats.
"""
import pytest
from src.accessibility_ai.adapters.axe_adapter import parse_axe_report
from src.accessibility_ai.adapters.pa11y_adapter import parse_pa11y_report
from src.accessibility_ai.models import AccessibilityIssue


class TestAxeAdapter:
    """Test suite for axe-core report adapter."""
    
    @pytest.fixture
    def axe_violation(self):
        """Sample axe violation."""
        return {
            "id": "image-alt",
            "impact": "critical",
            "description": "Images must have alternate text",
            "help": "Images must have alternate text",
            "helpUrl": "https://dequeuniversity.com/rules/axe/4.0/image-alt",
            "nodes": [
                {
                    "target": ["img.logo"],
                    "html": "<img class='logo' src='logo.png'>",
                    "impact": "critical",
                    "failureSummary": "Fix the following: Element does not have an alt attribute"
                },
                {
                    "target": ["#banner > img"],
                    "html": "<img src='banner.jpg'>",
                    "impact": "critical",
                    "failureSummary": "Fix the following: Element does not have an alt attribute"
                }
            ]
        }
    
    @pytest.fixture
    def axe_report_with_violations(self, axe_violation):
        """Sample axe report with violations."""
        return {
            "violations": [axe_violation],
            "passes": [],
            "incomplete": [],
            "inapplicable": []
        }
    
    def test_parse_axe_report_success(self, axe_report_with_violations):
        """Test successfully parsing axe report."""
        issues = parse_axe_report(axe_report_with_violations)
        
        # Should create 1 issue per violation, with all node selectors in elements array
        assert len(issues) == 1
        assert isinstance(issues[0], AccessibilityIssue)
        assert issues[0].id == "image-alt"
        assert issues[0].impact == "critical"
        assert len(issues[0].elements) == 2  # Both node selectors
        assert "img.logo" in issues[0].elements
        assert "#banner > img" in issues[0].elements
    
    def test_parse_empty_axe_report(self):
        """Test parsing empty axe report."""
        empty_report = {
            "violations": [],
            "passes": [],
            "incomplete": [],
            "inapplicable": []
        }
        
        issues = parse_axe_report(empty_report)
        assert len(issues) == 0
    
    def test_parse_axe_report_no_violations_key(self):
        """Test parsing axe report without violations key."""
        malformed_report = {"passes": [], "incomplete": []}
        
        issues = parse_axe_report(malformed_report)
        assert len(issues) == 0
    
    def test_axe_impact_mapping(self):
        """Test axe impact levels are correctly parsed."""
        impacts = ["critical", "serious", "moderate", "minor"]
        
        for impact in impacts:
            report = {
                "violations": [{
                    "id": "test-rule",
                    "impact": impact,
                    "description": "Test",
                    "help": "Test",
                    "nodes": [{
                        "target": [".test"],
                        "html": "<div class='test'></div>",
                        "impact": impact
                    }]
                }],
                "passes": [],
                "incomplete": [],
                "inapplicable": []
            }
            
            issues = parse_axe_report(report)
            assert len(issues) == 1
            assert issues[0].impact == impact
    
    def test_axe_selector_extraction(self, axe_violation):
        """Test selector (target) extraction from axe nodes."""
        report = {"violations": [axe_violation]}
        issues = parse_axe_report(report)
        
        # Should have 1 issue with 2 selectors in elements array
        assert len(issues) == 1
        assert len(issues[0].elements) == 2
        assert "img.logo" in issues[0].elements
        assert "#banner > img" in issues[0].elements


class TestPa11yAdapter:
    """Test suite for Pa11y report adapter."""
    
    @pytest.fixture
    def pa11y_error(self):
        """Sample Pa11y error."""
        return {
            "code": "WCAG2AA.Principle1.Guideline1_1.1_1_1.H37",
            "type": "error",
            "message": "Img element missing an alt attribute",
            "context": "<img src='logo.png'>",
            "selector": "html > body > div > img:nth-child(1)"
        }
    
    @pytest.fixture
    def pa11y_report_with_issues(self, pa11y_error):
        """Sample Pa11y report with issues."""
        return {
            "issues": [pa11y_error]
        }
    
    def test_parse_pa11y_report_success(self, pa11y_report_with_issues):
        """Test successfully parsing Pa11y report."""
        issues = parse_pa11y_report(pa11y_report_with_issues)
        
        assert len(issues) == 1
        assert isinstance(issues[0], AccessibilityIssue)
        assert issues[0].id == "WCAG2AA.Principle1.Guideline1_1.1_1_1.H37"
        assert issues[0].description == "Img element missing an alt attribute"
    
    def test_parse_empty_pa11y_report(self):
        """Test parsing empty Pa11y report."""
        empty_report = {"issues": []}
        
        issues = parse_pa11y_report(empty_report)
        assert len(issues) == 0
    
    def test_pa11y_type_to_impact_mapping(self):
        """Test Pa11y type to impact mapping."""
        type_to_impact = {
            "error": "critical",
            "warning": "moderate",
            "notice": "minor"
        }
        
        for pa11y_type, expected_impact in type_to_impact.items():
            report = {
                "issues": [{
                    "code": "TEST.Rule",
                    "type": pa11y_type,
                    "message": "Test message",
                    "context": "<div></div>",
                    "selector": "div"
                }]
            }
            
            issues = parse_pa11y_report(report)
            assert len(issues) == 1
            assert issues[0].impact == expected_impact
    
    def test_pa11y_selector_extraction(self, pa11y_error):
        """Test selector extraction from Pa11y issues."""
        report = {"issues": [pa11y_error]}
        issues = parse_pa11y_report(report)
        
        assert issues[0].elements[0] == "html > body > div > img:nth-child(1)"
    
    def test_pa11y_missing_fields(self):
        """Test handling of Pa11y issues with missing fields."""
        minimal_issue = {
            "code": "TEST.Rule",
            "message": "Test message"
            # Missing: type, context, selector
        }
        
        report = {"issues": [minimal_issue]}
        issues = parse_pa11y_report(report)
        
        assert len(issues) == 1
        assert issues[0].id == "TEST.Rule"
        # Should have defaults for missing fields
        assert issues[0].impact in ["critical", "moderate", "minor"]
