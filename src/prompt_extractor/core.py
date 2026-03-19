from typing import Dict, Any, List

from prompt_extractor.models import BranchInfo, UserPrompt


def extract_user_prompts(data: Dict[str, Any]) -> List[UserPrompt]:
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

        if chunk.get("role") != "user":
            continue

        text = chunk.get("text", "").strip()
        if not text:
            continue

        branch_parent = chunk.get("branchParent")
        branch_info = None
        if branch_parent:
            branch_info = BranchInfo(
                prompt_id=branch_parent["promptId"],
                display_name=branch_parent["displayName"],
            )

        prompts.append(UserPrompt(text=text, branch_info=branch_info))

    return prompts


def format_to_markdown(filename: str, prompts: List[UserPrompt]) -> str:
    """
    Formats a list of UserPrompt objects into a Markdown string.
    """
    if not prompts:
        return f"# File: {filename}\n\n*No user prompts found.*\n"

    lines = [f"# File: {filename}\n"]
    for index, prompt in enumerate(prompts, start=1):
        lines.append(f"## Prompt {index}")
        if prompt.branch_info:
            bi = prompt.branch_info
            lines.append(f"> 🌿 **Branched from:** {bi.display_name} (`{bi.prompt_id}`)\n")
        lines.append(f"{prompt.text}\n")

    return "\n".join(lines)
