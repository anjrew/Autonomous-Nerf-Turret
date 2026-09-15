"""A dependency-free web UI for live-tuning the aim PID gains.

Serves a single page of sliders (azimuth + elevation PID gains and output
limits) and a small JSON API:

    GET  /state   -> live controller telemetry (errors, outputs, firing)
    POST /gains   -> apply new gains, e.g. {"az": {"kp": .., "ki": .., "kd": ..},
                                            "el": {...}}

Gains live in a shared `TuningState` mapping guarded by a lock; the control
loop reads them every frame, so slider changes take effect immediately.
"""

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict

HTML = """<!doctype html>
<html><head><meta charset="utf-8"><title>Turret PID tuning</title>
<style>
 body{font-family:system-ui;background:#111;color:#ddd;margin:2rem}
 .row{margin:0.6rem 0}
 input[type=range]{width:22rem;vertical-align:middle}
 output{font-family:monospace;margin-left:0.6rem}
 h2{border-bottom:1px solid #444;padding-bottom:0.3rem}
 #telemetry{font-family:monospace;background:#1b1b1b;padding:0.8rem;border-radius:6px;white-space:pre}
 .sec{color:#8ab4f8}
</style></head><body>
<h1>Turret PID tuning</h1>
<div id="telemetry">connecting...</div>
<h2 class="sec">Azimuth PID</h2>
<div class="row">Kp <input type="range" id="az_kp" min="0" max="0.5" step="0.005"><output></output></div>
<div class="row">Ki <input type="range" id="az_ki" min="0" max="0.1" step="0.001"><output></output></div>
<div class="row">Kd <input type="range" id="az_kd" min="0" max="0.5" step="0.005"><output></output></div>
<h2 class="sec">Elevation PID</h2>
<div class="row">Kp <input type="range" id="el_kp" min="0" max="0.2" step="0.002"><output></output></div>
<div class="row">Ki <input type="range" id="el_ki" min="0" max="0.05" step="0.001"><output></output></div>
<div class="row">Kd <input type="range" id="el_kd" min="0" max="0.2" step="0.002"><output></output></div>
<p class="sec">Changes apply to the control loop immediately.</p>
<script>
async function pullState(){
  try{
    const s = await (await fetch('/state')).json();
    document.getElementById('telemetry').textContent = JSON.stringify(s, null, 1);
  }catch(e){ document.getElementById('telemetry').textContent = 'server unreachable'; }
}
setInterval(pullState, 500); pullState();
for (const id of ['az_kp','az_ki','az_kd','el_kp','el_ki','el_kd']){
  const el = document.getElementById(id);
  el.addEventListener('input', async () => {
    el.nextElementSibling.textContent = el.value;
    const axis = id.startsWith('az') ? 'az' : 'el';
    const gain = id.slice(3);
    await fetch('/gains', {method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({[axis]: {[gain]: parseFloat(el.value)}})});
  });
}
(async () => {
  const s = await (await fetch('/state')).json();
  for (const axis of ['az','el']) for (const g of ['kp','ki','kd']){
    const el = document.getElementById(axis+'_'+g);
    if (s.gains && s.gains[axis] && s.gains[axis][g] !== undefined){
      el.value = s.gains[axis][g]; el.nextElementSibling.textContent = el.value;
    }
  }
})();
</script></body></html>"""


class TuningState:
    """Thread-safe container for live-tuned gains and loop telemetry."""

    def __init__(self, initial_gains: Dict[str, Dict[str, float]]) -> None:
        self._lock = threading.Lock()
        self._gains: Dict[str, Dict[str, float]] = {
            axis: dict(gains) for axis, gains in initial_gains.items()
        }
        self._telemetry: Dict[str, Any] = {}

    def gains(self) -> Dict[str, Dict[str, float]]:
        with self._lock:
            return {axis: dict(g) for axis, g in self._gains.items()}

    def set_gains(self, gains: Dict[str, Dict[str, float]]) -> None:
        with self._lock:
            for axis, axis_gains in gains.items():
                if axis not in self._gains:
                    continue
                for key, value in axis_gains.items():
                    if key in ("kp", "ki", "kd") and isinstance(value, (int, float)):
                        self._gains[axis][key] = float(value)

    def telemetry(self, data: Dict[str, Any]) -> None:
        with self._lock:
            self._telemetry = data

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return {"gains": {a: dict(g) for a, g in self._gains.items()},
                    **self._telemetry}


def make_handler(state: TuningState):
    class Handler(BaseHTTPRequestHandler):
        def _send(self, code: int, body: bytes, ctype: str) -> None:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802 (stdlib naming)
            if self.path == "/":
                self._send(200, HTML.encode(), "text/html; charset=utf-8")
            elif self.path == "/state":
                self._send(200, json.dumps(state.snapshot()).encode(),
                           "application/json")
            else:
                self._send(404, b"not found", "text/plain")

        def do_POST(self) -> None:  # noqa: N802 (stdlib naming)
            if self.path != "/gains":
                self._send(404, b"not found", "text/plain")
                return
            length = int(self.headers.get("Content-Length", 0))
            try:
                state.set_gains(json.loads(self.rfile.read(length).decode()))
                self._send(200, b'{"ok":true}', "application/json")
            except (ValueError, TypeError, json.JSONDecodeError) as e:
                self._send(400, json.dumps({"error": str(e)}).encode(),
                           "application/json")

        def log_message(self, *args) -> None:  # silence per-request noise
            pass

    return Handler


def start_tuning_ui(state: TuningState, port: int) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer(("0.0.0.0", port), make_handler(state))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server
