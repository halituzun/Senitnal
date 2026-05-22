#!/usr/bin/env python3
"""Local proxy: Claude Desktop -> DeepSeek API with model name mapping."""
import json
import sys
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
import urllib.request
import urllib.error

DEEPSEEK_URL = "https://api.deepseek.com/anthropic"
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "sk-4f44e968a3714881bb22e77831bb1a01")
LISTEN_PORT = 8765

MODEL_MAP = {
    "claude-sonnet-4-6": "deepseek-v4-pro[1m]",
    "claude-opus-4-7": "deepseek-v4-pro[1m]",
    "claude-haiku-4-5": "deepseek-v4-flash",
    "claude-sonnet-4-5": "deepseek-v4-pro[1m]",
    "claude-opus-4-6": "deepseek-v4-pro[1m]",
    "claude-opus-4-5": "deepseek-v4-pro[1m]",
    "claude-sonnet-4": "deepseek-v4-pro[1m]",
    "claude-haiku-4": "deepseek-v4-flash",
    "claude-sonnet": "deepseek-v4-pro[1m]",
    "claude-opus": "deepseek-v4-pro[1m]",
    "claude-haiku": "deepseek-v4-flash",
}

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

class ProxyHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            req_data = json.loads(body)

            model = req_data.get("model", "")
            if model in MODEL_MAP:
                req_data["model"] = MODEL_MAP[model]

            forward_body = json.dumps(req_data).encode("utf-8")
            forward_url = DEEPSEEK_URL + self.path

            req = urllib.request.Request(
                forward_url, data=forward_body,
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": DEEPSEEK_API_KEY,
                },
                method="POST",
            )

            model = req_data.get("model", "?")
            has_tools = "tools" in req_data
            print(f"[proxy] -> {model} (tools={has_tools})", file=sys.stderr, flush=True)

            with urllib.request.urlopen(req, timeout=180) as resp:
                resp_body = resp.read()
                resp_text = resp_body.decode("utf-8", errors="replace")
                if "stop_reason" in resp_text[:500]:
                    sr = resp_text.split('"stop_reason"')[1][:30] if '"stop_reason"' in resp_text else "?"
                    print(f"[proxy] <- 200 stop={sr}", file=sys.stderr, flush=True)
                self.send_response(resp.status)
                for k, v in resp.getheaders():
                    if k.lower() not in ("transfer-encoding", "connection"):
                        self.send_header(k, v)
                self.end_headers()
                self.wfile.write(resp_body)
        except urllib.error.HTTPError as e:
            err_body = e.read()
            print(f"[proxy] <- {e.code} {e.reason}", file=sys.stderr, flush=True)
            self.send_response(e.code)
            self.end_headers()
            self.wfile.write(err_body)
        except Exception as e:
            print(f"[proxy] POST error: {e}", file=sys.stderr, flush=True)
            self.send_response(502)
            self.end_headers()
            self.wfile.write(b'{"error":"proxy error"}')

    def do_GET(self):
        try:
            if self.path.startswith("/v1/models"):
                models = {
                    "object": "list",
                    "data": [
                        {"id": k, "object": "model", "created": 1, "owned_by": "proxy"}
                        for k in MODEL_MAP
                    ],
                }
                body = json.dumps(models).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(body)
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"{}")
        except Exception as e:
            print(f"[proxy] GET error: {e}", file=sys.stderr, flush=True)

    def log_message(self, format, *args):
        print(f"[proxy] {format % args}", file=sys.stderr, flush=True)

if __name__ == "__main__":
    print(f"[proxy] http://localhost:{LISTEN_PORT} (models: {len(MODEL_MAP)})", file=sys.stderr, flush=True)
    server = ThreadedHTTPServer(("127.0.0.1", LISTEN_PORT), ProxyHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("[proxy] stopped", file=sys.stderr, flush=True)
