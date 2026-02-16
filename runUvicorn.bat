@echo off
REM Set environment variables
set ENV=dev
python -m backend.run_uvicorn_windows
pause