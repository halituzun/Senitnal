#!/usr/bin/env bash
# Start panel dev servers (API + Web)
# Usage: ./panel/scripts/dev.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PANEL_DIR="$(dirname "$SCRIPT_DIR")"

echo "Installing dependencies..."
cd "$PANEL_DIR"
pnpm install

echo ""
echo "Starting Senitnal Panel (dev mode)"
echo "  API  → http://localhost:3787"
echo "  Web  → http://localhost:5173"
echo "  Proxy→ http://localhost:5173 (API proxied via Vite)"
echo ""
echo "Credentials will be shown in the API output below."
echo ""

# Start API
cd "$PANEL_DIR/api"
pnpm dev &
API_PID=$!

# Start Web
cd "$PANEL_DIR/web"
pnpm dev &
WEB_PID=$!

# Trap Ctrl+C
trap "kill $API_PID $WEB_PID 2>/dev/null; exit 0" INT TERM

wait
