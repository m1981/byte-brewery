from datetime import datetime, timezone
from html import escape
from typing import List, Tuple

from prompt_extractor.models import MessageNode

# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------

_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: #edf2f7;
    color: #1a202c;
    padding: 20px;
}

h1 {
    margin-bottom: 20px;
    font-size: 1.3rem;
    color: #2d3748;
    letter-spacing: 0.02em;
}

.lanes {
    display: flex;
    gap: 14px;
    align-items: flex-start;
    overflow-x: auto;
    padding-bottom: 12px;
}

/* ── Lane ── */
.lane {
    flex: 0 0 300px;
    background: #fff;
    border-radius: 10px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.08);
    overflow: hidden;
}

.lane-header {
    background: #2d3748;
    color: #e2e8f0;
    padding: 10px 14px;
    font-size: 0.78rem;
    font-weight: 600;
    word-break: break-all;
    letter-spacing: 0.01em;
}

.lane-body {
    padding: 10px;
    display: flex;
    flex-direction: column;
    gap: 8px;
}

/* ── Messages ── */
.message {
    border-radius: 7px;
    padding: 9px 11px;
    font-size: 0.82rem;
    line-height: 1.5;
}

.message.user   { background: #ebf8ff; border-left: 3px solid #3182ce; }
.message.model  { background: #faf5ff; border-left: 3px solid #805ad5; }

.msg-header {
    display: flex;
    align-items: center;
    gap: 5px;
    margin-bottom: 5px;
    font-size: 0.72rem;
    color: #718096;
}

.msg-header .role  { font-weight: 700; color: #4a5568; }
.msg-header .time  { margin-left: auto; }

.msg-body .text {
    white-space: pre-wrap;
    word-break: break-word;
    max-height: 110px;
    overflow: hidden;
    transition: max-height 0.25s ease;
}

.msg-body .text.expanded { max-height: none; }

.expand-btn {
    display: inline-block;
    margin-top: 4px;
    font-size: 0.7rem;
    color: #3182ce;
    cursor: pointer;
    background: none;
    border: none;
    padding: 0;
}

.image-ref {
    font-size: 0.73rem;
    color: #718096;
    margin-bottom: 3px;
}

/* ── Branch marker ── */
.branch-marker {
    background: #fffbeb;
    border: 1px solid #f6ad55;
    border-radius: 7px;
    padding: 7px 10px;
    font-size: 0.78rem;
    display: flex;
    align-items: center;
    gap: 6px;
    flex-wrap: wrap;
}

.branch-marker strong { color: #c05621; }
.branch-from          { color: #744210; font-style: italic; }
.branch-marker .time  { margin-left: auto; font-size: 0.7rem; color: #a0aec0; }
"""

# ---------------------------------------------------------------------------
# JS (expand / collapse long model responses)
# ---------------------------------------------------------------------------

_JS = """
document.querySelectorAll('.msg-body .text').forEach(el => {
    if (el.scrollHeight > el.clientHeight + 4) {
        const btn = document.createElement('button');
        btn.className = 'expand-btn';
        btn.textContent = '▼ Show more';
        btn.onclick = () => {
            el.classList.toggle('expanded');
            btn.textContent = el.classList.contains('expanded') ? '▲ Show less' : '▼ Show more';
        };
        el.parentNode.appendChild(btn);
    }
});
"""

# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------

def _time_str(node: MessageNode) -> str:
    sentinel = datetime.min.replace(tzinfo=timezone.utc)
    if node.timestamp == sentinel:
        return "??:??:??"
    return node.timestamp.strftime("%H:%M:%S")


def _render_branch_marker(node: MessageNode) -> str:
    display_name = escape(node.branch_parent.get("displayName", ""))
    return (
        f'<div class="branch-marker">'
        f'<span>🔀</span>'
        f'<strong>BRANCH</strong>'
        f'<span class="branch-from">from: &ldquo;{display_name}&rdquo;</span>'
        f'<span class="time">{_time_str(node)}</span>'
        f'</div>'
    )


def _render_message(node: MessageNode) -> str:
    role_label = "User" if node.role == "user" else "Model"
    role_class = "user" if node.role == "user" else "model"
    icon = "🧑" if node.role == "user" else "🤖"

    body_parts: List[str] = []
    if node.image_id:
        body_parts.append(
            f'<div class="image-ref">📎 Image: <code>{escape(node.image_id)}</code></div>'
        )
    if node.text:
        body_parts.append(f'<div class="text">{escape(node.text)}</div>')

    body_html = "\n".join(body_parts)

    return (
        f'<div class="message {role_class}">'
        f'<div class="msg-header">'
        f'<span>{icon}</span>'
        f'<span class="role">{role_label}</span>'
        f'<span class="time">{_time_str(node)}</span>'
        f'</div>'
        f'<div class="msg-body">{body_html}</div>'
        f'</div>'
    )


def _render_lane(filename: str, nodes: List[MessageNode]) -> str:
    items: List[str] = []
    for node in nodes:
        if node.branch_parent:
            items.append(_render_branch_marker(node))
        items.append(_render_message(node))

    body = "\n".join(items)
    return (
        f'<div class="lane">'
        f'<div class="lane-header">{escape(filename)}</div>'
        f'<div class="lane-body">{body}</div>'
        f'</div>'
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def format_html(conversations: List[Tuple[str, List[MessageNode]]]) -> str:
    """Render conversations as a self-contained HTML swimlane document.

    Each (filename, nodes) pair becomes one vertical lane. Branch markers
    are inserted where branchParent is detected.
    """
    lanes_html = "\n".join(_render_lane(name, nodes) for name, nodes in conversations)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Conversation Map</title>
<style>{_CSS}</style>
</head>
<body>
<h1>Conversation Map</h1>
<div class="lanes">
{lanes_html}
</div>
<script>{_JS}</script>
</body>
</html>"""
