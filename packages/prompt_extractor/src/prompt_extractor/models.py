from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List


@dataclass
class MessageNode:
    timestamp: datetime
    role: str
    text: str
    image_id: Optional[str] = None
    branch_parent: Optional[dict] = None
    children: List["MessageNode"] = field(default_factory=list)
