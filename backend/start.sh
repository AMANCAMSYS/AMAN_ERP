#!/bin/bash
# AMAN ERP - Start Script

echo "🚀 Starting AMAN ERP System..."

# 1. Start Backend
echo "📡 Starting Backend..."
cd "$(dirname "$0")"
source venv/bin/activate
nohup uvicorn main:app --host 0.0.0.0 --port 8000 --reload > backend.log 2>&1 &
echo "✅ Backend started in background (PID: $!)"

# 2. Start Frontend
echo "💻 Starting Frontend..."
cd ../frontend
nohup npm run dev > ../backend/frontend.log 2>&1 &
echo "✅ Frontend started in background (PID: $!)"

echo ""
echo "✨ AMAN ERP is running!"
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:5173"
echo "Check logs: tail -f backend/backend.log"
