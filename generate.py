#!/usr/bin/env python3
"""Generate self-contained dashboard HTML from data.json — no fetch needed."""
import json
import html as html_mod
from pathlib import Path

data = json.loads(Path("data.json").read_text())

def esc(s):
    return html_mod.escape(str(s), quote=False)

def status_label(status):
    return {"active": "Active", "waiting": "Waiting", "done": "Done", "dormant": "Dormant"}.get(status, status)

def render_cards(projects):
    parts = []
    for p in projects:
        sc = p.get("status", "active")
        last = p.get("lastActivity", "")

        # Links
        link_parts = []
        for l in p.get("links", []):
            href = l.get("path", "#")
            label = l.get("label", href)
            clean = href.replace("file:///home/bayard_devries/", "").replace(" ", "%20")
            link_parts.append('<li><span class="label">' + esc(label) + '</span> <a href="' + esc(href) + '">' + esc(clean) + '</a></li>')
        links_html = "".join(link_parts)
        links_section = '<div class="card-section">Key links</div><ul class="link-list">' + links_html + '</ul>' if p.get("links") else ""

        # Diagrams
        diag_parts = []
        for d in p.get("diagrams", []):
            is_arrow = "→" in d.get("label", "")
            cls = "diagram-thumb" + (" arrow" if is_arrow else "")
            diag_parts.append(
                '<div class="' + cls + '" onclick="openDiagram(\'' + esc(d["file"]) + '\')">'
                '<img src="' + esc(d["file"]) + '" alt="' + esc(d["label"]) + '">'
                '<div class="label">' + esc(d["label"]) + '</div></div>'
            )
        diag_html = "".join(diag_parts)
        diag_section = '<div class="card-section">Diagrams</div><div class="diagram-grid">' + diag_html + '</div>' if p.get("diagrams") else ""

        # Open items
        item_parts = []
        for item in p.get("openItems", []):
            pin = '<span class="pin">●</span> ' if item.get("pin") else ""
            item_parts.append('<li>' + pin + esc(item["text"]) + '</li>')
        items_html = "".join(item_parts)
        items_section = '<div class="card-section">Open items</div><ul class="open-items">' + items_html + '</ul>'

        # Sub-sections
        sub_parts = []
        for sub in p.get("subSections", []):
            sub_item_parts = []
            for si in sub.get("openItems", []):
                sub_pin = '<span class="pin">●</span> ' if si.get("pin") else ""
                sub_item_parts.append('<li>' + sub_pin + esc(si["text"]) + '</li>')
            sub_items_html = "".join(sub_item_parts)
            sub_parts.append(
                '<div class="sub-section"><h4>' + esc(sub["title"]) + '</h4>'
                '<div class="detail">' + esc(sub.get("detail", "")) + '</div>'
                '<div class="card-section" style="margin-top:6px;">Open items</div>'
                '<ul class="open-items">' + sub_items_html + '</ul></div>'
            )
        subs_html = "".join(sub_parts)

        card = (
            '<div class="card">'
            '<div class="card-top"><h2>' + esc(p["name"]) + '</h2>'
            '<span class="badge ' + sc + '">' + status_label(sc) + '</span></div>'
            '<div class="desc">' + esc(p.get("desc", "")) + '</div>'
            '<div class="last-updated"><strong>Last:</strong> ' + esc(last) + '</div>'
            + links_section + diag_section + items_section + subs_html +
            '</div>'
        )
        parts.append(card)
    return "\n".join(parts)

def render_ideas(ideas):
    parts = []
    for i in ideas:
        parts.append(
            '<div class="idea-item">'
            '<div class="idea-title">' + esc(i["title"]) + '</div>'
            '<div class="idea-meta">Session: ' + esc(i["session"]) + '</div>'
            '<div class="idea-body">' + esc(i["body"]) + '</div>'
            '<div class="idea-suggest">→ ' + esc(i["suggest"]) + '</div>'
            '</div>'
        )
    return "\n".join(parts)

def render_upcoming(upcoming):
    parts = []
    for u in upcoming:
        prep_parts = []
        for item in u.get("prepItems", []):
            cls = "critical" if item.get("critical") else ("check" if item.get("check") else "")
            star = "● " if item.get("critical") else ""
            check = "✓ " if item.get("check") else ""
            note = ' <span style="color:var(--muted);font-size:0.72rem;">— ' + esc(item.get("note", "")) + '</span>' if item.get("note") else ""
            prep_parts.append('<li class="' + cls + '">' + star + check + esc(item["text"]) + note + '</li>')
        prep_html = "".join(prep_parts)

        also_parts = []
        for a in u.get("alsoNeeded", []):
            also_parts.append('<li>' + esc(a) + '</li>')
        also_html = "".join(also_parts)
        also_section = '<div class="card-section" style="margin-top:8px;">Also needed</div><ul class="open-items">' + also_html + '</ul>' if u.get("alsoNeeded") else ""

        parts.append(
            '<div class="upcoming-item"><h3>' + esc(u["title"]) + '</h3>'
            '<div class="when">' + esc(u["when"]) + '</div>'
            '<div class="card-section" style="margin-top:8px;">Pack checklist</div>'
            '<ul class="prep-list">' + prep_html + '</ul>'
            + also_section +
            '</div>'
        )
    return "\n".join(parts)

