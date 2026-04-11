#!/bin/bash
echo "=========================================================="
echo "Task Flow Platform - Linux Deployment Script (Linux/Mac)"
echo "=========================================================="

echo "[1/3] Building Frontend Application (Vue 3 + Vite)..."
cd frontend
npm install
npm run build
if [ $? -ne 0 ]; then
    echo "Frontend build failed!"
    exit 1
fi
cd ..

echo ""
echo "[2/3] Setting up Backend Python Environment..."
cd backend
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi
source venv/bin/activate
echo "Installing Python dependencies..."
pip install fastapi uvicorn peewee python-multipart aiofiles

echo ""
echo "[3/3] Starting Unified Server on Port 8000..."
echo "-------------------------------------------------------------"
echo "DEPLOYMENT SUCCESSFUL!"
echo "You can now access the application from any computer on your network"
echo "via: http://<YOUR_LINUX_IP_ADDRESS>:8000"
echo "-------------------------------------------------------------"
python -m uvicorn main:app --host 0.0.0.0 --port 8000
