#!/usr/bin/env python3
"""
War Room Dashboard Generator
Reads all local/brainstorms/YYYY-MM.md session files + local/PORTFOLIO.md and emits
a self-contained local/dashboard.html with charts and tables.

Usage:
    python3 scripts/generate_dashboard.py

Output:
    local/dashboard.html (open in any browser, no server needed)
"""

import re
import json
from pathlib import Path
from datetime import datetime

try:
    import yfinance as yf
    HAS_YFINANCE = True
except ImportError:
    HAS_YFINANCE = False

BASE = Path(__file__).parent.parent

CHART_JS_URL = "https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"
MARKED_JS_URL = "https://cdn.jsdelivr.net/npm/marked@12/marked.min.js"
FONTS_URL = "https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap"


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------

def parse_frontmatter(text: str) -> dict:
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return {}
    fm = {}
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        fm[key.strip()] = val.strip().strip('"')
    trades = re.findall(r"^\s+-\s+(.+)$", m.group(1), re.MULTILINE)
    if trades:
        fm["trades"] = [t.strip() for t in trades]
    return fm


def parse_sessions() -> list:
    sessions = []
    for path in sorted(BASE.glob("local/brainstorms/[0-9][0-9][0-9][0-9]-[0-9][0-9].md")):
        text = path.read_text()
        fm = parse_frontmatter(text)
        if not fm:
            continue
        s = {
            "file": path.name,
            "date": fm.get("date", ""),
            "session": fm.get("session", path.stem),
            "session_number": int(fm.get("session_number", 0)),
            "status": fm.get("status", ""),
            "regime": fm.get("regime", "unknown"),
            "ecb_rate": fm.get("ecb_rate", ""),
            "trades": fm.get("trades", []),
            "nav_invested_pct": _pct(fm.get("nav_invested", "0%")),
            "nav_cash_pct": _pct(fm.get("nav_cash", "100%")),
        }
        gate_m = re.search(r"(\d+)\s*GREEN\s*/\s*(\d+)\s*AMBER\s*/\s*(\d+)\s*RED", text)
        if gate_m:
            s["gates_green"] = int(gate_m.group(1))
            s["gates_amber"] = int(gate_m.group(2))
            s["gates_red"]   = int(gate_m.group(3))
        p7_m = re.search(r"\*\*Summary:\s*(\d+)\s*APPROVE,\s*(\d+)\s*FLAG,\s*(\d+)\s*BLOCK", text)
        if p7_m:
            s["p7_approve"] = int(p7_m.group(1))
            s["p7_flag"]    = int(p7_m.group(2))
            s["p7_block"]   = int(p7_m.group(3))
        dep_m = re.search(r"This session:\s*€([\d,]+)\s*/\s*€([\d,]+)\s*\(([\d.]+)%\)", text)
        if dep_m:
            s["deploy_pct"] = float(dep_m.group(3))
        s["raw_md"] = re.sub(r"^---\n.*?\n---\n", "", text, count=1, flags=re.DOTALL)
        sessions.append(s)
    return sessions


def parse_portfolio() -> dict:
    path = BASE / "local" / "PORTFOLIO.md"
    if not path.exists():
        return {"holdings": []}
    text = path.read_text()
    holdings = []
    section = re.search(
        r"## Current Holdings\n(.*?)(?=### Example Entry|^## |\Z)",
        text, re.DOTALL | re.MULTILINE)
    if not section:
        return {"holdings": []}
    for line in section.group(1).splitlines():
        if not line.startswith("| ") or "---" in line:
            continue
        cols = [c.strip() for c in line.strip("|").split("|")]
        if len(cols) < 8 or cols[0] in ("Ticker", ""):
            continue
        # Support optional ISIN column between Ticker and Name
        has_isin = len(cols) >= 10 and cols[1].startswith("IE") or (len(cols) >= 10 and len(cols[1]) == 12)
        if has_isin:
            isin, name, entry_date, qty, price, cost, strategy, stop, status = (
                cols[1], cols[2], cols[3], cols[4], cols[5], cols[6], cols[7], cols[8], cols[9] if len(cols) > 9 else ""
            )
        else:
            isin, name, entry_date, qty, price, cost, strategy, stop, status = (
                "", cols[1], cols[2], cols[3], cols[4], cols[5], cols[6], cols[7], cols[8] if len(cols) > 8 else ""
            )
        holdings.append({
            "ticker":      cols[0],
            "isin":        isin,
            "name":        name,
            "entry_date":  entry_date,
            "quantity":    qty,
            "entry_price": price,
            "entry_cost":  cost,
            "strategy":    strategy,
            "stop_loss":   stop,
            "status":      status,
        })
    return {"holdings": holdings}


def get_prices(holdings: list) -> dict:
    """Fetch live prices keyed by ticker.
    Uses ISIN only for bare tickers (no exchange suffix) to avoid USD/EUR ambiguity.
    Tickers with a suffix (e.g. VWCE.DE) are looked up directly — already unambiguous.
    """
    if not HAS_YFINANCE or not holdings:
        return {}
    prices = {}
    for h in holdings:
        ticker = h["ticker"]
        isin   = h.get("isin", "")
        lookup = isin if (isin and "." not in ticker) else ticker
        try:
            prices[ticker] = round(float(yf.Ticker(lookup).fast_info.last_price), 2)
        except Exception:
            pass
    return prices


def _pct(s: str) -> float:
    try:
        return float(s.replace("%", "").strip())
    except ValueError:
        return 0.0


def _js(v) -> str:
    return json.dumps(v)


def _pnl_html(entry_str: str, live, qty_str: str) -> str:
    try:
        entry = float(str(entry_str).replace("€","").replace(",","").strip())
        qty   = float(str(qty_str).strip())
        if isinstance(live, (int, float)):
            diff = (live - entry) * qty
            pct  = (live - entry) / entry * 100
            sign = "+" if diff >= 0 else ""
            cls  = "pnl-pos" if diff >= 0 else "pnl-neg"
            return f'<span class="{cls}">{sign}€{diff:.2f} <small>({sign}{pct:.2f}%)</small></span>'
    except Exception:
        pass
    return '<span class="pnl-neu">—</span>'


def _strategy_badge(strategy: str) -> str:
    s = strategy.lower()
    if "defence" in s or "defense" in s or "rearmament" in s:
        return f'<span class="badge badge-teal">{strategy}</span>'
    if "global" in s or "equity" in s or "core" in s:
        return f'<span class="badge badge-blue">{strategy}</span>'
    if "gold" in s or "commodity" in s:
        return f'<span class="badge badge-amber">{strategy}</span>'
    return f'<span class="badge badge-muted">{strategy}</span>'


def _status_badge(status: str) -> str:
    s = status.lower()
    if "open" in s:
        return '<span class="badge badge-green"><span class="badge-dot"></span>OPEN</span>'
    if "pending" in s:
        return '<span class="badge badge-amber"><span class="badge-dot"></span>PENDING FILL</span>'
    if "closed" in s:
        return '<span class="badge badge-red"><span class="badge-dot"></span>CLOSED</span>'
    return f'<span class="badge badge-muted">{status}</span>'


# ---------------------------------------------------------------------------
# Static CSS (raw string — no f-string escaping needed)
# ---------------------------------------------------------------------------

