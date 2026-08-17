#!/usr/bin/env python3
"""Generate self-contained dashboard HTML from data.json — no fetch needed."""
import json
import html as html_mod
from datetime import datetime, timezone
from pathlib import Path

data = json.loads(Path("data.json").read_text())

TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")

def esc(s):
    return html_mod.escape(str(s), quote=False)

def status_label(status):
    return {"active": "Active", "waiting": "Waiting", "done": "Done", "dormant": "Dormant"}.get(status, status)

def type_label(t):
    return {
        "next_action": "Next",
        "blocked": "Blocked",
        "open": "Open",
        "info": "Info",
        "future": "Later",
        "milestone": "Milestone",
        "unknown": "Open",
    }.get(t, t)

def type_class(t):
    return {
        "next_action": "item-next",
        "blocked": "item-blocked",
        "open": "item-open",
        "info": "item-info",
        "future": "item-future",
        "milestone": "item-milestone",
    }.get(t, "")

def days_label(days):
    if days is None:
        return ""
    if days <= 0:
        return '<span class="days-today">TODAY</span>'
    if days == 1:
        return '<span class="days-tomorrow">TOMORROW</span>'
    if days <= 3:
        return f'<span class="days-soon">in {days} days</span>'
    return f'<span class="days-far">in {days} days</span>'

def render_carry_forward(items):
    if not items:
        return ""
    parts = []
    for item in items:
        parts.append('<li class="carry-item">' + esc(item) + '</li>')
    return ('<div class="card-section" style="margin-top:8px;">Carry forward</div>'
            '<ul class="carry-list">' + "".join(parts) + '</ul>')

def render_last_session(session):
    if not session:
        return ""
    parts = []
    parts.append('<div class="last-session-date">' + esc(session.get("date", "")) + '</div>')
    if session.get("summary"):
        parts.append('<div class="last-session-summary">' + esc(session["summary"]) + '</div>')
    ref = session.get(" OurBrainRef")
    if ref:
        local = "file://" in ref or "/mnt/" in ref
        if local:
            parts.append('<div class="last-session-ref local">OurBrain: ' + esc(ref) + ' <span class="local-tag">(local)</span></div>')
        else:
            parts.append('<div class="last-session-ref">OurBrain: <a href="' + esc(ref) + '">' + esc(ref) + '</a></div>')
    return '<div class="last-session">' + "".join(parts) + '</div>'

def render_links(links):
    parts = []
    for l in links:
        href = l.get("path", "#")
        label = l.get("label", href)
        local = l.get("localOnly", False) or ("file://" in href or "/mnt/" in href)
        if local:
            clean = href
            display = esc(label)
            parts.append('<li><span class="label">' + display + '</span> '
                         '<span class="link-local">' + esc(clean) + ' <span class="local-tag">local</span></span></li>')
        else:
            clean = href.replace("file:///home/bayard_devries/", "").replace(" ", "%20")
            parts.append('<li><span class="label">' + esc(label) + '</span> '
                         '<a href="' + esc(href) + '">' + esc(clean) + '</a></li>')
    if not parts:
        return ""
    return '<div class="card-section">Key links</div><ul class="link-list">' + "".join(parts) + '</ul>'

def render_diagrams(diagrams):
    parts = []
    for d in diagrams:
        is_arrow = "→" in d.get("label", "")
        cls = "diagram-thumb" + (" arrow" if is_arrow else "")
        src = d["file"]
        local = "file://" in src or "/mnt/" in src
        if local:
            # Local-only diagram: show thumbnail as placeholder
            parts.append(
                '<div class="' + cls + '" style="background:#eee;border-style:dashed;cursor:default;">'
                '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#999;font-size:0.6rem;">local</div>'
                '<div class="label">' + esc(d["label"]) + ' <span class="local-tag">local</span></div></div>'
            )
        else:
            parts.append(
                '<div class="' + cls + '" onclick="openDiagram(\'' + esc(src) + '\')">'
                '<img src="' + esc(src) + '" alt="' + esc(d["label"]) + '">'
                '<div class="label">' + esc(d["label"]) + '</div></div>'
            )
    if not parts:
        return ""
    return '<div class="card-section">Diagrams</div><div class="diagram-grid">' + "".join(parts) + '</div>'

