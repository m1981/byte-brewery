import os
import json
from pathlib import Path
from typing import Dict, List, Tuple, Set

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

    def _get_all_known_tags(self) -> Set[str]:
        """Extract all unique tags currently stored in the cache."""
        known_tags = set()
        for tags in self.cache_data.values():
            known_tags.update(tags)
        return known_tags

    def _call_llm(self, prompt: str, chat_titles: List[str], known_tags: List[str]) -> List[str]:
        """
        Calls the Gemini API to generate tags for a given prompt and its associated titles.
        Passes known_tags to prevent tag bloat and enforce reuse, but allows dynamic creation.
        """
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("Warning: GEMINI_API_KEY not found. Skipping auto-tagging.")
            return []

        try:
            # Initialize the new Gemini Client
            client = genai.Client(api_key=api_key)

            # Format known tags for the prompt
            known_tags_str = ", ".join(sorted(known_tags)) if known_tags else "None yet. You are creating the first tags."

            # Updated System Instruction: Explains the FORMAT, but leaves the actual tags 100% dynamic
            sys_instruct = f"""You are an expert librarian organizing a developer's knowledge base.
We use a dynamic Prefix Tagging System. You must generate tags using these formats:
1. Domain Tags: Enclosed in brackets representing the broad industry or field (e.g., [DOMAIN_NAME]).
2. Tech/Tool Tags: Prefixed with # representing specific technologies, frameworks, or tools (e.g., #TechnologyName).
3. Intent/Concept Tags: Prefixed with # representing the architectural pattern or goal (e.g., #ConceptName).

EXISTING TAG VOCABULARY:
{known_tags_str}

Read the provided Chat Titles and the Initial Prompt, then generate 2 to 4 tags.

RULES:
1. REUSE tags from the "EXISTING TAG VOCABULARY" whenever possible to prevent tag bloat!
2. If no existing tag fits, dynamically GENERATE a new one strictly following the Prefix Tagging System formats above.
3. Always try to include at least one Domain tag (in brackets).
4. IGNORE persona instructions (do NOT output tags like '#Roleplay', '#Expert').
5. IGNORE generic action words (do NOT output tags like '#Analysis', '#Summary').

Output ONLY valid JSON in this exact format: {{"tags": ["tag1", "tag2"]}}"""

            titles_str = " | ".join(chat_titles)
            truncated_prompt = prompt[:1000]
            payload = f"Chat Titles: {titles_str}\n\nInitial Prompt: {truncated_prompt}"

            self._debug(f"Sending API Request...")
            self._debug(f"  Model: gemini-2.5-flash")
            self._debug(f"  Known Tags Count: {len(known_tags)}")

            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=payload,
                config=types.GenerateContentConfig(
                    system_instruction=sys_instruct,
                    response_mime_type="application/json",
                    temperature=0.1, # Keep low so it prefers reusing existing tags over hallucinating synonyms
                )
            )

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

            # 1. Load all currently known tags from the cache
            known_tags_set = self._get_all_known_tags()

        for prompt_text, chat_names in pending_prompts.items():
            self._debug(f"Fetching tags for branches: {chat_names}")

            # 2. Pass the current known_tags_set to the LLM
            tags = self._call_llm(prompt_text, chat_names, list(known_tags_set))

            # 3. Immediately add the newly generated tags to our running set!
            # This ensures the NEXT prompt in this loop knows about the tags we JUST created.
            known_tags_set.update(tags)

            self.cache_data[prompt_text] = tags
            cache_updated = True

            # Apply the fetched tags to ALL branches that shared this prompt
            for chat_name in chat_names:
                result[chat_name] = tags

        # 3. Save cache to disk if we fetched new data
        if cache_updated:
            self._save_cache()

        return result