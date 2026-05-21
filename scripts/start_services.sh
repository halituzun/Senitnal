#!/bin/bash
set -e
cd "$(dirname "$0")/.."

# Load env
[ -f .env ] && export $(grep -v '^#' .env | xargs)

# Kill existing
lsof -ti:3787 | xargs kill -9 2>/dev/null || true
sleep 1

# Start API
cd panel/api && nohup npx tsx src/index.ts > /tmp/api.log 2>&1 &
sleep 3

# Start learning loop  
cd ../.. && nohup uv run python scripts/run_learning_loop.py --interval 10 > /tmp/learn.log 2>&1 &

sleep 4
echo "=== Learning loop ==="
head -5 /tmp/learn.log 2>/dev/null || echo "(starting...)"
echo ""
echo "=== API ==="
grep "Password" /tmp/api.log 2>/dev/null
