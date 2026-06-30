@echo off
REM Conversational BI Assistant - Startup Script for Windows

echo.
echo ====================================================
echo   Conversational BI Assistant - Quick Start
echo ====================================================
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate

REM Install requirements
echo Installing dependencies...
pip install -r requirements.txt

REM Generate sample data if not exists
if not exist "data\sales_data.db" (
    echo Generating sample data...
    python data\sample_data.py
)

REM Start backend
echo.
echo ====================================================
echo Starting Flask backend on http://localhost:5000
echo ====================================================
echo.
echo Press Ctrl+C to stop the server
echo.

python backend\app.py

pause
