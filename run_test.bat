@echo off
setlocal enabledelayedexpansion
if exist .venv\Scripts\activate (
    call .venv\Scripts\activate
)
md logs 2>nul || rem
pytest -q 2>&1 | tee logs\test_run.log
