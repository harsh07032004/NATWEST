@echo off
echo Starting all servers...

start cmd /k "cd backend && npm run dev"
start cmd /k "cd execution_engine && uvicorn src.main:app --reload --port 8000"
start cmd /k "cd frontend && npm run dev -- --port 3000"

echo All servers starting up!
