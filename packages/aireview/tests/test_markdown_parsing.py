import pytest
import json
from unittest.mock import Mock
from src.aireview.engine import ReviewEngine
from src.aireview.domain import Config


# --- Fixture ---
@pytest.fixture
def engine():
    return ReviewEngine(
        config=Mock(spec=Config),
        runner=Mock(),
        provider_factory=Mock(),
        debugger=Mock(),
        patch_manager=Mock()
    )


# --- The Test Case ---

def test_parse_markdown_wrapped_fix_response(engine):
    """
    Scenario: AI returns a 'FIX' response wrapped in Markdown text and code blocks.
    This mimics the exact failure seen in the logs.
    """

    # This is the exact structure from your log
    raw_response = """# Code Analysis Report

I've analyzed your code against the provided rules. Here's my assessment:

```json
{
    "status": "FIX",
    "feedback": "## Issues Found\\n\\n### 1. Magic Numbers...",
    "modified_files": [
        {
            "path": "models/entities.py",
            "content": "class SystemConfig:\\n    DEFAULT_TAGS = []"
        }
    ]
}
"""

    # Action
    result = engine._parse_json_response(raw_response)

    # Assertions

    # 1. Status should be FIX (not MANUAL)
    assert result["status"] == "FIX", "Engine failed to extract JSON from Markdown"

    # 2. Feedback should come from the JSON, not the outer markdown
    assert "Magic Numbers" in result["feedback"]

    # 3. Modified files should be parsed correctly
    assert len(result["modified_files"]) == 1
    assert result["modified_files"][0]["path"] == "models/entities.py"
    assert "SystemConfig" in result["modified_files"][0]["content"]