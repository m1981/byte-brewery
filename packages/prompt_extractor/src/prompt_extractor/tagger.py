# prompt_extractor/tagger.py

from pathlib import Path
from typing import List, Tuple, Dict
from prompt_extractor.models import MessageNode

class TagManager:
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_file = self.cache_dir / "chatmap_tags.json"

    def get_tags(self, conversations: List[Tuple[str, List[MessageNode]]]) -> Dict[str, List[str]]:
        # TODO: Implement logic
        return {}

    def _call_llm(self, prompt_text: str) -> List[str]:
        # TODO: Implement API call
        return []