CSS = """:root{--bg:#0b0d15;--surface:#11141f;--surface2:#181c2c;--surface3:#1e2235;--border:#252a40;--border2:#2e3450;--text:#dde3f0;--text2:#a8b2c8;--muted:#6b7592;--blue:#4a82f5;--blue-dim:rgba(74,130,245,0.12);--green:#1ec870;--green-dim:rgba(30,200,112,0.12);--amber:#f0a229;--amber-dim:rgba(240,162,41,0.12);--red:#e84545;--red-dim:rgba(232,69,69,0.12);--teal:#22d4bf;--teal-dim:rgba(34,212,191,0.10);--purple:#9b7ef8;--purple-dim:rgba(155,126,248,0.10);--radius:8px;--radius-lg:12px;--mono:'JetBrains Mono','SF Mono',monospace;--sans:'Space Grotesk',system-ui,sans-serif;}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}body{background:var(--bg);color:var(--text);font-family:var(--sans);font-size:14px;line-height:1.6;-webkit-font-smoothing:antialiased;}a{color:var(--blue);text-decoration:none;}
header{background:var(--surface);border-bottom:1px solid var(--border);padding:0 36px;}.header-inner{display:flex;align-items:center;justify-content:space-between;gap:16px;height:64px;}.header-brand{display:flex;align-items:center;gap:12px;flex-shrink:0;}.header-icon{width:34px;height:34px;background:var(--blue-dim);border:1px solid rgba(74,130,245,0.3);border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:15px;line-height:1;flex-shrink:0;}.header-brand h1{font-size:14px;font-weight:700;letter-spacing:-0.01em;color:var(--text);}.header-brand .sub{font-size:10px;color:var(--muted);font-family:var(--mono);}.regime-badge{display:flex;align-items:center;gap:8px;background:rgba(240,162,41,0.1);border:1px solid rgba(240,162,41,0.3);border-radius:6px;padding:6px 14px;flex-shrink:0;}.regime-dot{width:7px;height:7px;border-radius:50%;background:var(--amber);box-shadow:0 0 8px var(--amber);animation:pulse-a 2s ease-in-out infinite;}@keyframes pulse-a{0%,100%{opacity:1;}50%{opacity:.4;}}.regime-label{font-size:11px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:var(--amber);font-family:var(--mono);}.header-meta{display:flex;align-items:center;gap:16px;font-size:11px;color:var(--muted);font-family:var(--mono);}.header-meta .sep{color:var(--border2);}.header-meta strong{color:var(--text2);font-weight:500;}
.tab-bar{display:flex;border-bottom:1px solid var(--border);background:var(--surface);padding:0 36px;}.tab-btn{padding:13px 20px;font-family:var(--sans);font-size:13px;font-weight:600;color:var(--muted);background:none;border:none;border-bottom:2px solid transparent;cursor:pointer;transition:color .12s;margin-bottom:-1px;}.tab-btn:hover{color:var(--text2);}.tab-btn.active{color:var(--text);border-bottom-color:var(--blue);}.tab-panel{display:none;}.tab-panel.active{display:block;}
.container{max-width:1320px;margin:0 auto;padding:28px 36px;}.section-hd{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:18px;padding-bottom:14px;border-bottom:1px solid var(--border);position:relative;}.section-hd::before{content:'';position:absolute;bottom:-1px;left:0;width:48px;height:2px;}.section-hd.blue::before{background:var(--blue);}.section-hd.green::before{background:var(--green);}.section-hd.amber::before{background:var(--amber);}.section-hd-left{display:flex;flex-direction:column;gap:3px;}.section-tag{font-family:var(--mono);font-size:10px;font-weight:600;letter-spacing:.12em;text-transform:uppercase;}.section-hd.blue .section-tag{color:var(--blue);}.section-hd.green .section-tag{color:var(--green);}.section-hd.amber .section-tag{color:var(--amber);}.section-name{font-size:17px;font-weight:700;color:var(--text);letter-spacing:-.02em;}.section-desc{font-size:12px;color:var(--muted);}section{margin-bottom:36px;}
.kpi-grid{display:grid;grid-template-columns:repeat(6,1fr);gap:12px;margin-bottom:32px;}.kpi{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-lg);padding:18px 18px 14px;position:relative;overflow:hidden;}.kpi::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;}.kpi.blue::before{background:var(--blue);}.kpi.green::before{background:var(--green);}.kpi.amber::before{background:var(--amber);}.kpi.red::before{background:var(--red);}.kpi.teal::before{background:var(--teal);}.kpi.purple::before{background:var(--purple);}.kpi-label{font-size:10px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin-bottom:8px;font-family:var(--mono);}.kpi-value{font-family:var(--mono);font-size:1.9rem;font-weight:600;line-height:1;letter-spacing:-.02em;}.kpi-value.green{color:var(--green);}.kpi-value.amber{color:var(--amber);}.kpi-value.blue{color:var(--blue);}.kpi-value.teal{color:var(--teal);}.kpi-sub{font-size:11px;color:var(--muted);margin-top:6px;}.kpi-p7{font-family:var(--mono);font-size:1.05rem;font-weight:600;line-height:1;display:flex;gap:5px;align-items:center;margin-top:2px;}
.chart-grid-3{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:16px;}.chart-grid-2{display:grid;grid-template-columns:repeat(2,1fr);gap:16px;margin-bottom:16px;}.chart-card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-lg);padding:18px;}.chart-card-title{font-size:10px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin-bottom:3px;font-family:var(--mono);}.chart-card-subtitle{font-size:12px;color:var(--text2);margin-bottom:14px;}.chart-wrap{position:relative;height:190px;}
.table-card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-lg);overflow:hidden;}table{width:100%;border-collapse:collapse;font-size:13px;}th{text-align:left;padding:9px 14px;background:var(--surface2);border-bottom:1px solid var(--border2);color:var(--muted);font-weight:600;font-size:10px;text-transform:uppercase;letter-spacing:.08em;white-space:nowrap;font-family:var(--mono);}td{padding:10px 14px;border-bottom:1px solid var(--border);vertical-align:middle;}tr:last-child td{border-bottom:none;}tbody tr:hover td{background:var(--surface2);}.ticker{font-family:var(--mono);font-weight:600;color:var(--text);}.name-cell{color:var(--text2);font-size:12px;}.mono{font-family:var(--mono);font-size:12px;}
.badge{display:inline-flex;align-items:center;gap:4px;padding:3px 8px;border-radius:5px;font-size:11px;font-weight:600;font-family:var(--mono);letter-spacing:.04em;}.badge-green{background:var(--green-dim);color:var(--green);}.badge-amber{background:var(--amber-dim);color:var(--amber);}.badge-red{background:var(--red-dim);color:var(--red);}.badge-blue{background:var(--blue-dim);color:var(--blue);}.badge-teal{background:var(--teal-dim);color:var(--teal);}.badge-muted{background:var(--surface3);color:var(--muted);border:1px solid var(--border);}.badge-dot{width:5px;height:5px;border-radius:50%;background:currentColor;}.pnl-pos{color:var(--green);font-family:var(--mono);font-weight:600;}.pnl-neg{color:var(--red);font-family:var(--mono);font-weight:600;}.pnl-neu{color:var(--muted);font-family:var(--mono);}.live-price{color:var(--green);font-family:var(--mono);font-weight:600;}.regime-tag{display:inline-block;background:var(--surface3);border:1px solid var(--border2);border-radius:5px;padding:2px 8px;font-size:11px;color:var(--text2);font-family:var(--mono);}.notice{font-size:11px;color:var(--muted);margin-top:10px;font-family:var(--mono);}.notice.warn{color:var(--amber);}.notice code{background:var(--surface2);border:1px solid var(--border);border-radius:4px;padding:1px 6px;}
.reports-layout{display:grid;grid-template-columns:220px 1fr;min-height:calc(100vh - 113px);}.report-sidebar{background:var(--surface);border-right:1px solid var(--border);padding:20px 12px;display:flex;flex-direction:column;gap:2px;position:sticky;top:0;height:calc(100vh - 113px);overflow-y:auto;}.report-sidebar-label{font-family:var(--mono);font-size:10px;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);padding:0 10px;margin-bottom:8px;}.report-nav-btn{text-align:left;padding:8px 12px;border-radius:6px;border:none;background:none;color:var(--text2);font-family:var(--sans);font-size:13px;font-weight:500;cursor:pointer;transition:background .1s,color .1s;display:flex;align-items:center;gap:8px;width:100%;}.report-nav-btn:hover{background:var(--surface2);color:var(--text);}.report-nav-btn.active{background:var(--surface2);color:var(--text);border-left:2px solid var(--blue);padding-left:10px;}.report-nav-btn .s-num{font-family:var(--mono);font-size:10px;color:var(--muted);background:var(--surface3);border-radius:4px;padding:1px 6px;flex-shrink:0;}.toc-sep{border-top:1px solid var(--border);margin:12px 4px 10px;}.toc-heading{font-family:var(--mono);font-size:10px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);padding:0 10px;margin-bottom:6px;display:none;}.toc-btn{text-align:left;padding:5px 10px;border-radius:5px;border:none;background:none;color:var(--muted);font-family:var(--mono);font-size:10px;cursor:pointer;width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;transition:background .1s,color .1s;}.toc-btn:hover{background:var(--surface2);color:var(--text2);}.toc-btn.phase{color:var(--blue);}
.report-right{display:flex;flex-direction:column;min-width:0;}.report-meta-strip{display:flex;align-items:center;gap:16px;flex-wrap:wrap;background:var(--surface2);border-bottom:1px solid var(--border);padding:12px 40px;font-family:var(--mono);font-size:11px;}.rms-item{display:flex;align-items:center;gap:6px;}.rms-label{color:var(--muted);}.rms-val{color:var(--text2);font-weight:500;}.rms-sep{color:var(--border2);}.report-main{padding:32px 40px;max-width:900px;}
.md-body h1{font-size:1.45rem;font-weight:700;letter-spacing:-.02em;color:var(--text);margin:0 0 20px;padding-bottom:14px;border-bottom:1px solid var(--border);}.md-body h2{font-size:1rem;font-weight:700;color:var(--text);margin:30px 0 10px;display:flex;align-items:center;gap:8px;}.md-body h2::before{content:'';display:inline-block;width:3px;height:13px;background:var(--blue);border-radius:2px;flex-shrink:0;}.md-body h3{font-size:.85rem;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;margin:18px 0 8px;}.md-body p{margin:0 0 11px;color:var(--text2);line-height:1.75;}.md-body ul,.md-body ol{margin:0 0 11px 18px;}.md-body li{margin-bottom:5px;color:var(--text2);line-height:1.65;}.md-body strong{color:var(--text);font-weight:700;}.md-body a{color:var(--blue);}.md-body hr{border:none;border-top:1px solid var(--border);margin:26px 0;}.md-body code{background:var(--surface2);border:1px solid var(--border);border-radius:4px;padding:1px 6px;font-family:var(--mono);font-size:12px;color:var(--teal);}.md-body pre{background:var(--surface2);border:1px solid var(--border);border-radius:8px;padding:14px 16px;overflow-x:auto;margin:12px 0;}.md-body pre code{background:none;border:none;padding:0;color:var(--text2);}.md-body blockquote{border-left:3px solid var(--border2);padding:8px 14px;color:var(--muted);margin:12px 0;background:var(--surface2);border-radius:0 6px 6px 0;}
.tbl-scroll{overflow-x:auto;-webkit-overflow-scrolling:touch;border-radius:var(--radius);border:1px solid var(--border);margin:14px 0;}.md-body table{width:100%;border-collapse:collapse;font-size:12.5px;min-width:420px;}.md-body th{text-align:left;padding:8px 12px;background:var(--surface2);border-bottom:1px solid var(--border2);color:var(--muted);font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.08em;font-family:var(--mono);}.md-body td{padding:8px 12px;border-bottom:1px solid var(--border);vertical-align:top;color:var(--text2);}.md-body tr:last-child td{border-bottom:none;}.md-body tr:hover td{background:var(--surface2);}.td-ok{color:var(--green)!important;}.td-warn{color:var(--amber)!important;}
.callout{border-radius:8px;padding:12px 16px;margin:12px 0;border-left:3px solid;}.callout-info{background:var(--blue-dim);border-color:var(--blue);}.callout-warning{background:var(--amber-dim);border-color:var(--amber);}.callout-important{background:var(--red-dim);border-color:var(--red);}.callout-tip{background:var(--green-dim);border-color:var(--green);}.callout-title{font-family:var(--mono);font-size:10px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;margin-bottom:5px;}.callout-info .callout-title{color:var(--blue);}.callout-warning .callout-title{color:var(--amber);}.callout-important .callout-title{color:var(--red);}.callout-tip .callout-title{color:var(--green);}.callout p,.callout li{color:var(--text2)!important;margin-bottom:0!important;}.callout p:not(:last-child){margin-bottom:5px!important;}
.ph-badge{display:inline-flex;align-items:center;justify-content:center;width:26px;height:26px;border-radius:6px;background:var(--blue-dim);border:1px solid rgba(74,130,245,0.35);color:var(--blue);font-size:9px;font-weight:700;font-family:var(--mono);margin-right:4px;flex-shrink:0;vertical-align:middle;}
.verdict-go{background:var(--green-dim)!important;border:1px solid rgba(30,200,112,.3)!important;border-left:3px solid var(--green)!important;border-radius:8px;padding:11px 16px!important;color:var(--green)!important;font-weight:700;font-family:var(--mono);font-size:13px;display:flex!important;align-items:center;gap:10px;margin:10px 0!important;}
.p9-bar{display:flex;align-items:center;gap:14px;flex-wrap:wrap;background:var(--surface2);border:1px solid var(--border2);border-radius:8px;padding:14px 18px;margin:12px 0;}.p9-bar .p9-num{font-family:var(--mono);font-weight:700;font-size:1.3rem;line-height:1;}.p9-bar .p9-approve{color:var(--green);}.p9-bar .p9-flag{color:var(--amber);}.p9-bar .p9-block{color:var(--red);}.p9-bar .p9-lbl{font-size:10px;font-family:var(--mono);text-transform:uppercase;letter-spacing:.06em;color:var(--muted);}.p9-bar .p9-group{display:flex;flex-direction:column;align-items:center;gap:2px;}.p9-bar .p9-div{width:1px;height:32px;background:var(--border2);}.p9-bar .p9-note{font-size:11px;color:var(--muted);margin-left:auto;font-style:italic;}
.trade-card{background:var(--surface2);border:1px solid var(--border2);border-left:3px solid var(--teal);border-radius:10px;padding:18px 20px;margin:16px 0;}.trade-card h3{color:var(--teal)!important;text-transform:none!important;letter-spacing:0!important;font-size:.95rem!important;margin:0 0 14px!important;font-weight:700;}.trade-card ul{margin:0!important;list-style:none;display:grid;grid-template-columns:1fr 1fr;gap:6px 20px;}.trade-card li{color:var(--text2)!important;font-size:12.5px;display:flex;gap:6px;}.trade-card li strong{color:var(--text)!important;font-family:var(--mono);font-size:12px;flex-shrink:0;}
.wtmfy-box{background:linear-gradient(135deg,var(--purple-dim),var(--blue-dim));border:1px solid rgba(155,126,248,.25);border-radius:10px;padding:20px 22px;margin:20px 0;}.wtmfy-box h3{color:var(--purple)!important;text-transform:none!important;letter-spacing:0!important;font-size:.95rem!important;margin:0 0 10px!important;font-weight:700;}.wtmfy-box p{color:var(--text)!important;line-height:1.8;font-size:13.5px;}
.concept-box{background:var(--surface2);border:1px solid var(--border2);border-top:2px solid var(--amber);border-radius:8px;padding:20px 22px;margin:20px 0;}.concept-box h2{color:var(--amber)!important;}.concept-box h2::before{background:var(--amber)!important;}.concept-box p{color:var(--text2)!important;}
.check-done,.check-open{list-style:none!important;padding-left:0;display:flex;align-items:flex-start;gap:8px;}.check-done::before{content:'✓';color:var(--green);font-weight:700;flex-shrink:0;margin-top:1px;}.check-open::before{content:'○';color:var(--muted);flex-shrink:0;margin-top:1px;}
@media(max-width:1100px){.kpi-grid{grid-template-columns:repeat(3,1fr);}}
@media(max-width:900px){.chart-grid-3{grid-template-columns:1fr;}.chart-grid-2{grid-template-columns:1fr;}header{padding:0 16px;}.container{padding:20px 16px;}.header-meta{display:none;}}
@media(max-width:768px){.kpi-grid{grid-template-columns:repeat(2,1fr);}.tab-bar{padding:0 16px;}.tab-btn{padding:11px 14px;font-size:12px;}.reports-layout{grid-template-columns:1fr;grid-template-rows:auto auto 1fr;}.report-sidebar{position:static;height:auto;flex-direction:row;flex-wrap:wrap;border-right:none;border-bottom:1px solid var(--border);padding:10px 12px;gap:6px;overflow-x:auto;}.report-sidebar-label{display:none;}.toc-sep,.toc-heading,.toc-btn{display:none;}.report-nav-btn{width:auto;}.report-meta-strip{padding:10px 16px;gap:10px;}.report-main{padding:20px 16px;}.trade-card ul{grid-template-columns:1fr;}.p9-bar .p9-note{display:none;}}
@media(max-width:500px){.kpi-grid{grid-template-columns:repeat(2,1fr);}.header-inner{height:auto;padding:10px 0;flex-wrap:wrap;}.regime-badge{order:3;width:100%;justify-content:center;}.header-brand h1{font-size:13px;}}
#dash-tip{position:fixed;z-index:9999;background:#11141f;border:1px solid var(--border2);border-radius:8px;padding:10px 13px;font-size:11px;font-family:var(--sans);color:var(--text);pointer-events:none;display:none;max-width:280px;box-shadow:0 8px 32px rgba(0,0,0,.55);line-height:1.5;}
#dash-tip .tip-title{font-size:10px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin-bottom:6px;}
#dash-tip .tip-row{display:flex;gap:8px;margin-bottom:3px;align-items:baseline;}
#dash-tip .tip-row:last-child{margin-bottom:0;}
#dash-tip .tip-name{font-family:var(--mono);font-size:10.5px;color:var(--text);white-space:nowrap;}
#dash-tip .tip-note{color:var(--text2);font-size:10px;}
#dash-tip .tip-empty{color:var(--muted);font-style:italic;font-size:10px;}"""


