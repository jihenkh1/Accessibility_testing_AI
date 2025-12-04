from __future__ import annotations

import sys
from pathlib import Path

from fastapi import FastAPI

# Ensure repo root on sys.path to import analyzer code
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.api.routes.scans import router as scans_router  # noqa: E402
from backend.api.routes.manual_testing_v2 import router as manual_testing_v2_router  # noqa: E402
from backend.api.routes.analytics import router as analytics_router  # noqa: E402


def create_app() -> FastAPI:
    app = FastAPI(title="AI Accessibility Analyzer API", version="0.1.0")
    app.include_router(scans_router, prefix="/api")
    app.include_router(manual_testing_v2_router)  # Streamlined bug-focused manual testing
    app.include_router(analytics_router, prefix="/api/analytics")
    return app


app = create_app()

