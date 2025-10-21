
## AI Accessibility Analyzer — Backend & Frontend

This project analyzes accessibility scan output (axe-core/Pa11y) and enriches it with AI to produce a prioritized backlog.

### Secrets & Configuration

- Create a `.env` at the repo root (not committed):
  - `OPENROUTER_API_KEY=sk-or-...`
  - `OPENROUTER_MODEL=deepseek/deepseek-chat`
  - `OPENROUTER_BASE_URL=https://openrouter.ai/api/v1`
  - `OPENROUTER_TIMEOUT=30`
- Environment variables override `.env` when set.
- Optionally, you can provide secrets via `.secrets.json` (flat JSON object with key/value pairs).

Resolution order used by the AI client:
1. Environment variables
2. `.env` (loaded via python-dotenv, if installed)
3. Optional local secrets file: `.secrets.json`

### Backend (FastAPI)

- Install deps: `pip install -r requirements.txt`
- Run: `uvicorn backend.main:app --reload --port 8000`
- API endpoints:
  - `POST /api/scans` — analyze a scan JSON
  - `GET /api/scans` — list summaries
  - `GET /api/scans/{id}` — get a stored summary

### Frontend (React + Vite + Tailwind)

- `cd frontend`
- `npm install`
- `npm run dev` (Vite proxies `/api` to `http://localhost:8000`)

### Notes

- The AI logic lives in `src/accessibility_ai/` and is reused by the FastAPI service.
- Reflex and Streamlit have been removed from the project.
