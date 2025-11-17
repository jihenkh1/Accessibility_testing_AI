"""
Custom exceptions for the AI Accessibility Analyzer.

Provides specific exception types for better error handling and debugging.
"""
from typing import Any, Dict, Optional


class AccessibilityAnalyzerError(Exception):
    """Base exception for all application errors."""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details
        }


class ValidationError(AccessibilityAnalyzerError):
    """Raised when input validation fails."""
    pass


class ReportParsingError(AccessibilityAnalyzerError):
    """Raised when accessibility report parsing fails."""
    pass


class AIServiceError(AccessibilityAnalyzerError):
    """Raised when AI service encounters an error."""
    pass


class DatabaseError(AccessibilityAnalyzerError):
    """Raised when database operations fail."""
    pass


class FileProcessingError(AccessibilityAnalyzerError):
    """Raised when file upload/processing fails."""
    pass


class ConfigurationError(AccessibilityAnalyzerError):
    """Raised when application configuration is invalid."""
    pass


class RateLimitError(AccessibilityAnalyzerError):
    """Raised when rate limits are exceeded."""
    pass
