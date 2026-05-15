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

    def _call_llm_batch(self, batch_payload: List[dict], known_tags: List[str]) -> Dict[str, List[str]]:
        """
        Calls the Gemini API to generate exactly 4 tags for a BATCH of prompts.
        """
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("Warning: GEMINI_API_KEY not found. Skipping auto-tagging.")
            return {}

        try:
            client = genai.Client(api_key=api_key)

            known_tags_str = ", ".join(
                sorted(known_tags)) if known_tags else "None yet. You are creating the first tags."

            sys_instruct = f"""Please help me tag my LLM prompts based on chat title and first prompt.
            You will receive a JSON array of items. Each item has an 'id', 'titles', and 'prompt'.

            For EACH item, you MUST generate an array of EXACTLY 2 tags. 
            The s tags MUST follow this exact positional structure:

            1. Domain Tag: The broad hobby name in brackets and PascalCase. (e.g., #Programming, #Elctronics, #KitchenDesign, #DIY, etc.)
            2. Tool/Medium Tag: The primary language, framework, software, or physical medium. PascalCase with #. (e.g., #Python, #React, #Corpus). IF NO SPECIFIC TECH EXISTS, use the medium/toolset (e.g., #CadSoftware, #HandTools, #AgileFramework). NEVER use generic words like #GeneralTech or #Various.

            EXISTING TAG VOCABULARY:
            {known_tags_str}

            CRITICAL RULES:
            1. REUSE tags from the "EXISTING TAG VOCABULARY" whenever possible to prevent bloat!
            2. EXACTLY 2 TAGS PER ITEM.
            3. NO GENERIC WORDS. Banned tags: #GeneralTech, #Analysis, #InsightExtraction, #KnowledgeRetrieval, #ConceptExplanation.

            Output ONLY a valid JSON object where keys are the 'id' from the input, and values are arrays of exactly 2 tags."""

            payload_str = json.dumps(batch_payload, indent=2)

            self._debug(f"Sending API Batch Request ({len(batch_payload)} items)...")
            self._debug(f"  Model: gemini-3.1-pro-preview")
            self._debug(f"  Known Tags Count: {len(known_tags)}")

            response = client.models.generate_content(
                model='gemini-3.1-pro-preview',
                contents=payload_str,
                config=types.GenerateContentConfig(
                    system_instruction=sys_instruct,
                    response_mime_type="application/json",
                    temperature=0.1,  # Low temperature ensures strict adherence to the 4-tag rule
                )
            )

            data = json.loads(response.text)
            self._debug(f"  Successfully parsed batch response.")
            return data

        except Exception as e:
            print(f"Warning: LLM Batch API call failed ({type(e).__name__}: {str(e)}).")
            return {}

    def get_tags(self, conversations: List[Tuple[str, List[MessageNode]]], fetch_missing: bool = True) -> Dict[str, List[str]]:
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

        # 2. Process Misses in Batches
        if pending_prompts:
            unique_prompts = list(pending_prompts.items())
            self._debug(f"Found {len(unique_prompts)} unique prompts requiring API calls.")

            known_tags_set = self._get_all_known_tags()
            batch_size = 50

            # Chunk the unique prompts into batches of 20
            for i in range(0, len(unique_prompts), batch_size):
                batch = unique_prompts[i:i + batch_size]

                # Prepare the payload and a mapping to link IDs back to the original prompt text
                batch_payload = []
                id_to_prompt_text = {}

                for idx, (prompt_text, chat_names) in enumerate(batch):
                    item_id = f"item_{idx}"
                    id_to_prompt_text[item_id] = prompt_text

                    batch_payload.append({
                        "id": item_id,
                        "titles": chat_names,
                        "prompt": prompt_text[:800] # Truncated slightly more to save batch tokens
                    })

                # Call the LLM with the batch
                batch_results = self._call_llm_batch(batch_payload, list(known_tags_set))

                # Process the results
                for item_id, tags in batch_results.items():
                    if item_id in id_to_prompt_text:
                        original_prompt_text = id_to_prompt_text[item_id]
                        chat_names = pending_prompts[original_prompt_text]

                        # Update running state
                        known_tags_set.update(tags)
                        self.cache_data[original_prompt_text] = tags
                        cache_updated = True

                        # Apply to all branches
                        for chat_name in chat_names:
                            result[chat_name] = tags

        # 3. Save cache to disk if we fetched new data
        if cache_updated:
            self._save_cache()

        return result