# ---------------------------------------------------------------------------
# Static render JS (raw string — backslashes preserved)
# ---------------------------------------------------------------------------

RENDER_JS = r"""
const CMAP={'INFO':'callout-info','WARNING':'callout-warning','IMPORTANT':'callout-important','TIP':'callout-tip','NOTE':'callout-info'};
function styleCallouts(el){el.querySelectorAll('blockquote').forEach(bq=>{const t=bq.textContent||'';const m=t.match(/\[!(INFO|WARNING|IMPORTANT|TIP|NOTE)\]/i);if(m){const type=m[1].toUpperCase();bq.classList.add('callout',CMAP[type]||'callout-info');const fp=bq.querySelector('p');if(fp){fp.innerHTML=fp.innerHTML.replace(/\[!(INFO|WARNING|IMPORTANT|TIP|NOTE)\]\s*/i,'');const td=document.createElement('div');td.className='callout-title';td.textContent=type;bq.insertBefore(td,fp);}}})}
const STATUS_EXACT={'GREEN':'badge-green','AMBER':'badge-amber','RED':'badge-red','APPROVE':'badge-green','APPROVED':'badge-green','FLAG':'badge-amber','BLOCK':'badge-red','YES':'badge-green','NO':'badge-muted','GO':'badge-green','COMPLETE':'badge-green','OK':'badge-green','FAIL':'badge-red'};
function colorizeTables(el){el.querySelectorAll('td').forEach(td=>{const raw=td.textContent.trim();if(STATUS_EXACT[raw]){td.innerHTML='<span class="badge '+STATUS_EXACT[raw]+'">'+raw+'</span>';return;}if(raw.startsWith('✅')){td.classList.add('td-ok');return;}if(raw.startsWith('⚠')){td.classList.add('td-warn');return;}const clean=raw.replace(/\*/g,'');if(STATUS_EXACT[clean]){td.innerHTML='<span class="badge '+STATUS_EXACT[clean]+'">'+clean+'</span>';return;}if(raw.length<60&&/\b(GREEN|AMBER|RED)\b/.test(raw)){td.innerHTML=td.innerHTML.replace(/\bGREEN\b/g,'<span class="badge badge-green">GREEN</span>').replace(/\bAMBER\b/g,'<span class="badge badge-amber">AMBER</span>').replace(/\bRED\b/g,'<span class="badge badge-red">RED</span>');}})}
function addPhaseBadges(el){el.querySelectorAll('h2').forEach(h2=>{const m=h2.textContent.match(/^Phase\s+(\d+)\s*:/i);if(!m)return;const b=document.createElement('span');b.className='ph-badge';b.textContent=String(parseInt(m[1])).padStart(2,'0');h2.insertBefore(b,h2.firstChild);})}
function addVerdictBanner(el){el.querySelectorAll('p').forEach(p=>{const t=p.textContent||'';if(t.includes('Verdict')&&t.includes('GO')&&t.length<120){p.classList.add('verdict-go');p.innerHTML='<span style="font-size:1.1em">\u2713</span> VERDICT: GO \u00a0<span style="font-weight:400;font-size:12px;color:var(--green);opacity:.8">(full deployment per gate framework)</span>';}})}
function addP9Bar(el){el.querySelectorAll('p,li').forEach(p=>{const m=p.textContent.match(/Summary:\s*(\d+)\s*APPROVE,\s*(\d+)\s*FLAG,\s*(\d+)\s*BLOCK/i);if(!m)return;const bar=document.createElement('div');bar.className='p9-bar';bar.innerHTML=`<div class="p9-group"><span class="p9-num p9-approve">${m[1]}</span><span class="p9-lbl">Approve</span></div><div class="p9-div"></div><div class="p9-group"><span class="p9-num p9-flag">${m[2]}</span><span class="p9-lbl">Flag</span></div><div class="p9-div"></div><div class="p9-group"><span class="p9-num p9-block">${m[3]}</span><span class="p9-lbl">Block</span></div><span class="p9-note">No trade hit 3+ legitimate flags \u2014 plan stands.</span>`;p.replaceWith(bar);})}
function styleTradeCards(el){el.querySelectorAll('h3').forEach(h3=>{if(!/^Trade\s+\d/i.test(h3.textContent))return;const card=document.createElement('div');card.className='trade-card';h3.parentNode.insertBefore(card,h3);card.appendChild(h3);let next=card.nextSibling;while(next&&next.nodeName!=='H2'&&next.nodeName!=='H3'&&next.nodeName!=='HR'){const n2=next.nextSibling;if(next.nodeName==='UL'||next.nodeName==='P'){card.appendChild(next);}next=n2;}})}
function styleWTMFY(el){el.querySelectorAll('h3').forEach(h3=>{if(!/What This Means/i.test(h3.textContent))return;const box=document.createElement('div');box.className='wtmfy-box';h3.parentNode.insertBefore(box,h3);box.appendChild(h3);let next=box.nextSibling;while(next&&next.nodeName==='P'){const n2=next.nextSibling;box.appendChild(next);next=n2;}})}
function styleConceptBox(el){el.querySelectorAll('h2').forEach(h2=>{if(!/Concept of the Month/i.test(h2.textContent))return;const box=document.createElement('div');box.className='concept-box';h2.parentNode.insertBefore(box,h2);box.appendChild(h2);let next=box.nextSibling;while(next&&(next.nodeName==='P'||next.nodeName==='UL')){const n2=next.nextSibling;box.appendChild(next);next=n2;}})}
function styleChecklists(el){el.querySelectorAll('li').forEach(li=>{const t=li.textContent;if(/^\[x\]/i.test(t)){li.classList.add('check-done');li.innerHTML=li.innerHTML.replace(/^\[x\]\s*/i,'');}else if(/^\[ \]/.test(t)){li.classList.add('check-open');li.innerHTML=li.innerHTML.replace(/^\[ \]\s*/,'');}})}
function wrapTables(el){el.querySelectorAll('table').forEach(t=>{if(t.parentElement.classList.contains('tbl-scroll'))return;const w=document.createElement('div');w.className='tbl-scroll';t.parentNode.insertBefore(w,t);w.appendChild(t);})}
function buildTOC(el){const toc=document.getElementById('report-toc');const tocSep=document.getElementById('toc-sep');const tocHead=document.getElementById('toc-heading');toc.innerHTML='';const headings=el.querySelectorAll('h2');if(!headings.length){tocSep.style.display='none';tocHead.style.display='none';return;}tocSep.style.display='';tocHead.style.display='';headings.forEach((h,i)=>{const id='rh-'+i;h.id=id;const btn=document.createElement('button');btn.className='toc-btn'+(h.textContent.match(/^Phase/i)?' phase':'');btn.textContent=h.textContent.replace(/^\d{2}\s*/,'').replace(/Phase (\d+):/,'Ph.$1:');btn.title=h.textContent;btn.onclick=()=>{const top=h.getBoundingClientRect().top+window.pageYOffset-90;window.scrollTo({top,behavior:'smooth'});};toc.appendChild(btn);})}
function buildMetaStrip(slug){const m=SESSION_META[slug]||{};const el=document.getElementById('report-meta');if(!m.num){el.innerHTML='';return;}const items=[['Session','#'+m.num],['Date',m.date||'\u2014'],['Regime',m.regime||'\u2014'],['Status',m.status||'\u2014'],['Deployed',m.deployed||'\u2014'],['Cash',m.cash||'\u2014'],m.verdict?['Verdict','<span style="color:var(--green);font-weight:700">'+m.verdict+'</span>']:null,m.p9?['Phase\u00a09',m.p9]:null,m.gates?['Gates',m.gates]:null].filter(Boolean);el.innerHTML=items.map((it,i)=>(i>0?'<span class="rms-sep">\u00b7</span>':'')+'<span class="rms-item"><span class="rms-label">'+it[0]+'</span><span class="rms-val">'+it[1]+'</span></span>').join('');}
function renderReport(slug){const md=REPORTS[slug];if(!md)return;const body=document.getElementById('report-body');body.innerHTML=marked.parse(md);wrapTables(body);styleCallouts(body);addPhaseBadges(body);colorizeTables(body);addVerdictBanner(body);addP9Bar(body);styleTradeCards(body);styleWTMFY(body);styleConceptBox(body);styleChecklists(body);buildTOC(body);buildMetaStrip(slug);document.querySelectorAll('.report-nav-btn').forEach(b=>b.classList.remove('active'));const active=document.querySelector('.report-nav-btn[data-slug="'+slug+'"]');if(active)active.classList.add('active');}
document.querySelectorAll('.report-nav-btn').forEach(btn=>{btn.addEventListener('click',()=>renderReport(btn.dataset.slug));});

// --- Floating badge tooltips ---
const dashTip = document.createElement('div');
dashTip.id = 'dash-tip';
document.body.appendChild(dashTip);

function parseGates(slug) {
  const md = REPORTS[slug] || '';
  const result = {GREEN:[], AMBER:[], RED:[]};
  let inTable = false;
  for (const line of md.split('\n')) {
    if (/Deployment Gate Check/i.test(line)) { inTable = true; continue; }
    if (inTable && /^## /.test(line)) break;
    if (!inTable || !line.startsWith('|') || /---/.test(line)) continue;
    const cols = line.split('|').map(c => c.replace(/\*+/g,'').trim()).filter(Boolean);
    if (cols.length < 3 || cols[0] === 'Gate') continue;
    const name = cols[0], tier = cols[2].toUpperCase(), note = (cols[3]||'').replace(/\*+/g,'').trim();
    if (result[tier]) result[tier].push({name, note});
  }
  return result;
}

function parseP9(slug) {
  const md = REPORTS[slug] || '';
  const result = {APPROVE:[], FLAG:[], BLOCK:[]};
  let inTable = false;
  for (const line of md.split('\n')) {
    if (/Phase 9.*Full Desk|Full Desk.*Sign.Off/i.test(line)) { inTable = true; continue; }
    if (inTable && /^## /.test(line)) break;
    if (!inTable || !line.startsWith('|') || /---/.test(line)) continue;
    const cols = line.split('|').map(c => c.replace(/\*+/g,'').trim()).filter(Boolean);
    if (cols.length < 2 || /^Agent/i.test(cols[0])) continue;
    const agent = cols[0], verdictRaw = (cols[1]||'').toUpperCase();
    let note = (cols[2]||'').replace(/\*+/g,'').split('→')[0].replace(/\(.*?\)/g,'').replace(/^[—\-]+/,'').trim();
    for (const v of ['APPROVE','FLAG','BLOCK']) {
      if (verdictRaw.includes(v)) { result[v].push({agent, note}); break; }
    }
  }
  return result;
}

function buildTipHtml(type, tier, slug) {
  if (type === 'gate') {
    const gates = parseGates(slug);
    const items = gates[tier] || [];
    const colours = {GREEN:'var(--green)', AMBER:'var(--amber)', RED:'var(--red)'};
    const labels  = {GREEN:'Green Gates', AMBER:'Amber Gates', RED:'Red Gates'};
    if (!items.length) return `<div class="tip-title">${labels[tier]}</div><div class="tip-empty">None</div>`;
    return `<div class="tip-title" style="color:${colours[tier]}">${labels[tier]} (${items.length})</div>`
      + items.map(g => `<div class="tip-row"><span class="tip-name">${g.name}</span>${g.note ? '<span class="tip-note">· '+g.note+'</span>' : ''}</div>`).join('');
  } else {
    const p9 = parseP9(slug);
    const items = p9[tier] || [];
    const colours = {APPROVE:'var(--green)', FLAG:'var(--amber)', BLOCK:'var(--red)'};
    const labels  = {APPROVE:'Approve', FLAG:'Flag', BLOCK:'Block'};
    if (!items.length) return `<div class="tip-title">${labels[tier]}</div><div class="tip-empty">None</div>`;
    return `<div class="tip-title" style="color:${colours[tier]}">${labels[tier]} (${items.length})</div>`
      + items.map(a => `<div class="tip-row"><span class="tip-name">${a.agent}</span>${a.note ? '<span class="tip-note">· '+a.note+'</span>' : ''}</div>`).join('');
  }
}

function positionTip(e) {
  const pad = 14, vw = window.innerWidth, vh = window.innerHeight;
  let x = e.clientX + pad, y = e.clientY + pad;
  dashTip.style.left = '-9999px'; dashTip.style.top = '-9999px'; dashTip.style.display = 'block';
  const tw = dashTip.offsetWidth, th = dashTip.offsetHeight;
  if (x + tw > vw - pad) x = e.clientX - tw - pad;
  if (y + th > vh - pad) y = e.clientY - th - pad;
  dashTip.style.left = x + 'px'; dashTip.style.top = y + 'px';
}

document.addEventListener('mouseover', e => {
  const el = e.target.closest('[data-gate],[data-p9]');
  if (!el) { dashTip.style.display = 'none'; return; }
  const slug = el.dataset.slug;
  if (el.dataset.gate) {
    dashTip.innerHTML = buildTipHtml('gate', el.dataset.gate, slug);
  } else {
    dashTip.innerHTML = buildTipHtml('p9', el.dataset.p9, slug);
  }
  positionTip(e);
});
document.addEventListener('mousemove', e => {
  if (dashTip.style.display === 'none') return;
  if (!e.target.closest('[data-gate],[data-p9]')) { dashTip.style.display = 'none'; return; }
  positionTip(e);
});
"""


