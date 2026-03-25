from datetime import datetime, timezone, timedelta
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


# ---------------------------------------------------------------------------
# Prompts List View CSS
# ---------------------------------------------------------------------------

_PROMPTS_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: #f7fafc;
    color: #1a202c;
    padding: 30px 20px;
    max-width: 900px;
    margin: 0 auto;
}

h1 {
    margin-bottom: 30px;
    font-size: 1.8rem;
    color: #2d3748;
    letter-spacing: -0.02em;
}

.chat-list {
    display: flex;
    flex-direction: column;
    gap: 20px;
}

/* ── Chat Card ── */
.chat-card {
    background: #fff;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    overflow: hidden;
    border: 1px solid #e2e8f0;
}

.chat-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: #fff;
    padding: 16px 20px;
}

.chat-title {
    font-size: 1.1rem;
    font-weight: 600;
    margin-bottom: 6px;
    word-break: break-word;
}

.chat-datetime {
    font-size: 0.85rem;
    opacity: 0.95;
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
}

.datetime-main {
    font-weight: 500;
}

.datetime-relative {
    opacity: 0.85;
    font-style: italic;
}

.chat-body {
    padding: 16px 20px;
}

.prompts-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

/* ── Prompt Item ── */
.prompt-item {
    background: #f7fafc;
    border-left: 4px solid #4299e1;
    border-radius: 6px;
    padding: 12px 14px;
    transition: all 0.2s ease;
    position: relative;
}

.prompt-item:hover {
    background: #edf2f7;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.prompt-number {
    position: absolute;
    top: 8px;
    right: 12px;
    font-size: 0.75rem;
    font-weight: 700;
    color: #4299e1;
    background: #e6f2ff;
    padding: 2px 8px;
    border-radius: 12px;
}

.prompt-text {
    font-size: 0.9rem;
    line-height: 1.6;
    color: #2d3748;
    white-space: pre-wrap;
    word-break: break-word;
    padding-right: 50px;
}

.attachment-count {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 0.75rem;
    color: #718096;
    margin-top: 8px;
    padding: 4px 10px;
    background: #e2e8f0;
    border-radius: 12px;
    font-weight: 500;
}