CSS = """  :root {
    --bg: #faf8f5;
    --card: #fff;
    --ink: #1a1a1a;
    --muted: #6b6560;
    --rule: #e0d9d2;
    --accent: #8b4513;
    --accent-soft: #d4a574;
    --green: #2e6b3e;
    --green-bg: #e8f0e8;
    --amber: #b85c1a;
    --amber-bg: #fbf0e8;
    --blue: #2c5f7c;
    --blue-bg: #e8f0f5;
    --purple: #5c3a6e;
    --purple-bg: #f0e8f5;
  }
  * { box-sizing: border-box; }
  html { -webkit-text-size-adjust: 100%; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    line-height: 1.55;
    color: var(--ink);
    background: var(--bg);
    margin: 0;
    padding: 0 0 2rem;
  }
  .wrap { max-width: 720px; margin: 0 auto; padding: 0 12px; }
  header { padding: 16px 0 8px; border-bottom: 1px solid var(--rule); }
  header h1 { font-size: 1.4rem; margin: 0 0 2px; font-weight: 600; letter-spacing: -0.01em; }
  header .sub { font-size: 0.82rem; color: var(--muted); }
  header .updated { font-size: 0.75rem; color: var(--muted); margin-top: 4px; }
  .legend { display: flex; flex-wrap: wrap; gap: 6px 10px; margin: 10px 0 14px; font-size: 0.75rem; }
  .legend span { display: inline-flex; align-items: center; gap: 4px; }
  .badge { display: inline-block; padding: 2px 7px; border-radius: 999px; font-size: 0.7rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em; }
  .badge.active { background: var(--green-bg); color: var(--green); }
  .badge.waiting { background: var(--amber-bg); color: var(--amber); }
  .badge.done { background: #e8e8e8; color: #555; }
  .badge.dormant { background: #f0f0f0; color: #888; }
  .section-title {
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--muted);
    margin: 20px 0 8px;
    padding-bottom: 4px;
    border-bottom: 1px solid var(--rule);
  }
  .card {
    background: var(--card);
    border: 1px solid var(--rule);
    border-radius: 8px;
    padding: 14px;
    margin-bottom: 12px;
  }
  .card-top { display: flex; align-items: flex-start; gap: 10px; }
  .card-top h2 { font-size: 1.05rem; margin: 0 0 2px; font-weight: 600; flex: 1; }
  .card-top .badge { margin-top: 2px; }
  .card .desc { font-size: 0.85rem; color: var(--muted); margin: 0 0 8px; }
  .card .last-updated { font-size: 0.78rem; color: var(--muted); margin-bottom: 8px; }
  .card .last-updated strong { color: var(--ink); }
  .card-section { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--muted); margin: 10px 0 4px; font-weight: 600; }
  .link-list { list-style: none; padding: 0; margin: 0 0 6px; font-size: 0.82rem; }
  .link-list li { padding: 2px 0; display: flex; align-items: baseline; gap: 6px; }
  .link-list .label { color: var(--muted); flex-shrink: 0; }
  .link-list a { color: var(--accent); text-decoration: none; word-break: break-all; }
  .link-list a:hover { text-decoration: underline; }
  .diagram-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(120px, 1fr)); gap: 6px; margin: 4px 0 8px; }
  .diagram-thumb {
    aspect-ratio: 1;
    background: #f5f3f0;
    border: 1px solid var(--rule);
    border-radius: 4px;
    overflow: hidden;
    cursor: pointer;
    position: relative;
  }
  .diagram-thumb img { width: 100%; height: 100%; object-fit: cover; display: block; }
  .diagram-thumb .label { position: absolute; bottom: 0; left: 0; right: 0; background: rgba(0,0,0,0.6); color: #fff; font-size: 0.6rem; padding: 2px 4px; text-align: center; }
  .diagram-thumb.arrow img { object-fit: contain; background: #1a1a1a; padding: 10px; }
  .open-items { font-size: 0.82rem; margin: 4px 0 0; padding-left: 16px; }
  .open-items li { margin-bottom: 3px; }
  .open-items .pin { color: var(--amber); font-weight: 600; }
  .detail { font-size: 0.82rem; color: var(--muted); margin: 4px 0; }
  .diagram-modal {
    display: none;
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(0,0,0,0.85);
    z-index: 100;
    justify-content: center;
    align-items: center;
    padding: 20px;
  }
  .diagram-modal.open { display: flex; }
  .diagram-modal img { max-width: 100%; max-height: 90vh; border: 2px solid #fff; border-radius: 4px; }
  .diagram-modal .close { position: absolute; top: 16px; right: 16px; background: rgba(255,255,255,0.2); color: #fff; border: none; border-radius: 50%; width: 36px; height: 36px; font-size: 1.2rem; cursor: pointer; }
  .idea-item {
    background: #f9f7f4;
    border-left: 3px solid var(--accent-soft);
    padding: 10px 12px;
    margin-bottom: 8px;
    border-radius: 0 4px 4px 0;
  }
  .idea-item .idea-title { font-weight: 600; font-size: 0.88rem; margin-bottom: 2px; }
  .idea-item .idea-meta { font-size: 0.72rem; color: var(--muted); margin-bottom: 4px; }
  .idea-item .idea-body { font-size: 0.82rem; }
  .idea-item .idea-suggest { font-size: 0.78rem; color: var(--blue); margin-top: 4px; }
  .upcoming-item {
    background: var(--blue-bg);
    border: 1px solid #c5d8e5;
    border-radius: 8px;
    padding: 12px;
    margin-bottom: 10px;
  }
  .upcoming-item h3 { margin: 0 0 4px; font-size: 1rem; }
  .upcoming-item .when { font-size: 0.78rem; color: var(--blue); font-weight: 600; margin-bottom: 6px; }
  .prep-list { font-size: 0.82rem; padding-left: 16px; }
  .prep-list li { margin-bottom: 3px; }
  .prep-list .critical { color: var(--amber); font-weight: 600; }
  .prep-list .check { color: var(--green); }
  .sub-section { background: #f9f7f4; border: 1px solid var(--rule); border-radius: 6px; padding: 10px; margin-top: 8px; }
  .sub-section h4 { margin: 0 0 4px; font-size: 0.92rem; }
  footer { margin-top: 24px; padding-top: 10px; border-top: 1px solid var(--rule); font-size: 0.72rem; color: var(--muted); text-align: center; }
  @media (min-width: 600px) {
    .card { padding: 18px 20px; }
    .diagram-grid { grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); }
  }"""

