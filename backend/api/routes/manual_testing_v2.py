"""
API routes for streamlined manual testing and bug tracking.
Replaces session-based workflow with tool-first, bug-focused approach.
"""

from datetime import datetime
from pathlib import Path
from typing import List, Optional
import json
import shutil

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse

from backend.schemas import (
    ManualBugCreate,
    ManualBugResponse,
    ManualBugDetail,
    TestingMethodStats
)
from backend.services import db
from backend.utils.excel_parser import get_checklist_by_tool, save_checklist_to_excel, clear_cache

router = APIRouter(prefix="/api/manual-testing-v2", tags=["manual-testing-v2"])

DB_PATH = Path("data/a11y_runs.sqlite")
EVIDENCE_DIR = Path("data/manual-testing-evidence")
CHECKLISTS_DIR = Path("static/checklists")
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

# Allowed evidence file types
ALLOWED_EXTENSIONS = {
    "image": [".png", ".jpg", ".jpeg"],
    "audio": [".wav", ".mp3"],
    "video": [".mp4", ".webm"]
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


@router.get("/checklists/{tool}", response_model=dict)
async def get_checklist(tool: str):
    """
    Get WCAG 2.1 AA checklist for a testing tool from Excel file.
    
    Args:
        tool: nvda, keyboard, or zoom
        
    Returns:
        Parsed checklist with metadata and items
    """
    try:
        checklist = get_checklist_by_tool(tool, CHECKLISTS_DIR)
        return checklist
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Checklist not found for tool '{tool}'")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load checklist: {str(e)}")


@router.get("/checklists/{tool}/download")
async def download_checklist(tool: str):
    """
    Download the original Excel checklist file for offline editing.
    
    Args:
        tool: nvda, keyboard, or zoom
        
    Returns:
        Excel file download
    """
    allowed_tools = ["nvda", "keyboard", "zoom"]
    if tool not in allowed_tools:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid tool. Must be one of: {', '.join(allowed_tools)}"
        )
    
    checklist_file = CHECKLISTS_DIR / f"{tool}-wcag21aa-checklist.xlsx"
    
    if not checklist_file.exists():
        raise HTTPException(status_code=404, detail=f"Checklist not found for {tool}")
    
    return FileResponse(
        checklist_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=f"{tool}-wcag21aa-checklist.xlsx"
    )


