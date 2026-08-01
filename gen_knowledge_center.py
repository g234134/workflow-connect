#!/usr/bin/env python3
"""Generate AI Agent Knowledge Center static HTML site."""
import json
from pathlib import Path

data = json.loads(Path("D:/knowledge_center_data.json").read_text(encoding="utf-8"))

cat_display = {
    "Agent-Frameworks": "Agent Frameworks",
    "IDEs": "IDEs",
    "MCP-Servers": "MCP Servers",
    "Projects": "Projects",
    "Skills": "Agent Skills",
    "Tech-Notes": "Tech Notes",
    "Tools": "Tools",
}
cat_icons = {
    "Agent-Frameworks": "🤖",
    "IDEs": "💻",
    "MCP-Servers": "🔌",
    "Projects": "🚀",
    "Skills": "🧠",
    "Tech-Notes": "📝",
    "Tools": "🛠️",
}

# Build flat notes list
notes_list = []
for cat, notes in data["categories"].items():
    for n in notes:
        notes_list.append({
            "n": n["name"],
            "d": n["description"][:150],
            "s": n.get("stars", 0),
            "f": n.get("forks", 0),
            "l": n.get("language", ""),
            "lic": n.get("license", ""),
            "u": n.get("repo_url", ""),
            "c": cat_display.get(cat, cat),
            "t": n.get("tags", []),
            "cr": n.get("created", ""),
        })

# Build cat_meta
cat_meta = {}
for cat, notes in data["categories"].items():
    dn = cat_display.get(cat, cat)
    cat_meta[dn] = {
        "icon": cat_icons.get(cat, "📦"),
        "display": dn,
        "count": len(notes),
    }

total_stars = sum(n.get("stars", 0) for notes in data["categories"].values() for n in notes)
all_langs = set()
for notes in data["categories"].values():
    for n in notes:
        if n.get("language"):
            all_langs.add(n["language"])

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Agent Knowledge Center</title>
<style>
:root {
  --bg: #0d1117; --surface: #161b22; --surface2: #21262d;
  --border: #30363d; --text: #e6edf3; --text2: #8b949e;
  --accent: #58a6ff; --accent2: #3fb950; --accent3: #d2a8ff;
  --gold: #f0c43b; --radius: 8px; --shadow: 0 2px 8px rgba(0,0,0,0.3);
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; background: var(--bg); color: var(--text); line-height: 1.6; }
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }

.hero { text-align: center; padding: 48px 24px 32px; border-bottom: 1px solid var(--border); }
.hero h1 { font-size: 2.2rem; font-weight: 700; margin-bottom: 8px; }
.hero h1 span { color: var(--accent); }
.hero p { color: var(--text2); font-size: 1.05rem; max-width: 600px; margin: 0 auto; }
.stats { display: flex; gap: 32px; justify-content: center; margin-top: 20px; flex-wrap: wrap; }
.stat { text-align: center; }
.stat .num { font-size: 1.8rem; font-weight: 700; color: var(--accent); }
.stat .label { font-size: 0.8rem; color: var(--text2); text-transform: uppercase; letter-spacing: 0.5px; }

.container { max-width: 1200px; margin: 0 auto; padding: 24px 16px; }

.controls { display: flex; gap: 12px; margin-bottom: 16px; flex-wrap: wrap; align-items: center; }
.search { flex: 1; min-width: 240px; padding: 10px 16px; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); color: var(--text); font-size: 0.95rem; outline: none; }
.search:focus { border-color: var(--accent); box-shadow: 0 0 0 3px rgba(88,166,255,0.15); }
.search::placeholder { color: var(--text2); }

