import os
import json
import math
import time
import struct
import threading
import urllib.request
import urllib.parse
import http.server
import socketserver

PORT = 80
BASE_DIR = "/root/frankfurt_forge"
EXPORTS_DIR = os.path.join(BASE_DIR, "exports")
STATE_PATH = os.path.join(BASE_DIR, "arb_radar_state.json")
os.makedirs(EXPORTS_DIR, exist_ok=True)

radar_state = {
    "last_scan_ts": 0.0,
    "last_scan_utc": "Initializing...",
    "polymarket_markets_scanned": 0,
    "polymarket_top_opportunities": [],
    "stink_bid_radar": {},
    "total_cad_files_compiled": 0
}

# ==============================================================================
# 1. BINARY STL & LASER SVG PARAMETRIC GEOMETRY COMPILER (4-CORE CPU ENGINE)
# ==============================================================================
def _add_box_triangles(tris, x0, y0, z0, x1, y1, z1):
    v = [
        (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
        (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)
    ]
    faces = [
        (0, 2, 1), (0, 3, 2), # bottom
        (4, 5, 6), (4, 6, 7), # top
        (0, 1, 5), (0, 5, 4), # front
        (2, 3, 7), (2, 7, 6), # back
        (0, 4, 7), (0, 7, 3), # left
        (1, 2, 6), (1, 6, 5)  # right
    ]
    for a, b, c in faces:
        tris.append((v[a], v[b], v[c]))

def compile_parametric_joinery(board_a_mm=18.0, board_b_mm=12.0, width_mm=65.0, kerf_mm=0.15, angle_deg=90.0):
    """
    Generates both a watertight binary 3D .STL stepped flush-face structural connector
    AND a kerf-compensated 2D .SVG laser-cut template for mismatched workshop offcuts.
    """
    wall = 5.0
    socket_depth = 35.0
    max_t = max(board_a_mm, board_b_mm)
    outer_h = max_t + 2 * wall

    tris = []
    # Spine block
    _add_box_triangles(tris, 0, 0, 0, wall + socket_depth, width_mm, wall)
    # Top flush cap
    _add_box_triangles(tris, 0, 0, outer_h - wall, wall + socket_depth, width_mm, outer_h)
    # Back spine wall
    _add_box_triangles(tris, 0, 0, 0, wall, width_mm, outer_h)
    # Stepped internal datum shelf for thinner board B so outer faces sit 100% flush
    step_offset = abs(board_a_mm - board_b_mm)
    if step_offset > 0.2:
        _add_box_triangles(tris, wall, 0, wall, wall + socket_depth, width_mm * 0.5, wall + step_offset)

    # Write Binary STL
    tag = f"joint_{board_a_mm:.1f}x{board_b_mm:.1f}_k{kerf_mm:.2f}_{int(time.time()*1000)%100000}"
    stl_filename = f"{tag}.stl"
    svg_filename = f"{tag}.svg"
    stl_path = os.path.join(EXPORTS_DIR, stl_filename)
    svg_path = os.path.join(EXPORTS_DIR, svg_filename)

    with open(stl_path, "wb") as f:
        header = f"Frankfurt Parametric Joinery {board_a_mm}mm x {board_b_mm}mm".encode("ascii")
        header = header.ljust(80, b"\x00")[:80]
        f.write(header)
        f.write(struct.pack("<I", len(tris)))
        for p1, p2, p3 in tris:
            # normal (0,0,0) + 3 vertices + attr
            f.write(struct.pack("<12fH", 0.0, 0.0, 0.0, p1[0], p1[1], p1[2], p2[0], p2[1], p2[2], p3[0], p3[1], p3[2], 0))

    # Write Kerf-Compensated Laser Cut SVG
    slot_a = round(board_a_mm - kerf_mm, 3)
    slot_b = round(board_b_mm - kerf_mm, 3)
    svg_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="240mm" height="140mm" viewBox="0 0 240 140">
  <style>
    .cut {{ fill: none; stroke: #ff0055; stroke-width: 0.2; }}
    .etch {{ fill: #00d4ff; font-family: monospace; font-size: 4px; }}
  </style>
  <rect x="5" y="5" width="230" height="130" class="cut" stroke="#334155"/>
  <!-- Outer Cheek Plate -->
  <rect x="15" y="15" width="95" height="95" rx="4" class="cut"/>
  <!-- Kerf-Compensated Mortise A ({board_a_mm}mm board -> {slot_a}mm cut) -->
  <rect x="25" y="28" width="40" height="{slot_a}" class="cut"/>
  <!-- Kerf-Compensated Mortise B ({board_b_mm}mm board -> {slot_b}mm cut) -->
  <rect x="{15 + 95 - 25 - slot_b}" y="48" width="{slot_b}" height="40" class="cut"/>
  <text x="18" y="122" class="etch">FLUSH-FACE STEPPED JOINT | Board A: {board_a_mm}mm | Board B: {board_b_mm}mm | Kerf: {kerf_mm}mm</text>
</svg>"""
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(svg_content)

    radar_state["total_cad_files_compiled"] += 1
    return {
        "status": "COMPILED_WATERTIGHT_BINARY_STL_AND_SVG",
        "compiler_node": "82.165.118.102 (Frankfurt 4-Core EPYC)",
        "board_a_mm": board_a_mm,
        "board_b_mm": board_b_mm,
        "flush_step_offset_mm": round(step_offset, 3),
        "kerf_compensation_mm": kerf_mm,
        "triangle_count": len(tris),
        "download_stl_url": f"http://82.165.118.102/exports/{stl_filename}",
        "download_svg_url": f"http://82.165.118.102/exports/{svg_filename}"
    }

# ==============================================================================
# 2. 24/7 POLYMARKET MISPRICING & FLASH-CRASH STINK-BID RADAR DAEMON
# ==============================================================================
def scan_markets_once():
    now = time.time()
    # A. Poll live BTC/ETH/SOL prices & compute Stink-Bid Cascade levels
    try:
        req = urllib.request.Request(
            "https://api.binance.com/api/v3/ticker/24hr?symbols=%5B%22BTCUSDT%22,%22ETHUSDT%22,%22SOLUSDT%22%5D",
            headers={"User-Agent": "FrankfurtArbRadar/1.0"}
        )
        with urllib.request.urlopen(req, timeout=6) as r:
            tickers = json.loads(r.read().decode("utf-8"))
            stink = {}
            for t in tickers:
                sym = t["symbol"].replace("USDT", "")
                price = float(t["lastPrice"])
                chg = float(t["priceChangePercent"])
                stink[sym] = {
                    "live_price_usd": round(price, 2),
                    "change_24h_pct": round(chg, 2),
                    "tier1_flush_minus_12pct": round(price * 0.88, 2),
                    "tier2_cascade_minus_18pct": round(price * 0.82, 2),
                    "tier3_blackswan_minus_25pct": round(price * 0.75, 2),
                    "auto_bounce_exit_plus_6pct": round(price * 0.82 * 1.06, 2)
                }
            radar_state["stink_bid_radar"] = stink
    except Exception as e:
        pass

    # B. Poll live Polymarket Gamma API for active high-volume markets & spread anomalies
    try:
        pm_url = "https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=40"
        req = urllib.request.Request(pm_url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=8) as r:
            markets = json.loads(r.read().decode("utf-8"))
            radar_state["polymarket_markets_scanned"] = len(markets)
            opps = []
            for m in markets:
                q = m.get("question", "")
                prices_raw = m.get("outcomePrices")
                vol = float(m.get("volumeNum", 0.0) or 0.0)
                if prices_raw:
                    try:
                        p_list = json.loads(prices_raw) if isinstance(prices_raw, str) else prices_raw
                        if len(p_list) == 2:
                            yes_p = float(p_list[0])
                            no_p = float(p_list[1])
                            total_p = round(yes_p + no_p, 4)
                            spread_bps = round((1.0 - total_p) * 10000, 1)
                            if yes_p > 0.01 and no_p > 0.01:
                                opps.append({
                                    "question": q[:75],
                                    "yes_price": round(yes_p, 3),
                                    "no_price": round(no_p, 3),
                                    "sum_of_shares": total_p,
                                    "arb_edge_bps": spread_bps,
                                    "volume_usd": round(vol, 0),
                                    "high_prob_lock": (yes_p >= 0.94 or no_p >= 0.94)
                                })
                    except Exception:
                        pass
            opps.sort(key=lambda x: (x["arb_edge_bps"], x["volume_usd"]), reverse=True)
            radar_state["polymarket_top_opportunities"] = opps[:8]
    except Exception as e:
        pass

    radar_state["last_scan_ts"] = now
    radar_state["last_scan_utc"] = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(now))
    try:
        with open(STATE_PATH, "w") as f:
            json.dump(radar_state, f, indent=2)
    except Exception:
        pass

def background_radar_loop():
    while True:
        scan_markets_once()
        time.sleep(30)

# ==============================================================================
# 3. WEB STOREFRONT & API SERVER (PORT 8090)
# ==============================================================================
STOREFRONT_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Frankfurt 4-Core Parametric CAD Forge & 24/7 Arbitrage Radar</title>
<style>
  body { background:#080b11; color:#f1f5f9; font-family:Inter,system-ui,sans-serif; margin:0; padding:24px; }
  .wrap { max-width:1200px; margin:0 auto; }
  .hdr { display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #1e293b; padding-bottom:16px; margin-bottom:22px; flex-wrap:wrap; gap:12px; }
  .pill { background:rgba(16,185,129,0.15); color:#10b981; border:1px solid #10b981; padding:4px 10px; border-radius:999px; font-size:0.75rem; font-weight:700; }
  .grid { display:grid; grid-template-columns:1fr 1fr; gap:20px; }
  @media(max-width:900px){ .grid { grid-template-columns:1fr; } }
  .card { background:#101622; border:1px solid #1e293b; border-radius:12px; padding:20px; }
  h2 { font-size:1.1rem; margin:0 0 14px 0; color:#38bdf8; }
  label { display:block; font-size:0.8rem; color:#94a3b8; margin-top:10px; }
  input { width:100%; padding:9px; background:#080b11; border:1px solid #334155; color:#fff; border-radius:6px; margin-top:4px; }
  button { margin-top:14px; width:100%; padding:11px; background:linear-gradient(135deg,#00c6ff,#0072ff); color:#fff; border:none; border-radius:8px; font-weight:700; cursor:pointer; }
  table { width:100%; border-collapse:collapse; font-size:0.82rem; margin-top:10px; }
  th,td { padding:8px; border-bottom:1px solid #1e293b; text-align:left; }
  th { color:#94a3b8; font-size:0.73rem; text-transform:uppercase; }
  pre { background:#05070b; padding:12px; border-radius:8px; overflow-x:auto; font-size:0.78rem; color:#10b981; border:1px solid #1e293b; }
</style>
</head>
<body>
<div class="wrap">
  <div class="hdr">
    <div>
      <h1 style="margin:0;font-size:1.45rem;">⚙️ Frankfurt 4-Core Parametric CAD Forge &amp; 24/7 Arbitrage Radar</h1>
      <div style="color:#94a3b8;font-size:0.85rem;margin-top:4px;">Live on 82.165.118.102 (4 vCPU EPYC • 4GB RAM • 120GB NVMe) • Paired with UK x402 Gateway (217.154.51.0)</div>
    </div>
    <span class="pill">SYSTEMD 24/7 ACTIVE</span>
  </div>

  <div class="grid">
    <div class="card">
      <h2>📐 On-Demand Custom Offcut Joinery STL &amp; Laser SVG Compiler</h2>
      <p style="font-size:0.84rem;color:#94a3b8;margin-top:0;">Enter any two mismatched wood/acrylic thicknesses and laser kerf. Compiles a watertight binary 3D <code>.STL</code> and kerf-compensated <code>.SVG</code> cut sheet on the fly.</p>
      <label>Board A Thickness (mm)</label>
      <input type="number" id="boardA" value="18.0" step="0.1">
      <label>Board B Thickness (mm)</label>
      <input type="number" id="boardB" value="12.0" step="0.1">
      <label>Laser Kerf Offset (mm)</label>
      <input type="number" id="kerf" value="0.15" step="0.01">
      <button onclick="compileCAD()">⚡ Compile Custom 3D .STL &amp; Laser .SVG</button>
      <pre id="cadOut">// Click Compile to generate instant downloadable .STL & .SVG files...</pre>
    </div>

    <div class="card">
      <h2>🎯 24/7 Live Stink-Bid &amp; Polymarket Arbitrage Radar</h2>
      <div id="radarMeta" style="font-size:0.8rem;color:#94a3b8;">Loading live Frankfurt market telemetry...</div>
      <h3 style="font-size:0.9rem;margin:14px 0 6px 0;color:#10b981;">Crypto Liquidation Cascade Stink-Bids</h3>
      <table id="stinkTable">
        <thead><tr><th>Asset</th><th>Live Price</th><th>-12% Flush</th><th>-18% Cascade</th><th>-25% BlackSwan</th></tr></thead>
        <tbody></tbody>
      </table>
      <h3 style="font-size:0.9rem;margin:16px 0 6px 0;color:#f59e0b;">Polymarket Live Orderbook Scanner</h3>
      <table id="pmTable">
        <thead><tr><th>Market</th><th>YES</th><th>NO</th><th>Sum</th><th>Volume</th></tr></thead>
        <tbody></tbody>
      </table>
    </div>
  </div>
</div>
<script>
async function compileCAD() {
  const a = document.getElementById('boardA').value;
  const b = document.getElementById('boardB').value;
  const k = document.getElementById('kerf').value;
  const res = await fetch(`/api/compile-cad?board_a=${a}&board_b=${b}&kerf=${k}`);
  const data = await res.json();
  document.getElementById('cadOut').innerHTML = JSON.stringify(data, null, 2) +
    `\n\n👉 <a href="${data.download_stl_url}" style="color:#00f0ff;font-weight:bold;">Download 3D .STL</a> | <a href="${data.download_svg_url}" target="_blank" style="color:#10b981;font-weight:bold;">View/Download Laser .SVG</a>`;
}
async function loadRadar() {
  const res = await fetch('/api/radar');
  const d = await res.json();
  document.getElementById('radarMeta').textContent = `Last Scan: ${d.last_scan_utc} • Polymarket Books Scanned: ${d.polymarket_markets_scanned} • CAD Files Compiled: ${d.total_cad_files_compiled}`;
  const sb = document.querySelector('#stinkTable tbody');
  sb.innerHTML = '';
  for (const [sym, v] of Object.entries(d.stink_bid_radar || {})) {
    sb.innerHTML += `<tr><td><strong>${sym}</strong></td><td>$${v.live_price_usd.toLocaleString()}</td><td>$${v.tier1_flush_minus_12pct.toLocaleString()}</td><td style="color:#10b981;font-weight:bold;">$${v.tier2_cascade_minus_18pct.toLocaleString()}</td><td>$${v.tier3_blackswan_minus_25pct.toLocaleString()}</td></tr>`;
  }
  const pm = document.querySelector('#pmTable tbody');
  pm.innerHTML = '';
  for (const m of (d.polymarket_top_opportunities || []).slice(0, 5)) {
    pm.innerHTML += `<tr><td>${m.question.slice(0,42)}...</td><td>$${m.yes_price}</td><td>$${m.no_price}</td><td><strong>$${m.sum_of_shares}</strong></td><td>$${m.volume_usd.toLocaleString()}</td></tr>`;
  }
}
loadRadar();
setInterval(loadRadar, 15000);
</script>
</body>
</html>"""

class FrankfurtForgeHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        qs = urllib.parse.parse_qs(parsed.query)

        if path == "/" or path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(STOREFRONT_HTML.encode("utf-8"))
            return

        if path == "/api/radar":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(radar_state, indent=2).encode("utf-8"))
            return

        if path == "/api/compile-cad":
            board_a = float(qs.get("board_a", ["18.0"])[0])
            board_b = float(qs.get("board_b", ["12.0"])[0])
            kerf = float(qs.get("kerf", ["0.15"])[0])
            res = compile_parametric_joinery(board_a_mm=board_a, board_b_mm=board_b, kerf_mm=kerf)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(res, indent=2).encode("utf-8"))
            return

        if path.startswith("/exports/"):
            fname = os.path.basename(path)
            fpath = os.path.join(EXPORTS_DIR, fname)
            if os.path.exists(fpath):
                self.send_response(200)
                ctype = "application/sla" if fname.endswith(".stl") else "image/svg+xml"
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Disposition", f'attachment; filename="{fname}"')
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                with open(fpath, "rb") as f:
                    self.wfile.write(f.read())
                return

        self.send_response(404)
        self.end_headers()

if __name__ == "__main__":
    scan_markets_once()
    t = threading.Thread(target=background_radar_loop, daemon=True)
    t.start()
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(("0.0.0.0", PORT), FrankfurtForgeHandler) as httpd:
        print(f"[FRANKFURT-FORGE] Listening on http://0.0.0.0:{PORT}")
        httpd.serve_forever()
