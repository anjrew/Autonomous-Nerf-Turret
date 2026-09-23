"""A dependency-free web UI for live-tuning the turret.

Serves a single page (live MJPEG video, telemetry, collapsible controls) and
a small JSON API:

    GET  /state     -> live controller telemetry, gains, and mode params
    POST /gains     -> apply PID gains, e.g. {"az": {"kp": .., "ki": .., "kd": ..},
                                             "el": {...}}
    POST /params    -> runtime mode: {"target_type": "face"|"person",
                                      "targets": ["james_harper", ...]}
    GET  /settings  -> camera_vision inference/image settings (proxied)
    POST /settings  -> update camera_vision inference/image settings (proxied)

Gains/params live in a shared `TuningState` mapping guarded by a lock; the
control loop reads them every frame, so changes take effect immediately.
Camera settings are proxied to the camera_vision process, which applies them
per frame.
"""

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List, Optional

HTML_TEMPLATE = """<!doctype html>
<html><head><meta charset="utf-8"><title>Turret control</title>
<style>
 *{box-sizing:border-box}
 body{font-family:system-ui;background:#111;color:#ddd;margin:0;height:100vh;overflow:hidden;display:flex}
 #video-panel{flex:1;display:flex;align-items:center;justify-content:center;min-width:0;background:#000}
 #video{max-width:100%;max-height:100%}
 #sidebar{width:26rem;flex-shrink:0;padding:1rem;overflow-y:auto;background:#161616;border-left:1px solid #333;transition:margin-right .2s ease}
 body.collapsed #sidebar{margin-right:-26rem}
 #toggle{position:fixed;top:0.6rem;right:0.6rem;z-index:10;background:#222;color:#ddd;border:1px solid #444;border-radius:6px;padding:0.3rem 0.7rem;cursor:pointer;font-size:0.9rem}
 .row{margin:0.6rem 0}
 input[type=range]{width:14rem;vertical-align:middle}
 output{font-family:monospace;margin-left:0.6rem}
 button,.preset,select,input[type=text]{background:#222;color:#ddd;border:1px solid #444;border-radius:4px;padding:0.25rem 0.6rem;cursor:pointer;font-size:0.9rem}
 select{cursor:pointer}
 input[type=text]{cursor:text;width:100%}
 label{cursor:pointer}
 h2{border-bottom:1px solid #444;padding-bottom:0.3rem;margin-top:1.4rem}
 #telemetry{font-family:monospace;font-size:0.8rem;background:#1b1b1b;padding:0.8rem;border-radius:6px;white-space:pre-wrap}
 summary{cursor:pointer;color:#8ab4f8;margin-bottom:0.4rem;user-select:none}
 .sec{color:#8ab4f8}
</style></head><body>
<button id="toggle">hide controls</button>
<div id="video-panel">
 <img id="video" src="__VIDEO_URL__" alt="camera feed unavailable">
</div>
 <div id="sidebar">
 <details id="telemetry-box" open>
  <summary>Telemetry</summary>
  <div id="telemetry">connecting...</div>
 </details>
 <h2 class="sec">Azimuth PID</h2>
 <div class="row">Kp <input type="range" id="az_kp" min="0" max="0.5" step="0.005"><output></output></div>
 <div class="row">Ki <input type="range" id="az_ki" min="0" max="0.1" step="0.001"><output></output></div>
 <div class="row">Kd <input type="range" id="az_kd" min="0" max="0.5" step="0.005"><output></output></div>
 <h2 class="sec">Elevation PID</h2>
 <div class="row">Kp <input type="range" id="el_kp" min="0" max="0.2" step="0.002"><output></output></div>
 <div class="row">Ki <input type="range" id="el_ki" min="0" max="0.05" step="0.001"><output></output></div>
 <div class="row">Kd <input type="range" id="el_kd" min="0" max="0.2" step="0.002"><output></output></div>
 <h2 class="sec">Mode</h2>
 <div class="row">Target type
  <select id="target_type"><option value="person">person</option><option value="face">face</option></select>
 </div>
 <div class="row">Tracked IDs (face type only, comma separated)<br>
  <input type="text" id="targets" list="target-names" placeholder="james_harper, john_doe">
  <datalist id="target-names"></datalist>
 </div>
 <div class="row">
  <button class="preset" data-mode="face">Faces only</button>
  <button class="preset" data-mode="person">People only</button>
  <button class="preset" data-mode="center">People, aim face</button>
  <button class="preset" data-mode="id">Specific person</button>
 </div>
 <h2 class="sec">Aim calibration</h2>
 <div class="row">X offset px <input type="range" id="target_offset_x" data-param="target_offset_x" min="-100" max="100" step="1"><output></output></div>
 <div class="row">Y offset px <input type="range" id="target_offset_y" data-param="target_offset_y" min="-100" max="100" step="1"><output></output></div>
 <h2 class="sec">Search</h2>
 <div class="row"><label><input type="checkbox" id="search_enabled" data-param="search_enabled"> autonomous search when no targets</label></div>
 <div class="row">Sweep speed <input type="range" id="search_speed" data-param="search_speed" min="0.2" max="5" step="0.1"><output></output></div>
 <div class="row">Ease at ends <input type="range" id="search_ease" data-param="search_ease" min="0" max="2" step="0.1"><output></output></div>
 <div class="row">Cycle seconds <input type="range" id="search_period" data-param="search_period" min="2" max="30" step="1"><output></output></div>
 <h2 class="sec">Inference &amp; image</h2>
 <div class="row">imgsz <input type="range" id="imgsz" data-setting="imgsz" min="160" max="640" step="32"><output></output></div>
 <div class="row">Downscale <input type="range" id="image_compression" data-setting="image_compression" min="1" max="8" step="1"><output></output></div>
 <div class="row">Detect every N frames <input type="range" id="detect_every" data-setting="detect_every" min="1" max="60" step="1"><output></output></div>
 <div class="row">Confidence <input type="range" id="object_confidence" data-setting="object_confidence" min="0.05" max="0.95" step="0.05"><output></output></div>
 <div class="row">Loop delay ms <input type="range" id="loop_delay" data-setting="loop_delay" min="0" max="50" step="5"><output></output></div>
 <div class="row"><label><input type="checkbox" id="detect_faces" data-setting="detect_faces"> detect faces</label></div>
 <div class="row"><label><input type="checkbox" id="detect_objects" data-setting="detect_objects"> detect objects</label></div>
 <div class="row"><label><input type="checkbox" id="id_targets" data-setting="id_targets"> face ID targeting</label></div>
 <p class="sec">Changes apply to the control loop immediately.</p>
</div>
<script>
const toggleBtn = document.getElementById('toggle');
toggleBtn.addEventListener('click', () => {
  const collapsed = document.body.classList.toggle('collapsed');
  toggleBtn.textContent = collapsed ? 'show controls' : 'hide controls';
});
async function pullState(){
  try{
    const s = await (await fetch('/state')).json();
    document.getElementById('telemetry').textContent = JSON.stringify(s, null, 1);
    if (s.controller){
      const tt = document.getElementById('target_type');
      const ti = document.getElementById('targets');
      tt.value = s.controller.target_type || 'person';
      if (document.activeElement !== ti){
        ti.value = (s.controller.targets || []).join(', ');
      }
      ti.disabled = tt.value !== 'face';
    }
  }catch(e){ document.getElementById('telemetry').textContent = 'server unreachable'; }
}
setInterval(pullState, 500); pullState();
async function postJSON(url, body){
  const r = await fetch(url, {method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify(body)});
  return r.json();
}
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
for (const el of document.querySelectorAll('[data-setting]')){
  el.addEventListener('change', async () => {
    let value;
    if (el.type === 'checkbox') value = el.checked;
    else if (el.id === 'loop_delay') value = parseFloat(el.value) / 1000;
    else value = parseFloat(el.value);
    if (el.nextElementSibling) el.nextElementSibling.textContent = el.value;
    await postJSON('/settings', {[el.dataset.setting]: value});
    if (el.id === 'id_targets') refreshTargetNames();
  });
}
(async () => {
  try{
    const s = await (await fetch('/settings')).json();
    for (const el of document.querySelectorAll('[data-setting]')){
      const v = s[el.dataset.setting];
      if (v === undefined) continue;
      if (el.type === 'checkbox') el.checked = !!v;
      else {
        el.value = el.id === 'loop_delay' ? Math.round(v * 1000) : v;
        if (el.nextElementSibling) el.nextElementSibling.textContent = el.value;
      }
    }
  }catch(e){}
})();
const targetType = document.getElementById('target_type');
const targetsInput = document.getElementById('targets');
async function refreshTargetNames(){
  try{
    const names = await (await fetch('/targets?refresh=1')).json();
    document.getElementById('target-names').innerHTML =
      names.map(n => `<option value="${n}">`).join('');
  }catch(e){}
}
refreshTargetNames();
for (const el of document.querySelectorAll('[data-param]')){
  const send = async () => {
    const value = el.type === 'checkbox' ? el.checked : parseFloat(el.value);
    if (el.nextElementSibling) el.nextElementSibling.textContent = el.value;
    await postJSON('/params', {[el.dataset.param]: value});
  };
  el.addEventListener(el.type === 'checkbox' ? 'change' : 'input', send);
}
(async () => {
  try{
    const s = await (await fetch('/state')).json();
    for (const el of document.querySelectorAll('[data-param]')){
      const v = s.controller && s.controller[el.dataset.param];
      if (v === undefined) continue;
      if (el.type === 'checkbox') el.checked = !!v;
      else {
        el.value = v;
        if (el.nextElementSibling) el.nextElementSibling.textContent = el.value;
      }
    }
  }catch(e){}
})();
targetType.addEventListener('change', async () => {
  targetsInput.disabled = targetType.value !== 'face';
  await postJSON('/params', {target_type: targetType.value});
});
targetsInput.addEventListener('change', async () => {
  const ids = targetsInput.value.split(',').map(s => s.trim()).filter(Boolean);
  await postJSON('/params', {targets: ids});
});
const PRESETS = {
  face:   {settings:{detect_faces:true,  detect_objects:false, id_targets:false}, params:{target_type:'face'}},
  person: {settings:{detect_faces:false, detect_objects:true,  id_targets:false}, params:{target_type:'person'}},
  center: {settings:{detect_faces:true,  detect_objects:true,  id_targets:false}, params:{target_type:'person'}},
  id:     {settings:{detect_faces:true,  detect_objects:false, id_targets:true},  params:{target_type:'face'}},
};
for (const btn of document.querySelectorAll('.preset')){
  btn.addEventListener('click', async () => {
    const preset = PRESETS[btn.dataset.mode];
    await postJSON('/settings', preset.settings);
    await postJSON('/params', preset.params);
    for (const [key, value] of Object.entries(preset.settings)){
      const el = document.querySelector(`[data-setting="${key}"]`);
      if (!el) continue;
      if (el.type === 'checkbox') el.checked = !!value;
      else { el.value = value; if (el.nextElementSibling) el.nextElementSibling.textContent = el.value; }
    }
    targetType.value = preset.params.target_type;
    targetsInput.disabled = preset.params.target_type !== 'face';
    if (btn.dataset.mode === 'id') refreshTargetNames();
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

    def __init__(self, initial_gains: Dict[str, Dict[str, float]],
                 initial_params: Optional[Dict[str, Any]] = None) -> None:
        self._lock = threading.Lock()
        self._gains: Dict[str, Dict[str, float]] = {
            axis: dict(gains) for axis, gains in initial_gains.items()
        }
        self._params: Dict[str, Any] = dict(initial_params or {})
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

    def params(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._params)

    def set_params(self, values: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            if 'target_type' in values:
                target_type = str(values['target_type']).lower()
                if target_type in ('face', 'person'):
                    self._params['target_type'] = target_type
                    if target_type != 'face':
                        self._params['targets'] = []
            if 'targets' in values:
                names = [str(t).lower().strip().replace(' ', '_')
                         for t in values['targets'] if str(t).strip()]
                if self._params.get('target_type') == 'face':
                    self._params['targets'] = names
                else:
                    self._params['targets'] = []
            for key in ('target_offset_x', 'target_offset_y'):
                if key in values:
                    try:
                        self._params[key] = max(-250.0, min(250.0, float(values[key])))
                    except (TypeError, ValueError):
                        pass
            if 'search_enabled' in values:
                self._params['search_enabled'] = bool(values['search_enabled'])
            for key, clamp in (('search_speed', (0.0, 10.0)),
                               ('search_ease', (0.0, 3.0)),
                               ('search_period', (1.0, 60.0))):
                if key in values:
                    try:
                        self._params[key] = max(clamp[0], min(clamp[1], float(values[key])))
                    except (TypeError, ValueError):
                        pass
            return dict(self._params)

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return {"gains": {a: dict(g) for a, g in self._gains.items()},
                    "controller": dict(self._params),
                    **self._telemetry}


def make_handler(state: TuningState, video_url: str = "",
                 camera_settings_url: str = ""):
    html = HTML_TEMPLATE.replace("__VIDEO_URL__", video_url)
    import requests

    def proxy_camera_get(path: str, timeout: float = 1.0):
        try:
            response = requests.get(f"{camera_settings_url}{path}", timeout=timeout)
            return response.status_code, response.json()
        except Exception as e:
            return 502, {"error": f"camera settings unreachable: {e}"}

    def proxy_settings(method: str, body: Optional[Dict[str, Any]]):
        if method == "GET":
            return proxy_camera_get("/settings")
        try:
            response = requests.post(f"{camera_settings_url}/settings",
                                     json=body, timeout=1)
            return response.status_code, response.json()
        except Exception as e:
            return 502, {"error": f"camera settings unreachable: {e}"}

    class Handler(BaseHTTPRequestHandler):
        def _send(self, code: int, body: bytes, ctype: str) -> None:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_json(self, code: int, payload: Any) -> None:
            self._send(code, json.dumps(payload).encode(), "application/json")

        def do_GET(self) -> None:  # noqa: N802 (stdlib naming)
            if self.path == "/":
                self._send(200, html.encode(), "text/html; charset=utf-8")
            elif self.path == "/state":
                self._send_json(200, state.snapshot())
            elif self.path == "/settings":
                code, payload = proxy_settings("GET", None)
                self._send_json(code, payload)
            elif self.path == "/targets" or self.path.startswith("/targets?"):
                code, payload = proxy_camera_get(self.path, timeout=30.0)
                self._send_json(code, payload)
            else:
                self._send(404, b"not found", "text/plain")

        def do_POST(self) -> None:  # noqa: N802 (stdlib naming)
            length = int(self.headers.get("Content-Length", 0))
            try:
                payload = json.loads(self.rfile.read(length).decode())
            except (ValueError, TypeError, json.JSONDecodeError) as e:
                self._send_json(400, {"error": str(e)})
                return
            if self.path == "/gains":
                state.set_gains(payload)
                self._send_json(200, {"ok": True})
            elif self.path == "/params":
                self._send_json(200, state.set_params(payload))
            elif self.path == "/settings":
                code, response = proxy_settings("POST", payload)
                self._send_json(code, response)
            else:
                self._send(404, b"not found", "text/plain")

        def log_message(self, *args) -> None:  # silence per-request noise
            pass

    return Handler


def start_tuning_ui(state: TuningState, port: int, video_url: str = "",
                    camera_settings_url: str = "") -> ThreadingHTTPServer:
    ThreadingHTTPServer.allow_reuse_address = True
    server = ThreadingHTTPServer(
        ("0.0.0.0", port),
        make_handler(state, video_url, camera_settings_url),
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server
