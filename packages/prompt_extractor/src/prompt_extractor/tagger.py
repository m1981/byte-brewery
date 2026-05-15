import os
import json
from pathlib import Path
from typing import Dict, List, Tuple

from google import genai
from google.genai import types

from prompt_extractor.models import MessageNode


class TagManager:
    def __init__(self, directory: Path):
        """Initialize the TagManager and load the local cache."""
        self.cache_file = directory / "chatmap_tags.json"
        self.is_debug = os.environ.get("CHATMAP_DEBUG") == "1"
        self.cache_data = self._load_cache()

    def _debug(self, message: str):
        """Print debug messages if CHATMAP_DEBUG=1 is set."""
        if self.is_debug:
            print(f"[DEBUG] {message}")

    def _load_cache(self) -> dict:
        """Load tags from JSON, returning an empty dict if missing or corrupt."""
        if not self.cache_file.exists():
            self._debug(f"No cache file found at {self.cache_file}")
            return {}
        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._debug(f"Loaded {len(data)} cached prompts from {self.cache_file.name}")
                return data
        except (json.JSONDecodeError, IOError):
            self._debug("Cache file is corrupt or unreadable. Starting fresh.")
            return {}

    def _save_cache(self) -> None:
        """Persist the current cache dictionary to disk."""
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(self.cache_data, f, indent=2)
        self._debug(f"Saved updated cache to {self.cache_file.name}")

    def _extract_first_prompt(self, nodes: List[MessageNode]) -> str:
        """Find the text of the very first user prompt in a conversation."""
        for node in nodes:
            if node.role == "user" and node.text:
                return node.text.strip()
        return ""

    def _call_llm(self, prompt: str, chat_titles: List[str]) -> List[str]:
        """
        Calls the Gemini API to generate tags for a given prompt and its associated titles.
        Requires GEMINI_API_KEY environment variable.
        """
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("Warning: GEMINI_API_KEY not found. Skipping auto-tagging.")
            return []

        try:
            # Initialize the new Gemini Client
            client = genai.Client(api_key=api_key)

            # Define the system instruction separately
            sys_instruct = (
                "You are an expert librarian organizing  knowledge base. "
                "Read the provided Chat Titles and the Initial Prompt, then generate 2 to 4 tags. "
                "\n\nRULES:"
                "\n1. Focus ONLY on technologies (e.g., python, react), architectural patterns (e.g., solid, mvvm), or core business domains (e.g., cybersecurity, ecommerce)."
                "\n2. IGNORE persona instructions (do NOT output tags like 'roleplay', 'expert', 'developer')."
                "\n3. IGNORE action words (do NOT output tags like 'analysis', 'summary', 'opinion', 'help', 'transcript')."
                "\n4. Use singular, lowercase nouns."
                "\n\nOutput ONLY valid JSON in this exact format: {\"tags\": [\"tag1\", \"tag2\"]}"
            )

            # Combine titles and prompt into a single payload
            titles_str = " | ".join(chat_titles)
            truncated_prompt = prompt[:1000]
            payload = f"Chat Titles: {titles_str}\n\nInitial Prompt: {truncated_prompt}"

            self._debug(f"Sending API Request...")
            self._debug(f"  Model: gemini-2.5-flash")
            self._debug(f"  Payload: {payload[:150]}...")

            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=payload,
                config=types.GenerateContentConfig(
                    system_instruction=sys_instruct,
                    response_mime_type="application/json",
                    temperature=0.1,
                )
            )

            self._debug(f"  Raw Response: {response.text.strip()}")

            data = json.loads(response.text)
            tags = data.get("tags", [])
            self._debug(f"  Parsed Tags: {tags}")
            return tags

        except Exception as e:
            print(f"Warning: LLM API call failed ({type(e).__name__}: {str(e)}). Skipping tags.")
            return []

    def get_tags(self, conversations: List[Tuple[str, List[MessageNode]]], fetch_missing: bool = True) -> Dict[
        str, List[str]]:
        """
        Process conversations, fetch missing tags via LLM, and return a mapping.
        """
        result: Dict[str, List[str]] = {}
        pending_prompts: Dict[str, List[str]] = {}

        self._debug(f"Processing {len(conversations)} conversations for tags...")

        for chat_name, nodes in conversations:
            first_prompt = self._extract_first_prompt(nodes)

            if not first_prompt:
                self._debug(f"[{chat_name}] No user prompts found. Skipping.")
                result[chat_name] = []
                continue

            if first_prompt in self.cache_data:
                self._debug(f"[{chat_name}] Cache HIT.")
                result[chat_name] = self.cache_data[first_prompt]
            else:
                # Cache miss. Queue it up if we are allowed to fetch.
                if fetch_missing:
                    self._debug(f"[{chat_name}] Cache MISS. Queuing for API.")
                    if first_prompt not in pending_prompts:
                        pending_prompts[first_prompt] = []
                    pending_prompts[first_prompt].append(chat_name)
                else:
                    # Offline mode, no tags available
                    result[chat_name] = []

        # 2. Fetch missing tags from LLM (Deduplicated by unique prompt text)
        cache_updated = False

        if pending_prompts:
            self._debug(f"Found {len(pending_prompts)} unique prompts requiring API calls.")

        for prompt_text, chat_names in pending_prompts.items():
            self._debug(f"Fetching tags for branches: {chat_names}")

            # Pass both the prompt and the list of chat titles to the LLM
            tags = self._call_llm(prompt_text, chat_names)

            self.cache_data[prompt_text] = tags
            cache_updated = True

            # Apply the fetched tags to ALL branches that shared this prompt
            for chat_name in chat_names:
                result[chat_name] = tags

        # 3. Save cache to disk if we fetched new data
        if cache_updated:
            self._save_cache()

        return result