def render_open_items(items, inline=False):
    if not items:
        return ""
    # Sort: next_action and blocked first, then milestones, then open/info, then future
    order = {"next_action": 0, "blocked": 1, "milestone": 2, "open": 3, "info": 4, "future": 5}
    sorted_items = sorted(items, key=lambda i: order.get(i.get("type", "unknown"), 99))
    parts = []
    for item in sorted_items:
        pin = '<span class="pin">●</span> ' if item.get("pin") else ""
        cls = type_class(item.get("type", ""))
        tlabel = type_label(item.get("type", ""))
        type_badge = '<span class="item-type ' + cls + '">' + esc(tlabel) + '</span>'
        deadline = item.get("deadline")
        deadline_html = ""
        if deadline:
            deadline_html = ' <span class="item-deadline">due ' + esc(deadline) + '</span>'
        blocker = item.get("blocker")
        blocker_html = ""
        if blocker:
            blocker_html = ' <span class="item-blocker">blocked: ' + esc(blocker) + '</span>'
        text = pin + esc(item["text"]) + deadline_html + blocker_html
        if inline:
            parts.append('<li class="' + cls + '">' + type_badge + ' ' + text + '</li>')
        else:
            parts.append('<div class="open-item ' + cls + '">'
                         '<div class="item-row"><span class="item-type ' + cls + '">' + esc(tlabel) + '</span> '
                         '<span class="item-text">' + text + '</span></div>'
                         '</div>')
    if not parts:
        return ""
    if inline:
        return '<ul class="open-items">' + "".join(parts) + '</ul>'
    return '<div class="card-section">Open items</div><div class="open-items-list">' + "".join(parts) + '</div>'

def render_cards(projects):
    parts = []
    for p in projects:
        sc = p.get("status", "active")
        last = p.get("lastActivity", "")

        card = (
            '<div class="card">'
            '<div class="card-top"><h2>' + esc(p["name"]) + '</h2>'
            '<span class="badge ' + sc + '">' + status_label(sc) + '</span></div>'
            '<div class="card-desc">' + esc(p.get("desc", "")) + '</div>'
        )

        # Last session block (replaces old single-line lastActivity)
        session = p.get("lastSession")
        if session:
            card += render_last_session(session)
        elif last:
            card += '<div class="last-updated"><strong>Last:</strong> ' + esc(last) + '</div>'

        # Carry forward
        card += render_carry_forward(p.get("carryForward", []))

        # Links
        card += render_links(p.get("links", []))

        # Diagrams
        card += render_diagrams(p.get("diagrams", []))

        # Open items
        card += render_open_items(p.get("openItems", []))

        # Sub-sections (for Field Events)
        sub_parts = []
        for sub in p.get("subSections", []):
            sub_card = (
                '<div class="sub-section">'
                '<h4>' + esc(sub["title"]) + '</h4>'
                '<div class="sub-detail">' + esc(sub.get("detail", "")) + '</div>'
            )
            sub_session = sub.get("lastSession")
            if sub_session:
                sub_card += render_last_session(sub_session)
            sub_card += render_carry_forward(sub.get("carryForward", []))
            sub_card += render_open_items(sub.get("openItems", []))
            sub_card += '</div>'
            sub_parts.append(sub_card)
        if sub_parts:
            card += '<div class="sub-sections">' + "".join(sub_parts) + '</div>'

        card += '</div>'
        parts.append(card)
    return "\n".join(parts)

def render_ideas(ideas):
    parts = []
    for i in ideas:
        status = i.get("status", "open")
        status_badge = '<span class="idea-status badge ' + status + '">' + status.title() + '</span>'
        first_step = i.get("firstStep")
        first_html = ""
        if first_step:
            first_html = '<div class="idea-first">→ ' + esc(first_step) + '</div>'
        ref = i.get(" OurBrainRef")
        ref_html = ""
        if ref:
            local = "file://" in ref or "/mnt/" in ref
            if local:
                ref_html = '<div class="idea-ref local">OurBrain: ' + esc(ref) + ' <span class="local-tag">local</span></div>'
            else:
                ref_html = '<div class="idea-ref">OurBrain: <a href="' + esc(ref) + '">' + esc(ref) + '</a></div>'
        parts.append(
            '<div class="idea-item">'
            '<div class="idea-top">'
            '<div class="idea-title">' + esc(i["title"]) + '</div>'
            '<div class="idea-meta">Session: ' + esc(i["session"]) + ' ' + status_badge + '</div>'
            '</div>'
            '<div class="idea-body">' + esc(i["body"]) + '</div>'
            + first_html + ref_html +
            '</div>'
        )
    return "\n".join(parts)

