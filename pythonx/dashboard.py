"""Local browser dashboard for PYTHONX UNIVERSAL (standard library only)."""
from __future__ import annotations

import csv
import json
import os
import threading
import time
import webbrowser
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .scanner import inspect_file

INTERESTING = {".py", ".pyc", ".pyo", ".pyz", ".zip", ".whl", ".egg"}
SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", ".cache"}
REPORT_DIR = Path.home() / "PYTHONX-Reports"


class ScanJob:
    def __init__(self):
        self.lock = threading.RLock()
        self.pause_event = threading.Event()
        self.pause_event.set()
        self.cancel_event = threading.Event()
        self.reset()

    def reset(self):
        with getattr(self, "lock", threading.RLock()):
            self.status = "idle"
            self.root = ""
            self.files_seen = 0
            self.inspected = 0
            self.findings = []
            self.errors = 0
            self.started = None
            self.finished = None
            self.report_json = ""
            self.report_csv = ""

    def snapshot(self):
        with self.lock:
            elapsed = round((time.time() - self.started), 1) if self.started and not self.finished else (
                round(self.finished - self.started, 1) if self.started and self.finished else 0)
            return {"status": self.status, "root": self.root, "files_seen": self.files_seen,
                    "inspected": self.inspected, "errors": self.errors, "elapsed_seconds": elapsed,
                    "findings": self.findings[-300:], "report_json": self.report_json,
                    "report_csv": self.report_csv}

    def start(self, root):
        path = Path(root).expanduser()
        if not path.exists() or not path.is_dir():
            raise ValueError("Please enter an existing folder path.")
        if self.status in ("running", "paused"):
            raise ValueError("A scan is already running.")
        self.reset()
        self.pause_event.set()
        self.cancel_event.clear()
        self.root = str(path.resolve())
        self.status = "running"
        self.started = time.time()
        threading.Thread(target=self.run, args=(path,), daemon=True).start()

    def run(self, root):
        rows = []
        try:
            for current, dirs, names in os.walk(root, topdown=True, followlinks=False):
                self.pause_event.wait()
                if self.cancel_event.is_set():
                    break
                dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not (Path(current) / d).is_symlink()]
                for name in names:
                    self.pause_event.wait()
                    if self.cancel_event.is_set():
                        break
                    p = Path(current) / name
                    with self.lock:
                        self.files_seen += 1
                    if p.suffix.lower() not in INTERESTING:
                        continue
                    try:
                        item = inspect_file(p)
                        rows.append(item)
                        with self.lock:
                            self.inspected += 1
                            self.findings.append(item)
                    except (OSError, ValueError, PermissionError) as exc:
                        item = {"path": str(p), "error": f"{type(exc).__name__}: {exc}"}
                        rows.append(item)
                        with self.lock:
                            self.errors += 1
                            self.findings.append(item)
            REPORT_DIR.mkdir(parents=True, exist_ok=True)
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            jp = REPORT_DIR / f"pythonx-scan-{stamp}.json"
            cp = REPORT_DIR / f"pythonx-scan-{stamp}.csv"
            jp.write_text(json.dumps({"root": str(root), "files_seen": self.files_seen,
                                      "inspected": self.inspected, "results": rows},
                                     indent=2, ensure_ascii=False), encoding="utf-8")
            with cp.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["path", "type", "size", "sha256", "error"])
                writer.writeheader()
                for row in rows:
                    writer.writerow({k: row.get(k, "") for k in writer.fieldnames})
            with self.lock:
                self.report_json, self.report_csv = str(jp), str(cp)
                self.status = "cancelled" if self.cancel_event.is_set() else "completed"
        except Exception as exc:
            with self.lock:
                self.status = "error"
                self.findings.append({"error": f"{type(exc).__name__}: {exc}"})
        finally:
            with self.lock:
                self.finished = time.time()

    def pause(self):
        if self.status == "running":
            self.pause_event.clear()
            self.status = "paused"

    def resume(self):
        if self.status == "paused":
            self.status = "running"
            self.pause_event.set()

    def cancel(self):
        self.cancel_event.set()
        self.pause_event.set()


JOB = ScanJob()

