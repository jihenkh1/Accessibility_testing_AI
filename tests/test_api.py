"""
Integration tests for FastAPI endpoints.

Tests API functionality including:
- Scan submission and analysis
- Issue retrieval
- Error handling
- Input validation
"""
import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import sys

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.main import app
from backend.exceptions import ValidationError


@pytest.fixture
def client():
    """Create test client for FastAPI app."""
    return TestClient(app)


@pytest.fixture
def sample_axe_report():
    """Sample axe-core report for testing."""
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
            }
        ],
        "passes": [],
        "incomplete": [],
        "inapplicable": []
    }


class TestHealthEndpoint:
    """Test health check endpoint."""
    
    def test_health_check_returns_200(self, client):
        """Test health endpoint returns 200 OK."""
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestScanEndpoints:
    """Test scan-related endpoints."""
    
    def test_post_scan_success(self, client, sample_axe_report):
        """Test successful scan submission."""
        request_data = {
            "report": sample_axe_report,
            "framework": "html",
            "use_ai": False,  # Disable AI for faster tests
            "url": "https://example.com",
            "project_name": "Test Project"
        }
        
        response = client.post("/api/scans", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "scan_id" in data
        assert "summary" in data
        assert "issues" in data
        assert data["summary"]["total_issues"] > 0
    
    def test_post_scan_invalid_framework(self, client, sample_axe_report):
        """Test scan submission with invalid framework."""
        request_data = {
            "report": sample_axe_report,
            "framework": "invalid-framework",
            "use_ai": False,
            "url": "https://example.com"
        }
        
        response = client.post("/api/scans", json=request_data)
        assert response.status_code == 422  # Validation error
    
    def test_post_scan_empty_report(self, client):
        """Test scan submission with empty report."""
        request_data = {
            "report": {},
            "framework": "html",
            "use_ai": False,
            "url": "https://example.com"
        }
        
        response = client.post("/api/scans", json=request_data)
        assert response.status_code == 422  # Validation error
    
    def test_post_scan_max_ai_issues_too_large(self, client, sample_axe_report):
        """Test scan submission with max_ai_issues exceeding limit."""
        request_data = {
            "report": sample_axe_report,
            "framework": "html",
            "use_ai": True,
            "max_ai_issues": 2000,  # Exceeds 1000 limit
            "url": "https://example.com"
        }
        
        response = client.post("/api/scans", json=request_data)
        assert response.status_code == 422  # Validation error
    
    def test_post_scan_negative_max_ai_issues(self, client, sample_axe_report):
        """Test scan submission with negative max_ai_issues."""
        request_data = {
            "report": sample_axe_report,
            "framework": "html",
            "use_ai": True,
            "max_ai_issues": -5,
            "url": "https://example.com"
        }
        
        response = client.post("/api/scans", json=request_data)
        assert response.status_code == 422  # Validation error
    
    def test_list_scans(self, client):
        """Test listing scans."""
        response = client.get("/api/scans")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_get_scan_by_id(self, client, sample_axe_report):
        """Test retrieving specific scan by ID."""
        # First create a scan
        create_response = client.post("/api/scans", json={
            "report": sample_axe_report,
            "framework": "html",
            "use_ai": False,
            "url": "https://example.com"
        })
        
        scan_id = create_response.json()["scan_id"]
        
        # Then retrieve it
        response = client.get(f"/api/scans/{scan_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == scan_id
        assert "total_issues" in data
    
    def test_get_scan_not_found(self, client):
        """Test retrieving non-existent scan returns 404."""
        response = client.get("/api/scans/99999")
        assert response.status_code == 404


class TestIssueEndpoints:
    """Test issue-related endpoints."""
    
    def test_get_scan_issues(self, client, sample_axe_report):
        """Test retrieving issues for a scan."""
        # Create scan first
        create_response = client.post("/api/scans", json={
            "report": sample_axe_report,
            "framework": "html",
            "use_ai": False,
            "url": "https://example.com"
        })
        
        scan_id = create_response.json()["scan_id"]
        
        # Get issues
        response = client.get(f"/api/scans/{scan_id}/issues")
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) > 0
    
    def test_get_scan_issues_with_filter(self, client, sample_axe_report):
        """Test filtering issues by severity."""
        # Create scan first
        create_response = client.post("/api/scans", json={
            "report": sample_axe_report,
            "framework": "html",
            "use_ai": False,
            "url": "https://example.com"
        })
        
        scan_id = create_response.json()["scan_id"]
        
        # Get only critical issues
        response = client.get(
            f"/api/scans/{scan_id}/issues",
            params={"severity": "critical"}
        )
        assert response.status_code == 200
        
        data = response.json()
        # Should only return critical issues if any exist
        if data["items"]:
            assert all(
                item["priority"] == "critical" 
                for item in data["items"]
            )
    
    def test_update_issue_status(self, client, sample_axe_report):
        """Test updating issue status."""
        # Create scan and get an issue
        create_response = client.post("/api/scans", json={
            "report": sample_axe_report,
            "framework": "html",
            "use_ai": False,
            "url": "https://example.com"
        })
        
        scan_id = create_response.json()["scan_id"]
        issues_response = client.get(f"/api/scans/{scan_id}/issues")
        issue_id = issues_response.json()["items"][0]["id"]
        
        # Update status
        response = client.patch(
            f"/api/issues/{issue_id}/status",
            params={"status": "in_progress"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["status"] == "in_progress"
    
    def test_update_issue_invalid_status(self, client, sample_axe_report):
        """Test updating issue with invalid status."""
        # Create scan and get an issue
        create_response = client.post("/api/scans", json={
            "report": sample_axe_report,
            "framework": "html",
            "use_ai": False,
            "url": "https://example.com"
        })
        
        scan_id = create_response.json()["scan_id"]
        issues_response = client.get(f"/api/scans/{scan_id}/issues")
        issue_id = issues_response.json()["items"][0]["id"]
        
        # Update with invalid status
        response = client.patch(
            f"/api/issues/{issue_id}/status",
            params={"status": "invalid_status"}
        )
        assert response.status_code == 400  # Bad request


class TestAIStatsEndpoints:
    """Test AI statistics endpoints."""
    
    def test_get_ai_usage_stats(self, client):
        """Test retrieving AI usage statistics."""
        response = client.get("/api/ai/usage-stats")
        assert response.status_code == 200
        
        data = response.json()
        assert "stats" in data or "available" in data
    
    def test_get_ai_cache_stats(self, client):
        """Test retrieving AI cache statistics."""
        response = client.get("/api/ai/cache-stats")
        assert response.status_code == 200
        
        data = response.json()
        assert "stats" in data or "available" in data
