import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional


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
"""


def _connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(db_path))
    con.execute("PRAGMA journal_mode=WAL;")
    con.execute("PRAGMA synchronous=NORMAL;")
    con.execute(SCHEMA_SQL)
    return con


def insert_run(db_path: Path, summary: Dict[str, Any], url: str, framework: str, ts_iso: str) -> None:
    con = _connect(db_path)
    try:
        con.execute(
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
    finally:
        con.close()


def list_runs(db_path: Path, limit: int = 200) -> List[Dict[str, Any]]:
    con = _connect(db_path)
    try:
        rows = con.execute(
            "SELECT ts, url, framework, total_issues, critical_issues, high_issues, medium_issues, low_issues, estimated_total_time_minutes, ai_enhanced_issues FROM run_summaries ORDER BY ts DESC LIMIT ?",
            (limit,),
        ).fetchall()
        cols = [
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

