@echo off
REM Windows batch test runner: creates venv, installs deps, runs pytest and logs output
python -m venv .venv
call .venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt
if not exist logs mkdir logs
pytest -q > logs\test_run.log 2>&1
