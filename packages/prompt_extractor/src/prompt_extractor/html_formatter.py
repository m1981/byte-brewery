from datetime import datetime, timezone, timedelta
from html import escape
from pathlib import Path
from typing import List, Tuple, Optional, Dict
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

.datetime-main { font-weight: 500; }
.datetime-relative { opacity: 0.85; font-style: italic; }

.chat-body { padding: 16px 20px; }

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

/* ── Search & Tags ── */
.search-container { margin-bottom: 24px; }
.search-input {
    width: 100%;
    padding: 14px 18px;
    border: 2px solid #e2e8f0;
    border-radius: 10px;
    font-size: 1rem;
    outline: none;
    transition: border-color 0.2s;
}
.search-input:focus { border-color: #667eea; }

.tags-container {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    margin-top: 14px;
    padding-top: 14px;
    border-top: 1px solid #edf2f7;
}
.tag-pill {
    background: #edf2f7;
    color: #4a5568;
    padding: 4px 12px;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.02em;
}

/* ── Global Tag Cloud Groups ── */
.tag-groups-container {
    display: flex;
    flex-direction: column;
    gap: 20px;
    margin-bottom: 30px;
    background: #fff;
    padding: 20px;
    border-radius: 12px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.03);
}

.tag-group h3 {
    font-size: 0.85rem;
    color: #718096;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 12px;
    border-bottom: 1px solid #edf2f7;
    padding-bottom: 6px;
}

.global-tags-cloud {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}

.global-tag-pill {
    background: #fff;
    border: 1px solid #cbd5e0;
    padding: 6px 14px;
    border-radius: 999px;
    font-size: 0.8rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
    user-select: none;
}

.global-tag-pill:hover { transform: translateY(-1px); box-shadow: 0 2px 4px rgba(0,0,0,0.05); }

