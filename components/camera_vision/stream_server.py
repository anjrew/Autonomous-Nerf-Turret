"""Dependency-free MJPEG stream of the annotated camera feed.

GET /video.mjpg -> multipart/x-mixed-replace stream of the latest processed
frame. The camera loop pushes JPEG frames via `update()`; the handler only
re-serves the latest frame while a client is connected.
"""

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

_BOUNDARY = "frame"
_latest_jpeg: bytes | None = None
_lock = threading.Lock()


class TurretSettings:
    """Thread-safe store of live-tunable inference/image settings.

    Values are validated and clamped on update; unknown keys are ignored
    so a newer UI posting extra fields cannot break a running camera loop.
    """

    VALID = {
        'imgsz': (int, 96, 1280),
        'image_compression': (int, 1, 10),
        'detect_every': (int, 1, 2000),
        'object_confidence': (float, 0.05, 0.99),
        'detect_faces': (bool, None, None),
        'detect_objects': (bool, None, None),
        'id_targets': (bool, None, None),
        'segmentation': (bool, None, None),
        'loop_delay': (float, 0.0, 0.5),
    }

    def __init__(self, initial: dict) -> None:
        self._lock = threading.Lock()
        self._settings: dict = dict(initial)

    def get(self, key: str, default=None):
        with self._lock:
            return self._settings.get(key, default)

    def snapshot(self) -> dict:
        with self._lock:
            return dict(self._settings)

    def update(self, values: dict) -> dict:
        with self._lock:
            for key, value in values.items():
                if key not in self.VALID:
                    continue
                value_type, minimum, maximum = self.VALID[key]
                try:
                    if value_type is bool:
                        value = bool(value)
                    elif value_type is int:
                        value = int(round(float(value)))
                    else:
                        value = float(value)
                    if minimum is not None:
                        value = max(minimum, value)
                    if maximum is not None:
                        value = min(maximum, value)
                except (TypeError, ValueError):
                    continue
                self._settings[key] = value
            return dict(self._settings)


def update(jpeg_bytes: bytes) -> None:
    global _latest_jpeg
    with _lock:
        _latest_jpeg = jpeg_bytes


def make_handler(settings: TurretSettings, targets_provider=None):
    class Handler(BaseHTTPRequestHandler):
        def _send(self, code: int, body: bytes, ctype: str) -> None:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802 (stdlib naming)
            if self.path == "/settings":
                self._send(200, json.dumps(settings.snapshot()).encode(),
                           "application/json")
            elif urlparse(self.path).path == "/targets":
                refresh = bool(parse_qs(urlparse(self.path).query).get('refresh'))
                try:
                    names = list(targets_provider(refresh)) if targets_provider else []
                except Exception:
                    names = []
                self._send(200, json.dumps(names).encode(), "application/json")
            elif self.path == "/video.mjpg":
                self.send_response(200)
                self.send_header(
                    "Content-Type",
                    f"multipart/x-mixed-replace; boundary={_BOUNDARY}",
                )
                self.end_headers()
                try:
                    while True:
                        with _lock:
                            jpeg = _latest_jpeg
                        if jpeg is not None:
                            self.wfile.write(
                                f"--{_BOUNDARY}\r\n"
                                f"Content-Type: image/jpeg\r\n"
                                f"Content-Length: {len(jpeg)}\r\n\r\n".encode()
                                + jpeg
                                + b"\r\n"
                            )
                        time.sleep(1 / 30)
                except (BrokenPipeError, ConnectionResetError):
                    pass
            else:
                self.send_response(404)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"not found")

        def do_POST(self) -> None:  # noqa: N802 (stdlib naming)
            if self.path != "/settings":
                self._send(404, b"not found", "text/plain")
                return
            length = int(self.headers.get("Content-Length", 0))
            try:
                updated = settings.update(json.loads(self.rfile.read(length).decode()))
                self._send(200, json.dumps(updated).encode(), "application/json")
            except (ValueError, TypeError, json.JSONDecodeError) as e:
                self._send(400, json.dumps({"error": str(e)}).encode(),
                           "application/json")

        def log_message(self, *args) -> None:  # silence per-request noise
            pass

    return Handler


def start_stream_server(port: int, settings: TurretSettings,
                        targets_provider=None) -> ThreadingHTTPServer:
    ThreadingHTTPServer.allow_reuse_address = True
    server = ThreadingHTTPServer(
        ("0.0.0.0", port),
        make_handler(settings, targets_provider),
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server
