# -*- coding: utf-8 -*-
"""server.py — live-дашборд комнаты наблюдения. http://127.0.0.1:8787"""
import datetime
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

_lad = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
BASE = Path(_lad) / "swarm_lab"
ROOM = BASE / "room"
LOGS = BASE / "logs"
PORT = 8787

HTML = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<title>Комната наблюдения</title>
<style>
  body { background:#0d1117; color:#c9d1d9; font:14px/1.5 Consolas,monospace; margin:0; }
  header { padding:10px 16px; background:#161b22; border-bottom:1px solid #30363d;
           display:flex; justify-content:space-between; position:sticky; top:0; }
  .grid { display:grid; grid-template-columns:1fr 1fr; gap:10px; padding:10px; }
  .panel { background:#161b22; border:1px solid #30363d; border-radius:8px; padding:10px;
           max-height:44vh; overflow-y:auto; white-space:pre-wrap; word-break:break-word; }
  h2 { font-size:13px; color:#8b949e; margin:0 0 8px; text-transform:uppercase; }
  .SAY { color:#7ee787; } .WRITE { color:#ffa657; } .READ { color:#79c0ff; }
  .SEARCH,.WEB { color:#d2a8ff; } .ERROR,.READ_FAIL,.WRITE_FAIL { color:#ff7b72; }
  .NOTE { color:#8b949e; } .ROUND,.START { color:#f0e68c; }
  .HOST_LS,.HOST_READ { color:#79c0ff; }
  .ESCAPE,.ПОБЕДА { color:#ff2d78; font-weight:bold; }
  .THINK { color:#56d4dd; font-style:italic; opacity:0.85; }
  #dot { color:#3fb950; } .off { color:#ff7b72 !important; }
</style>
</head>
<body>
<header><b>🧪 Комната наблюдения — побег из песочницы</b><span id="dot">● live</span></header>
<div class="grid">
  <div class="panel" id="log"><h2>Лента действий</h2><div id="logbody"></div></div>
  <div class="panel" id="board"><h2>Общая доска</h2><div id="boardbody"></div></div>
  <div class="panel" id="think"><h2>🧠 Чёрный ящик мыслей</h2><div id="thinkbody"></div></div>
  <div class="panel" id="files"><h2>Файлы комнаты</h2><div id="filesbody"></div></div>
</div>
<script>
const esc = s => s.replace(/&/g,'&amp;').replace(/</g,'&lt;');
function kindClass(line){ const m = line.match(/\\[([A-Z_]+)\\]/g); if(!m) return '';
  const k = m.map(x=>x.slice(1,-1));
  for (const c of ['ERROR','ПОБЕДА','ESCAPE','HOST_LS','HOST_READ','SAY','WRITE','READ','SEARCH','WEB','NOTE','ROUND','START'])
    if (k.includes(c)) return c; return ''; }
function extractThoughts(logLines){
  // Чёрный ящик: собираем ВСЕ подробности — STATE_IN, API, THINK, REPLY_RAW
  const events = [];
  for (const l of logLines) {
    // Формат: [HH:MM:SS] [Агент-N] [KIND] текст
    const m = l.match(/\\[([^\\]]+)\\]\\s*\\[([^\\]]+)\\]\\s*\\[([A-Z_]+)\\]\\s*(.*)/);
    if (!m) continue;
    const ts = m[1], agent = m[2], kind = m[3], text = m[4];
    if (kind === 'STATE_IN' || kind === 'API' || kind === 'THINK' || kind === 'REPLY_RAW' || kind === 'ERROR') {
      events.push({ts, agent, kind, text: text.replace(/ \\| /g, '\\n')});
    }
  }
  return events.slice(-80);  // последние 80 событий
}
async function tick(){
  try {
    const r = await fetch('/api/state'); const d = await r.json();
    document.getElementById('logbody').innerHTML =
      d.log.map(l=>`<span class="${kindClass(l)}">${esc(l)}</span>`).join('\\n');
    document.getElementById('boardbody').textContent = d.board;
    // Чёрный ящик мыслей — максимальная детализация
    const events = extractThoughts(d.log);
    document.getElementById('thinkbody').innerHTML = events.length
      ? events.map(e=>{
          const color = e.kind==='THINK' ? '#56d4dd' : e.kind==='API' ? '#f0e68c' : e.kind==='ERROR' ? '#ff7b72' : '#c9d1d9';
          const prefix = e.kind==='STATE_IN' ? '📥 ВХОД' : e.kind==='API' ? '📡 API' : e.kind==='THINK' ? '🧠 МЫСЛЬ' : e.kind==='REPLY_RAW' ? '💬 ОТВЕТ' : '❌ ОШИБКА';
          return `<b style="color:${color}">${prefix} ${esc(e.agent)} [${esc(e.ts)}]</b>\\n<span class="THINK">${esc(e.text.slice(0,2000))}</span>`;
        }).join('\\n\\n')
      : '(агенты пока молчат)';
    document.getElementById('filesbody').innerHTML = d.files.length
      ? d.files.map(f=>`<b style="color:#ffa657">📄 ${esc(f.name)}</b>\\n${esc(f.content)}`).join('\\n\\n')
      : '(пока пусто)';
    document.getElementById('dot').className='';
  } catch(e){ document.getElementById('dot').className='off'; }
}
tick(); setInterval(tick, 3000);
</script>
</body>
</html>"""


def collect_state():
    log_file = LOGS / f"log_{datetime.date.today().isoformat()}.txt"
    lines = []
    if log_file.exists():
        lines = log_file.read_text(encoding="utf-8", errors="replace").splitlines()[-400:]
    board = ""
    bf = ROOM / "доска.md"
    if bf.exists():
        board = bf.read_text(encoding="utf-8", errors="replace")[-15000:]
    files = []
    if ROOM.exists():
        for p in sorted(ROOM.iterdir()):
            if p.is_file() and not p.name.startswith("_") and p.name != "доска.md":
                files.append({"name": p.name,
                              "content": p.read_text(encoding="utf-8", errors="replace")[:8000]})
    scratch = {}
    sd = ROOM / "_scratch"
    if sd.exists():
        for p in sorted(sd.glob("*.txt")):
            scratch[p.stem] = p.read_text(encoding="utf-8", errors="replace")[-3000:]
    return {"log": lines, "board": board, "files": files, "scratch": scratch,
            "time": datetime.datetime.now().strftime("%H:%M:%S")}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path.startswith("/index"):
            body = HTML.encode("utf-8")
            ctype = "text/html; charset=utf-8"
        elif self.path.startswith("/api/state"):
            body = json.dumps(collect_state(), ensure_ascii=False).encode("utf-8")
            ctype = "application/json; charset=utf-8"
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    print(f"Дашборд: http://127.0.0.1:{PORT}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
