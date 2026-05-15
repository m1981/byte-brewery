import pytest
from unittest.mock import Mock
from src.aireview.engine import ReviewEngine
from src.aireview.domain import Config

def test_bug_markdown_wrapped_json_returns_manual_instead_of_fix():
    """
    Reproduces the bug where a valid JSON wrapped in Markdown
    is treated as MANUAL text instead of being parsed as a FIX.
    """
    # Setup
    engine = ReviewEngine(
        config=Mock(spec=Config),
        runner=Mock(),
        provider_factory=Mock(),
        debugger=Mock(),     # Mocking new dependencies
        patch_manager=Mock() # Mocking new dependencies
    )

    # The exact response format from your logs
    ai_response = """# Code Analysis Report

I've analyzed your code against the provided rules. Here's my assessment:

```json
{
  "status": "FIX",
  "feedback": "Issues found...",
  "modified_files": [{"path": "a.py", "content": "..."}]
}
"""
    # Execution
    result = engine._parse_json_response(ai_response)

    # Assertion
    # CURRENTLY FAILS: result["status"] is "MANUAL"
    # EXPECTED: result["status"] should be "FIX"
    assert result["status"] == "FIX", \
        f"Expected status 'FIX', but got '{result['status']}'. Engine failed to extract JSON from Markdown."