# ---------------------------------------------------------------------------
# HTML builders
# ---------------------------------------------------------------------------

def _js(v) -> str:
    return json.dumps(v)


def build_session_meta_js(sessions: list) -> str:
    entries = []
    for s in sessions:
        slug  = s["file"].replace(".md", "")
        p9    = f"{s.get('p7_approve','?')} APPROVE · {s.get('p7_flag','?')} FLAG · {s.get('p7_block','?')} BLOCK"
        gates = (
            f"{s.get('gates_green','?')}G / {s.get('gates_amber','?')}A / {s.get('gates_red','?')}R"
            if "gates_green" in s else ""
        )
        meta = {
            "num":      s["session_number"],
            "date":     s["date"],
            "regime":   s["regime"].replace("-"," ").title(),
            "status":   s.get("status",""),
            "deployed": f"{s.get('deploy_pct', s['nav_invested_pct']):.0f}%",
            "cash":     f"{s['nav_cash_pct']:.0f}%",
            "p9":       p9,
            "gates":    gates,
        }
        entries.append(f"  {_js(slug)}: {_js(meta)}")
    return "const SESSION_META = {\n" + ",\n".join(entries) + "\n};"


def build_reports_js(sessions: list) -> str:
    entries = []
    for s in sessions:
        slug = s["file"].replace(".md", "")
        entries.append(f"  {_js(slug)}: {_js(s.get('raw_md', ''))}")
    return "const REPORTS = {\n" + ",\n".join(entries) + "\n};"


