from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class ContextDefinition:
    id: str
    tag: str
    cmd: str

@dataclass
class PromptDefinition:
    id: str
    text: str

@dataclass
class CheckDefinition:
    id: str
    prompt_id: str
    model: str
    context_ids: List[str]
    max_chars: int = 16000

@dataclass
class Config:
    definitions: Dict[str, ContextDefinition]
    prompts: Dict[str, PromptDefinition]
    checks: List[CheckDefinition]