def render_upcoming(upcoming):
    parts = []
    for u in upcoming:
        days = u.get("daysUntil")
        days_html = days_label(days) if days is not None else ""

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
            atype = a.get("type", "open")
            acls = type_class(atype)
            atlabel = type_label(atype)
            atext = esc(a["text"])
            adeadline = a.get("deadline")
            adeadline_html = ' <span class="item-deadline">due ' + esc(adeadline) + '</span>' if adeadline else ""
            ablocker = a.get("blocker")
            ablocker_html = ' <span class="item-blocker">blocked: ' + esc(ablocker) + '</span>' if ablocker else ""
            also_parts.append(
                '<div class="also-item ' + acls + '">'
                '<span class="item-type ' + acls + '">' + esc(atlabel) + '</span> '
                '<span class="item-text">' + atext + adeadline_html + ablocker_html + '</span>'
                '</div>'
            )
        also_html = "".join(also_parts)
        also_section = ('<div class="card-section" style="margin-top:8px;">Also needed</div>'
                        '<div class="open-items-list">' + also_html + '</div>') if also_parts else ""

        parts.append(
            '<div class="upcoming-item">'
            '<div class="upcoming-header">'
            '<h3>' + esc(u["title"]) + ' ' + days_html + '</h3>'
            '<div class="when">' + esc(u["when"]) + '</div>'
            '</div>'
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
    --red: #b33d3d;
    --red-bg: #fbe8e8;
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
  .badge.open { background: var(--blue-bg); color: var(--blue); }
  .badge.blocked { background: var(--red-bg); color: var(--red); }
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
  .card-desc { font-size: 0.85rem; color: var(--muted); margin: 0 0 8px; }
  .last-updated { font-size: 0.78rem; color: var(--muted); margin-bottom: 8px; }
  .last-updated strong { color: var(--ink); }
  .last-session { margin: 6px 0 8px; padding: 8px 10px; background: #f9f7f4; border-radius: 4px; border-left: 3px solid var(--accent-soft); }
  .last-session-date { font-size: 0.72rem; color: var(--accent); font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 2px; }
  .last-session-summary { font-size: 0.82rem; margin-bottom: 2px; }
  .last-session-ref { font-size: 0.72rem; color: var(--blue); }
  .last-session-ref a { color: var(--blue); text-decoration: none; }
  .local-tag { color: var(--muted); font-size: 0.65rem; font-style: italic; margin-left: 4px; }
  .link-list { list-style: none; padding: 0; margin: 0 0 6px; font-size: 0.82rem; }
  .link-list li { padding: 2px 0; display: flex; align-items: baseline; gap: 6px; flex-wrap: wrap; }
  .link-list .label { color: var(--muted); flex-shrink: 0; }
  .link-list a { color: var(--accent); text-decoration: none; word-break: break-all; }
  .link-list a:hover { text-decoration: underline; }
  .link-local { color: var(--muted); font-size: 0.72rem; font-style: italic; word-break: break-all; }
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
  .carry-list { list-style: none; padding: 0; margin: 0 0 6px; font-size: 0.82rem; }
  .carry-list li { padding: 2px 0 2px 16px; position: relative; border-left: 2px solid var(--accent-soft); margin-bottom: 2px; }
  .carry-list li::before { content: "↪"; position: absolute; left: -14px; color: var(--accent); font-size: 0.7rem; }
  .open-items-list { margin: 4px 0 0; }
  .open-item {
    padding: 6px 0;
    border-bottom: 1px solid rgba(0,0,0,0.06);
    font-size: 0.82rem;
  }
  .open-item:last-child { border-bottom: none; }
  .item-row { display: flex; align-items: baseline; gap: 6px; flex-wrap: wrap; }
  .item-type { display: inline-block; padding: 1px 5px; border-radius: 3px; font-size: 0.65rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.03em; flex-shrink: 0; }
  .item-next { background: var(--green-bg); color: var(--green); }
  .item-blocked { background: var(--red-bg); color: var(--red); }
  .item-open { background: var(--blue-bg); color: var(--blue); }
  .item-info { background: #eee; color: #666; }
  .item-future { background: #f0f0f0; color: #999; }
  .item-milestone { background: var(--purple-bg); color: var(--purple); }
  .item-text { flex: 1; min-width: 0; word-break: break-word; }
  .item-deadline { color: var(--amber); font-size: 0.72rem; font-weight: 600; }
  .item-blocker { color: var(--red); font-size: 0.72rem; font-style: italic; }
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
  .idea-top { display: flex; align-items: baseline; gap: 8px; flex-wrap: wrap; margin-bottom: 4px; }
  .idea-title { font-weight: 600; font-size: 0.88rem; }
  .idea-meta { font-size: 0.72rem; color: var(--muted); }
  .idea-body { font-size: 0.82rem; margin-bottom: 4px; }
  .idea-first { font-size: 0.78rem; color: var(--blue); }
  .idea-ref { font-size: 0.72rem; color: var(--blue); }
  .idea-ref a { color: var(--blue); text-decoration: none; }
  .upcoming-item {
    background: var(--blue-bg);
    border: 1px solid #c5d8e5;
    border-radius: 8px;
    padding: 12px;
    margin-bottom: 10px;
  }
  .upcoming-header { margin-bottom: 6px; }
  .upcoming-item h3 { margin: 0 0 2px; font-size: 1rem; display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
  .days-today { background: var(--red-bg); color: var(--red); padding: 1px 7px; border-radius: 999px; font-size: 0.65rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em; }
  .days-tomorrow { background: var(--amber-bg); color: var(--amber); padding: 1px 7px; border-radius: 999px; font-size: 0.65rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em; }
  .days-soon { color: var(--amber); font-size: 0.72rem; font-weight: 600; }
  .days-far { color: var(--muted); font-size: 0.72rem; }
  .upcoming-item .when { font-size: 0.78rem; color: var(--blue); font-weight: 600; margin-bottom: 6px; }
  .prep-list { font-size: 0.82rem; padding-left: 16px; }
  .prep-list li { margin-bottom: 3px; }
  .prep-list .critical { color: var(--amber); font-weight: 600; }
  .prep-list .check { color: var(--green); }
  .also-item { padding: 4px 0; border-bottom: 1px solid rgba(0,0,0,0.06); font-size: 0.82rem; display: flex; align-items: baseline; gap: 6px; flex-wrap: wrap; }
  .also-item:last-child { border-bottom: none; }
  .sub-section { background: #f9f7f4; border: 1px solid var(--rule); border-radius: 6px; padding: 10px; margin-top: 8px; }
  .sub-section h4 { margin: 0 0 4px; font-size: 0.92rem; }
  .sub-detail { font-size: 0.82rem; color: var(--muted); margin-bottom: 6px; }
  footer { margin-top: 24px; padding-top: 10px; border-top: 1px solid var(--rule); font-size: 0.72rem; color: var(--muted); text-align: center; }
  @media (min-width: 600px) {
    .card { padding: 18px 20px; }
    .diagram-grid { grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); }
  }
"""

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
    '<div class="sub">Project dashboard — pick up where you left off</div>'
    '<div class="updated" id="updated"></div>'
    '</header>'
    '<div class="legend">'
    '<span><span class="badge active">Active</span> going now</span>'
    '<span><span class="badge waiting">Waiting</span> blocked / pending</span>'
    '<span><span class="badge done">Done</span> wrapped</span>'
    '<span><span class="badge dormant">Dormant</span> paused</span>'
    '<span style="margin-left:8px;color:var(--muted);font-size:0.7rem;">·</span>'
    '<span style="color:var(--green);font-size:0.7rem;"><span class="item-type item-next">Next</span> = do this next</span>'
    '<span style="color:var(--red);font-size:0.7rem;"><span class="item-type item-blocked">Blocked</span> = stuck</span>'
    '<span style="color:var(--purple);font-size:0.7rem;"><span class="item-type item-milestone">Milestone</span> = date-driven</span>'
    '<span style="color:#999;font-size:0.7rem;"><span class="item-type item-future">Later</span> = someday</span>'
    '</div>'
    '<div class="section-title">Projects</div>'
    '<div id="cards">' + render_cards(data["projects"]) + '</div>'
    '<div class="section-title">Idea Inbox — Big Sessions</div>'
    '<div class="detail" style="margin-bottom:10px;">Half-finished threads from the biggest sessions. Pick up or drop.</div>'
    '<div id="ideaInbox">' + render_ideas(data["ideaInbox"]) + '</div>'
    '<div class="section-title">Upcoming</div>'
    '<div id="upcoming">' + render_upcoming(data["upcoming"]) + '</div>'
    '<footer>'
    'Dashboard built Aug 17, 2026 · GitHub Pages · Edit data.json and push — rebuilds automatically'
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
print(f"Updated: {data['updated']}")