def build_kpi_grid(sessions: list, portfolio: dict) -> str:
    last    = sessions[-1] if sessions else {}
    open_pos = len([h for h in portfolio["holdings"] if "CLOSED" not in h.get("status","").upper()])
    p7a = last.get("p7_approve","?")
    p7f = last.get("p7_flag","?")
    p7b = last.get("p7_block","?")
    return f"""<div class="kpi-grid">
  <div class="kpi blue"><div class="kpi-label">Sessions</div><div class="kpi-value blue">{len(sessions)}</div><div class="kpi-sub">live War Rooms</div></div>
  <div class="kpi teal"><div class="kpi-label">Open Positions</div><div class="kpi-value teal">{open_pos}</div><div class="kpi-sub">{len(portfolio['holdings'])} total tracked</div></div>
  <div class="kpi green"><div class="kpi-label">Deployed NAV</div><div class="kpi-value green">{last.get('nav_invested_pct',0):.0f}%</div><div class="kpi-sub">of NAV invested</div></div>
  <div class="kpi amber"><div class="kpi-label">Cash Reserve</div><div class="kpi-value amber">{last.get('nav_cash_pct',0):.0f}%</div><div class="kpi-sub">incl. dry powder</div></div>
  <div class="kpi purple"><div class="kpi-label">ECB Rate</div><div class="kpi-value" style="color:var(--purple)">{last.get('ecb_rate','—')}</div><div class="kpi-sub">last known</div></div>
  <div class="kpi red"><div class="kpi-label">Phase 9 Sign-off</div><div class="kpi-p7"><span style="color:var(--green)">{p7a}A</span><span style="color:var(--border2)">/</span><span style="color:var(--amber)">{p7f}F</span><span style="color:var(--border2)">/</span><span style="color:var(--red)">{p7b}B</span></div><div class="kpi-sub">Approve / Flag / Block</div></div>
</div>"""


