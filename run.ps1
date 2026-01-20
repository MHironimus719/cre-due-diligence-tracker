# Due Diligence Tracker Startup Script for PowerShell

Write-Host "🏢 Due Diligence Tracker for CRE" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (-not (Test-Path "venv")) {
    Write-Host "📦 Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
Write-Host "🔄 Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# Install/upgrade requirements
Write-Host "📥 Installing dependencies..." -ForegroundColor Yellow
pip install -q -r requirements.txt

# Start the application
Write-Host ""
Write-Host "🚀 Starting Due Diligence Tracker..." -ForegroundColor Green
Write-Host "   Access the app at: http://localhost:8501" -ForegroundColor Green
Write-Host ""
streamlit run app.py