/* Color Coding by Slot */
.pill-domain { color: #2d3748; border-color: #a0aec0; background: #f7fafc; }
.pill-domain.active { background: #4a5568; color: #fff; border-color: #2d3748; }

.pill-tool { color: #c53030; border-color: #feb2b2; background: #fff5f5; }
.pill-tool.active { background: #e53e3e; color: #fff; border-color: #c53030; }

.pill-concept { color: #276749; border-color: #9ae6b4; background: #f0fff4; }
.pill-concept.active { background: #38a169; color: #fff; border-color: #276749; }

.pill-deliverable { color: #553c9a; border-color: #d6bcfa; background: #faf5ff; }
.pill-deliverable.active { background: #805ad5; color: #fff; border-color: #553c9a; }

.global-tag-pill.disabled {
    display: none !important;
}

/* ── Favorites ── */
.fav-btn {
    position: absolute;
    top: 8px;
    right: 50px; /* Place it next to the prompt number */
    background: none;
    border: none;
    font-size: 1.2rem;
    cursor: pointer;
    color: #cbd5e0;
    transition: all 0.2s;
    outline: none;
}
.fav-btn:hover { transform: scale(1.1); }
.prompt-item.is-favorite .fav-btn { color: #ecc94b; /* Gold star */ }
.prompt-item.is-favorite {
    border-left-color: #ecc94b;
    background: #fffff0; /* Slight yellow tint */
}

/* Favorite Filter Toggle */
.fav-filter-btn {
    padding: 10px 16px;
    border: 2px solid #e2e8f0;
    border-radius: 10px;
    background: #fff;
    cursor: pointer;
    font-weight: 600;
    color: #4a5568;
    transition: all 0.2s;
}
.fav-filter-btn.active {
    border-color: #ecc94b;
    background: #fffff0;
    color: #b7791f;
}
.search-row {
    display: flex;
    gap: 10px;
    margin-bottom: 24px;
}
"""

_PROMPTS_JS = """
document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('tag-search');
    const favFilterBtn = document.getElementById('fav-filter');
    const cards = document.querySelectorAll('.chat-card');
    const globalTags = document.querySelectorAll('.global-tag-pill');
    const tagGroups = document.querySelectorAll('.tag-group');

    let activeTags = new Set();
    let showOnlyFavorites = false;

    // 1. Load Favorites from LocalStorage
    let favorites = new Set(JSON.parse(localStorage.getItem('chatmap_favorites') || '[]'));

    // 2. Apply Favorite State and Sort DOM
    function applyFavoritesAndSort() {
        cards.forEach(card => {
            const promptsList = card.querySelector('.prompts-list');
            const prompts = Array.from(promptsList.querySelectorAll('.prompt-item'));

            let hasAnyFavorite = false;

            prompts.forEach(prompt => {
                const pid = prompt.getAttribute('data-prompt-id');
                if (favorites.has(pid)) {
                    prompt.classList.add('is-favorite');
                    hasAnyFavorite = true;
                } else {
                    prompt.classList.remove('is-favorite');
                }
            });

            // Mark the card itself if it contains favorites (useful for filtering)
            if (hasAnyFavorite) {
                card.setAttribute('data-has-favorites', 'true');
            } else {
                card.removeAttribute('data-has-favorites');
            }

            // Sort: Favorites first, then by original DOM order
            prompts.sort((a, b) => {
                const aFav = a.classList.contains('is-favorite') ? -1 : 1;
                const bFav = b.classList.contains('is-favorite') ? -1 : 1;
                return aFav - bFav; 
            });

            // Re-append in sorted order
            prompts.forEach(p => promptsList.appendChild(p));
        });
    }

    // 3. Main Filter Function
    function filterCards() {
        const query = searchInput ? searchInput.value.toLowerCase().trim() : "";
        let availableTags = new Set();

        cards.forEach(card => {
            const cardTagsStr = card.getAttribute('data-tags') || "";
            const cardTagsArray = cardTagsStr.split(' ').filter(t => t);
            const hasFavs = card.hasAttribute('data-has-favorites');

            const matchesText = query === "" || cardTagsStr.includes(query) || card.innerText.toLowerCase().includes(query);
            const matchesFavFilter = !showOnlyFavorites || hasFavs;

            let matchesPills = true;
            if (activeTags.size > 0) {
                for (let tag of activeTags) {
                    if (!cardTagsArray.includes(tag)) {
                        matchesPills = false;
                        break;
                    }
                }
            }

            if (matchesText && matchesPills && matchesFavFilter) {
                card.style.display = 'block';
                cardTagsArray.forEach(t => availableTags.add(t));

                // If "Show Favorites" is on, hide non-favorited prompts inside the visible cards
                const prompts = card.querySelectorAll('.prompt-item');
                prompts.forEach(p => {
                    if (showOnlyFavorites && !p.classList.contains('is-favorite')) {
                        p.style.display = 'none';
                    } else {
                        p.style.display = 'block';
                    }
                });

            } else {
                card.style.display = 'none';
            }
        });

        // Update Tag Pills UI
        globalTags.forEach(pill => {
            const tag = pill.getAttribute('data-tag');
            if (availableTags.has(tag) || activeTags.has(tag)) {
                pill.classList.remove('disabled');
            } else {
                pill.classList.add('disabled');
            }
        });

        // Hide empty Tag Groups
        tagGroups.forEach(group => {
            const hasVisiblePills = Array.from(group.querySelectorAll('.global-tag-pill')).some(p => !p.classList.contains('disabled'));
            group.style.display = hasVisiblePills ? 'block' : 'none';
        });
    }

    // 4. Event Listeners
    document.querySelectorAll('.fav-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const promptItem = e.target.closest('.prompt-item');
            const pid = promptItem.getAttribute('data-prompt-id');

            if (favorites.has(pid)) {
                favorites.delete(pid);
            } else {
                favorites.add(pid);
            }

            // Save to storage
            localStorage.setItem('chatmap_favorites', JSON.stringify(Array.from(favorites)));

            // Re-apply and re-sort
            applyFavoritesAndSort();
            filterCards();
        });
    });

    if (favFilterBtn) {
        favFilterBtn.addEventListener('click', () => {
            showOnlyFavorites = !showOnlyFavorites;
            favFilterBtn.classList.toggle('active', showOnlyFavorites);
            filterCards();
        });
    }

    if (searchInput) searchInput.addEventListener('input', filterCards);

    globalTags.forEach(pill => {
        pill.addEventListener('click', () => {
            const tag = pill.getAttribute('data-tag');
            if (activeTags.has(tag)) {
                activeTags.delete(tag);
                pill.classList.remove('active');
            } else {
                activeTags.add(tag);
                pill.classList.add('active');
            }
            filterCards();
        });
    });

    // Initialize
    applyFavoritesAndSort();
    filterCards();
});
"""


# ---------------------------------------------------------------------------
# Helper functions for prompts list view
# ---------------------------------------------------------------------------

def _format_datetime_full(dt: datetime) -> str:
    """Format datetime as 'Monday 2nd March 12:34'."""
    sentinel = datetime.min.replace(tzinfo=timezone.utc)
    if dt == sentinel:
        return "Date unavailable"

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
        return "time unknown"

    now = datetime.now(timezone.utc)
    delta = now - dt

    # Handle future dates (shouldn't happen, but be defensive)
    if delta < timedelta(0):
        return "in the future"

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
    """Safely clip text to max_length or the first '```', and sanitize.

    Ensures we don't break in the middle of HTML entities or special characters,
    and hides large code blocks from the summary view.
    """
    code_block_idx = text.find("```")

    # Determine the effective cutoff point
    if code_block_idx != -1:
        effective_max = min(max_length, code_block_idx)
    else:
        effective_max = max_length

    # If text is short enough and has no code blocks, return it as-is
    if len(text) <= effective_max and code_block_idx == -1:
        return escape(text)

    # Clip the text and strip trailing whitespace/newlines before the ellipsis
    clipped = text[:effective_max].rstrip()

    # Escape HTML to prevent breaking
    safe_text = escape(clipped)

    # Add ellipsis to indicate truncation
    return safe_text + "..."


def _render_prompt_item(node: MessageNode, prompt_number: int, has_attachment: bool) -> str:
    """Render a single user prompt item with number, attachment, and favorite button."""
    parts = []

    # Generate a unique ID based on the timestamp
    prompt_id = str(int(node.timestamp.timestamp()))

    parts.append(f'<button class="fav-btn" title="Toggle Favorite">★</button>')
    parts.append(f'<div class="prompt-number">#{prompt_number}</div>')

    if node.text:
        safe_text = _sanitize_and_clip_text(node.text, 300)
        parts.append(f'<div class="prompt-text">{safe_text}</div>')
    else:
        parts.append('<div class="prompt-text">(empty prompt)</div>')

    if has_attachment:
        parts.append('<div class="attachment-count">📎 1 attachment</div>')

    content = "\n".join(parts)
    # Add the data-prompt-id attribute here
    return f'<div class="prompt-item" data-prompt-id="{prompt_id}">{content}</div>'


def _render_chat_card(
    chat_name: str,
    nodes: List[MessageNode],
    file_path: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> str:
    """Render a single chat card with all user prompts and tags.

    Args:
        chat_name: Name of the chat
        nodes: List of message nodes
        file_path: Optional path to source file for fallback timestamp
        tags: Optional list of tags for this chat
    """
    # Filter only user messages
    user_prompts = [n for n in nodes if n.role == "user"]

    if not user_prompts:
        return ""

    # Count total prompts
    prompt_count = len(user_prompts)

    # Get the earliest timestamp for the chat
    sentinel = datetime.min.replace(tzinfo=timezone.utc)
    first_timestamp = min(n.timestamp for n in user_prompts)

    # If timestamp is missing, use file modification time as fallback
    if first_timestamp == sentinel and file_path:
        try:
            file_mtime = Path(file_path).stat().st_mtime
            first_timestamp = datetime.fromtimestamp(file_mtime, tz=timezone.utc)
        except (OSError, ValueError):
            # If file access fails, keep sentinel
            pass

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

    # Handle Tags
    tags = tags or []
    data_tags_attr = " ".join(escape(t.lower()) for t in tags)

    tags_html = ""
    if tags:
        pills = "\n".join(f'<span class="tag-pill">{escape(t)}</span>' for t in tags)
        tags_html = f'<div class="tags-container">{pills}</div>'

    return f"""<div class="chat-card" data-tags="{data_tags_attr}">
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
        {tags_html}
    </div>
</div>"""


def format_prompts_list(
        conversations: List[Tuple[str, List[MessageNode]]],
    file_paths: Optional[List[str]] = None,
    tags_map: Optional[Dict[str, List[str]]] = None
) -> str:
    """Render all user prompts from all conversations as a list view.

    Conversations are sorted by their earliest user prompt timestamp.
    Shared history across branches is deduplicated so identical prompts
    (matching timestamp + text) only appear once.

    Args:
        conversations: List of (name, nodes) tuples
        file_paths: Optional list of file paths for fallback timestamps
        tags_map: Optional dictionary mapping chat names to lists of tags
    """
    tags_map = tags_map or {}
    chat_cards = []

    # A global set to track prompts we've already seen across all files
    seen_prompts = set()

    for idx, (name, nodes) in enumerate(conversations):
        # 1. Find ALL user prompts to determine the true start time of the chat
        all_user_prompts = [n for n in nodes if n.role == "user"]

        if not all_user_prompts:
            continue

        # 2. Filter down to ONLY unique prompts we haven't rendered yet
        unique_user_prompts = []
        for n in all_user_prompts:
            # Create a unique fingerprint for this prompt
            prompt_fingerprint = (n.timestamp, n.text)

            if prompt_fingerprint not in seen_prompts:
                seen_prompts.add(prompt_fingerprint)
                unique_user_prompts.append(n)

        # 3. Only create a card if this file actually contains NEW unique prompts
        if unique_user_prompts:
            earliest = min(n.timestamp for n in all_user_prompts)

            file_path = file_paths[idx] if file_paths and idx < len(file_paths) else None

            # Pass ONLY the unique prompts to the renderer
            chat_cards.append((earliest, name, unique_user_prompts, file_path))

    # Sort by timestamp (earliest first)
    chat_cards.sort(key=lambda x: x[0])

    # 2. Render Chat Cards
    cards_html = "\n".join(
        _render_chat_card(name, unique_nodes, file_path, tags_map.get(name, []))
        for _, name, unique_nodes, file_path in chat_cards
    )

    if not cards_html:
        cards_html = '<div class="no-prompts">No user prompts found.</div>'

    # ---------------------------------------------------------
    # Group Tags by Slot (Index)
    # ---------------------------------------------------------
    domains, tools = {}, {}

    for tags in tags_map.values():
        for i, t in enumerate(tags):
            lower_t = t.lower()

            # Slot 0: Domain (Strictly by index 0)
            if i == 0:
                domains[lower_t] = t
            # Slot 1: Tool/Medium (Strictly by index 1)
            elif i == 1:
                tools[lower_t] = t
            # Ignore any extra tags
            else:
                continue

    def _render_tag_group(title: str, tag_dict: dict, color_class: str) -> str:
        if not tag_dict: return ""
        pills = []
        for lower_tag in sorted(tag_dict.keys()):
            display_tag = tag_dict[lower_tag]
            pills.append(f'<div class="global-tag-pill {color_class}" data-tag="{escape(lower_tag)}">{escape(display_tag)}</div>')
        return f'<div class="tag-group"><h3>{title}</h3><div class="global-tags-cloud">{"".join(pills)}</div></div>'

    groups_html = []
    groups_html.append(_render_tag_group("🌐 Domains", domains, "pill-domain"))
    groups_html.append(_render_tag_group("🛠️ Tools & Mediums", tools, "pill-tool"))

    tag_groups_container = f'<div class="tag-groups-container">{"".join(groups_html)}</div>' if any(domains or tools) else ""

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
<div class="search-row">
    <input type="text" id="tag-search" class="search-input" placeholder="Search prompts or filter by tags...">
    <button id="fav-filter" class="fav-filter-btn">⭐ Favorites</button>
</div>

{tag_groups_container}

<div class="chat-list">
{cards_html}
</div>
<script>{_PROMPTS_JS}</script>
</body>
</html>"""