def build_holdings_rows(portfolio: dict, prices: dict) -> str:
    rows = ""
    for h in portfolio["holdings"]:
        ticker = h["ticker"]
        live   = prices.get(ticker)
        live_html = f'<span class="live-price">€{live}</span>' if live else '<span class="pnl-neu">—</span>'
        pnl   = _pnl_html(h["entry_price"].replace("€",""), live, h["quantity"]) if live else '<span class="pnl-neu">pending</span>'
        rows += f"""
      <tr><td><span class="ticker">{ticker}</span></td><td><span class="name-cell">{h['name']}</span></td>
      <td><span class="mono">{h['entry_date']}</span></td><td><span class="mono">{h['quantity']}</span></td>
      <td><span class="mono">€{h['entry_price'].replace('€','')}</span></td><td>{live_html}</td><td>{pnl}</td>
      <td>{_strategy_badge(h['strategy'])}</td>
      <td><span class="mono" style="color:var(--muted)">{h['stop_loss']}</span></td>
      <td>{_status_badge(h['status'])}</td></tr>"""
    return rows


def build_session_rows(sessions: list) -> str:
    max_n = max((s["session_number"] for s in sessions), default=0)
    rows  = ""
    for s in reversed(sessions):
        n   = s["session_number"]
        bc  = "badge-blue" if n == max_n else "badge-muted"
        dep = f"{s.get('deploy_pct', s['nav_invested_pct']):.0f}%"
        dcl = "pnl-pos" if s.get('nav_invested_pct',0) > 0 else "mono"
        trades = ", ".join(s.get("trades",[])) or "—"
        slug = s["file"].replace(".md","")
        gg  = s.get("gates_green","?"); ga = s.get("gates_amber","?"); gr = s.get("gates_red","?")
        gates_html = (
            f'<span class="badge badge-green" style="cursor:help" data-slug="{slug}" data-gate="GREEN">{gg}G</span>&nbsp;'
            f'<span class="badge badge-amber" style="cursor:help" data-slug="{slug}" data-gate="AMBER">{ga}A</span>&nbsp;'
            f'<span class="badge badge-red"   style="cursor:help" data-slug="{slug}" data-gate="RED">{gr}R</span>'
        ) if "gates_green" in s else '<span class="mono" style="color:var(--muted)">—</span>'
        p7a = s.get("p7_approve","?"); p7f = s.get("p7_flag","?"); p7b = s.get("p7_block","?")
        p9_html = (
            f'<span class="badge badge-green" style="cursor:help" data-slug="{slug}" data-p9="APPROVE">{p7a}A</span>&nbsp;'
            f'<span class="badge badge-amber" style="cursor:help" data-slug="{slug}" data-p9="FLAG">{p7f}F</span>&nbsp;'
            f'<span class="badge badge-muted" style="cursor:help" data-slug="{slug}" data-p9="BLOCK">{p7b}B</span>'
        ) if isinstance(p7a, int) else f'<span class="mono" style="color:var(--muted)">{p7a}A/{p7f}F/{p7b}B</span>'
        regime = s["regime"].replace("-"," ").title()
        rows += f"""
      <tr><td><span class="badge {bc}">#{n}</span></td><td><span class="mono">{s['date']}</span></td>
      <td>{s['session']}</td><td><span class="regime-tag">{regime}</span></td>
      <td><span class="mono" style="font-size:12px">{trades}</span></td>
      <td><span class="{dcl}">{dep}</span></td><td>{gates_html}</td><td>{p9_html}</td>
      <td><span class="mono">{s.get('ecb_rate','—')}</span></td></tr>"""
    return rows


