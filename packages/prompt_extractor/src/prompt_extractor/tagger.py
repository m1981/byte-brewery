import json
from pathlib import Path
from typing import Dict, List, Tuple

from prompt_extractor.models import MessageNode


class TagManager:
    def __init__(self, directory: Path):
        """Initialize the TagManager and load the local cache."""
        self.cache_file = directory / "chatmap_tags.json"
        self.cache_data = self._load_cache()

    def _load_cache(self) -> dict:
        """Load tags from JSON, returning an empty dict if missing or corrupt."""
        if not self.cache_file.exists():
            return {}
        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            # If the file is corrupt, we start fresh. 
            # It will be overwritten with valid JSON on the next save.
            return {}

    def _save_cache(self) -> None:
        """Persist the current cache dictionary to disk."""
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(self.cache_data, f, indent=2)

    def _extract_first_prompt(self, nodes: List[MessageNode]) -> str:
        """Find the text of the very first user prompt in a conversation."""
        for node in nodes:
            if node.role == "user" and node.text:
                return node.text.strip()
        return ""

    def _call_llm(self, prompt: str) -> List[str]:
        """
        Stub for the actual LLM API call.
        In production, this will use google-genai or openai to generate tags.
        """
        # TODO: Implement actual API call here
        return []

    def get_tags(self, conversations: List[Tuple[str, List[MessageNode]]]) -> Dict[str, List[str]]:
        """
        Process conversations, fetch missing tags via LLM, and return a mapping
        of chat_name -> list of tags.
        """
        result: Dict[str, List[str]] = {}

        # Map of unique prompt_text -> list of chat_names that share this exact prompt
        # This is how we deduplicate branches!
        pending_prompts: Dict[str, List[str]] = {}

        # 1. Check cache and identify what needs fetching
        for chat_name, nodes in conversations:
            first_prompt = self._extract_first_prompt(nodes)

            if not first_prompt:
                # Edge case: No user prompts
                result[chat_name] = []
                continue

            if first_prompt in self.cache_data:
                # Cache hit! No API call needed.
                result[chat_name] = self.cache_data[first_prompt]
            else:
                # Cache miss. Queue it up.
                if first_prompt not in pending_prompts:
                    pending_prompts[first_prompt] = []
                pending_prompts[first_prompt].append(chat_name)

        # 2. Fetch missing tags from LLM (Deduplicated by unique prompt text)
        cache_updated = False
        for prompt_text, chat_names in pending_prompts.items():
            try:
                # This is where the mock intercepts during testing
                tags = self._call_llm(prompt_text)
            except Exception:
                # Edge case: API failure. Fail gracefully so the CLI doesn't crash.
                tags = []

            # Update our in-memory cache
            self.cache_data[prompt_text] = tags
            cache_updated = True

            # Apply the fetched tags to ALL branches that shared this prompt
            for chat_name in chat_names:
                result[chat_name] = tags

        # 3. Save cache to disk if we fetched new data
        if cache_updated:
            self._save_cache()

        return result