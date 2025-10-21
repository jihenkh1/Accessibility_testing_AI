"""
Python SDK for AI Accessibility Dashboard
Install in your testing project: pip install requests

Usage:
    from a11y_dashboard_client import A11yDashboardClient
    
    client = A11yDashboardClient(
        api_url="https://dashboard.company.com",
        api_key="your-api-key"
    )
    
    # Send report
    result = client.send_report(
        report_path="./reports/axe-results.json",
        project_name="main-website",
        branch="main"
    )
    
    print(f"View results: {result['dashboard_url']}")
"""

import json
import requests
from typing import Dict, Any, Optional
from pathlib import Path


class A11yDashboardClient:
    """Client for sending accessibility reports to AI Dashboard"""
    
    def __init__(
        self, 
        api_url: str = "http://localhost:8000",
        api_key: Optional[str] = None,
        timeout: int = 30
    ):
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()
        
        if api_key:
            self.session.headers['Authorization'] = f'Bearer {api_key}'
    
    def send_report(
        self,
        report_path: str,
        project_name: str = "unknown",
        framework: str = "axe",
        use_ai: bool = True,
        max_ai_issues: int = 50,
        fail_on_critical: bool = False
    ) -> Dict[str, Any]:
        """
        Send an accessibility report to the dashboard for analysis
        
        Args:
            report_path: Path to the JSON report file
            project_name: Name of the project/website being tested
            framework: Testing framework used ('axe' or 'pa11y')
            use_ai: Whether to use AI enhancement
            max_ai_issues: Maximum number of issues to enhance with AI
            fail_on_critical: Raise exception if critical issues found
            
        Returns:
            Dict with scan_id, summary, and dashboard_url
            
        Raises:
            Exception: If fail_on_critical=True and critical issues found
        """
        # Load report
        report_file = Path(report_path)
        if not report_file.exists():
            raise FileNotFoundError(f"Report not found: {report_path}")
        
        with open(report_file, 'r', encoding='utf-8') as f:
            report_data = json.load(f)
        
        # Send to API
        payload = {
            "report": report_data,
            "url": project_name,
            "framework": framework,
            "use_ai": use_ai,
            "max_ai_issues": max_ai_issues
        }
        
        response = self.session.post(
            f"{self.api_url}/api/scans",
            json=payload,
            timeout=self.timeout
        )
        response.raise_for_status()
        
        result = response.json()
        scan_id = result.get('scan_id')
        summary = result.get('summary', {})
        
        # Add dashboard URL
        result['dashboard_url'] = f"{self.api_url}/scan/{scan_id}"
        
        # Print summary
        print("\n" + "="*50)
        print("📊 Accessibility Analysis Complete")
        print("="*50)
        print(f"Total Issues:     {summary.get('total_issues', 0)}")
        print(f"Critical:         {summary.get('critical_issues', 0)}")
        print(f"High Priority:    {summary.get('high_issues', 0)}")
        print(f"AI Enhanced:      {summary.get('ai_enhanced_issues', 0)}")
        print(f"Est. Fix Time:    {summary.get('estimated_total_time_minutes', 0)} min")
        print(f"\n🌐 Dashboard:     {result['dashboard_url']}")
        print("="*50 + "\n")
        
        # Fail build if requested
        if fail_on_critical and summary.get('critical_issues', 0) > 0:
            raise Exception(
                f"Build failed: {summary['critical_issues']} critical "
                f"accessibility issues found. View: {result['dashboard_url']}"
            )
        
        return result
    
    def scan_url(
        self,
        url: str,
        max_pages: int = 10,
        same_origin_only: bool = True,
        framework: str = "axe",
        use_ai: bool = True,
        max_ai_issues: int = 50
    ) -> Dict[str, Any]:
        """
        Trigger a live URL scan via the dashboard's crawler
        
        Args:
            url: URL to scan
            max_pages: Maximum number of pages to crawl
            same_origin_only: Only crawl pages on same domain
            framework: Testing framework to use
            use_ai: Whether to use AI enhancement
            max_ai_issues: Maximum issues to enhance with AI
            
        Returns:
            Dict with scan results and dashboard URL
        """
        payload = {
            "url": url,
            "max_pages": max_pages,
            "same_origin_only": same_origin_only,
            "framework": framework,
            "use_ai": use_ai,
            "max_ai_issues": max_ai_issues
        }
        
        print(f"🔍 Scanning {url} (max {max_pages} pages)...")
        
        response = self.session.post(
            f"{self.api_url}/api/scans/scan_url",
            json=payload,
            timeout=self.timeout * 3  # Longer timeout for crawling
        )
        response.raise_for_status()
        
        result = response.json()
        scan_id = result.get('scan_id')
        result['dashboard_url'] = f"{self.api_url}/scan/{scan_id}"
        
        print(f"✅ Scan complete: {result['dashboard_url']}")
        return result
    
    def get_scan(self, scan_id: int) -> Dict[str, Any]:
        """Get details of a previous scan"""
        response = self.session.get(
            f"{self.api_url}/api/scans/{scan_id}",
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def list_scans(self, limit: int = 20) -> list[Dict[str, Any]]:
        """List recent scans"""
        response = self.session.get(
            f"{self.api_url}/api/scans",
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()[:limit]


# Convenience function for pytest integration
def pytest_a11y_report(report_path: str, **kwargs):
    """
    Send accessibility report from pytest session
    
    Usage in conftest.py:
        from a11y_dashboard_client import pytest_a11y_report
        
        def pytest_sessionfinish(session):
            pytest_a11y_report('./reports/a11y.json', project_name='myapp')
    """
    import os
    client = A11yDashboardClient(
        api_url=os.getenv('A11Y_DASHBOARD_URL', 'http://localhost:8000'),
        api_key=os.getenv('A11Y_DASHBOARD_KEY')
    )
    return client.send_report(report_path, **kwargs)
