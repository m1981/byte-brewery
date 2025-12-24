from dataclasses import dataclass, field
from typing import List, Dict, Optional
from pydantic import BaseModel, Field

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
    include_patterns: List[str] = field(default_factory=list)
    exclude_patterns: List[str] = field(default_factory=list)

@dataclass
class Config:
    definitions: Dict[str, ContextDefinition]
    prompts: Dict[str, PromptDefinition]
    checks: List[CheckDefinition]

class ModifiedFile(BaseModel):
    path: str = Field(description="The file path relative to the project root")
    content: str = Field(description="The FULL content of the file after fixes")

class ReviewResult(BaseModel):
    status: Literal["PASS", "FAIL", "FIX"] = Field(description="The outcome of the review")
    feedback: str = Field(description="Markdown explanation of the findings")
    modified_files: List[ModifiedFile] = Field(
        default_factory=list,
        description="List of files that need changes (only if status is FIX)"
    )