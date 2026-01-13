#!/bin/bash
# Due Diligence Tracker Startup Script

echo "🏢 Due Diligence Tracker for CRE"
echo "================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install/upgrade requirements
echo "📥 Installing dependencies..."
pip install -q -r requirements.txt

# Start the application
echo ""
echo "🚀 Starting Due Diligence Tracker..."
echo "   Access the app at: http://localhost:8501"
echo ""
streamlit run app.py
