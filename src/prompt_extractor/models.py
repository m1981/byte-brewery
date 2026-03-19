from dataclasses import dataclass
from typing import Optional

@dataclass
class BranchInfo:
    prompt_id: str
    display_name: str

@dataclass
class UserPrompt:
    text: str
    branch_info: Optional[BranchInfo] = None