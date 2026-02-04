#!/bin/bash
# Setup script for Windows (PowerShell compatible)
# This script can be called from PowerShell with: bash setup.sh

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "=== Flask SearchableMixin Event Binding - Setup ===" -ForegroundColor Green
Write-Host "OS: Windows"
Write-Host ""

# Check Python version
$pythonVersion = (python --version 2>&1) -split ' ' | Select-Object -Last 1
Write-Host "Python version: $pythonVersion"

# Create virtual environment if it doesn't exist
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv venv
} else {
    Write-Host "Virtual environment already exists."
}

# Activate virtual environment
Write-Host "Activating virtual environment..."
& ".\venv\Scripts\Activate.ps1"

# Upgrade pip
Write-Host "Upgrading pip..."
python -m pip install --upgrade pip setuptools wheel

# Install requirements
Write-Host "Installing dependencies..."
pip install -r requirements.txt

Write-Host ""
Write-Host "=== Setup Complete ===" -ForegroundColor Green
Write-Host "To activate the virtual environment, run:"
Write-Host "  .\venv\Scripts\Activate.ps1"
Write-Host ""
Write-Host "To run tests, use:"
Write-Host "  .\run_test.bat"
