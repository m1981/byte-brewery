from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from prompt_extractor.models import MessageNode


def _parse_timestamp(create_time: str) -> datetime:
    if not create_time:
        return datetime.min.replace(tzinfo=timezone.utc)
    try:
        return datetime.fromisoformat(create_time.replace("Z", "+00:00"))
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)


def parse_chunks(data: Dict[str, Any]) -> List[MessageNode]:
    """Parse conversation chunks into a sorted list of MessageNodes.

    Filters out thought chunks (isThought=True) and empty chunks
    (no text and no driveImage). Results are sorted chronologically.
    """
    try:
        chunks = data.get("chunkedPrompt", {}).get("chunks", [])
    except AttributeError:
        return []

    if chunks is None:
        return []

    nodes = []
    for chunk in chunks:
        if not isinstance(chunk, dict):
            continue
        if chunk.get("isThought"):
            continue

        text = chunk.get("text", "").strip()
        image_id: Optional[str] = None
        drive_image = chunk.get("driveImage")
        if drive_image:
            image_id = drive_image.get("id")

        if not text and not image_id:
            continue

        nodes.append(
            MessageNode(
                timestamp=_parse_timestamp(chunk.get("createTime", "")),
                role=chunk.get("role", ""),
                text=text,
                image_id=image_id,
                branch_parent=chunk.get("branchParent"),
            )
        )

    nodes.sort(key=lambda n: n.timestamp)
    return nodes


def build_threads(
    nodes: List[MessageNode],
) -> List[Tuple[Optional[str], List[MessageNode]]]:
    """Split nodes into conversation threads based on branchParent markers.

    Returns a list of (branch_display_name, nodes) tuples. The first entry
    is always the main thread with None as the name.
    """
    if not nodes:
        return [(None, [])]

    threads: List[Tuple[Optional[str], List[MessageNode]]] = []
    current_name: Optional[str] = None
    current_thread: List[MessageNode] = []

    for node in nodes:
        if node.branch_parent:
            threads.append((current_name, current_thread))
            current_name = node.branch_parent.get("displayName")
            current_thread = [node]
        else:
            current_thread.append(node)

    threads.append((current_name, current_thread))
    return threads


def _time_str(node: MessageNode) -> str:
    sentinel = datetime.min.replace(tzinfo=timezone.utc)
    if node.timestamp == sentinel:
        return "??:??:??"
    return node.timestamp.strftime("%H:%M:%S")


def _render_node(node: MessageNode) -> List[str]:
    """Render a single message node with callout-style formatting."""
    lines = []

    if node.role == "user":
        # User prompt as callout box
        lines.append(f"> **💭 User Prompt** · `{_time_str(node)}`")
        if node.image_id:
            lines.append(f"> 📎 *Attached Image:* `{node.image_id}`")
            if node.text:
                lines.append(">")
        if node.text:
            # Split text into lines and prefix each with blockquote marker
            for text_line in node.text.split('\n'):
                lines.append(f"> {text_line}")
    else:
        # Model response - regular formatting with header
        lines.append(f"**🤖 Model Response** · `{_time_str(node)}`")
        lines.append("")
        if node.image_id:
            lines.append(f"📎 *Attached Image:* `{node.image_id}`")
            lines.append("")
        if node.text:
            lines.append(node.text)

    lines.append("")
    return lines


def format_timeline(nodes: List[MessageNode]) -> str:
    """Format nodes as a chronological timeline with branch rewind markers."""
    lines: List[str] = ["# Conversation Timeline\n"]
    for node in nodes:
        if node.branch_parent:
            display_name = node.branch_parent.get("displayName", "")
            lines += [
                "",
                f"> **🔄 TIMELINE BRANCH** · `{_time_str(node)}`",
                f"> *Branched from: \"{display_name}\"*",
                "",
            ]
        lines += _render_node(node)
    return "\n".join(lines)


def format_tree(threads: List[Tuple[Optional[str], List[MessageNode]]]) -> str:
    """Format conversation threads as a tree with main thread and branches."""
    lines: List[str] = ["# Conversation Threads\n"]
    branch_count = 0

    for branch_name, nodes in threads:
        if not nodes:
            continue

        if branch_name is None:
            lines.append("## 🌿 Main Thread")
        else:
            branch_count += 1
            lines.append(f"## 🌿 Branch {branch_count}")
            lines.append(f"> *Branched from: \"{branch_name}\"*")

        lines.append("")

        for node in nodes:
            lines += _render_node(node)

        lines.append("---\n")

    return "\n".join(lines)