JS_UTILS = """function openDiagram(path) {
  document.getElementById('diagramImg').src = path;
  document.getElementById('diagramModal').classList.add('open');
}
function closeDiagram() {
  document.getElementById('diagramModal').classList.remove('open');
}
"""

body = (
    '<header>'
    '<h1>Our Work</h1>'
    '<div class="sub">Project dashboard — all active work, one glanceable view</div>'
    '<div class="updated" id="updated"></div>'
    '</header>'
    '<div class="legend">'
    '<span><span class="badge active">Active</span> going now</span>'
    '<span><span class="badge waiting">Waiting</span> blocked / pending</span>'
    '<span><span class="badge done">Done</span> wrapped</span>'
    '<span><span class="badge dormant">Dormant</span> paused</span>'
    '</div>'
    '<div class="section-title">Projects</div>'
    '<div id="cards">' + render_cards(data["projects"]) + '</div>'
    '<div class="section-title">Idea Inbox — Big Sessions</div>'
    '<div class="detail" style="margin-bottom:10px;">Ideas, questions, and half-finished threads from the 4 biggest sessions (Aug 3–17) that never got followed up. Pick up or drop.</div>'
    '<div id="ideaInbox">' + render_ideas(data["ideaInbox"]) + '</div>'
    '<div class="section-title">Upcoming</div>'
    '<div id="upcoming">' + render_upcoming(data["upcoming"]) + '</div>'
    '<footer>'
    'Dashboard built Aug 17, 2026 · GitHub Pages · Both desktops can edit data.json and push to update'
    '</footer>'
)

output = (
    '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="UTF-8">\n'
    '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
    '<title>Our Work — Project Dashboard</title>\n'
    '<style>\n' + CSS + '\n</style>\n</head>\n<body>\n<div class="wrap">\n'
    + body + '\n</div>\n'
    '<div class="diagram-modal" id="diagramModal">\n'
    '<button class="close" onclick="closeDiagram()">×</button>\n'
    '<img id="diagramImg" src="" alt="Diagram">\n'
    '</div>\n'
    '<script>\n' + JS_UTILS + '\n'
    "document.getElementById('updated').textContent = 'Last updated: " + esc(data["updated"]) + "';\n"
    '</script>\n</body>\n</html>'
)

Path("index.html").write_text(output)
print(f"Generated {len(output)} bytes → index.html")
print(f"Projects: {len(data['projects'])}, Ideas: {len(data['ideaInbox'])}, Upcoming: {len(data['upcoming'])}")
