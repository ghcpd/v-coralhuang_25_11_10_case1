@echo off
REM Test runner for Windows
REM This script sets up the environment and runs tests

setlocal enabledelayedexpansion
cd /d "%~dp0"

REM Create logs directory if it doesn't exist
if not exist "logs" mkdir logs

echo ===Flask SearchableMixin Event Binding - Test Runner===
echo OS: Windows
echo.

REM Check if venv exists
if exist "venv\" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo Warning: Virtual environment not found. Using system Python.
)

REM Check if pytest is installed
python -m pytest --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: pytest not found. Please run setup.bat first.
    exit /b 1
)

echo Python: 
python --version
echo.
echo pytest:
python -m pytest --version
echo.

echo Running tests with coverage report...
python -m pytest test_search_events.py -v --tb=short --cov=. --cov-report=html --cov-report=term 2>&1 | tee logs\test_run.log

set TEST_RESULT=%errorlevel%

echo.
echo ===Test Execution Complete===
echo Log file: logs\test_run.log
echo Coverage report: htmlcov\index.html

exit /b %TEST_RESULT%
