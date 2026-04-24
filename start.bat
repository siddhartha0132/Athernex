@echo off
echo ============================================================
echo   AI Voice Call System - Startup Script
echo ============================================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo [ERROR] Virtual environment not found!
    echo Please run: python -m venv venv
    echo Then run: venv\Scripts\activate
    echo Then run: pip install -r requirements.txt
    pause
    exit /b 1
)

REM Check if .env exists
if not exist ".env" (
    echo [ERROR] .env file not found!
    echo Please copy .env.example to .env and fill in your credentials
    pause
    exit /b 1
)

echo [1/3] Activating virtual environment...
call venv\Scripts\activate

echo [2/3] Checking dependencies...
python -c "import flask, twilio, requests, dotenv" 2>nul
if errorlevel 1 (
    echo [ERROR] Dependencies not installed!
    echo Please run: pip install -r requirements.txt
    pause
    exit /b 1
)

echo [3/3] Starting Flask server...
echo.
echo ============================================================
echo   Server will start on http://localhost:5000
echo   Press Ctrl+C to stop
echo ============================================================
echo.
echo IMPORTANT: In another terminal, run: ngrok http 5000
echo.

python app.py

pause
