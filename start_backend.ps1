# Start backend from root directory
& .\.venv-1\Scripts\Activate.ps1
python -m uvicorn backend.main:app --reload