def build_report_nav(sessions: list) -> str:
    items = ""
    for s in reversed(sessions):
        slug   = s["file"].replace(".md","")
        active = "active" if s == sessions[-1] else ""
        items += f'<button class="report-nav-btn {active}" data-slug="{slug}"><span class="s-num">#{s["session_number"]}</span> {s["session"]}</button>\n'
    return items


def build_alloc_data(portfolio: dict, prices: dict):
    values, labels = [], []
    for h in portfolio["holdings"]:
        try:
            qty   = float(h["quantity"])
            price = prices.get(h["ticker"]) or float(str(h["entry_price"]).replace("€","").replace(",",""))
            values.append(qty * price)
            labels.append(f'{h["strategy"]} ({h["ticker"]})')
        except Exception:
            pass
    total = sum(values) or 1
    return labels, [round(v/total*100,1) for v in values]


def build_charts_js(sessions: list, portfolio: dict, prices: dict) -> str:
    short = []
    for s in sessions:
        m = re.match(r"(\w+)\s+(\d{4})", s["session"])
        short.append(f"{m.group(1)[:3]} {m.group(2)}" if m else s["session"])
    nav_d   = _js([s["nav_invested_pct"] for s in sessions])
    nav_c   = _js([s["nav_cash_pct"] for s in sessions])
    dep     = _js([s.get("deploy_pct",0) for s in sessions])
    gates_g = _js([s.get("gates_green",0) for s in sessions])
    gates_a = _js([s.get("gates_amber",0) for s in sessions])
    gates_r = _js([s.get("gates_red",0) for s in sessions])
    p9_a    = _js([s.get("p7_approve",0) for s in sessions])
    p9_f    = _js([s.get("p7_flag",0) for s in sessions])
    p9_b    = _js([s.get("p7_block",0) for s in sessions])
    al, ap  = build_alloc_data(portfolio, prices)
    acols   = ['rgba(74,130,245,0.8)','rgba(34,212,191,0.8)','rgba(240,162,41,0.8)','rgba(155,126,248,0.8)'][:len(al)]
    return f"""Chart.defaults.font={{family:"'JetBrains Mono',monospace",size:11}};
Chart.defaults.color='#6b7592';
const gridColor='#1e2235';
const tip={{backgroundColor:'#181c2c',borderColor:'#252a40',borderWidth:1,titleColor:'#dde3f0',bodyColor:'#a8b2c8',padding:10,cornerRadius:6}};
const labels={_js(short)};
new Chart(document.getElementById('navChart'),{{type:'bar',data:{{labels,datasets:[{{label:'Deployed',data:{nav_d},backgroundColor:'rgba(74,130,245,0.75)',borderRadius:4,borderSkipped:false}},{{label:'Cash',data:{nav_c},backgroundColor:'rgba(240,162,41,0.22)',borderRadius:4,borderSkipped:false}}]}},options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{position:'top',labels:{{boxWidth:10,padding:12}}}},tooltip:{{...tip}}}},scales:{{x:{{grid:{{color:gridColor}},stacked:true,border:{{color:gridColor}}}},y:{{grid:{{color:gridColor}},stacked:true,max:100,border:{{color:gridColor}},ticks:{{callback:v=>v+'%'}}}}}}}}}});
new Chart(document.getElementById('gateChart'),{{type:'bar',data:{{labels,datasets:[{{label:'Green',data:{gates_g},backgroundColor:'rgba(30,200,112,0.75)',borderRadius:4}},{{label:'Amber',data:{gates_a},backgroundColor:'rgba(240,162,41,0.75)',borderRadius:4}},{{label:'Red',data:{gates_r},backgroundColor:'rgba(232,69,69,0.75)',borderRadius:4}}]}},options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{position:'top',labels:{{boxWidth:10,padding:12}}}},tooltip:{{...tip}}}},scales:{{x:{{grid:{{color:gridColor}},stacked:true,border:{{color:gridColor}}}},y:{{grid:{{color:gridColor}},stacked:true,border:{{color:gridColor}},ticks:{{stepSize:2}}}}}}}}}});
new Chart(document.getElementById('p9Chart'),{{type:'bar',data:{{labels,datasets:[{{label:'Approve',data:{p9_a},backgroundColor:'rgba(30,200,112,0.75)',borderRadius:4}},{{label:'Flag',data:{p9_f},backgroundColor:'rgba(240,162,41,0.75)',borderRadius:4}},{{label:'Block',data:{p9_b},backgroundColor:'rgba(232,69,69,0.75)',borderRadius:4}}]}},options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{position:'top',labels:{{boxWidth:10,padding:12}}}},tooltip:{{...tip}}}},scales:{{x:{{grid:{{color:gridColor}},stacked:true,border:{{color:gridColor}}}},y:{{grid:{{color:gridColor}},stacked:true,border:{{color:gridColor}},ticks:{{stepSize:3}}}}}}}}}});
new Chart(document.getElementById('deployChart'),{{type:'line',data:{{labels,datasets:[{{label:'Deploy %',data:{dep},borderColor:'rgba(30,200,112,.9)',backgroundColor:'rgba(30,200,112,.08)',borderWidth:2,pointBackgroundColor:'rgba(30,200,112,1)',pointRadius:5,fill:true,tension:.3}}]}},options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{display:false}},tooltip:{{...tip}}}},scales:{{x:{{grid:{{color:gridColor}},border:{{color:gridColor}}}},y:{{grid:{{color:gridColor}},border:{{color:gridColor}},max:100,ticks:{{callback:v=>v+'%'}}}}}}}}}});
new Chart(document.getElementById('allocChart'),{{type:'doughnut',data:{{labels:{_js(al)},datasets:[{{data:{_js(ap)},backgroundColor:{_js(acols)},borderColor:['#11141f'],borderWidth:3,hoverOffset:6}}]}},options:{{responsive:true,maintainAspectRatio:false,cutout:'68%',plugins:{{legend:{{position:'bottom',labels:{{boxWidth:10,padding:12,font:{{size:11}}}}}},tooltip:{{...tip,callbacks:{{label:ctx=>' '+ctx.label+': '+ctx.parsed+'%'}}}}}}}}}});
document.querySelectorAll('.tab-btn').forEach(btn=>{{btn.addEventListener('click',()=>{{document.querySelectorAll('.tab-btn').forEach(b=>b.classList.remove('active'));document.querySelectorAll('.tab-panel').forEach(p=>p.classList.remove('active'));btn.classList.add('active');document.getElementById('tab-'+btn.dataset.tab).classList.add('active');}});}});"""


