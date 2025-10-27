from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional


SCHEMA_SQL = """
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
  ai_enhanced_issues INTEGER NOT NULL
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
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS test_sessions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id INTEGER,
  checklist_id INTEGER NOT NULL,
  tester_name TEXT NOT NULL,
  started_at TEXT NOT NULL,
  completed_at TEXT,
  status TEXT DEFAULT 'in-progress',
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
"""


def _connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(db_path))
    con.execute("PRAGMA journal_mode=WAL;")
    con.execute("PRAGMA synchronous=NORMAL;")
    con.executescript(SCHEMA_SQL)
    return con


def insert_run_returning_id(db_path: Path, summary: Dict[str, Any], url: str, framework: str, ts_iso: str) -> int:
    con = _connect(db_path)
    try:
        cur = con.execute(
            """
            INSERT INTO run_summaries (
                ts, url, framework,
                total_issues, critical_issues, high_issues, medium_issues, low_issues,
                estimated_total_time_minutes, ai_enhanced_issues
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            "SELECT id, ts, url, framework, total_issues, critical_issues, high_issues, medium_issues, low_issues, estimated_total_time_minutes, ai_enhanced_issues FROM run_summaries WHERE id = ?",
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
        ]
        return dict(zip(cols, row))
    finally:
        con.close()


def list_runs(db_path: Path, limit: int = 100) -> List[Dict[str, Any]]:
    con = _connect(db_path)
    try:
        rows = con.execute(
            "SELECT id, ts, url, framework, total_issues, critical_issues, high_issues, medium_issues, low_issues, estimated_total_time_minutes, ai_enhanced_issues FROM run_summaries ORDER BY ts DESC LIMIT ?",
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
        ]
        return [dict(zip(cols, r)) for r in rows]
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


def update_issue_status(db_path: Path, issue_id: int, status: str) -> bool:
    """Update the status of a single issue.
    
    Args:
        db_path: Path to the database
        issue_id: ID of the issue to update
        status: New status (todo, in_progress, done, wont_fix)
    
    Returns:
        True if update was successful, False otherwise
    """
    con = _connect(db_path)
    try:
        cursor = con.execute(
            "UPDATE run_issues SET status = ? WHERE id = ?",
            (status, issue_id)
        )
        con.commit()
        return cursor.rowcount > 0
    finally:
        con.close()


def bulk_update_issue_status(db_path: Path, issue_ids: List[int], status: str) -> int:
    """Update the status of multiple issues at once.
    
    Args:
        db_path: Path to the database
        issue_ids: List of issue IDs to update
        status: New status (todo, in_progress, done, wont_fix)
    
    Returns:
        Number of issues updated
    """
    if not issue_ids:
        return 0
    
    con = _connect(db_path)
    try:
        placeholders = ",".join(["?"] * len(issue_ids))
        cursor = con.execute(
            f"UPDATE run_issues SET status = ? WHERE id IN ({placeholders})",
            [status, *issue_ids]
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


def create_test_session(db_path: Path, checklist_id: int, tester_name: str, started_at: str, run_id: Optional[int] = None) -> int:
    """Create a new test session."""
    con = _connect(db_path)
    try:
        cur = con.execute(
            """
            INSERT INTO test_sessions (run_id, checklist_id, tester_name, started_at, status)
            VALUES (?, ?, ?, ?, 'in-progress')
            """,
            (run_id, checklist_id, tester_name, started_at),
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
            "SELECT id, run_id, checklist_id, tester_name, started_at, completed_at, status FROM test_sessions WHERE id = ?",
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
        }
    finally:
        con.close()


def list_test_sessions(db_path: Path, limit: int = 50) -> List[Dict[str, Any]]:
    """List all test sessions."""
    con = _connect(db_path)
    try:
        rows = con.execute(
            "SELECT id, run_id, checklist_id, tester_name, started_at, completed_at, status FROM test_sessions ORDER BY started_at DESC LIMIT ?",
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
