"""
AI Accessibility Suite
=====================

AI-powered accessibility analysis that prioritizes fixes and saves developer time.
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .analyzer import AccessibilityAnalyzer
from .models import AccessibilityIssue, AIAnalysis, AnalysisResult, Priority, EnhancedIssue, FixSuggestion

__all__ = [
    "AccessibilityAnalyzer",
    "AccessibilityIssue", 
    "AIAnalysis",
    "AnalysisResult",
    "Priority",
    "EnhancedIssue",
    "FixSuggestion",
]