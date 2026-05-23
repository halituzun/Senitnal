#!/usr/bin/env python3
"""Daemon to keep learning loop running via uv."""
import os, sys, time
os.environ.update({
    "DEEPSEEK_API_KEY": "sk-0e371d544bc1440bb19de3da845d8387",
    "TAAPI_API_KEY": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjbHVlIjoiNmEwNDgyNzNlZTAzMzMxMWE0NDE5ODBhIiwiaWF0IjoxNzc5MDE4NzY3LCJleHAiOjMzMjgzNDgyNzY3fQ.3Zr5FRkSM-u_WN6DM8B2K3T5BKQPT4K_9C-VejBphBM",
    "BINANCE_API_KEY": "ZuhqT8tTfLJBHNS1EsImUqTCq7aVkSZtmAC8CfTIR3uDrs3xnRWD2z0dzJhTEuok",
    "BINANCE_API_SECRET": "fF9kZmKEChWugf6nKt9ba1nShHH6T6ieE0HeozFewNuYgvo16FAzKt7oKWfQZYn3",
    "BINANCE_LIVE_TRADING": "true",
    "BTCTURK_PUBLIC_KEY": "10b71708-9cef-4d17-901a-786cefd8b2f3",
    "BTCTURK_PRIVATE_KEY": "fEMbkX9r5N6WfX+GfkiE6GweRSlREd08",
})
os.chdir("/Users/halituzun/Projects/Senitnal")
log = open("/tmp/learn_daemon.log", "w")
p = subprocess.Popen(
    ["uv", "run", "python", "scripts/run_learning_loop.py", "--interval", "10"],
    stdout=log, stderr=log, env=os.environ,
)
print(f"Daemon started PID={p.pid} at {time.ctime()}")
p.wait()
