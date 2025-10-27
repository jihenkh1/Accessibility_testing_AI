"""
API routes for manual accessibility testing workflow.
"""

from datetime import datetime
from pathlib import Path
from typing import List
import json
import shutil

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse

from backend.schemas import (
    ChecklistGenerateRequest,
    ChecklistResponse,
    TestSessionCreate,
    TestSessionResponse,
    TestResultRecord,
    TestResultResponse,
    SessionResultsSummary,
    ChecklistItem
)
from backend.services import db
from src.accessibility_ai.manual_testing.checklist_generator import (
    generate_checklist,
    get_supported_page_types,
    get_supported_components,
    detect_components_from_report
)

router = APIRouter(prefix="/api/manual-testing", tags=["manual-testing"])

DB_PATH = Path("data/a11y_runs.sqlite")
SCREENSHOTS_DIR = Path("data/screenshots")
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/checklists/generate", response_model=ChecklistResponse)
async def generate_testing_checklist(request: ChecklistGenerateRequest):
    """
    Generate a manual testing checklist based on page type and components.
    """
    # Validate page type
    if request.page_type not in get_supported_page_types():
        raise HTTPException(
            status_code=400,
            detail=f"Invalid page type. Supported: {get_supported_page_types()}"
        )
    
    # Validate components
    supported_components = get_supported_components()
    invalid_components = [c for c in request.components if c not in supported_components]
    if invalid_components:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid components: {invalid_components}. Supported: {supported_components}"
        )
    
    # Generate checklist
    checklist_data = generate_checklist(request.page_type, request.components)
    
    # Save to database
    created_at = datetime.now().isoformat()
    components_str = ",".join(request.components)
    checklist_json = json.dumps(checklist_data)
    
    checklist_id = db.insert_checklist(
        DB_PATH,
        request.page_type,
        components_str,
        checklist_json,
        created_at
    )
    
    return ChecklistResponse(
        checklist_id=checklist_id,
        page_type=checklist_data["page_type"],
        components=checklist_data["components"],
        total_items=checklist_data["total_items"],
        categories=checklist_data["categories"],
        priority_counts=checklist_data["priority_counts"],
        estimated_minutes=checklist_data["estimated_minutes"],
        items=[ChecklistItem(**item) for item in checklist_data["items"]],
        created_at=created_at
    )


@router.get("/checklists/{checklist_id}", response_model=ChecklistResponse)
async def get_checklist(checklist_id: int):
    """
    Get a checklist by ID.
    """
    checklist_row = db.get_checklist(DB_PATH, checklist_id)
    if not checklist_row:
        raise HTTPException(status_code=404, detail="Checklist not found")
    
    checklist_data = json.loads(checklist_row["checklist_json"])
    
    return ChecklistResponse(
        checklist_id=checklist_row["id"],
        page_type=checklist_data["page_type"],
        components=checklist_data["components"],
        total_items=checklist_data["total_items"],
        categories=checklist_data["categories"],
        priority_counts=checklist_data["priority_counts"],
        estimated_minutes=checklist_data["estimated_minutes"],
        items=[ChecklistItem(**item) for item in checklist_data["items"]],
        created_at=checklist_row["created_at"]
    )


