#!/usr/bin/env python3
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


APP_NAME = "Foundry Smoke"
HOST = "127.0.0.1"
PORT = int(os.environ.get("PORT", "8000"))


class FoundrySmokeHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            body = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{APP_NAME}</title>
  </head>
  <body>
    <main>
      <h1>{APP_NAME}</h1>
      <p>Minimal Python seed app for Foundry smoke checks.</p>
    </main>
  </body>
</html>
"""
            payload = body.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return

        if self.path == "/health":
            payload = json.dumps({"app": APP_NAME, "status": "ok"}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return

        self.send_error(404)

    def log_message(self, format, *args):
        return


def main():
    server = ThreadingHTTPServer((HOST, PORT), FoundrySmokeHandler)
    print(f"Serving {APP_NAME} on http://{HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
