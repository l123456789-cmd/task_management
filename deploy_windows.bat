@echo off
echo ========================================================
echo Task Flow Platform - Windows Deployment Script (Windows)
echo ========================================================

echo [1/3] Building Frontend Application (Vue 3 + Vite)...
cd frontend
call npm install
call npm run build
if %errorlevel% neq 0 (
    echo Frontend build failed!
    pause
    exit /b %errorlevel%
)
cd ..

echo.
echo [2/3] Setting up Backend Python Environment...
cd backend
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)
call venv\Scripts\activate.bat
echo Installing dependencies...
pip install fastapi uvicorn peewee python-multipart aiofiles

echo.
echo [3/3] Starting Unified Server on Port 8000...
echo -------------------------------------------------------------
echo DEPLOYMENT SUCCESSFUL!
echo You can now access the application from any computer on your LAN 
echo via: http://^<YOUR_WINDOWS_IP_ADDRESS^>:8000
echo -------------------------------------------------------------
python -m uvicorn main:app --host 0.0.0.0 --port 8000
pause
