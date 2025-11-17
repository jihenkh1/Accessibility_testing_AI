from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from backend.services import db as dbsvc


router = APIRouter()
DB_PATH = Path("data/a11y_runs.sqlite")


@router.get("/fix-metrics")
def get_fix_metrics() -> Dict[str, Any]:
    """Get fix turnaround time metrics.
    
    Returns:
        - avg_fix_time_hours: Average hours to fix issues
        - fix_rate: Percentage of issues marked as done
        - total_issues: Total number of issues
        - fixed_issues: Number of issues marked as done
        - avg_by_severity: Average fix time grouped by priority
    """
    try:
        metrics = dbsvc.get_fix_metrics(DB_PATH)
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
