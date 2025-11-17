from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, File, UploadFile, Form
from fastapi.responses import StreamingResponse, FileResponse

from backend.schemas import AnalyzeRequest, AnalyzeResponse, ScanSummary, IssuesPage, IssueOut
from backend.services.analyze import analyze_report
from backend.services import db as dbsvc


router = APIRouter()


DB_PATH = Path("data/a11y_runs.sqlite")


@router.get("/health")
def health() -> Dict[str, Any]:
    return {"status": "healthy"}


@router.get("/ai/usage-stats")
def get_ai_usage_stats() -> Dict[str, Any]:
    """Get current AI usage statistics (token counting, costs, success rate)"""
    try:
        # Create analyzer to access AI client
        from src.accessibility_ai.analyzer import AccessibilityAnalyzer
        analyzer = AccessibilityAnalyzer(use_ai=True)
        
        # Initialize AI client if not already done
        analyzer._ensure_ai_client()
        
        # Get usage stats from AI client
        if analyzer.ai_client and hasattr(analyzer.ai_client, 'get_usage_stats'):
            stats = analyzer.ai_client.get_usage_stats()
            return {
                "available": True,
                "stats": stats
            }
        else:
            return {
                "available": False,
                "error": "AI client not available or stats not supported"
            }
    except Exception as e:
        return {
            "available": False,
            "error": str(e)
        }


@router.get("/ai/cache-stats")
def get_ai_cache_stats() -> Dict[str, Any]:
    """Get AI cache statistics (entries, expiration, disk usage)"""
    try:
        from src.accessibility_ai.analyzer import AccessibilityAnalyzer
        analyzer = AccessibilityAnalyzer(use_ai=True, enable_persistent_cache=True)
        
        if analyzer._persistent_cache and hasattr(analyzer._persistent_cache, 'get_stats'):
            stats = analyzer._persistent_cache.get_stats()
            return {
                "available": True,
                "stats": stats
            }
        else:
            return {
                "available": False,
                "error": "Cache not available"
            }
    except Exception as e:
        return {
            "available": False,
            "error": str(e)
        }


