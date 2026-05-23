#!/bin/bash
cd /Users/halituzun/Projects/Senitnal
source .env 2>/dev/null
export DEEPSEEK_API_KEY=sk-0e371d544bc1440bb19de3da845d8387
export TAAPI_API_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjbHVlIjoiNmEwNDgyNzNlZTAzMzMxMWE0NDE5ODBhIiwiaWF0IjoxNzc5MDE4NzY3LCJleHAiOjMzMjgzNDgyNzY3fQ.3Zr5FRkSM-u_WN6DM8B2K3T5BKQPT4K_9C-VejBphBM"

echo "=== STARTING SENTINEL ==="

# API
cd panel/api
nohup npx tsx src/index.ts > /tmp/api.log 2>&1 &
echo "API PID: $!"

# Web
cd /Users/halituzun/Projects/Senitnal/panel/web
nohup npx vite --port 5173 > /tmp/web.log 2>&1 &
echo "Web PID: $!"

# Learning loop
cd /Users/halituzun/Projects/Senitnal
nohup uv run python scripts/run_learning_loop.py --interval 10 > /tmp/learn.log 2>&1 &
echo "Learn PID: $!"

sleep 4
PASS=$(grep "Password:" /tmp/api.log 2>/dev/null | tail -1 | sed 's/.*Password: //' | sed 's/ *║//' | xargs)
echo ""
echo "╔══════════════════════════════════╗"
echo "║  Panel: http://localhost:5173    ║"
echo "║  Email: panel@senitnal.local     ║"
echo "║  Pass:  ${PASS:-senitnal2026}    ║"
echo "╚══════════════════════════════════╝"
