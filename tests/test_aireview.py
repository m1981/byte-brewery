import pytest
import json
import os
import subprocess
from unittest.mock import MagicMock, patch, mock_open
from dataclasses import asdict

# Import your module.
# Assuming the code is in 'aireview.core'. Adjust import if needed.
from aireview.core import (
    Config,
    ReviewEngine,
    ShellCommandRunner,
    CheckDefinition,
    PromptDefinition,
    ContextDefinition,
    UniversalAIProvider
)


# ==========================================
# 1. CONFIGURATION TESTS
# ==========================================

def test_config_parsing_valid_yaml():
    """Test that a valid dictionary is correctly parsed into data structures."""
    data = {
        "definitions": [{"id": "diff", "cmd": "git diff"}],
        "prompts": [{"id": "p1", "text": "Review this."}],
        "checks": [
            {"id": "c1", "prompt_id": "p1", "context": ["diff"], "model": "gpt-4", "max_chars": 500}
        ]
    }
    config = Config.from_dict(data)

    assert "diff" in config.definitions
    assert config.checks[0].max_chars == 500
    assert config.checks[0].model == "gpt-4"
    # Verify JSON instruction was appended automatically
    assert "JSON" in config.prompts["p1"].text


def test_config_parsing_defaults():
    """Test that missing optional fields use safe defaults."""
    data = {
        "checks": [{"id": "c1"}]  # Minimal check
    }
    config = Config.from_dict(data)

    check = config.checks[0]
    assert check.model == "gpt-3.5-turbo"
    assert check.max_chars == 16000
    assert check.prompt_id == "basic_reviewer"
    # Ensure the default prompt was created
    assert "basic_reviewer" in config.prompts


def test_prompt_file_loading_failure():
    """Test that if a prompt file is missing, we don't crash, but load an error message."""
    data = {
        "prompts": [{"id": "p1", "file": "non_existent.txt"}]
    }
    config = Config.from_dict(data)
    assert "ERROR" in config.prompts["p1"].text


# ==========================================
# 2. ENGINE & CONTEXT TESTS
# ==========================================

@pytest.fixture
def mock_runner():
    runner = MagicMock(spec=ShellCommandRunner)
    runner.run.return_value = "some code changes"
    return runner


@pytest.fixture
def mock_ai():
    ai = MagicMock(spec=UniversalAIProvider)
    ai.analyze.return_value = '{"status": "PASS", "reason": "Looks good"}'
    return ai


@pytest.fixture
def basic_config():
    return Config(
        definitions={"diff": ContextDefinition("diff", "git_changes", "git diff")},
        prompts={"p1": PromptDefinition("p1", "Review this")},
        checks=[CheckDefinition("c1", "p1", "gpt-4", ["diff"], max_chars=100)]
    )


def test_build_context_truncation(basic_config, mock_runner, mock_ai):
    """Test that context is truncated if it exceeds max_chars."""
    # Setup runner to return a long string (150 chars)
    mock_runner.run.return_value = "A" * 150

    engine = ReviewEngine(basic_config, mock_runner, mock_ai)
    context = engine.build_context(basic_config.checks[0])

    # Check max_chars is 100.
    # The engine adds markdown overhead, but the *content* should be truncated.
    # We check if the truncation marker exists.
    assert "[TRUNCATED" in context
    assert len(mock_runner.run.return_value) > 100


def test_build_context_empty_skips_ai(basic_config, mock_runner, mock_ai):
    """Test that if git diff returns empty string, we skip the AI call."""
    mock_runner.run.return_value = ""  # No changes

    engine = ReviewEngine(basic_config, mock_runner, mock_ai)
    result = engine.run_check("c1")

    assert result is True  # Should pass by default
    mock_ai.analyze.assert_not_called()  # Save money!


def test_context_injection_safety(basic_config, mock_runner, mock_ai):
    """Test that malicious user code doesn't break the prompt structure."""
    # User code contains markdown backticks
    mock_runner.run.return_value = "def foo():\n    return ```malicious```"

    engine = ReviewEngine(basic_config, mock_runner, mock_ai)
    context = engine.build_context(basic_config.checks[0])

    # Ensure the engine wrapped it safely (it should still be inside the outer block)
    assert "### Context: git_changes" in context
    assert "```text" in context


# ==========================================
# 3. AI RESPONSE PARSING TESTS
# ==========================================

def test_parse_json_clean(basic_config, mock_runner, mock_ai):
    """Test parsing a clean JSON response."""
    mock_ai.analyze.return_value = '{"status": "FAIL", "reason": "Bad code"}'
    engine = ReviewEngine(basic_config, mock_runner, mock_ai)

    assert engine.run_check("c1") is False


def test_parse_json_markdown_wrapped(basic_config, mock_runner, mock_ai):
    """Test parsing JSON wrapped in Markdown code blocks (common LLM behavior)."""
    mock_ai.analyze.return_value = """
    Here is the review:
    ```json
    {
        "status": "PASS",
        "reason": "Good job"
    }
    ```
    """
    engine = ReviewEngine(basic_config, mock_runner, mock_ai)
    assert engine.run_check("c1") is True


def test_parse_malformed_json_fallback(basic_config, mock_runner, mock_ai):
    """Test fallback when AI returns garbage text but includes the keyword FAIL."""
    mock_ai.analyze.return_value = "I cannot parse this code. FAIL."
    engine = ReviewEngine(basic_config, mock_runner, mock_ai)

    # It should detect "FAIL" in the text and return False
    assert engine.run_check("c1") is False


def test_parse_malformed_json_pass_fallback(basic_config, mock_runner, mock_ai):
    """Test fallback when AI returns garbage text without FAIL keyword."""
    mock_ai.analyze.return_value = "I'm not sure what to do."
    engine = ReviewEngine(basic_config, mock_runner, mock_ai)

    # Default safety: if we can't find FAIL, we assume PASS (or you might want strict mode)
    # Based on current implementation:
    assert engine.run_check("c1") is True


# ==========================================
# 4. PROVIDER & INTEGRATION TESTS
# ==========================================

@patch("subprocess.run")
def test_shell_runner_success(mock_subproc):
    """Test shell runner executes correctly."""
    mock_subproc.return_value.stdout = "file.py"
    runner = ShellCommandRunner()
    output = runner.run("ls")
    assert output == "file.py"


@patch("subprocess.run")
def test_shell_runner_failure(mock_subproc):
    """Test shell runner handles errors gracefully."""
    mock_subproc.side_effect = subprocess.CalledProcessError(1, "cmd", stderr="Not found")
    runner = ShellCommandRunner()
    output = runner.run("bad_cmd")
    assert "ERROR" in output


@patch("openai.OpenAI")
def test_openai_provider_call(mock_openai_cls):
    """Test that OpenAI provider constructs the request correctly."""
    # Setup mock
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "{}"
    mock_client.chat.completions.create.return_value = mock_response

    # Inject API Key to trigger client creation
    with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}):
        provider = UniversalAIProvider()
        provider.analyze("gpt-4", "hello")

        # Verify call arguments
        call_args = mock_client.chat.completions.create.call_args[1]
        assert call_args["model"] == "gpt-4"
        assert call_args["response_format"] == {"type": "json_object"}  # Ensure JSON mode is on


