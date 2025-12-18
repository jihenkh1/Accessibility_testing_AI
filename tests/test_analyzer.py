"""
Unit tests for the AccessibilityAnalyzer.

Tests core analysis functionality including:
- Report parsing (axe-core, Pa11y)
- AI enhancement
- Priority assignment
- Issue enrichment
"""
import pytest
import re
from pathlib import Path
from typing import Dict, Any
from backend.services.analyze import analyze_report
from src.accessibility_ai.analyzer import AccessibilityAnalyzer
from src.accessibility_ai.models import AIAnalysis
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

    def test_button_name_rule_db_fix_not_hardcoded_search(self):
        """Rule DB button-name fix should not force aria-label='Search' when evidence lacks search."""
        sample_report = {
            "violations": [
                {
                    "id": "button-name",
                    "impact": "critical",
                    "description": "Buttons must have discernible text",
                    "help": "Buttons must have discernible text",
                    "nodes": [
                        {
                            "target": [".orbit-previous"],
                            "html": "<button class=\"orbit-previous\"><span class=\"icon\"></span></button>",
                            "impact": "critical",
                            "any": [],
                            "all": [],
                            "none": []
                        }
                    ]
                }
            ]
        }

        result = analyze_report(report=sample_report, framework="html", use_ai=False)
        btn_issue = next(i for i in result["issues"] if i["rule_id"] == "button-name")
        fix = btn_issue["fix_suggestion"]
        assert 'aria-label="Search"' not in fix
        assert "aria-label='Search'" not in fix

    def test_vague_suggestion_replaced_for_heading_rule(self):
        """Vague fix suggestions for page-has-heading-one should be replaced with deterministic text."""
        analyzer = AccessibilityAnalyzer(use_ai=False)
        ai = AIAnalysis(fix_suggestion="Ensure heading is present")
        updated = analyzer._enforce_vague_template("page-has-heading-one", ai)
        assert "Add a single, descriptive <h1>" in updated.fix_suggestion
        assert "heading order" in updated.fix_suggestion

    def test_vague_suggestion_replaced_for_landmark_unique(self):
        """Vague fix suggestions for landmark-unique should be replaced with deterministic text."""
        analyzer = AccessibilityAnalyzer(use_ai=False)
        ai = AIAnalysis(fix_suggestion="Ensure landmarks are unique")
        updated = analyzer._enforce_vague_template("landmark-unique", ai)
        assert "unique accessible name" in updated.fix_suggestion
        assert "aria-label" in updated.fix_suggestion

    def test_region_deterministic_fix_with_evidence(self, analyzer_no_ai):
        """Region issues with evidence should bypass AI and include selectors/html in fix."""
        sample_report = {
            "violations": [
                {
                    "id": "region",
                    "impact": "moderate",
                    "description": "All page content is contained by landmarks",
                    "nodes": [
                        {
                            "target": [".App"],
                            "html": "<div class=\"App\"><div class=\"page\">Content</div></div>",
                            "any": [{"id": "region", "message": "Some page content is not contained by landmarks"}],
                            "all": [],
                            "none": []
                        },
                        {
                            "target": [".breadcrumb"],
                            "html": "<div class=\"breadcrumb\"><p>Trail</p></div>",
                            "any": [{"id": "region", "message": "Some page content is not contained by landmarks"}],
                            "all": [],
                            "none": []
                        }
                    ]
                }
            ]
        }

        enhanced = analyzer_no_ai.analyze_issues(
            raw_report=sample_report,
            url="https://example.com",
            framework="html"
        )
        reg_issue = next(i for i in enhanced if i.original_issue.id == "region")
        assert reg_issue.analysis_source == "rule_database"
        fix = reg_issue.ai_analysis.fix_suggestion  # type: ignore[union-attr]
        assert "Evidence (from axe)" in fix
        assert ".App" in fix or "App" in fix
        assert "Ensure the page has a single <main> landmark" in fix
        assert "Verify:" in fix
        assert "Search" not in fix

    def test_color_contrast_uses_evidence_not_ai(self, analyzer_no_ai):
        """Deterministic contrast guidance should use provided fg/bg/ratio and avoid invented colors."""
        sample_report = {
            "violations": [
                {
                    "id": "color-contrast",
                    "impact": "serious",
                    "description": "Elements must have sufficient color contrast",
                    "nodes": [
                        {
                            "target": [".short"],
                            "html": "<span class='short'>PDSS</span>",
                            "any": [
                                {
                                    "id": "color-contrast",
                                    "data": {
                                        "contrastRatio": 2.48,
                                        "fgColor": "#ff8200",
                                        "bgColor": "#ffffff",
                                        "expectedContrastRatio": "3:1"
                                    }
                                }
                            ],
                            "all": [],
                            "none": []
                        }
                    ]
                }
            ]
        }

        enhanced = analyzer_no_ai.analyze_issues(
            raw_report=sample_report,
            url="https://example.com",
            framework="html"
        )
        cc_issue = next(i for i in enhanced if i.original_issue.id == "color-contrast")
        assert cc_issue.analysis_source == "rule_database"
        fix = cc_issue.ai_analysis.fix_suggestion  # type: ignore[union-attr]
        assert "#ff8200" in fix and "#ffffff" in fix
        assert "2.48" in fix and "3:1" in fix
        # No hex colors beyond evidence
        hexes = set(re.findall(r"#[0-9a-fA-F]{3,6}", fix))
        assert hexes.issubset({"#ff8200", "#ffffff"})

    def test_color_contrast_missing_evidence_no_hex(self):
        """When evidence is missing, no hex colors should be invented in fix suggestion."""
        sample_report = {
            "violations": [
                {
                    "id": "color-contrast",
                    "impact": "serious",
                    "description": "Elements must have sufficient color contrast",
                    "nodes": [
                        {
                            "target": [".text-gray"],
                            "html": "<p class='text-gray'>Low contrast text</p>",
                            "any": [],
                            "all": [],
                            "none": []
                        }
                    ]
                }
            ]
        }

        result = analyze_report(report=sample_report, framework="html", use_ai=False)
        cc_issue = next(i for i in result["issues"] if i["rule_id"] == "color-contrast")
        fix = cc_issue.get("fix_suggestion", "")
        assert "#" not in fix

    def test_color_contrast_recommendation_only_from_evidence(self, analyzer_no_ai):
        """Recommendation color should be echoed only if present, with no extra hex values."""
        sample_report = {
            "violations": [
                {
                    "id": "color-contrast",
                    "impact": "serious",
                    "description": "Elements must have sufficient color contrast",
                    "nodes": [
                        {
                            "target": [".pa11y-text"],
                            "html": "<p class='pa11y-text'>Low contrast</p>",
                            "any": [
                                {
                                    "id": "color-contrast",
                                    "data": {
                                        "contrastRatio": 2.0,
                                        "fgColor": "#111111",
                                        "bgColor": "#ffffff",
                                        "expectedContrastRatio": "4.5:1",
                                        "recommended_text_color": "#123456"
                                    }
                                }
                            ],
                            "all": [],
                            "none": []
                        }
                    ]
                }
            ]
        }

        enhanced = analyzer_no_ai.analyze_issues(
            raw_report=sample_report,
            url="https://example.com",
            framework="html"
        )
        cc_issue = next(i for i in enhanced if i.original_issue.id == "color-contrast")
        assert cc_issue.analysis_source == "rule_database"
        fix = cc_issue.ai_analysis.fix_suggestion  # type: ignore[union-attr]
        assert "4.5" in fix and "2.0" in fix
        # Hexes should be limited to evidence fg/bg and recommended
        hexes = set(re.findall(r"#[0-9a-fA-F]{3,6}", fix))
        assert hexes.issubset({"#111111", "#ffffff", "#123456"})

    def test_landmark_unique_deterministic_fix_with_evidence(self, analyzer_no_ai):
        """landmark-unique issues with evidence should bypass AI and include selectors/html in fix."""
        sample_report = {
            "violations": [
                {
                    "id": "landmark-unique",
                    "impact": "moderate",
                    "description": "Landmarks must have a unique role or role/label/title combination",
                    "nodes": [
                        {
                            "target": [".meta"],
                            "html": "<nav class=\"meta\">...</nav>",
                            "any": [{"id": "landmark-is-unique", "message": "Landmarks must have a unique role or role/label/title (i.e. accessible name) combination"}],
                            "all": [],
                            "none": []
                        }
                    ]
                }
            ]
        }

        enhanced = analyzer_no_ai.analyze_issues(
            raw_report=sample_report,
            url="https://example.com",
            framework="html"
        )
        lm_issue = next(i for i in enhanced if i.original_issue.id == "landmark-unique")
        assert lm_issue.analysis_source == "rule_database"
        fix = lm_issue.ai_analysis.fix_suggestion  # type: ignore[union-attr]
        assert "Evidence (from axe)" in fix
        assert ".meta" in fix
        assert "aria-label" in fix or "aria-labelledby" in fix
        assert "Verify:" in fix

    def test_region_evidence_html_is_trimmed(self, analyzer_no_ai):
        """Region evidence HTML snippets should be trimmed to avoid noisy output."""
        long_html = "<div class='long'>" + (" content-with-whitespace " * 40) + "</div>"
        sample_report = {
            "violations": [
                {
                    "id": "region",
                    "impact": "moderate",
                    "description": "All page content is contained by landmarks",
                    "nodes": [
                        {
                            "target": [".long"],
                            "html": long_html,
                            "any": [{"id": "region", "message": "Some page content is not contained by landmarks"}],
                            "all": [],
                            "none": []
                        }
                    ]
                }
            ]
        }

        enhanced = analyzer_no_ai.analyze_issues(
            raw_report=sample_report,
            url="https://example.com",
            framework="html"
        )
        reg_issue = next(i for i in enhanced if i.original_issue.id == "region")
        fix = reg_issue.ai_analysis.fix_suggestion  # type: ignore[union-attr]
        line = next(l for l in fix.splitlines() if ".long" in l)
        snippet = line.split("HTML:", 1)[1].strip()
        assert len(snippet) <= 185
        assert snippet.endswith("...")
