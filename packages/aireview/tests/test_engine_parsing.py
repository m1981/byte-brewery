import pytest
import json
from unittest.mock import Mock
from src.aireview.engine import ReviewEngine
from src.aireview.domain import Config


# --- Fixtures ---

@pytest.fixture
def engine():
    """Creates an engine instance with mocked dependencies."""
    # We only need to test parsing, so dependencies can be mocks
    return ReviewEngine(
        config=Mock(spec=Config),
        runner=Mock(),
        provider_factory=Mock(),
        debugger=Mock(),
        patch_manager=Mock()
    )


# --- Tests ---

def test_parse_clean_json_pass(engine):
    """Scenario: AI returns perfect JSON with PASS status."""
    raw_response = json.dumps({
        "status": "PASS",
        "feedback": "Looks good!",
        "modified_files": []
    })

    result = engine._parse_json_response(raw_response)

    assert result["status"] == "PASS"
    assert result["feedback"] == "Looks good!"
    assert result["modified_files"] == []


def test_parse_clean_json_fix(engine):
    """Scenario: AI returns perfect JSON with FIX status and files."""
    raw_response = json.dumps({
        "status": "FIX",
        "feedback": "Typo found.",
        "modified_files": [{"path": "a.py", "content": "print('hello')"}]
    })

    result = engine._parse_json_response(raw_response)

    assert result["status"] == "FIX"
    assert len(result["modified_files"]) == 1
    assert result["modified_files"][0]["path"] == "a.py"


def test_parse_markdown_wrapped_json(engine):
    """Scenario: AI wraps JSON in markdown code blocks (Common LLM behavior)."""
    raw_response = """
    Here is the analysis:
    ```json
    {
        "status": "FAIL",
        "feedback": "Security vulnerability detected.",
        "modified_files": []
    }
    ```
    Hope this helps!
    """

    result = engine._parse_json_response(raw_response)

    assert result["status"] == "FAIL"
    assert "Security vulnerability" in result["feedback"]


def test_parse_markdown_wrapped_json_no_lang_tag(engine):
    """Scenario: AI uses ``` without 'json' tag."""
    raw_response = """
    ```
    {
        "status": "PASS",
        "feedback": "OK"
    }
    ```
    """
    result = engine._parse_json_response(raw_response)
    assert result["status"] == "PASS"


def test_parse_legacy_format_fallback(engine):
    """Scenario: AI returns old format (reason instead of feedback)."""
    raw_response = json.dumps({
        "status": "FAIL",
        "reason": "Legacy reason field"
    })

    result = engine._parse_json_response(raw_response)

    assert result["status"] == "FAIL"
    assert result["feedback"] == "Legacy reason field"  # Should map reason -> feedback
    assert result["modified_files"] == []


def test_parse_invalid_json_returns_manual(engine):
    """Scenario: AI returns plain text (Hallucination or refusal)."""
    raw_response = "I cannot process this request because it violates policy."

    result = engine._parse_json_response(raw_response)

    assert result["status"] == "MANUAL"
    assert result["feedback"] == raw_response
    assert result["modified_files"] == []


def test_parse_broken_json_in_markdown(engine):
    """Scenario: AI tries to return JSON but it's syntactically broken."""
    raw_response = """
    ```json
    {
        "status": "PASS",
        "feedback": "Missing closing brace
    ```
    """

    result = engine._parse_json_response(raw_response)

    # Should fall back to MANUAL because regex match succeeds but json.loads fails
    assert result["status"] == "MANUAL"
    assert "Missing closing brace" in result["feedback"]


def test_parse_missing_keys_defaults(engine):
    """Scenario: AI returns JSON but misses optional keys."""
    raw_response = json.dumps({"status": "PASS"})

    result = engine._parse_json_response(raw_response)

    assert result["status"] == "PASS"
    assert result["feedback"] == "No feedback"  # Default
    assert result["modified_files"] == []  # Default