@router.post("/sessions", response_model=TestSessionResponse)
async def create_session(session: TestSessionCreate):
    """
    Create a new test session.
    """
    # Verify checklist exists
    checklist = db.get_checklist(DB_PATH, session.checklist_id)
    if not checklist:
        raise HTTPException(status_code=404, detail="Checklist not found")
    
    # Verify run exists if provided
    if session.run_id:
        run = db.get_run(DB_PATH, session.run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")
    
    # Create session
    started_at = datetime.now().isoformat()
    session_id = db.create_test_session(
        DB_PATH,
        session.checklist_id,
        session.tester_name,
        started_at,
        session.run_id
    )
    
    return TestSessionResponse(
        id=session_id,
        run_id=session.run_id,
        checklist_id=session.checklist_id,
        tester_name=session.tester_name,
        started_at=started_at,
        completed_at=None,
        status="in-progress"
    )


@router.get("/sessions", response_model=List[TestSessionResponse])
async def list_sessions(limit: int = 50):
    """
    List all test sessions.
    """
    sessions = db.list_test_sessions(DB_PATH, limit)
    return [TestSessionResponse(**session) for session in sessions]


@router.get("/sessions/{session_id}", response_model=TestSessionResponse)
async def get_session(session_id: int):
    """
    Get a test session by ID.
    """
    session = db.get_test_session(DB_PATH, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return TestSessionResponse(**session)


@router.put("/sessions/{session_id}/complete")
async def complete_session(session_id: int):
    """
    Mark a test session as complete.
    """
    completed_at = datetime.now().isoformat()
    success = db.update_test_session(DB_PATH, session_id, completed_at=completed_at, status="completed")
    
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"message": "Session marked as complete", "completed_at": completed_at}


@router.post("/tests/record", response_model=TestResultResponse)
async def record_test_result(result: TestResultRecord):
    """
    Record a manual test result.
    """
    # Verify session exists
    session = db.get_test_session(DB_PATH, result.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Validate status
    valid_statuses = ["passed", "failed", "needs_retest", "skipped"]
    if result.status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {valid_statuses}"
        )
    
    # Insert result
    created_at = datetime.now().isoformat()
    result_id = db.insert_test_result(
        DB_PATH,
        result.session_id,
        session["checklist_id"],
        result.item_id,
        result.status,
        result.notes,
        None,  # screenshot_path initially None
        created_at
    )
    
    return TestResultResponse(
        id=result_id,
        session_id=result.session_id,
        checklist_id=session["checklist_id"],
        item_id=result.item_id,
        status=result.status,
        notes=result.notes,
        screenshot_path=None,
        created_at=created_at
    )


@router.post("/tests/{result_id}/screenshot")
async def upload_screenshot(result_id: int, file: UploadFile = File(...)):
    """
    Upload a screenshot for a test result.
    """
    # Verify result exists (we need to query via session results)
    # This is a simplified check - in production you might want a dedicated function
    # For now, we'll just save the file and update the path
    
    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"test_{result_id}_{timestamp}_{file.filename}"
    filepath = SCREENSHOTS_DIR / filename
    
    # Save file
    with filepath.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Update result with screenshot path
    relative_path = f"screenshots/{filename}"
    success = db.update_test_result(DB_PATH, result_id, screenshot_path=relative_path)
    
    if not success:
        # Clean up file if update failed
        filepath.unlink(missing_ok=True)
        raise HTTPException(status_code=404, detail="Test result not found")
    
    return {
        "message": "Screenshot uploaded successfully",
        "screenshot_path": relative_path
    }


@router.get("/screenshots/{filename}")
async def get_screenshot(filename: str):
    """
    Retrieve a screenshot file.
    """
    filepath = SCREENSHOTS_DIR / filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Screenshot not found")
    
    return FileResponse(filepath)


@router.get("/sessions/{session_id}/results", response_model=SessionResultsSummary)
async def get_session_results(session_id: int):
    """
    Get all results for a test session with summary.
    """
    # Get session
    session = db.get_test_session(DB_PATH, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get checklist
    checklist_row = db.get_checklist(DB_PATH, session["checklist_id"])
    if not checklist_row:
        raise HTTPException(status_code=404, detail="Checklist not found")
    
    checklist_data = json.loads(checklist_row["checklist_json"])
    
    # Get results
    results = db.get_session_results(DB_PATH, session_id)
    
    # Calculate progress
    progress = {
        "passed": len([r for r in results if r["status"] == "passed"]),
        "failed": len([r for r in results if r["status"] == "failed"]),
        "needs_retest": len([r for r in results if r["status"] == "needs_retest"]),
        "skipped": len([r for r in results if r["status"] == "skipped"]),
        "total": checklist_data["total_items"]
    }
    
    return SessionResultsSummary(
        session=TestSessionResponse(**session),
        checklist=ChecklistResponse(
            checklist_id=checklist_row["id"],
            page_type=checklist_data["page_type"],
            components=checklist_data["components"],
            total_items=checklist_data["total_items"],
            categories=checklist_data["categories"],
            priority_counts=checklist_data["priority_counts"],
            estimated_minutes=checklist_data["estimated_minutes"],
            items=[ChecklistItem(**item) for item in checklist_data["items"]],
            created_at=checklist_row["created_at"]
        ),
        results=[TestResultResponse(**r) for r in results],
        progress=progress
    )


@router.get("/page-types")
async def list_page_types():
    """
    Get list of supported page types.
    """
    return {"page_types": get_supported_page_types()}


@router.get("/components")
async def list_components():
    """
    Get list of supported component types.
    """
    return {"components": get_supported_components()}


@router.get("/runs/{run_id}/detect-components")
async def detect_components(run_id: int):
    """
    Detect components from an existing automated scan run.
    """
    # Get run issues
    issues = db.list_run_issues(DB_PATH, run_id)
    if not issues:
        return {"components": []}
    
    # Detect components
    detected = detect_components_from_report(issues)
    
    return {"components": detected}