@router.put("/checklists/{tool}")
async def update_checklist(tool: str, checklist_items: List[dict]):
    """
    Update checklist items and save to Excel file.
    
    Args:
        tool: nvda, keyboard, or zoom
        checklist_items: List of checklist items with all 9 columns
        
    Returns:
        Success message with updated item count
    """
    try:
        # Save to Excel
        save_checklist_to_excel(tool, checklist_items, CHECKLISTS_DIR)
        
        return {
            "message": f"Checklist updated successfully",
            "tool": tool,
            "items_count": len(checklist_items)
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update checklist: {str(e)}")


@router.get("/testing-methods/stats")
async def get_testing_method_stats(project_name: Optional[str] = None):
    """
    Get statistics for each testing method (NVDA, Keyboard, Zoom).
    Shows bug count and last tested date for each tool.
    """
    try:
        stats = db.get_testing_method_stats(DB_PATH, project_name)
        
        # Ensure all tools are represented
        all_tools = ["NVDA", "Keyboard", "Zoom"]
        result = []
        
        for tool in all_tools:
            tool_stats = stats.get(tool, {"bug_count": 0, "last_tested": None})
            result.append({
                "tool": tool,
                "bug_count": tool_stats["bug_count"],
                "last_tested": tool_stats["last_tested"]
            })
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects", response_model=List[str])
async def get_projects():
    """
    Get list of all unique project names from bugs.
    """
    try:
        projects = db.get_bug_projects(DB_PATH)
        return projects
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bugs", response_model=ManualBugResponse)
async def create_bug(bug: ManualBugCreate):
    """
    Create a new bug report.
    """
    try:
        bug_id = db.create_manual_bug(
            DB_PATH,
            title=bug.title,
            wcag_criterion=bug.wcag_criterion,
            severity=bug.severity,
            testing_tool=bug.testing_tool,
            description=bug.description,
            expected_behavior=bug.expected_behavior,
            actual_behavior=bug.actual_behavior,
            project_name=bug.project_name,
            run_id=bug.run_id,
            steps_to_reproduce=bug.steps_to_reproduce,
            affected_user_groups=bug.affected_user_groups,
            notes=bug.notes,
            created_by=bug.created_by
        )
        
        # Fetch and return created bug
        bug_detail = db.get_manual_bug(DB_PATH, bug_id)
        if not bug_detail:
            raise HTTPException(status_code=500, detail="Failed to retrieve created bug")
        
        return ManualBugResponse(**bug_detail)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bugs", response_model=List[ManualBugResponse])
async def list_bugs(
    project_name: Optional[str] = None,
    testing_tool: Optional[str] = None,
    severity: Optional[str] = None,
    status: str = "open",
    limit: int = 100
):
    """
    List bugs with optional filters.
    """
    try:
        bugs = db.list_manual_bugs(
            DB_PATH,
            project_name=project_name,
            testing_tool=testing_tool,
            severity=severity,
            status=status,
            limit=limit
        )
        return [ManualBugResponse(**bug) for bug in bugs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bugs/{bug_id}", response_model=ManualBugDetail)
async def get_bug(bug_id: int):
    """
    Get a single bug with evidence files.
    """
    try:
        bug = db.get_manual_bug(DB_PATH, bug_id)
        if not bug:
            raise HTTPException(status_code=404, detail="Bug not found")
        return ManualBugDetail(**bug)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bugs/{bug_id}/evidence")
async def upload_evidence(bug_id: int, file: UploadFile = File(...)):
    """
    Upload evidence file (screenshot, audio, video) for a bug.
    Max size: 10MB. Allowed types: png, jpg, wav, mp3, mp4, webm
    """
    # Verify bug exists
    bug = db.get_manual_bug(DB_PATH, bug_id)
    if not bug:
        raise HTTPException(status_code=404, detail="Bug not found")
    
    # Check file extension
    file_ext = Path(file.filename or "").suffix.lower()
    all_allowed = sum(ALLOWED_EXTENSIONS.values(), [])
    
    if file_ext not in all_allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(all_allowed)}"
        )
    
    # Determine file type category
    file_type = "unknown"
    for category, extensions in ALLOWED_EXTENSIONS.items():
        if file_ext in extensions:
            file_type = category
            break
    
    # Check file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Max size: {MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"bug_{bug_id}_{timestamp}{file_ext}"
    file_path = EVIDENCE_DIR / safe_filename
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # Add evidence record to database
    try:
        evidence_id = db.add_bug_evidence(
            DB_PATH,
            bug_id=bug_id,
            file_path=str(file_path),
            file_type=file_type,
            file_size=file_size
        )
        
        return {
            "success": True,
            "evidence_id": evidence_id,
            "file_path": str(file_path),
            "file_type": file_type,
            "file_size": file_size
        }
    except Exception as e:
        # Clean up file if database insert fails
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Failed to save evidence record: {str(e)}")


@router.get("/bugs/{bug_id}/evidence/{evidence_id}/download")
async def download_evidence(bug_id: int, evidence_id: int):
    """
    Download an evidence file.
    """
    # Get bug with evidence
    bug = db.get_manual_bug(DB_PATH, bug_id)
    if not bug:
        raise HTTPException(status_code=404, detail="Bug not found")
    
    # Find evidence file
    evidence = next((e for e in bug["evidence"] if e["id"] == evidence_id), None)
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")
    
    file_path = Path(evidence["file_path"])
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Evidence file not found on disk")
    
    return FileResponse(
        path=file_path,
        filename=file_path.name,
        media_type="application/octet-stream"
    )


@router.patch("/bugs/{bug_id}/status")
async def update_bug_status(bug_id: int, status: str):
    """
    Update bug status.
    Allowed values: open, in_progress, resolved, closed
    """
    allowed_statuses = ["open", "in_progress", "resolved", "closed"]
    if status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(allowed_statuses)}"
        )
    
    try:
        success = db.update_bug_status(DB_PATH, bug_id, status)
        if not success:
            raise HTTPException(status_code=404, detail="Bug not found")
        return {"success": True, "status": status}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/bugs/{bug_id}")