.no-prompts {
    color: #718096;
    font-style: italic;
    text-align: center;
    padding: 20px;
}
"""

_PROMPTS_JS = """
document.querySelectorAll('.prompt-item').forEach(item => {
    const textEl = item.querySelector('.prompt-text');
    if (!textEl) return;

    const fullText = textEl.textContent;

    // Only add toggle if text is longer than 300 chars
    if (fullText.length > 300) {
        textEl.classList.add('collapsed');

        const btn = document.createElement('button');
        btn.className = 'expand-toggle';
        btn.textContent = '▼ Show full prompt';

        btn.onclick = () => {
            const isExpanded = textEl.classList.contains('expanded');
            if (isExpanded) {
                textEl.classList.remove('expanded');
                textEl.classList.add('collapsed');
                btn.textContent = '▼ Show full prompt';
            } else {
                textEl.classList.remove('collapsed');
                textEl.classList.add('expanded');
                btn.textContent = '▲ Show less';
            }
        };

        item.appendChild(btn);
    }
});
"""


# ---------------------------------------------------------------------------
# Helper functions for prompts list view
# ---------------------------------------------------------------------------

def _format_datetime_full(dt: datetime) -> str:
    """Format datetime as 'Monday 2nd March 12:34'."""
    sentinel = datetime.min.replace(tzinfo=timezone.utc)
    if dt == sentinel:
        return "Unknown date"

    # Get day with ordinal suffix
    day = dt.day
    if 10 <= day % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")

    return dt.strftime(f"%A {day}{suffix} %B %H:%M")


def _format_relative_time(dt: datetime) -> str:
    """Format relative time like 'x days ago', '2 weeks ago', etc."""
    sentinel = datetime.min.replace(tzinfo=timezone.utc)
    if dt == sentinel:
        return ""

    now = datetime.now(timezone.utc)
    delta = now - dt

    if delta < timedelta(minutes=1):
        return "just now"
    elif delta < timedelta(hours=1):
        minutes = int(delta.total_seconds() / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif delta < timedelta(days=1):
        hours = int(delta.total_seconds() / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif delta < timedelta(days=7):
        days = delta.days
        return f"{days} day{'s' if days != 1 else ''} ago"
    elif delta < timedelta(days=30):
        weeks = delta.days // 7
        return f"{weeks} week{'s' if weeks != 1 else ''} ago"
    elif delta < timedelta(days=365):
        months = delta.days // 30
        return f"{months} month{'s' if months != 1 else ''} ago"
    else:
        years = delta.days // 365
        return f"{years} year{'s' if years != 1 else ''} ago"


def _sanitize_and_clip_text(text: str, max_length: int = 300) -> str:
    """Safely clip text to max_length and sanitize to prevent HTML breaking.

    Ensures we don't break in the middle of HTML entities or special characters.
    """
    if len(text) <= max_length:
        return escape(text)

    # Clip to max_length
    clipped = text[:max_length]

    # Escape HTML to prevent breaking
    safe_text = escape(clipped)

    # Add ellipsis to indicate truncation
    return safe_text + "..."


def _render_prompt_item(node: MessageNode, prompt_number: int, has_attachment: bool) -> str:
    """Render a single user prompt item with number and attachment indicator."""
    parts = []

    # Add prompt number
    parts.append(f'<div class="prompt-number">#{prompt_number}</div>')

    if node.text:
        # Hard clip to 300 characters and sanitize
        safe_text = _sanitize_and_clip_text(node.text, 300)
        parts.append(f'<div class="prompt-text">{safe_text}</div>')
    else:
        parts.append('<div class="prompt-text">(empty prompt)</div>')

    # Show attachment count instead of details
    if has_attachment:
        parts.append('<div class="attachment-count">📎 1 attachment</div>')

    content = "\n".join(parts)

    return f'<div class="prompt-item">{content}</div>'


def _render_chat_card(chat_name: str, nodes: List[MessageNode]) -> str:
    """Render a single chat card with all user prompts."""
    # Filter only user messages
    user_prompts = [n for n in nodes if n.role == "user"]

    if not user_prompts:
        return ""

    # Count total prompts
    prompt_count = len(user_prompts)

    # Get the earliest timestamp for the chat
    sentinel = datetime.min.replace(tzinfo=timezone.utc)
    first_timestamp = min(n.timestamp for n in user_prompts)

    # If all timestamps are sentinel (unknown), use current time as fallback
    if first_timestamp == sentinel:
        first_timestamp = datetime.now(timezone.utc)

    datetime_full = _format_datetime_full(first_timestamp)
    datetime_relative = _format_relative_time(first_timestamp)

    # Render prompts with numbering
    prompts_html_parts = []
    for idx, node in enumerate(user_prompts, start=1):
        has_attachment = node.image_id is not None
        prompts_html_parts.append(_render_prompt_item(node, idx, has_attachment))

    prompts_html = "\n".join(prompts_html_parts)

    # Add prompt count to title
    title_with_count = f"{escape(chat_name)} ({prompt_count} prompt{'s' if prompt_count != 1 else ''})"

    return f"""<div class="chat-card">
    <div class="chat-header">
        <div class="chat-title">{title_with_count}</div>
        <div class="chat-datetime">
            <span class="datetime-main">{datetime_full}</span>
            <span class="datetime-relative">({datetime_relative})</span>
        </div>
    </div>
    <div class="chat-body">
        <div class="prompts-list">
{prompts_html}
        </div>
    </div>
</div>"""


def format_prompts_list(conversations: List[Tuple[str, List[MessageNode]]]) -> str:
    """Render all user prompts from all conversations as a list view.

    Conversations are sorted by their earliest user prompt timestamp.
    Each chat shows its title, datetime, and all user prompts with
    expandable content (max 200 chars visible initially).
    """
    # Filter out conversations with no user prompts and sort by earliest timestamp
    chat_cards = []
    for name, nodes in conversations:
        user_prompts = [n for n in nodes if n.role == "user"]
        if user_prompts:
            earliest = min(n.timestamp for n in user_prompts)
            chat_cards.append((earliest, name, nodes))

    # Sort by timestamp (earliest first)
    chat_cards.sort(key=lambda x: x[0])

    # Render cards
    cards_html = "\n".join(
        _render_chat_card(name, nodes)
        for _, name, nodes in chat_cards
    )

    if not cards_html:
        cards_html = '<div class="no-prompts">No user prompts found.</div>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>User Prompts List</title>
<style>{_PROMPTS_CSS}</style>
</head>
<body>
<h1>📝 User Prompts from All Chats</h1>
<div class="chat-list">
{cards_html}
</div>
<script>{_PROMPTS_JS}</script>
</body>
</html>"""
