@echo off
if not exist logs mkdir logs
powershell -Command "pytest -q | Tee-Object -FilePath logs\\test_run.log"