HTML = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>PYTHONX UNIVERSAL</title><style>
:root{color-scheme:dark;--bg:#080b12;--panel:#111827;--line:#263246;--muted:#93a4ba;--cyan:#48d9e8;--green:#6be3a2}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(ellipse at top,#15243a,#080b12 55%);color:#edf4ff;font:15px system-ui,Arial}
main{max-width:1180px;margin:auto;padding:24px}.top{display:flex;justify-content:space-between;align-items:center;gap:16px;flex-wrap:wrap}
h1{margin:0;font-size:clamp(25px,5vw,38px);letter-spacing:1px}.sub,.muted{color:var(--muted)}.panel{background:#111827eF;border:1px solid var(--line);border-radius:18px;padding:20px;margin-top:18px;box-shadow:0 12px 38px #0005}
input{width:100%;padding:14px;background:#080f1b;color:white;border:1px solid #34445d;border-radius:10px;font-size:15px}
button{border:0;border-radius:10px;padding:12px 17px;font-weight:700;cursor:pointer;background:var(--cyan);color:#06131a}
button.secondary{background:#26364c;color:#e8f2ff}button.danger{background:#7d3442;color:white}.actions{display:flex;gap:9px;flex-wrap:wrap;margin-top:13px}
.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}.stat{background:#0b1320;border:1px solid var(--line);padding:15px;border-radius:13px}.num{font-size:27px;font-weight:800;color:var(--cyan)}
.bar{height:11px;background:#263246;border-radius:20px;overflow:hidden;margin:15px 0}.bar span{display:block;height:100%;width:0;background:linear-gradient(90deg,#35a9dc,#6be3a2);transition:width .3s}
table{width:100%;border-collapse:collapse;font-size:13px}th,td{text-align:left;padding:11px;border-bottom:1px solid var(--line);overflow-wrap:anywhere}th{color:var(--cyan)}
.tablewrap{overflow:auto;max-height:430px}.pill{padding:5px 9px;border-radius:30px;background:#203449;color:#a8edff;font-size:12px}
a{color:var(--green);overflow-wrap:anywhere}.status{font-weight:800}.foot{margin:20px 0;color:var(--muted);font-size:12px}
@media(max-width:700px){main{padding:14px}.grid{grid-template-columns:repeat(2,1fr)}.panel{padding:15px}th,td{padding:8px}}
</style></head><body><main>
<div class="top"><div><h1>PYTHONX <span style="color:var(--cyan)">UNIVERSAL</span></h1><div class="sub">Storage intelligence · Safe inspection · Recovery reports</div></div><span class="pill">LOCAL DEVICE DASHBOARD</span></div>
<section class="panel"><h2>Start a storage scan</h2><p class="muted">Choose a folder path. Android Termux users can scan shared storage after granting storage permission.</p>
<input id="root" spellcheck="false" placeholder="/storage/emulated/0 or C:\Users\YourName">
<div class="actions"><button onclick="startScan()">▶ Start scan</button><button class="secondary" onclick="control('pause')">Ⅱ Pause</button><button class="secondary" onclick="control('resume')">▶ Resume</button><button class="danger" onclick="control('cancel')">■ Cancel</button></div>
<p class="muted" id="hint">Only Python-related files and common Python archives are inspected. All files are counted during the folder walk.</p></section>
<section class="panel"><div class="top"><h2>Live dashboard</h2><span class="status" id="status">IDLE</span></div><div class="grid">
<div class="stat"><div class="muted">Files discovered</div><div class="num" id="seen">0</div></div>
<div class="stat"><div class="muted">Python items inspected</div><div class="num" id="inspected">0</div></div>
<div class="stat"><div class="muted">Read errors</div><div class="num" id="errors">0</div></div>
<div class="stat"><div class="muted">Elapsed</div><div class="num" id="elapsed">0s</div></div></div>
<div class="bar"><span id="progress"></span></div><div class="muted" id="rootlabel">No scan started</div></section>
<section class="panel"><div class="top"><h2>Scan results</h2><span class="pill" id="count">0 records</span></div>
<div class="tablewrap"><table><thead><tr><th>File</th><th>Type</th><th>Size</th><th>Result</th></tr></thead><tbody id="rows"><tr><td colspan="4" class="muted">Results will appear here.</td></tr></tbody></table></div></section>
<section class="panel"><h2>Output files</h2><p class="muted">Reports are saved on this device in the PYTHONX-Reports folder.</p><div id="outputs" class="muted">Complete a scan to generate JSON and CSV reports.</div></section>
<div class="foot">PYTHONX UNIVERSAL · Local-only dashboard · Does not upload scanned files.</div>
</main><script>
const $=id=>document.getElementById(id);let lastStatus="";
async function post(action,data={}){const r=await fetch('/api/'+action,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});const j=await r.json();if(!r.ok)alert(j.error||'Request failed');return j}
async function startScan(){await post('start',{root:$('root').value})}
async function control(a){await post(a)}
function esc(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function size(n){n=Number(n||0);return n<1024?n+' B':n<1048576?(n/1024).toFixed(1)+' KB':(n/1048576).toFixed(1)+' MB'}
async function refresh(){try{const r=await fetch('/api/status');const d=await r.json();$('status').textContent=d.status.toUpperCase();$('seen').textContent=d.files_seen.toLocaleString();$('inspected').textContent=d.inspected.toLocaleString();$('errors').textContent=d.errors.toLocaleString();$('elapsed').textContent=d.elapsed_seconds+'s';$('rootlabel').textContent=d.root||'No scan started';$('count').textContent=d.findings.length+' visible records';$('progress').style.width=d.status==='completed'?'100%':(d.files_seen?Math.min(92,8+Math.log10(d.files_seen+1)*18):0)+'%';
if(d.findings.length){$('rows').innerHTML=d.findings.slice().reverse().map(x=>'<tr><td>'+esc(x.path||'')+'</td><td>'+esc(x.type||'unknown')+'</td><td>'+size(x.size)+'</td><td>'+esc(x.error|| (x.syntax_valid===false?'Syntax error':'Inspected'))+'</td></tr>').join('')}
if(d.report_json){$('outputs').innerHTML='JSON: <b>'+esc(d.report_json)+'</b><br>CSV: <b>'+esc(d.report_csv)+'</b>'}
if(d.status==='error')$('hint').textContent=(d.findings.at(-1)||{}).error||'Scan error';else if(d.status==='completed')$('hint').textContent='Scan completed. Reports saved.';else if(d.status==='cancelled')$('hint').textContent='Scan cancelled. Partial reports saved.';lastStatus=d.status;
}catch(e){}}setInterval(refresh,1000);refresh();
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, data, content_type="application/json; charset=utf-8"):
        body = data if isinstance(data, bytes) else json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        route = urlparse(self.path).path
        if route == "/":
            self._send(200, HTML.encode(), "text/html; charset=utf-8")
        elif route == "/api/status":
            self._send(200, JOB.snapshot())
        else:
            self._send(404, {"error": "Not found"})

    def do_POST(self):
        if not self.path.startswith("/api/"):
            return self._send(404, {"error": "Not found"})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length > 16384:
                return self._send(413, {"error": "Request too large"})
            data = json.loads(self.rfile.read(length) or b"{}")
            action = self.path.rsplit("/", 1)[-1]
            if action == "start":
                JOB.start(data.get("root", ""))
            elif action == "pause":
                JOB.pause()
            elif action == "resume":
                JOB.resume()
            elif action == "cancel":
                JOB.cancel()
            else:
                return self._send(404, {"error": "Unknown action"})
            self._send(200, JOB.snapshot())
        except Exception as exc:
            self._send(400, {"error": str(exc)})

    def log_message(self, *_):
        pass


def default_root():
    android = Path("/storage/emulated/0")
    return str(android if android.is_dir() else Path.home())


def main():
    import argparse
    parser = argparse.ArgumentParser(description="PYTHONX UNIVERSAL local dashboard")
    parser.add_argument("--host", default="127.0.0.1", help="Keep localhost for private device-only access")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    if args.host not in ("127.0.0.1", "localhost", "::1"):
        parser.error("For safety, dashboard only binds to localhost.")
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    url = f"http://127.0.0.1:{args.port}"
    print("PYTHONX UNIVERSAL dashboard:", url)
    print("Default scan folder:", default_root())
    print("Reports folder:", REPORT_DIR)
    if not args.no_browser:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDashboard stopped.")
    finally:
        JOB.cancel()
        server.server_close()


if __name__ == "__main__":
    main()
