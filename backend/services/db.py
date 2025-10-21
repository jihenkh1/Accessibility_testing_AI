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