.tabs { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 16px; }
.tab { padding: 6px 14px; border-radius: 20px; font-size: 0.85rem; cursor: pointer; border: 1px solid var(--border); background: var(--surface); color: var(--text2); transition: all 0.15s; white-space: nowrap; }
.tab:hover { border-color: var(--accent); color: var(--text); }
.tab.active { background: var(--accent); color: #fff; border-color: var(--accent); }
.tab .cnt { font-size: 0.75rem; opacity: 0.7; margin-left: 4px; }

.sort-bar { display: flex; gap: 8px; align-items: center; margin-bottom: 12px; }
.sort-bar span { color: var(--text2); font-size: 0.8rem; }
.sort-btn { padding: 4px 10px; border-radius: 4px; font-size: 0.8rem; cursor: pointer; border: 1px solid var(--border); background: transparent; color: var(--text2); }
.sort-btn.active { background: var(--surface2); color: var(--text); border-color: var(--accent); }

.results-info { color: var(--text2); font-size: 0.85rem; margin-bottom: 12px; }

.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 16px; }
.card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 18px; transition: border-color 0.15s, box-shadow 0.15s; display: flex; flex-direction: column; }
.card:hover { border-color: var(--accent); box-shadow: var(--shadow); }
.card-title { font-size: 1.05rem; font-weight: 600; margin-bottom: 8px; word-break: break-word; }
.card-title a { color: var(--text); }
.card-title a:hover { color: var(--accent); text-decoration: none; }
.card-desc { color: var(--text2); font-size: 0.88rem; margin-bottom: 12px; flex: 1; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
.card-meta { display: flex; gap: 12px; flex-wrap: wrap; font-size: 0.78rem; color: var(--text2); align-items: center; }
.star { color: var(--gold); font-weight: 600; }
.lang { color: var(--accent3); }
.lic { color: var(--accent2); }
.cat-badge { background: var(--surface2); padding: 2px 8px; border-radius: 12px; font-size: 0.72rem; }
.empty { text-align: center; padding: 64px 24px; color: var(--text2); }
.empty h3 { font-size: 1.2rem; margin-bottom: 8px; color: var(--text); }
@media (max-width: 600px) {
  .hero h1 { font-size: 1.5rem; }
  .grid { grid-template-columns: 1fr; }
  .stats { gap: 16px; }
}
</style>
</head>
<body>

<div class="hero">
  <h1>🧠 <span>AI Agent</span> Knowledge Center</h1>
  <p>Curated collection of AI Agent frameworks, MCP servers, tools &amp; resources</p>
  <div class="stats">
    <div class="stat"><div class="num" id="s-total"></div><div class="label">Projects</div></div>
    <div class="stat"><div class="num" id="s-stars"></div><div class="label">Total ⭐</div></div>
    <div class="stat"><div class="num" id="s-cats"></div><div class="label">Categories</div></div>
    <div class="stat"><div class="num" id="s-langs"></div><div class="label">Languages</div></div>
  </div>
</div>

<div class="container">
  <div class="controls">
    <input class="search" id="search" type="text" placeholder="Search projects... (e.g. crewai, mcp, rag, ollama)" autofocus>
  </div>
  <div class="tabs" id="tabs"></div>
  <div class="sort-bar">
    <span>Sort:</span>
    <button class="sort-btn active" data-sort="stars">⭐ Stars</button>
    <button class="sort-btn" data-sort="name">A-Z</button>
    <button class="sort-btn" data-sort="recent">🕐 Recent</button>
  </div>
  <div class="results-info" id="info"></div>
  <div class="grid" id="grid"></div>
  <div class="empty" id="empty" style="display:none"><h3>No projects found</h3><p>Try a different search or category</p></div>
</div>

<script>
const N = %%NOTES_JSON%%;
const CM = %%CAT_META_JSON%%;

let aCat = "all", aSort = "stars", sQ = "";

function init() {
  document.getElementById("s-total").textContent = N.length;
  document.getElementById("s-stars").textContent = %%TOTAL_STARS%%.toLocaleString();
  document.getElementById("s-cats").textContent = Object.keys(CM).length;
  const langs = new Set(N.map(n=>n.l).filter(Boolean));
  document.getElementById("s-langs").textContent = langs.size;

  let th = `<button class="tab active" data-cat="all">All<span class="cnt">${N.length}</span></button>`;
  for (const [k,v] of Object.entries(CM)) {
    th += `<button class="tab" data-cat="${k}">${v.icon} ${v.display}<span class="cnt">${v.count}</span></button>`;
  }
  document.getElementById("tabs").innerHTML = th;

  document.querySelectorAll(".tab").forEach(t=>t.addEventListener("click",()=>{
    document.querySelectorAll(".tab").forEach(x=>x.classList.remove("active"));
    t.classList.add("active"); aCat=t.dataset.cat; render();
  }));
  document.querySelectorAll(".sort-btn").forEach(b=>b.addEventListener("click",()=>{
    document.querySelectorAll(".sort-btn").forEach(x=>x.classList.remove("active"));
    b.classList.add("active"); aSort=b.dataset.sort; render();
  }));
  document.getElementById("search").addEventListener("input",e=>{ sQ=e.target.value.toLowerCase(); render(); });
  render();
}

function render() {
  let f = N;
  if (aCat !== "all") f = f.filter(n=>n.c===aCat);
  if (sQ) f = f.filter(n=> n.n.toLowerCase().includes(sQ) || n.d.toLowerCase().includes(sQ) || n.l.toLowerCase().includes(sQ) || (n.t&&n.t.some(t=>t.toLowerCase().includes(sQ))));
  if (aSort==="stars") f.sort((a,b)=>(b.s||0)-(a.s||0));
  else if (aSort==="name") f.sort((a,b)=>a.n.localeCompare(b.n));
  else if (aSort==="recent") f.sort((a,b)=>(b.cr||"").localeCompare(a.cr||""));

  const g = document.getElementById("grid");
  const e = document.getElementById("empty");
  const i = document.getElementById("info");
  if (!f.length) { g.innerHTML=""; e.style.display="block"; i.textContent=""; return; }
  e.style.display="none";
  i.textContent=`Showing ${f.length} of ${N.length} projects`;
  g.innerHTML = f.map(n=>{
    const s = n.s ? `<span class="star">⭐ ${fmt(n.s)}</span>` : "";
    const lk = n.u ? n.u : "#";
    const tg = n.u ? ' target="_blank" rel="noopener"' : "";
    return `<div class="card"><div class="card-title"><a href="${lk}"${tg}>${esc(n.n)}</a></div><div class="card-desc">${esc(n.d)||"<em>No description</em>"}</div><div class="card-meta">${s}${n.l?`<span class="lang">● ${n.l}</span>`:""}${n.lic?`<span class="lic">${n.lic}</span>`:""}<span class="cat-badge">${esc(n.c)}</span></div></div>`;
  }).join("");
}
function fmt(n){return n>=1000?(n/1000).toFixed(1).replace(/\.0$/,"")+"k":n;}
function esc(s){const d=document.createElement("div");d.textContent=s||"";return d.innerHTML;}
init();
</script>
</body>
</html>"""

html = HTML
html = html.replace("%%NOTES_JSON%%", json.dumps(notes_list, ensure_ascii=False))
html = html.replace("%%CAT_META_JSON%%", json.dumps(cat_meta, ensure_ascii=False))
html = html.replace("%%TOTAL_STARS%%", str(total_stars))

out = Path("D:/knowledge_center.html")
out.write_text(html, encoding="utf-8")
print(f"Written: {out} ({out.stat().st_size / 1024:.1f} KB)")
