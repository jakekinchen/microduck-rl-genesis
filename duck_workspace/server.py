"""Loopback-only, GET-only viewer with an exact development-artifact allowlist."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
from pathlib import Path
import re
from urllib.parse import parse_qs, urlsplit

from .core import Inspector, ROOT

STATIC = Path(__file__).parent / "web"


def handler_for(inspector: Inspector):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def send_content_headers(self, status, mime, length):
            self.send_response(status)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(length))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; media-src 'self'; connect-src 'self'; frame-ancestors 'none'")

        def reply(self, status, value):
            data = json.dumps(value, allow_nan=False).encode()
            self.send_content_headers(status, "application/json", len(data))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            # Reject non-loopback Host headers (including DNS rebinding).
            host = self.headers.get("Host", "").split(":")[0]
            if host not in {"127.0.0.1", "localhost"}:
                return self.reply(403, {"error": "loopback host required"})
            target = urlsplit(self.path)
            query = parse_qs(target.query)
            try:
                if target.path == "/api/snapshot":
                    return self.reply(200, inspector.snapshot())
                if target.path == "/api/run":
                    return self.reply(200, inspector.detail(query.get("id", [""])[0]))
                if target.path in {"/", "/app.js", "/style.css"}:
                    path = STATIC / ({"/": "index.html"}.get(target.path, target.path[1:]))
                elif target.path == "/artifact":
                    path = inspector.artifact(query.get("path", [""])[0])
                else:
                    return self.reply(404, {"error": "unknown viewer route"})
                size = path.stat().st_size
                start, end, status = 0, size - 1, 200
                range_header = self.headers.get("Range")
                if range_header:
                    match = re.fullmatch(r"bytes=(\d+)-(\d*)", range_header)
                    if not match:
                        return self.reply(416, {"error": "unsupported byte range"})
                    start = int(match[1])
                    end = min(int(match[2]), size - 1) if match[2] else size - 1
                    if start > end or start >= size:
                        return self.reply(416, {"error": "byte range outside artifact"})
                    status = 206
                self.send_content_headers(status, mimetypes.guess_type(path.name)[0] or "application/octet-stream", end - start + 1)
                self.send_header("Accept-Ranges", "bytes")
                if status == 206:
                    self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
                self.end_headers()
                with path.open("rb") as stream:
                    stream.seek(start)
                    remaining = end - start + 1
                    while remaining > 0:
                        chunk = stream.read(min(256 * 1024, remaining))
                        if not chunk:
                            break
                        self.wfile.write(chunk)
                        remaining -= len(chunk)
            except (OSError, ValueError, KeyError, TypeError) as error:
                if not isinstance(error, (BrokenPipeError, ConnectionResetError)):
                    self.reply(400, {"error": str(error)})
    return Handler


def serve(port: int, root: Path = ROOT):
    if not 0 <= port <= 65535:
        raise ValueError("port must be 0..65535")
    server = ThreadingHTTPServer(("127.0.0.1", port), handler_for(Inspector(root)))
    print(f"Duck Lab: http://127.0.0.1:{server.server_port} (read-only; Ctrl-C to stop)", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
