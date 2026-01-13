@echo off
REM Due Diligence Tracker Startup Script for Windows

echo 🏢 Due Diligence Tracker for CRE
echo ================================
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo 🔄 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/upgrade requirements
echo 📥 Installing dependencies...
pip install -q -r requirements.txt

REM Start the application
echo.
echo 🚀 Starting Due Diligence Tracker...
echo    Access the app at: http://localhost:8501
echo.
streamlit run app.py