@router.post("/ai/cache/cleanup")
def cleanup_ai_cache() -> Dict[str, Any]:
    """Manually trigger cache cleanup (remove expired entries)"""
    try:
        from src.accessibility_ai.analyzer import AccessibilityAnalyzer
        analyzer = AccessibilityAnalyzer(use_ai=True, enable_persistent_cache=True)
        
        if analyzer._persistent_cache and hasattr(analyzer._persistent_cache, 'cleanup_expired'):
            deleted = analyzer._persistent_cache.cleanup_expired()
            return {
                "success": True,
                "deleted": deleted,
                "message": f"Removed {deleted} expired cache entries"
            }
        else:
            return {
                "success": False,
                "error": "Cache not available"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/ai/usage-stats/reset")
def reset_ai_usage_stats() -> Dict[str, Any]:
    """Reset AI usage statistics"""
    try:
        from src.accessibility_ai.analyzer import AccessibilityAnalyzer
        analyzer = AccessibilityAnalyzer(use_ai=True)
        
        # Initialize AI client if not already done
        analyzer._ensure_ai_client()
        
        if analyzer.ai_client and hasattr(analyzer.ai_client, 'reset_usage_stats'):
            analyzer.ai_client.reset_usage_stats()
            return {
                "success": True,
                "message": "Usage statistics reset successfully"
            }
        else:
            return {
                "success": False,
                "error": "AI client not available"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/scans", response_model=AnalyzeResponse)
def post_scan(req: AnalyzeRequest) -> AnalyzeResponse:
    # Analyze
    result = analyze_report(
        report=req.report,
        framework=req.framework,
        use_ai=req.use_ai,
        max_ai_issues=req.max_ai_issues,
        url=req.url or "api_request",
    )
    summary = result["summary"]
    issues = result["issues"]
    # Persist minimal summary
    ts_iso = datetime.now(timezone.utc).isoformat()
    try:
        scan_id = dbsvc.insert_run_returning_id(
            DB_PATH, 
            summary, 
            req.url or "api_request", 
            req.framework, 
            ts_iso,
            project_name=req.project_name or "Default Project"
        )
        if scan_id:
            dbsvc.insert_run_issues(DB_PATH, scan_id, issues)
    except Exception:
        scan_id = None
    return AnalyzeResponse(scan_id=scan_id, summary=summary, issues=issues)


@router.put("/scans/{scan_id}/analyze", response_model=AnalyzeResponse)
def analyze_existing_scan(scan_id: int, req: AnalyzeRequest) -> AnalyzeResponse:
    """Analyze an existing pending scan and update it with results"""
    # Analyze
    result = analyze_report(
        report=req.report,
        framework=req.framework,
        use_ai=req.use_ai,
        max_ai_issues=req.max_ai_issues,
        url=req.url or "api_request",
    )
    summary = result["summary"]
    issues = result["issues"]
    
    # Update the existing scan with analysis results
    try:
        # Update the scan summary with analysis results
        dbsvc.update_run_summary(DB_PATH, scan_id, summary)
        # Clear old issues and insert new ones
        dbsvc.delete_run_issues(DB_PATH, scan_id)
        dbsvc.insert_run_issues(DB_PATH, scan_id, issues)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update scan: {str(e)}")
    
    return AnalyzeResponse(scan_id=scan_id, summary=summary, issues=issues)


@router.post("/scans/upload-raw")
async def upload_raw_scan(
    report_json: str = Form(...),
    scenario_name: str = Form(...),
    pdf_report: Optional[UploadFile] = File(None),
    html_report: Optional[UploadFile] = File(None),
) -> Dict[str, Any]:
    """
    Upload raw accessibility report with optional PDF/HTML attachments.
    The report will be stored without immediate analysis - users can analyze later from UI.
    """
    try:
        # Parse JSON report
        report_data = json.loads(report_json)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=422, detail=f"Invalid JSON: {str(e)}")
    
    # Create reports directory
    reports_dir = Path("data/uploaded_reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique ID for this upload
    ts_iso = datetime.now(timezone.utc).isoformat()
    upload_id = f"{scenario_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Save PDF if provided
    pdf_path_str = None
    if pdf_report and pdf_report.filename:
        pdf_path = reports_dir / f"{upload_id}.pdf"
        with open(pdf_path, "wb") as f:
            content = await pdf_report.read()
            f.write(content)
        # Store relative path from project root
        pdf_path_str = str(pdf_path)
    
    # Save HTML if provided
    html_path_str = None
    if html_report and html_report.filename:
        html_path = reports_dir / f"{upload_id}.html"
        with open(html_path, "wb") as f:
            content = await html_report.read()
            f.write(content)
        # Store relative path from project root
        html_path_str = str(html_path)
    
    # Store raw report without analysis (summary will be minimal)
    summary = {
        "total_issues": 0,
        "critical_issues": 0,
        "high_issues": 0,
        "medium_issues": 0,
        "low_issues": 0,
        "estimated_total_time_minutes": 0,
        "ai_enhanced_issues": 0,
    }
    
    # Save to database with raw JSON and file paths
    try:
        scan_id = dbsvc.insert_run_returning_id(
            DB_PATH,
            summary,
            scenario_name,
            "html",  # default framework
            ts_iso,
            raw_report_json=report_json,
            pdf_report_path=pdf_path_str,
            html_report_path=html_path_str,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    return {
        "success": True,
        "scan_id": scan_id,
        "message": "Report uploaded successfully. Analyze it from the dashboard.",
        "pdf_uploaded": pdf_path_str is not None,
        "html_uploaded": html_path_str is not None,
    }


@router.post("/scans/upload-docs")
async def upload_documentation_reports(
    scenario_name: str = Form(...),
    pdf_report: Optional[UploadFile] = File(None),
    html_report: Optional[UploadFile] = File(None),
) -> Dict[str, Any]:
    """
    Upload ONLY PDF/HTML documentation reports (test scenario execution reports).
    No JSON accessibility data - these are just documentation for developers to view.
    """
    if not pdf_report and not html_report:
        raise HTTPException(status_code=422, detail="At least one report file (PDF or HTML) is required")
    
    # Create reports directory
    reports_dir = Path("data/uploaded_reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique ID for this upload
    ts_iso = datetime.now(timezone.utc).isoformat()
    upload_id = f"{scenario_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Save PDF if provided
    pdf_path_str = None
    if pdf_report and pdf_report.filename:
        pdf_path = reports_dir / f"{upload_id}.pdf"
        with open(pdf_path, "wb") as f:
            content = await pdf_report.read()
            f.write(content)
        pdf_path_str = str(pdf_path)
    
    # Save HTML if provided
    html_path_str = None
    if html_report and html_report.filename:
        html_path = reports_dir / f"{upload_id}.html"
        with open(html_path, "wb") as f:
            content = await html_report.read()
            f.write(content)
        html_path_str = str(html_path)
    
    # Store as documentation-only entry (no JSON, no issues to analyze)
    summary = {
        "total_issues": -1,  # Use -1 to indicate this is documentation-only
        "critical_issues": 0,
        "high_issues": 0,
        "medium_issues": 0,
        "low_issues": 0,
        "estimated_total_time_minutes": 0,
        "ai_enhanced_issues": 0,
    }
    
    # Save to database
    try:
        scan_id = dbsvc.insert_run_returning_id(
            DB_PATH,
            summary,
            scenario_name,
            "documentation",  # framework = "documentation" to distinguish
            ts_iso,
            raw_report_json=None,
            pdf_report_path=pdf_path_str,
            html_report_path=html_path_str,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    return {
        "success": True,
        "scan_id": scan_id,
        "message": "Documentation reports uploaded successfully.",
        "pdf_uploaded": pdf_path_str is not None,
        "html_uploaded": html_path_str is not None,
    }


@router.get("/scans", response_model=List[ScanSummary])
def list_scans(project: Optional[str] = None) -> List[ScanSummary]:
    try:
        rows = dbsvc.list_runs(DB_PATH, limit=100, project_name=project)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    
    # Enrich each scan with computed fields
    enriched = []
    for row in rows:
        scan_dict = dict(row)
        scan_id = scan_dict.get('id')
        
        # Compute name from URL (domain or path)
        url = scan_dict.get('url', '')
        if url and url != 'api_request':
            try:
                from urllib.parse import urlparse
                parsed = urlparse(url)
                scan_dict['name'] = parsed.netloc or parsed.path or url[:30]
            except:
                scan_dict['name'] = url[:30]
        else:
            scan_dict['name'] = f"Scan #{scan_id}"
        
        # Get most violated rule from issues
        if scan_id:
            try:
                issues = dbsvc.list_run_issues(DB_PATH, scan_id, limit=1000)
                if issues:
                    # Count rule occurrences
                    rule_counts: Dict[str, int] = {}
                    rule_wcag: Dict[str, str] = {}
                    for issue in issues:
                        rule_id = issue.get('rule_id', 'unknown')
                        rule_counts[rule_id] = rule_counts.get(rule_id, 0) + 1
                        if not rule_wcag.get(rule_id):
                            wcag_refs = issue.get('wcag_refs', [])
                            if wcag_refs:
                                # wcag_refs is now a list, get first element
                                if isinstance(wcag_refs, list) and len(wcag_refs) > 0:
                                    rule_wcag[rule_id] = wcag_refs[0]
                                elif isinstance(wcag_refs, str):
                                    rule_wcag[rule_id] = wcag_refs.split(',')[0] if ',' in wcag_refs else wcag_refs
                    
                    # Get most common rule
                    if rule_counts:
                        most_violated = max(rule_counts.items(), key=lambda x: x[1])
                        scan_dict['most_violated_rule'] = most_violated[0]
                        scan_dict['most_violated_wcag'] = rule_wcag.get(most_violated[0], '')
            except:
                pass
        
        # Compute trend (simplified: compare to previous scan's total)
        try:
            prev_scans = [r for r in rows if r['id'] < scan_id]
            if prev_scans and scan_id:
                prev_total = prev_scans[0].get('total_issues', 0)
                curr_total = scan_dict.get('total_issues', 0)
                if prev_total > 0:
                    trend_pct = ((curr_total - prev_total) / prev_total) * 100
                    scan_dict['trend'] = round(trend_pct, 1)
        except:
            pass
        
        enriched.append(ScanSummary(**scan_dict))
    
    return enriched


@router.get("/projects", response_model=List[str])
def list_projects() -> List[str]:
    """Get all unique project names"""
    try:
        projects = dbsvc.get_all_projects(DB_PATH)
        return projects if projects else ["Default Project"]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/scans/{scan_id}", response_model=ScanSummary)
def get_scan(scan_id: int) -> ScanSummary:
    row = dbsvc.get_run(DB_PATH, scan_id)
    if not row:
        raise HTTPException(status_code=404, detail="Scan not found")
    return ScanSummary(**row)


@router.get("/scans/{scan_id}/issues", response_model=IssuesPage)
def get_scan_issues(
    scan_id: int,
    severity: Optional[List[str]] = Query(default=None, description="Repeatable severity filter e.g. ?severity=critical&severity=high"),
    rule_id: Optional[str] = None,
    q: Optional[str] = None,
    page: int = 1,
    size: int = 50,
) -> IssuesPage:
    if page < 1:
        page = 1
    if size < 1:
        size = 50
    offset = (page - 1) * size
    severities = [s.lower() for s in (severity or []) if s]
    items = dbsvc.list_run_issues(DB_PATH, scan_id, severities=severities or None, rule_id=rule_id, q=q, limit=size, offset=offset)
    total = dbsvc.count_run_issues(DB_PATH, scan_id, severities=severities or None, rule_id=rule_id, q=q)
    norm_items = [IssueOut(**it) for it in items]
    return IssuesPage(items=norm_items, total=total)


@router.get("/scans/{scan_id}/issues.csv")
def export_scan_issues_csv(
    scan_id: int,
    severity: Optional[List[str]] = Query(default=None),
    rule_id: Optional[str] = None,
    q: Optional[str] = None,
) -> StreamingResponse:
    import io, csv
    severities = [s.lower() for s in (severity or []) if s]
    items = dbsvc.list_run_issues(DB_PATH, scan_id, severities=severities or None, rule_id=rule_id, q=q, limit=10000, offset=0)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["rule_id", "priority", "user_impact", "fix_suggestion", "effort_minutes", "wcag_refs", "selector", "source"])
    for it in items:
        writer.writerow([
            it.get("rule_id", ""),
            it.get("priority", ""),
            it.get("user_impact", ""),
            it.get("fix_suggestion", ""),
            it.get("effort_minutes", 0),
            "; ".join(it.get("wcag_refs", [])),
            it.get("selector", ""),
            it.get("source", ""),
        ])
    buf.seek(0)
    return StreamingResponse(buf, media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=scan-{scan_id}-issues.csv"})


@router.patch("/issues/{issue_id}/status")
def update_issue_status(issue_id: int, status: str = Query(..., description="Status: todo, in_progress, done, wont_fix")) -> Dict[str, Any]:
    """Update the status of a single issue"""
    valid_statuses = ["todo", "in_progress", "done", "wont_fix"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
    
    # Record timestamp when status changes
    timestamp = datetime.now(timezone.utc).isoformat()
    success = dbsvc.update_issue_status(DB_PATH, issue_id, status, timestamp)
    if not success:
        raise HTTPException(status_code=404, detail="Issue not found")
    
    return {"success": True, "issue_id": issue_id, "status": status}


@router.patch("/issues/bulk-status")
def bulk_update_issue_status(issue_ids: List[int], status: str = Query(..., description="Status: todo, in_progress, done, wont_fix")) -> Dict[str, Any]:
    """Update the status of multiple issues at once"""
    valid_statuses = ["todo", "in_progress", "done", "wont_fix"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
    
    # Record timestamp when status changes
    timestamp = datetime.now(timezone.utc).isoformat()
    count = dbsvc.bulk_update_issue_status(DB_PATH, issue_ids, status, timestamp)
    return {"success": True, "updated": count, "status": status}


@router.get("/scans/{scan_id}/status-summary")
def get_scan_status_summary(scan_id: int) -> Dict[str, Any]:
    """Get a summary of issue statuses for a scan"""
    # First check if scan exists
    scan = dbsvc.get_run(DB_PATH, scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    summary = dbsvc.get_status_summary(DB_PATH, scan_id)
    total = sum(summary.values())
    
    return {
        "scan_id": scan_id,
        "total_issues": total,
        "status_counts": summary,
        "completion_percentage": round((summary['done'] / total * 100) if total > 0 else 0, 1)
    }


@router.get("/scans/{scan_id}/pdf-report")
def get_pdf_report(scan_id: int, download: bool = False):
    """View or download the PDF report for a scan"""
    scan = dbsvc.get_run(DB_PATH, scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    pdf_path = scan.get('pdf_report_path')
    if not pdf_path:
        raise HTTPException(status_code=404, detail="No PDF report available for this scan")
    
    file_path = Path(pdf_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="PDF file not found on disk")
    
    headers = {}
    if download:
        headers['Content-Disposition'] = f'attachment; filename="accessibility_report_{scan_id}.pdf"'
    else:
        headers['Content-Disposition'] = 'inline'
    
    return FileResponse(
        path=file_path,
        media_type='application/pdf',
        headers=headers
    )


@router.get("/scans/{scan_id}/html-report")
def get_html_report(scan_id: int, download: bool = False):
    """View or download the HTML report for a scan"""
    scan = dbsvc.get_run(DB_PATH, scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    html_path = scan.get('html_report_path')
    if not html_path:
        raise HTTPException(status_code=404, detail="No HTML report available for this scan")
    
    file_path = Path(html_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="HTML file not found on disk")
    
    headers = {}
    if download:
        headers['Content-Disposition'] = f'attachment; filename="accessibility_report_{scan_id}.html"'
    else:
        headers['Content-Disposition'] = 'inline'
    
    return FileResponse(
        path=file_path,
        media_type='text/html',
        headers=headers
    )


@router.delete("/scans/{scan_id}")
def delete_scan(scan_id: int) -> Dict[str, Any]:
    """Delete a scan and all its associated issues"""
    try:
        # Get scan details first to potentially clean up files
        scan = dbsvc.get_run(DB_PATH, scan_id)
        if not scan:
            raise HTTPException(status_code=404, detail="Scan not found")
        
        # Delete associated files if they exist
        if scan.get('pdf_report_path'):
            pdf_path = Path(scan['pdf_report_path'])
            if pdf_path.exists():
                pdf_path.unlink()
        
        if scan.get('html_report_path'):
            html_path = Path(scan['html_report_path'])
            if html_path.exists():
                html_path.unlink()
        
        if scan.get('screenshots_dir'):
            screenshots_dir = Path(scan['screenshots_dir'])
            if screenshots_dir.exists():
                import shutil
                shutil.rmtree(screenshots_dir)
        
        # Delete from database (CASCADE will delete issues)
        dbsvc.delete_scan(DB_PATH, scan_id)
        
        return {"message": "Scan deleted successfully", "scan_id": scan_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete scan: {str(e)}")


@router.delete("/manual-tests/{session_id}")
def delete_manual_test_session(session_id: int) -> Dict[str, Any]:
    """Delete a manual test session"""
    try:
        dbsvc.delete_manual_test_session(DB_PATH, session_id)
        return {"message": "Manual test session deleted successfully", "session_id": session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete manual test session: {str(e)}")


@router.delete("/checklists/{checklist_id}")
def delete_checklist(checklist_id: int) -> Dict[str, Any]:
    """Delete a manual checklist"""
    try:
        dbsvc.delete_checklist(DB_PATH, checklist_id)
        return {"message": "Checklist deleted successfully", "checklist_id": checklist_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete checklist: {str(e)}")