# ---------------------------------------------------------------------------
# Main HTML assembler
# ---------------------------------------------------------------------------

def generate_html(sessions: list, portfolio: dict, prices: dict) -> str:
    generated_at   = datetime.now().strftime("%Y-%m-%d %H:%M")
    last           = sessions[-1] if sessions else {}
    regime_display = last.get("regime","Unknown").replace("-"," ").title()
    first_slug     = sessions[-1]["file"].replace(".md","") if sessions else ""
    yf_notice = (
        '<p class="notice">Live prices via yfinance. Unrealised P&amp;L at last known price.</p>'
        if HAS_YFINANCE and prices
        else '<p class="notice warn">yfinance not available — <code>pip install yfinance</code> for live prices.</p>'
    )
    kpi        = build_kpi_grid(sessions, portfolio)
    hold_rows  = build_holdings_rows(portfolio, prices)
    sess_rows  = build_session_rows(sessions)
    rpt_nav    = build_report_nav(sessions)
    charts_js  = build_charts_js(sessions, portfolio, prices)
    reports_js = build_reports_js(sessions)
    meta_js    = build_session_meta_js(sessions)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>War Room Dashboard</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="{FONTS_URL}" rel="stylesheet">
<script src="{CHART_JS_URL}"></script>
<script src="{MARKED_JS_URL}"></script>
<style>{CSS}</style>
</head>
<body>
<header>
  <div class="header-inner">
    <div class="header-brand">
      <div class="header-icon">⚔️</div>
      <div><h1>War Room Dashboard</h1><div class="sub">Quant Strategy Desk · Generated {generated_at}</div></div>
    </div>
    <div class="regime-badge"><div class="regime-dot"></div><div class="regime-label">{regime_display}</div></div>
    <div class="header-meta">
      <span>Session <strong>#{last.get('session_number','—')}</strong></span>
      <span class="sep">|</span><span>{last.get('session','—')}</span>
      <span class="sep">|</span><span>ECB <strong>{last.get('ecb_rate','—')}</strong></span>
    </div>
  </div>
</header>
<nav class="tab-bar">
  <button class="tab-btn active" data-tab="dashboard">Dashboard</button>
  <button class="tab-btn" data-tab="reports">Reports</button>
</nav>
<div id="tab-dashboard" class="tab-panel active">
<div class="container">
{kpi}
  <section>
    <div class="section-hd blue"><div class="section-hd-left"><div class="section-tag">01 · Analytics</div><div class="section-name">Portfolio Metrics</div><div class="section-desc">Session-by-session deployment, gates, and sign-off trends</div></div></div>
    <div class="chart-grid-3">
      <div class="chart-card"><div class="chart-card-title">NAV Allocation</div><div class="chart-card-subtitle">Deployed vs Cash per session</div><div class="chart-wrap"><canvas id="navChart"></canvas></div></div>
      <div class="chart-card"><div class="chart-card-title">Deployment Gate Traffic</div><div class="chart-card-subtitle">Green / Amber / Red per session</div><div class="chart-wrap"><canvas id="gateChart"></canvas></div></div>
      <div class="chart-card"><div class="chart-card-title">Phase 9 Sign-off</div><div class="chart-card-subtitle">Approve / Flag / Block per session</div><div class="chart-wrap"><canvas id="p9Chart"></canvas></div></div>
    </div>
    <div class="chart-grid-2">
      <div class="chart-card"><div class="chart-card-title">Deployment Efficiency</div><div class="chart-card-subtitle">% of session contribution deployed</div><div class="chart-wrap"><canvas id="deployChart"></canvas></div></div>
      <div class="chart-card"><div class="chart-card-title">Portfolio Allocation</div><div class="chart-card-subtitle">By strategy · current session</div><div class="chart-wrap"><canvas id="allocChart"></canvas></div></div>
    </div>
  </section>
  <section>
    <div class="section-hd green"><div class="section-hd-left"><div class="section-tag">02 · Holdings</div><div class="section-name">Current Holdings</div><div class="section-desc">Live positions, unrealised P&amp;L, and execution status</div></div></div>
    <div class="table-card"><table>
      <thead><tr><th>Ticker</th><th>Name</th><th>Entry Date</th><th>Qty</th><th>Entry €</th><th>Live Price</th><th>Unrealised P&amp;L</th><th>Strategy</th><th>Stop-Loss</th><th>Status</th></tr></thead>
      <tbody>{hold_rows}</tbody>
    </table></div>
    {yf_notice}
  </section>
  <section>
    <div class="section-hd amber"><div class="section-hd-left"><div class="section-tag">03 · History</div><div class="section-name">Session History</div><div class="section-desc">All War Room sessions — regime, deployment, and gate outcomes</div></div></div>
    <div class="table-card"><table>
      <thead><tr><th>#</th><th>Date</th><th>Session</th><th>Regime</th><th>Trades</th><th>Deployed</th><th>Gates</th><th>Phase 9</th><th>ECB</th></tr></thead>
      <tbody>{sess_rows}</tbody>
    </table></div>
  </section>
</div>
</div>
<div id="tab-reports" class="tab-panel">
  <div class="reports-layout">
    <nav class="report-sidebar" id="report-sidebar">
      <div class="report-sidebar-label">Sessions</div>
      {rpt_nav}
      <div class="toc-sep" id="toc-sep" style="display:none"></div>
      <div class="toc-heading" id="toc-heading">In this report</div>
      <div id="report-toc"></div>
    </nav>
    <div class="report-right">
      <div class="report-meta-strip" id="report-meta"></div>
      <div class="report-main"><div id="report-body" class="md-body"></div></div>
    </div>
  </div>
</div>
<script>
{reports_js}
{meta_js}
{charts_js}
{RENDER_JS}
renderReport({_js(first_slug)});
</script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    print("Reading sessions...")
    sessions = parse_sessions()
    print(f"  Found {len(sessions)} session(s): {[s['session'] for s in sessions]}")

    print("Reading portfolio...")
    portfolio = parse_portfolio()
    print(f"  Found {len(portfolio['holdings'])} holding(s)")

    tickers = [h["ticker"] for h in portfolio["holdings"]]
    if HAS_YFINANCE and tickers:
        lookup_ids = [h.get("isin") or h["ticker"] for h in portfolio["holdings"]]
        print(f"Fetching live prices via: {lookup_ids}...")
        prices = get_prices(portfolio["holdings"])
        print(f"  Got prices: {prices}")
    else:
        prices = {}
        if not HAS_YFINANCE:
            print("  yfinance not installed — skipping live prices (pip install yfinance)")

    print("Generating local/dashboard.html...")
    html = generate_html(sessions, portfolio, prices)
    out = BASE / "local" / "dashboard.html"
    out.write_text(html)
    print(f"  Done → {out}")
    print(f"\nOpen with: open {out}")


if __name__ == "__main__":
    main()
