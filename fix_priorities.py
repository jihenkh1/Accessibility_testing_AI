#!/usr/bin/env python3
"""Fix priority values in the database from Priority.CRITICAL to critical format."""

import sqlite3
from pathlib import Path

DB_PATH = Path("data/a11y_runs.sqlite")

def main():
    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}")
        return
    
    con = sqlite3.connect(DB_PATH)
    cursor = con.cursor()
    
    # Check current values
    cursor.execute("SELECT DISTINCT priority FROM run_issues")
    current_values = [row[0] for row in cursor.fetchall()]
    print(f"Current priority values: {current_values}")
    
    # Update priority values
    updates = [
        ("Priority.CRITICAL", "critical"),
        ("Priority.HIGH", "high"),
        ("Priority.MEDIUM", "medium"),
        ("Priority.LOW", "low"),
    ]
    
    total_updated = 0
    for old_val, new_val in updates:
        cursor.execute("UPDATE run_issues SET priority = ? WHERE priority = ?", (new_val, old_val))
        count = cursor.rowcount
        if count > 0:
            print(f"Updated {count} rows from '{old_val}' to '{new_val}'")
            total_updated += count
    
    con.commit()
    
    # Verify changes
    cursor.execute("SELECT DISTINCT priority FROM run_issues")
    new_values = [row[0] for row in cursor.fetchall()]
    print(f"\nNew priority values: {new_values}")
    print(f"Total rows updated: {total_updated}")
    
    con.close()
    print("\n✅ Migration complete!")

if __name__ == "__main__":
    main()
