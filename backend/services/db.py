from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS projects (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL,
  description TEXT
);

CREATE TABLE IF NOT EXISTS run_summaries (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  url TEXT NOT NULL,
  framework TEXT NOT NULL,
  total_issues INTEGER NOT NULL,
  critical_issues INTEGER NOT NULL,
  high_issues INTEGER NOT NULL,
  medium_issues INTEGER NOT NULL,
  low_issues INTEGER NOT NULL,
  estimated_total_time_minutes INTEGER NOT NULL,
  ai_enhanced_issues INTEGER NOT NULL,
  raw_report_json TEXT,
  pdf_report_path TEXT,
  html_report_path TEXT,
  screenshots_dir TEXT,
  project_name TEXT DEFAULT 'Default Project'
);

CREATE TABLE IF NOT EXISTS run_issues (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id INTEGER NOT NULL,
  rule_id TEXT,
  priority TEXT,
  user_impact TEXT,
  fix_suggestion TEXT,
  effort_minutes INTEGER,
  wcag_refs TEXT,
  selector TEXT,
  source TEXT,
  status TEXT DEFAULT 'todo',
  FOREIGN KEY(run_id) REFERENCES run_summaries(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS manual_checklists (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  page_type TEXT NOT NULL,
  components TEXT NOT NULL,
  checklist_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  project_name TEXT DEFAULT 'Default Project'
);

CREATE TABLE IF NOT EXISTS test_sessions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id INTEGER,
  checklist_id INTEGER NOT NULL,
  tester_name TEXT NOT NULL,
  started_at TEXT NOT NULL,
  completed_at TEXT,
  status TEXT DEFAULT 'in-progress',
  project_name TEXT DEFAULT 'Default Project',
  FOREIGN KEY(run_id) REFERENCES run_summaries(id) ON DELETE SET NULL,
  FOREIGN KEY(checklist_id) REFERENCES manual_checklists(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS manual_test_results (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id INTEGER NOT NULL,
  checklist_id INTEGER NOT NULL,
  item_id TEXT NOT NULL,
  status TEXT NOT NULL,
  notes TEXT,
  screenshot_path TEXT,
  created_at TEXT NOT NULL,
  FOREIGN KEY(session_id) REFERENCES test_sessions(id) ON DELETE CASCADE,
  FOREIGN KEY(checklist_id) REFERENCES manual_checklists(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS manual_bugs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  wcag_criterion TEXT NOT NULL,
  severity TEXT NOT NULL,
  testing_tool TEXT NOT NULL,
  description TEXT NOT NULL,
  expected_behavior TEXT NOT NULL,
  actual_behavior TEXT NOT NULL,
  steps_to_reproduce TEXT,
  affected_user_groups TEXT,
  notes TEXT,
  project_name TEXT DEFAULT 'Default Project',
  run_id INTEGER,
  created_at TEXT NOT NULL,
  created_by TEXT,
  status TEXT DEFAULT 'open',
  FOREIGN KEY(run_id) REFERENCES run_summaries(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS bug_evidence (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  bug_id INTEGER NOT NULL,
  file_path TEXT NOT NULL,
  file_type TEXT NOT NULL,
  file_size INTEGER NOT NULL,
  uploaded_at TEXT NOT NULL,
  FOREIGN KEY(bug_id) REFERENCES manual_bugs(id) ON DELETE CASCADE
);
"""


def _connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(db_path))
    con.execute("PRAGMA journal_mode=WAL;")
    con.execute("PRAGMA synchronous=NORMAL;")
    con.executescript(SCHEMA_SQL)
    return con


def insert_run_returning_id(
    db_path: Path,
    summary: Dict[str, Any],
    url: str,
    framework: str,
    ts_iso: str,
    raw_report_json: Optional[str] = None,
    pdf_report_path: Optional[str] = None,
    html_report_path: Optional[str] = None,
    screenshots_dir: Optional[str] = None,
    project_name: str = "Default Project"
) -> int:
    con = _connect(db_path)
    try:
        cur = con.execute(
            """
            INSERT INTO run_summaries (
                ts, url, framework,
                total_issues, critical_issues, high_issues, medium_issues, low_issues,
                estimated_total_time_minutes, ai_enhanced_issues,
                raw_report_json, pdf_report_path, html_report_path, screenshots_dir, project_name
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ts_iso,
                url,
                framework,
                int(summary.get("total_issues", 0)),
                int(summary.get("critical_issues", 0)),
                int(summary.get("high_issues", 0)),
                int(summary.get("medium_issues", 0)),
                int(summary.get("low_issues", 0)),
                int(summary.get("estimated_total_time_minutes", 0)),
                int(summary.get("ai_enhanced_issues", 0)),
                raw_report_json,
                pdf_report_path,
                html_report_path,
                screenshots_dir,
                project_name,
            ),
        )
        con.commit()
        row_id = cur.lastrowid
        if row_id is None:
            raise ValueError("Failed to insert row")
        return int(row_id)
    finally:
        con.close()


def get_run(db_path: Path, run_id: int) -> Optional[Dict[str, Any]]:
    con = _connect(db_path)
    try:
        row = con.execute(
            "SELECT id, ts, url, framework, total_issues, critical_issues, high_issues, medium_issues, low_issues, estimated_total_time_minutes, ai_enhanced_issues, raw_report_json, pdf_report_path, html_report_path, screenshots_dir, project_name FROM run_summaries WHERE id = ?",
            (run_id,),
        ).fetchone()
        if not row:
            return None
        cols = [
            "id",
            "ts",
            "url",
            "framework",
            "total_issues",
            "critical_issues",
            "high_issues",
            "medium_issues",
            "low_issues",
            "estimated_total_time_minutes",
            "ai_enhanced_issues",
            "raw_report_json",
            "pdf_report_path",
            "html_report_path",
            "screenshots_dir",
            "project_name",
        ]
        return dict(zip(cols, row))
    finally:
        con.close()


def list_runs(db_path: Path, limit: int = 100, project_name: Optional[str] = None) -> List[Dict[str, Any]]:
    con = _connect(db_path)
    try:
        if project_name:
            rows = con.execute(
                "SELECT id, ts, url, framework, total_issues, critical_issues, high_issues, medium_issues, low_issues, estimated_total_time_minutes, ai_enhanced_issues, raw_report_json, pdf_report_path, html_report_path, screenshots_dir, project_name FROM run_summaries WHERE project_name = ? ORDER BY ts DESC LIMIT ?",
                (project_name, limit),
            ).fetchall()
        else:
            rows = con.execute(
                "SELECT id, ts, url, framework, total_issues, critical_issues, high_issues, medium_issues, low_issues, estimated_total_time_minutes, ai_enhanced_issues, raw_report_json, pdf_report_path, html_report_path, screenshots_dir, project_name FROM run_summaries ORDER BY ts DESC LIMIT ?",
                (limit,),
            ).fetchall()
        cols = [
            "id",
            "ts",
            "url",
            "framework",
            "total_issues",
            "critical_issues",
            "high_issues",
            "medium_issues",
            "low_issues",
            "estimated_total_time_minutes",
            "ai_enhanced_issues",
            "raw_report_json",
            "pdf_report_path",
            "html_report_path",
            "screenshots_dir",
            "project_name",
        ]
        return [dict(zip(cols, r)) for r in rows]
    finally:
        con.close()


def get_all_projects(db_path: Path) -> List[str]:
    """Get list of all unique project names"""
    con = _connect(db_path)
    try:
        # First get from projects table
        rows = con.execute(
            "SELECT name FROM projects ORDER BY name"
        ).fetchall()
        project_names = [row[0] for row in rows]
        
        # Also include any projects from run_summaries that aren't in projects table
        run_projects = con.execute(
            "SELECT DISTINCT project_name FROM run_summaries WHERE project_name IS NOT NULL"
        ).fetchall()
        for row in run_projects:
            if row[0] and row[0] not in project_names:
                project_names.append(row[0])
        
        return sorted(project_names) if project_names else []
    finally:
        con.close()


def create_project(db_path: Path, name: str, description: str = "") -> Dict[str, Any]:
    """Create a new project"""
    from datetime import datetime, timezone
    
    con = _connect(db_path)
    try:
        ts_iso = datetime.now(timezone.utc).isoformat()
        con.execute(
            "INSERT INTO projects (name, created_at, description) VALUES (?, ?, ?)",
            (name, ts_iso, description)
        )
        con.commit()
        return {
            "name": name,
            "created_at": ts_iso,
            "description": description
        }
    except sqlite3.IntegrityError:
        raise ValueError(f"Project '{name}' already exists")
    finally:
        con.close()


def cleanup_project_creation_scans(db_path: Path) -> int:
    """Remove old project_creation placeholder scans"""
    con = _connect(db_path)
    try:
        # Delete issues first (foreign key constraint)
        con.execute(
            """DELETE FROM run_issues 
               WHERE run_id IN (
                   SELECT id FROM run_summaries WHERE url = 'project_creation'
               )"""
        )
        # Delete the scans
        cursor = con.execute(
            "DELETE FROM run_summaries WHERE url = 'project_creation'"
        )
        deleted_count = cursor.rowcount
        con.commit()
        return deleted_count
    finally:
        con.close()


def delete_project(db_path: Path, project_name: str) -> Dict[str, Any]:
    """Delete a project and optionally all its scans"""
    con = _connect(db_path)
    try:
        # Check if project exists
        project_exists = con.execute(
            "SELECT COUNT(*) FROM projects WHERE name = ?", (project_name,)
        ).fetchone()[0]
        
        # Count scans in this project
        scan_count = con.execute(
            "SELECT COUNT(*) FROM run_summaries WHERE project_name = ?", (project_name,)
        ).fetchone()[0]
        
        # Count bugs in this project
        bug_count = con.execute(
            "SELECT COUNT(*) FROM manual_bugs WHERE project_name = ?", (project_name,)
        ).fetchone()[0]
        
        # Delete all bugs and their evidence for this project
        if bug_count > 0:
            # Delete bug evidence first (foreign key)
            con.execute(
                """DELETE FROM bug_evidence 
                   WHERE bug_id IN (
                       SELECT id FROM manual_bugs WHERE project_name = ?
                   )""",
                (project_name,)
            )
            # Delete bugs
            con.execute(
                "DELETE FROM manual_bugs WHERE project_name = ?", (project_name,)
            )
        
        # Delete all scans and issues for this project
        if scan_count > 0:
            # Delete issues first (foreign key)
            con.execute(
                """DELETE FROM run_issues 
                   WHERE run_id IN (
                       SELECT id FROM run_summaries WHERE project_name = ?
                   )""",
                (project_name,)
            )
            # Delete scans
            con.execute(
                "DELETE FROM run_summaries WHERE project_name = ?", (project_name,)
            )
        
        # Delete from projects table
        if project_exists:
            con.execute("DELETE FROM projects WHERE name = ?", (project_name,))
        
        con.commit()
        return {
            "deleted_scans": scan_count,
            "deleted_bugs": bug_count,
            "project_removed": bool(project_exists)
        }
    finally:
        con.close()


def insert_run_issues(db_path: Path, run_id: int, issues: List[Dict[str, Any]]) -> None:
    """Persist a list of issues for a given run.

    Expects issue dict keys: rule_id, priority, user_impact, fix_suggestion,
    effort_minutes, wcag_refs (list), selector, source
    """
    if not issues:
        return
    con = _connect(db_path)
    try:
        rows = []
        for it in issues:
            wcag_refs = it.get("wcag_refs")
            if isinstance(wcag_refs, list):
                wcag_text = ",".join(str(x) for x in wcag_refs)
            else:
                wcag_text = str(wcag_refs or "")
            rows.append(
                (
                    int(run_id),
                    str(it.get("rule_id", "")),
                    str(it.get("priority", "")),
                    str(it.get("user_impact", "")),
                    str(it.get("fix_suggestion", "")),
                    int(it.get("effort_minutes", 0) or 0),
                    wcag_text,
                    str(it.get("selector", "")),
                    str(it.get("source", "")),
                )
            )
        con.executemany(
            """
            INSERT INTO run_issues (
              run_id, rule_id, priority, user_impact, fix_suggestion, effort_minutes, wcag_refs, selector, source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        con.commit()
    finally:
        con.close()


def update_run_summary(db_path: Path, run_id: int, summary: Dict[str, Any], project_name: Optional[str] = None) -> None:
    """Update an existing run with new analysis summary data and optionally project assignment"""
    con = _connect(db_path)
    try:
        con.execute(
            """
            UPDATE run_summaries SET
                total_issues = ?,
                critical_issues = ?,
                high_issues = ?,
                medium_issues = ?,
                low_issues = ?,
                estimated_total_time_minutes = ?,
                ai_enhanced_issues = ?,
                project_name = COALESCE(?, project_name)
            WHERE id = ?
            """,
            (
                summary.get("total_issues", 0),
                summary.get("critical", 0),
                summary.get("serious", 0),
                summary.get("moderate", 0),
                summary.get("minor", 0),
                summary.get("estimated_total_time_minutes", 0),
                summary.get("ai_enhanced_issues", 0),
                project_name,
                run_id,
            ),
        )
        con.commit()
    finally:
        con.close()


def delete_run_issues(db_path: Path, run_id: int) -> None:
    """Delete all issues for a given run"""
    con = _connect(db_path)
    try:
        con.execute("DELETE FROM run_issues WHERE run_id = ?", (run_id,))
        con.commit()
    finally:
        con.close()


def list_run_issues(
    db_path: Path,
    run_id: int,
    severities: Optional[List[str]] = None,
    rule_id: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    con = _connect(db_path)
    try:
        where = ["run_id = ?"]
        args: List[Any] = [run_id]
        if severities:
            placeholders = ",".join(["?"] * len(severities))
            where.append(f"priority IN ({placeholders})")
            args.extend(severities)
        if rule_id:
            where.append("rule_id = ?")
            args.append(rule_id)
        if q:
            like = f"%{q}%"
            where.append("(rule_id LIKE ? OR user_impact LIKE ? OR fix_suggestion LIKE ? OR selector LIKE ?)")
            args.extend([like, like, like, like])
        sql = (
            "SELECT id, rule_id, priority, user_impact, fix_suggestion, effort_minutes, wcag_refs, selector, source, COALESCE(status, 'todo') as status "
            "FROM run_issues WHERE " + " AND ".join(where) + " ORDER BY CASE priority WHEN 'critical' THEN 4 WHEN 'high' THEN 3 WHEN 'medium' THEN 2 ELSE 1 END DESC, rule_id ASC LIMIT ? OFFSET ?"
        )
        args.extend([limit, offset])
        rows = con.execute(sql, tuple(args)).fetchall()
        cols = [
            "id",
            "rule_id",
            "priority",
            "user_impact",
            "fix_suggestion",
            "effort_minutes",
            "wcag_refs",
            "selector",
            "source",
            "status",
        ]
        result = [dict(zip(cols, r)) for r in rows]
        # Split wcag_refs back into list
        for r in result:
            refs = r.get("wcag_refs") or ""
            r["wcag_refs"] = [x for x in str(refs).split(",") if x]
        return result
    finally:
        con.close()


def count_run_issues(
    db_path: Path,
    run_id: int,
    severities: Optional[List[str]] = None,
    rule_id: Optional[str] = None,
    q: Optional[str] = None,
) -> int:
    con = _connect(db_path)
    try:
        where = ["run_id = ?"]
        args: List[Any] = [run_id]
        if severities:
            placeholders = ",".join(["?"] * len(severities))
            where.append(f"priority IN ({placeholders})")
            args.extend(severities)
        if rule_id:
            where.append("rule_id = ?")
            args.append(rule_id)
        if q:
            like = f"%{q}%"
            where.append("(rule_id LIKE ? OR user_impact LIKE ? OR fix_suggestion LIKE ? OR selector LIKE ?)")
            args.extend([like, like, like, like])
        sql = "SELECT COUNT(*) FROM run_issues WHERE " + " AND ".join(where)
        row = con.execute(sql, tuple(args)).fetchone()
        return int(row[0]) if row else 0
    finally:
        con.close()


def update_issue_status(db_path: Path, issue_id: int, status: str, timestamp: Optional[str] = None) -> bool:
    """Update the status of a single issue.
    
    Args:
        db_path: Path to the database
        issue_id: ID of the issue to update
        status: New status (todo, in_progress, done, wont_fix)
        timestamp: ISO timestamp when status changed (optional)
    
    Returns:
        True if update was successful, False otherwise
    """
    con = _connect(db_path)
    try:
        cursor = con.execute(
            "UPDATE run_issues SET status = ?, status_updated_at = ? WHERE id = ?",
            (status, timestamp, issue_id)
        )
        con.commit()
        return cursor.rowcount > 0
    finally:
        con.close()


def bulk_update_issue_status(db_path: Path, issue_ids: List[int], status: str, timestamp: Optional[str] = None) -> int:
    """Update the status of multiple issues at once.
    
    Args:
        db_path: Path to the database
        issue_ids: List of issue IDs to update
        status: New status (todo, in_progress, done, wont_fix)
        timestamp: ISO timestamp when status changed (optional)
    
    Returns:
        Number of issues updated
    """
    if not issue_ids:
        return 0
    
    con = _connect(db_path)
    try:
        placeholders = ",".join(["?"] * len(issue_ids))
        cursor = con.execute(
            f"UPDATE run_issues SET status = ?, status_updated_at = ? WHERE id IN ({placeholders})",
            [status, timestamp, *issue_ids]
        )
        con.commit()
        return cursor.rowcount
    finally:
        con.close()


def get_status_summary(db_path: Path, run_id: int) -> Dict[str, int]:
    """Get a summary of issue statuses for a run.
    
    Args:
        db_path: Path to the database
        run_id: ID of the run
    
    Returns:
        Dictionary with counts for each status
    """
    con = _connect(db_path)
    try:
        rows = con.execute(
            """
            SELECT COALESCE(status, 'todo') as status, COUNT(*) as count
            FROM run_issues
            WHERE run_id = ?
            GROUP BY status
            """,
            (run_id,)
        ).fetchall()
        
        result = {
            'todo': 0,
            'in_progress': 0,
            'done': 0,
            'wont_fix': 0
        }
        
        for row in rows:
            status, count = row
            if status in result:
                result[status] = count
        
        return result
    finally:
        con.close()


# Manual Testing Functions

def insert_checklist(db_path: Path, page_type: str, components: str, checklist_json: str, created_at: str) -> int:
    """Insert a new manual testing checklist."""
    con = _connect(db_path)
    try:
        cur = con.execute(
            """
            INSERT INTO manual_checklists (page_type, components, checklist_json, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (page_type, components, checklist_json, created_at),
        )
        con.commit()
        row_id = cur.lastrowid
        if row_id is None:
            raise ValueError("Failed to insert checklist")
        return int(row_id)
    finally:
        con.close()


def get_checklist(db_path: Path, checklist_id: int) -> Optional[Dict[str, Any]]:
    """Get a checklist by ID."""
    con = _connect(db_path)
    try:
        row = con.execute(
            "SELECT id, page_type, components, checklist_json, created_at FROM manual_checklists WHERE id = ?",
            (checklist_id,),
        ).fetchone()
        if not row:
            return None
        return {
            "id": row[0],
            "page_type": row[1],
            "components": row[2],
            "checklist_json": row[3],
            "created_at": row[4],
        }
    finally:
        con.close()


def create_test_session(db_path: Path, checklist_id: int, tester_name: str, started_at: str, run_id: Optional[int] = None, project_name: str = "Default Project") -> int:
    """Create a new test session."""
    con = _connect(db_path)
    try:
        cur = con.execute(
            """
            INSERT INTO test_sessions (run_id, checklist_id, tester_name, started_at, status, project_name)
            VALUES (?, ?, ?, ?, 'in-progress', ?)
            """,
            (run_id, checklist_id, tester_name, started_at, project_name),
        )
        con.commit()
        row_id = cur.lastrowid
        if row_id is None:
            raise ValueError("Failed to create session")
        return int(row_id)
    finally:
        con.close()


def get_test_session(db_path: Path, session_id: int) -> Optional[Dict[str, Any]]:
    """Get a test session by ID."""
    con = _connect(db_path)
    try:
        row = con.execute(
            "SELECT id, run_id, checklist_id, tester_name, started_at, completed_at, status, project_name FROM test_sessions WHERE id = ?",
            (session_id,),
        ).fetchone()
        if not row:
            return None
        return {
            "id": row[0],
            "run_id": row[1],
            "checklist_id": row[2],
            "tester_name": row[3],
            "started_at": row[4],
            "completed_at": row[5],
            "status": row[6],
            "project_name": row[7] if len(row) > 7 else "Default Project",
        }
    finally:
        con.close()


def list_test_sessions(db_path: Path, limit: int = 50) -> List[Dict[str, Any]]:
    """List all test sessions."""
    con = _connect(db_path)
    try:
        rows = con.execute(
            "SELECT id, run_id, checklist_id, tester_name, started_at, completed_at, status, project_name FROM test_sessions ORDER BY started_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [
            {
                "id": row[0],
                "run_id": row[1],
                "checklist_id": row[2],
                "tester_name": row[3],
                "started_at": row[4],
                "completed_at": row[5],
                "status": row[6],
                "project_name": row[7] if len(row) > 7 else "Default Project",
            }
            for row in rows
        ]
    finally:
        con.close()


def update_test_session(db_path: Path, session_id: int, completed_at: Optional[str] = None, status: Optional[str] = None) -> bool:
    """Update a test session."""
    con = _connect(db_path)
    try:
        updates = []
        params: List[Any] = []
        if completed_at is not None:
            updates.append("completed_at = ?")
            params.append(completed_at)
        if status is not None:
            updates.append("status = ?")
            params.append(status)
        
        if not updates:
            return False
        
        params.append(session_id)
        cursor = con.execute(
            f"UPDATE test_sessions SET {', '.join(updates)} WHERE id = ?",
            params
        )
        con.commit()
        return cursor.rowcount > 0
    finally:
        con.close()


def insert_test_result(db_path: Path, session_id: int, checklist_id: int, item_id: str, status: str, notes: Optional[str], screenshot_path: Optional[str], created_at: str) -> int:
    """Insert a manual test result."""
    con = _connect(db_path)
    try:
        cur = con.execute(
            """
            INSERT INTO manual_test_results (session_id, checklist_id, item_id, status, notes, screenshot_path, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (session_id, checklist_id, item_id, status, notes, screenshot_path, created_at),
        )
        con.commit()
        row_id = cur.lastrowid
        if row_id is None:
            raise ValueError("Failed to insert test result")
        return int(row_id)
    finally:
        con.close()


def get_session_results(db_path: Path, session_id: int) -> List[Dict[str, Any]]:
    """Get all test results for a session."""
    con = _connect(db_path)
    try:
        rows = con.execute(
            "SELECT id, session_id, checklist_id, item_id, status, notes, screenshot_path, created_at FROM manual_test_results WHERE session_id = ? ORDER BY created_at",
            (session_id,),
        ).fetchall()
        return [
            {
                "id": row[0],
                "session_id": row[1],
                "checklist_id": row[2],
                "item_id": row[3],
                "status": row[4],
                "notes": row[5],
                "screenshot_path": row[6],
                "created_at": row[7],
            }
            for row in rows
        ]
    finally:
        con.close()


def update_test_result(db_path: Path, result_id: int, status: Optional[str] = None, notes: Optional[str] = None, screenshot_path: Optional[str] = None) -> bool:
    """Update a test result."""
    con = _connect(db_path)
    try:
        updates = []
        params: List[Any] = []
        if status is not None:
            updates.append("status = ?")
            params.append(status)
        if notes is not None:
            updates.append("notes = ?")
            params.append(notes)
        if screenshot_path is not None:
            updates.append("screenshot_path = ?")
            params.append(screenshot_path)
        
        if not updates:
            return False
        
        params.append(result_id)
        cursor = con.execute(
            f"UPDATE manual_test_results SET {', '.join(updates)} WHERE id = ?",
            params
        )
        con.commit()
        return cursor.rowcount > 0
    finally:
        con.close()


def delete_scan(db_path: Path, scan_id: int) -> bool:
    """Delete a scan and all its associated issues (CASCADE)"""
    con = sqlite3.connect(db_path)
    try:
        # Enable foreign keys to make CASCADE work
        con.execute("PRAGMA foreign_keys = ON")
        cursor = con.execute("DELETE FROM run_summaries WHERE id = ?", (scan_id,))
        con.commit()
        return cursor.rowcount > 0
    finally:
        con.close()


def delete_manual_test_session(db_path: Path, session_id: int) -> bool:
    """Delete a manual test session and all its results (CASCADE)"""
    con = sqlite3.connect(db_path)
    try:
        # Enable foreign keys to make CASCADE work
        con.execute("PRAGMA foreign_keys = ON")
        cursor = con.execute("DELETE FROM test_sessions WHERE id = ?", (session_id,))
        con.commit()
        return cursor.rowcount > 0
    finally:
        con.close()


def delete_checklist(db_path: Path, checklist_id: int) -> bool:
    """Delete a manual checklist"""
    con = sqlite3.connect(db_path)
    try:
        cursor = con.execute("DELETE FROM manual_checklists WHERE id = ?", (checklist_id,))
        con.commit()
        return cursor.rowcount > 0
    finally:
        con.close()


def get_fix_metrics(db_path: Path) -> Dict[str, Any]:
    """Get fix turnaround metrics for analytics.
    
    Returns:
        Dictionary with:
        - avg_fix_time_hours: Average hours to fix (from created_at to status_updated_at when status='done')
        - fix_rate: Percentage of issues marked as done
        - total_issues: Total number of issues
        - fixed_issues: Number of issues marked as done
        - avg_by_severity: Average fix time grouped by priority
    """
    con = _connect(db_path)
    try:
        # Calculate average fix time in hours for completed issues
        cursor = con.execute("""
            SELECT 
                AVG((julianday(status_updated_at) - julianday(created_at)) * 24) as avg_hours
            FROM run_issues
            WHERE status = 'done' 
                AND created_at IS NOT NULL 
                AND status_updated_at IS NOT NULL
        """)
        result = cursor.fetchone()
        avg_fix_time = round(result[0], 2) if result[0] else 0
        
        # Get total and fixed counts
        cursor = con.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'done' THEN 1 ELSE 0 END) as fixed
            FROM run_issues
        """)
        total, fixed = cursor.fetchone()
        fix_rate = round((fixed / total * 100), 1) if total > 0 else 0
        
        # Get average fix time by severity
        cursor = con.execute("""
            SELECT 
                priority,
                AVG((julianday(status_updated_at) - julianday(created_at)) * 24) as avg_hours,
                COUNT(*) as count
            FROM run_issues
            WHERE status = 'done' 
                AND created_at IS NOT NULL 
                AND status_updated_at IS NOT NULL
            GROUP BY priority
        """)
        by_severity = [
            {
                "priority": row[0],
                "avg_fix_time_hours": round(row[1], 2) if row[1] else 0,
                "count": row[2]
            }
            for row in cursor.fetchall()
        ]
        
        return {
            "avg_fix_time_hours": avg_fix_time,
            "fix_rate": fix_rate,
            "total_issues": total,
            "fixed_issues": fixed,
            "avg_by_severity": by_severity
        }
    finally:
        con.close()


# ============================================================================
# MANUAL BUG TRACKING FUNCTIONS
# ============================================================================

def create_manual_bug(
    db_path: Path,
    title: str,
    wcag_criterion: str,
    severity: str,
    testing_tool: str,
    description: str,
    expected_behavior: str,
    actual_behavior: str,
    project_name: str = "Default Project",
    run_id: Optional[int] = None,
    steps_to_reproduce: Optional[str] = None,
    affected_user_groups: Optional[str] = None,
    notes: Optional[str] = None,
    created_by: Optional[str] = None
) -> int:
    """Create a new manual bug report."""
    from datetime import datetime, timezone
    
    con = _connect(db_path)
    try:
        created_at = datetime.now(timezone.utc).isoformat()
        cursor = con.execute(
            """INSERT INTO manual_bugs (
                title, wcag_criterion, severity, testing_tool, description,
                expected_behavior, actual_behavior, steps_to_reproduce,
                affected_user_groups, notes, project_name, run_id,
                created_at, created_by, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'open')""",
            (
                title, wcag_criterion, severity, testing_tool, description,
                expected_behavior, actual_behavior, steps_to_reproduce,
                affected_user_groups, notes, project_name, run_id,
                created_at, created_by
            )
        )
        con.commit()
        bug_id = cursor.lastrowid
        if bug_id is None:
            raise ValueError("Failed to create bug")
        return int(bug_id)
    finally:
        con.close()


def add_bug_evidence(
    db_path: Path,
    bug_id: int,
    file_path: str,
    file_type: str,
    file_size: int
) -> int:
    """Add evidence file to a bug report."""
    from datetime import datetime, timezone
    
    con = _connect(db_path)
    try:
        uploaded_at = datetime.now(timezone.utc).isoformat()
        cursor = con.execute(
            """INSERT INTO bug_evidence (bug_id, file_path, file_type, file_size, uploaded_at)
               VALUES (?, ?, ?, ?, ?)""",
            (bug_id, file_path, file_type, file_size, uploaded_at)
        )
        con.commit()
        evidence_id = cursor.lastrowid
        if evidence_id is None:
            raise ValueError("Failed to add evidence")
        return int(evidence_id)
    finally:
        con.close()


def get_bug_projects(db_path: Path) -> List[str]:
    """Get list of unique project names from bugs."""
    con = _connect(db_path)
    try:
        query = """
            SELECT DISTINCT project_name 
            FROM manual_bugs 
            WHERE project_name IS NOT NULL 
            ORDER BY project_name
        """
        rows = con.execute(query).fetchall()
        return [r[0] for r in rows if r[0]]
    finally:
        con.close()


def list_manual_bugs(
    db_path: Path,
    project_name: Optional[str] = None,
    testing_tool: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """List manual bugs with optional filters."""
    con = _connect(db_path)
    try:
        query = """
            SELECT 
                b.id, b.title, b.wcag_criterion, b.severity, b.testing_tool,
                b.description, b.expected_behavior, b.actual_behavior,
                b.steps_to_reproduce, b.affected_user_groups, b.notes,
                b.project_name, b.run_id, b.created_at, b.created_by,
                COUNT(e.id) as evidence_count
            FROM manual_bugs b
            LEFT JOIN bug_evidence e ON b.id = e.bug_id
            WHERE 1=1
        """
        params: List[Any] = []
        
        if project_name:
            query += " AND b.project_name = ?"
            params.append(project_name)
        if testing_tool:
            query += " AND b.testing_tool = ?"
            params.append(testing_tool)
        if severity:
            query += " AND b.severity = ?"
            params.append(severity)
        query += " GROUP BY b.id ORDER BY b.created_at DESC LIMIT ?"
        params.append(limit)
        
        rows = con.execute(query, params).fetchall()
        return [
            {
                "id": r[0],
                "title": r[1],
                "wcag_criterion": r[2],
                "severity": r[3],
                "testing_tool": r[4],
                "description": r[5],
                "expected_behavior": r[6],
                "actual_behavior": r[7],
                "steps_to_reproduce": r[8],
                "affected_user_groups": r[9],
                "notes": r[10],
                "project_name": r[11],
                "run_id": r[12],
                "created_at": r[13],
                "created_by": r[14],
                "evidence_count": r[15]
            }
            for r in rows
        ]
    finally:
        con.close()


def get_manual_bug(db_path: Path, bug_id: int) -> Optional[Dict[str, Any]]:
    """Get a single bug with evidence files."""
    con = _connect(db_path)
    try:
        # Get bug details
        row = con.execute(
            """SELECT 
                id, title, wcag_criterion, severity, testing_tool,
                description, expected_behavior, actual_behavior,
                steps_to_reproduce, affected_user_groups, notes,
                project_name, run_id, created_at, created_by
               FROM manual_bugs WHERE id = ?""",
            (bug_id,)
        ).fetchone()
        
        if not row:
            return None
            
        # Get evidence files
        evidence_rows = con.execute(
            """SELECT id, file_path, file_type, file_size, uploaded_at
               FROM bug_evidence WHERE bug_id = ?""",
            (bug_id,)
        ).fetchall()
        
        return {
            "id": row[0],
            "title": row[1],
            "wcag_criterion": row[2],
            "severity": row[3],
            "testing_tool": row[4],
            "description": row[5],
            "expected_behavior": row[6],
            "actual_behavior": row[7],
            "steps_to_reproduce": row[8],
            "affected_user_groups": row[9],
            "notes": row[10],
            "project_name": row[11],
            "run_id": row[12],
            "created_at": row[13],
            "created_by": row[14],
            "evidence": [
                {
                    "id": e[0],
                    "file_path": e[1],
                    "file_type": e[2],
                    "file_size": e[3],
                    "uploaded_at": e[4]
                }
                for e in evidence_rows
            ]
        }
    finally:
        con.close()


def delete_manual_bug(db_path: Path, bug_id: int) -> bool:
    """Delete a bug and its evidence (CASCADE)."""
    con = _connect(db_path)
    try:
        cursor = con.execute("DELETE FROM manual_bugs WHERE id = ?", (bug_id,))
        con.commit()
        return cursor.rowcount > 0
    finally:
        con.close()


def get_testing_method_stats(db_path: Path, project_name: Optional[str] = None) -> Dict[str, Any]:
    """Get statistics for each testing method (NVDA, Keyboard, Zoom)."""
    con = _connect(db_path)
    try:
        query = """
            SELECT 
                testing_tool,
                COUNT(*) as bug_count,
                MAX(created_at) as last_tested
            FROM manual_bugs
            WHERE 1=1
        """
        params: List[Any] = []
        
        if project_name:
            query += " AND project_name = ?"
            params.append(project_name)
            
        query += " GROUP BY testing_tool"
        
        rows = con.execute(query, params).fetchall()
        
        stats = {}
        for row in rows:
            stats[row[0]] = {
                "bug_count": row[1],
                "last_tested": row[2]
            }
        
        return stats
    finally:
        con.close()
