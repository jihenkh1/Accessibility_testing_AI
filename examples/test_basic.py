#!/usr/bin/env python3
"""
Basic test of the AI accessibility analyzer
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.accessibility_ai import AccessibilityAnalyzer

def test_basic_analysis():
    """Test the analyzer with sample data"""
    
    # Sample axe-core report
    sample_report = {
        "violations": [
            {
                "id": "button-name",
                "description": "Buttons must have discernible text",
                "impact": "critical",
                "nodes": [
                    {"target": [".search-btn"]},
                    {"target": [".submit-btn"]},
                    {"target": [".icon-btn"]}
                ],
                "html": "<button class='search-btn'><span class='icon'></span></button>",
                "tags": ["wcag2a", "wcag412"],
                "helpUrl": "https://dequeuniversity.com/rules/axe/4.7/button-name"
            },
            {
                "id": "image-alt", 
                "description": "Images must have alternate text",
                "impact": "serious", 
                "nodes": [
                    {"target": ["img.product-image"]},
                    {"target": ["img.logo"]}
                ],
                "html": "<img src='logo.png'>",
                "tags": ["wcag2a", "wcag111"],
                "helpUrl": "https://dequeuniversity.com/rules/axe/4.7/image-alt"
            }
        ]
    }
    
    # Analyze
    analyzer = AccessibilityAnalyzer()
    result = analyzer.analyze_report(sample_report, "https://example.com")
    
    # Display results
    print("🤖 AI ACCESSIBILITY ANALYSIS RESULTS")
    print("=" * 50)
    print(f"URL: {result.url}")
    print(f"Summary: {result.summary}")
    print(f"Total issues: {result.total_issues}")
    print(f"Critical issues: {result.critical_issues}")
    print(f"Estimated fix time: {result.estimated_total_time} minutes")
    
    print("\n🚨 PRIORITY FIXES:")
    for i, insight in enumerate(result.priority_fixes, 1):
        print(f"\n{i}. {insight.issue.description}")
        print(f"   Priority: {insight.priority.value.upper()}")
        print(f"   Impact: {insight.user_impact}")
        print(f"   Risk: {insight.business_risk}")
        
        if insight.fix_suggestions:
            fix = insight.fix_suggestions[0]
            print(f"   Fix: {fix.title}")
            if fix.code_before and fix.code_after:
                print(f"   Code:")
                print(f"     Before: {fix.code_before}")
                print(f"     After:  {fix.code_after}")

if __name__ == "__main__":
    test_basic_analysis()