async def delete_bug(bug_id: int):
    """
    Delete a bug and its evidence files.
    """
    # Get bug to find evidence files
    bug = db.get_manual_bug(DB_PATH, bug_id)
    if bug:
        # Delete evidence files from disk
        for evidence in bug.get("evidence", []):
            file_path = Path(evidence["file_path"])
            file_path.unlink(missing_ok=True)
    
    # Delete from database (CASCADE deletes evidence records)
    try:
        success = db.delete_manual_bug(DB_PATH, bug_id)
        if not success:
            raise HTTPException(status_code=404, detail="Bug not found")
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bugs/{bug_id}/export/github")
async def export_bug_as_github_issue(bug_id: int):
    """
    Export bug as GitHub issue markdown template.
    """
    bug = db.get_manual_bug(DB_PATH, bug_id)
    if not bug:
        raise HTTPException(status_code=404, detail="Bug not found")
    
    # Generate GitHub issue markdown
    markdown = f"""## {bug['title']}

**WCAG Criterion:** {bug['wcag_criterion']}  
**Severity:** {bug['severity']}  
**Testing Tool:** {bug['testing_tool']}  
**Project:** {bug['project_name']}

### Description
{bug['description']}

### Expected Behavior
{bug['expected_behavior']}

### Actual Behavior
{bug['actual_behavior']}
"""
    
    if bug.get('steps_to_reproduce'):
        markdown += f"\n### Steps to Reproduce\n{bug['steps_to_reproduce']}\n"
    
    if bug.get('affected_user_groups'):
        markdown += f"\n### Affected User Groups\n{bug['affected_user_groups']}\n"
    
    if bug.get('notes'):
        markdown += f"\n### Additional Notes\n{bug['notes']}\n"
    
    if bug.get('evidence'):
        markdown += f"\n### Evidence\n{len(bug['evidence'])} file(s) attached\n"
    
    markdown += f"\n---\n*Reported: {bug['created_at']}*"
    if bug.get('created_by'):
        markdown += f" *by {bug['created_by']}*"
    
    return JSONResponse(content={"markdown": markdown})


@router.get("/automated-context")
async def get_automated_context(project_name: Optional[str] = None):
    """
    Get automated test results that need manual verification.
    Pulls latest scan and highlights issues requiring manual testing.
    """
    try:
        # Get latest scan for project
        scans = db.list_runs(DB_PATH, limit=1, project_name=project_name)
        
        if not scans:
            return {
                "has_automated_results": False,
                "message": "No automated scans found for this project"
            }
        
        latest_scan = scans[0]
        
        # Get issues from latest scan
        issues = db.list_run_issues(DB_PATH, latest_scan["id"], limit=1000)
        
        # Categorize issues by manual verification need
        manual_verification_needed = []
        automated_only = []
        
        # Keywords that indicate manual verification is needed
        manual_keywords = [
            "keyboard", "focus", "navigation", "label", "heading",
            "screen reader", "aria", "alternative text", "link purpose",
            "color contrast", "zoom", "reflow"
        ]
        
        for issue in issues:
            rule_id = (issue.get("rule_id") or "").lower()
            user_impact = (issue.get("user_impact") or "").lower()
            
            needs_manual = any(keyword in rule_id or keyword in user_impact 
                             for keyword in manual_keywords)
            
            if needs_manual:
                # Suggest which tool to use for manual verification
                suggested_tool = "NVDA"  # Default
                if "keyboard" in rule_id or "focus" in rule_id:
                    suggested_tool = "Keyboard"
                elif "zoom" in rule_id or "contrast" in rule_id or "reflow" in rule_id:
                    suggested_tool = "Zoom"
                
                manual_verification_needed.append({
                    **issue,
                    "suggested_tool": suggested_tool
                })
            else:
                automated_only.append(issue)
        
        return {
            "has_automated_results": True,
            "scan_id": latest_scan["id"],
            "scan_time": latest_scan["ts"],
            "total_violations": latest_scan["total_issues"],
            "manual_verification_needed": manual_verification_needed,
            "manual_verification_count": len(manual_verification_needed),
            "automated_only_count": len(automated_only)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
