from typing import Dict, Any, List


def extract_user_prompts(data: Dict[str, Any]) -> List[str]:
    """
    Extracts text from chunks where the role is 'user'.
    Ignores chunks without text (e.g., image-only uploads).
    """
    try:
        chunks = data.get("chunkedPrompt", {}).get("chunks", [])
    except AttributeError:
        return []

    prompts = []
    for chunk in chunks:
        if not isinstance(chunk, dict):
            continue

        is_user = chunk.get("role") == "user"
        text = chunk.get("text", "").strip()

        if is_user and text:
            prompts.append(text)

    return prompts


def format_to_markdown(filename: str, prompts: List[str]) -> str:
    """
    Formats a list of prompts into a Markdown string.
    """
    if not prompts:
        return f"# File: {filename}\n\n*No user prompts found.*\n"

    lines = [f"# File: {filename}\n"]
    for index, prompt in enumerate(prompts, start=1):
        lines.append(f"## Prompt {index}\n{prompt}\n")

    return "\n".join(lines)