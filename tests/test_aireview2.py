import pytest
from unittest.mock import MagicMock, patch, ANY
from src.aireview.core import (
    Config,
    ContextDefinition,
    PromptDefinition,
    CheckDefinition,
    ReviewEngine,
    UniversalAIProvider,
    ShellCommandRunner
)


# ==========================================
# 1. FIXTURES (Setup & Isolation)
# ==========================================

@pytest.fixture
def mock_runner():
    """Provides a mock command runner that returns predictable output."""
    runner = MagicMock(spec=ShellCommandRunner)
    runner.run.return_value = "mock_command_output"
    return runner


@pytest.fixture
def mock_ai_provider():
    """Provides a generic mock AI provider."""
    provider = MagicMock()
    provider.analyze.return_value = "PASS"
    return provider


@pytest.fixture
def sample_config():
    """Provides a valid, standard configuration object."""
    return Config(
        definitions={
            "git_diff": ContextDefinition("git_diff", "diff_tag", "git diff"),
        },
        prompts={
            "security_prompt": PromptDefinition("security_prompt", "Find bugs")
        },
        checks=[
            CheckDefinition(
                id="security_check",
                prompt_id="security_prompt",
                model="gpt-4",
                context_ids=["git_diff"]
            )
        ]
    )


# ==========================================
# 2. CONFIGURATION TESTS
# ==========================================

def test_config_parses_valid_dictionary():
    """Should correctly parse a valid dictionary into a Config object."""
    # Given
    data = {
        "definitions": [
            {"id": "d1", "tag": "t1", "cmd": "echo 1"}
        ],
        "prompts": [
            {"id": "p1", "text": "You are a bot"}
        ],
        "checks": [
            {"id": "c1", "prompt_id": "p1", "model": "m1", "context": ["d1"]}
        ]
    }

    # When
    config = Config.from_dict(data)

    # Then
    assert "d1" in config.definitions
    assert "p1" in config.prompts
    assert config.checks[0].prompt_id == "p1"

def test_config_handles_inline_prompts_backward_compatibility():
    """Should create a virtual prompt definition if 'system_prompt' is used inline."""
    # Given
    data = {
        "checks": [
            {"id": "c1", "system_prompt": "Inline Prompt", "context": []}
        ]
    }

    # When
    config = Config.from_dict(data)

    # Then
    assert "inline_c1" in config.prompts
    assert config.prompts["inline_c1"].text == "Inline Prompt"
    assert config.checks[0].prompt_id == "inline_c1"

# ==========================================
# 3. UNIVERSAL ROUTER TESTS (The New Feature)
# ==========================================

def test_router_routes_claude_models_to_anthropic():
    """Should route models starting with 'claude-' to AnthropicProvider."""
    # Given
    router = UniversalAIProvider()
    router.anthropic = MagicMock()  # Mock the internal provider
    router.openai = MagicMock()

    # When
    router.analyze("claude-3-opus", "sys", "user")

    # Then
    router.anthropic.analyze.assert_called_once()
    router.openai.analyze.assert_not_called()


def test_router_routes_gemini_models_to_google():
    """Should route models starting with 'gemini-' to GeminiProvider."""
    # Given
    router = UniversalAIProvider()
    router.gemini = MagicMock()
    router.openai = MagicMock()

    # When
    router.analyze("gemini-1.5-pro", "sys", "user")

    # Then
    router.gemini.analyze.assert_called_once()
    router.openai.analyze.assert_not_called()

# ==========================================
# 4. ENGINE BEHAVIOR TESTS
# ==========================================

def test_engine_builds_context_correctly(sample_config, mock_runner, mock_ai_provider):
    """Should execute commands and wrap output in XML tags."""
    # Given
    engine = ReviewEngine(sample_config, mock_runner, mock_ai_provider)
    mock_runner.run.return_value = "diff_content"

    # When
    context = engine.build_context("security_check")

    # Then
    assert "<diff_tag>" in context
    assert "diff_content" in context
    assert "</diff_tag>" in context
    mock_runner.run.assert_called_with("git diff")

def test_engine_resolves_prompt_correctly(sample_config, mock_runner, mock_ai_provider):
    """Should look up the prompt text from the registry before calling AI."""
    # Given
    engine = ReviewEngine(sample_config, mock_runner, mock_ai_provider)

    # When
    engine.run_check("security_check")

    # Then
    mock_ai_provider.analyze.assert_called_with(
        "gpt-4",
        "Find bugs", # The text from the prompt registry
        ANY          # <--- Fixed: Using unittest.mock.ANY
    )

def test_engine_fails_when_prompt_id_missing(sample_config, mock_runner, mock_ai_provider):
    """Should return False if the check references a non-existent prompt ID."""
    # Given
    sample_config.checks[0].prompt_id = "missing_prompt"
    engine = ReviewEngine(sample_config, mock_runner, mock_ai_provider)

    # When
    result = engine.run_check("security_check")

    # Then
    assert result is False
    mock_ai_provider.analyze.assert_not_called()

def test_engine_handles_missing_context_definition(sample_config, mock_runner, mock_ai_provider):
    """Should insert a warning comment if a check references a non-existent context (Edge Case)."""
    # Given
    sample_config.checks[0].context_ids = ["ghost_context"]
    engine = ReviewEngine(sample_config, mock_runner, mock_ai_provider)

    # When
    context = engine.build_context("security_check")

    # Then
    assert "<!-- Warning: Context 'ghost_context' not defined -->" in context
    mock_runner.run.assert_not_called()


def test_engine_skips_ai_if_context_is_empty(sample_config, mock_runner, mock_ai_provider):
    """Should return True (Pass) immediately if context is empty to save API costs (Edge Case)."""
    # Given
    engine = ReviewEngine(sample_config, mock_runner, mock_ai_provider)
    # Simulate empty output from command
    mock_runner.run.return_value = ""

    # When
    # Note: build_context wraps empty string in tags: <tag>\n\n</tag>.
    # We need to ensure the engine logic handles "effectively empty" or just accepts it.
    # In current implementation, it wraps empty output.
    # Let's simulate a check with NO context IDs to force empty string.
    sample_config.checks[0].context_ids = []

    result = engine.run_check("security_check")

    # Then
    assert result is True
    mock_ai_provider.analyze.assert_not_called()


def test_engine_fails_when_ai_says_fail(sample_config, mock_runner, mock_ai_provider):
    """Should return False if the AI provider returns a verdict containing 'FAIL'."""
    # Given
    engine = ReviewEngine(sample_config, mock_runner, mock_ai_provider)
    mock_ai_provider.analyze.return_value = "FAIL: Security vulnerability found."

    # When
    result = engine.run_check("security_check")

    # Then
    assert result is False


def test_engine_passes_when_ai_says_pass(sample_config, mock_runner, mock_ai_provider):
    """Should return True if the AI provider returns a verdict without 'FAIL'."""
    # Given
    engine = ReviewEngine(sample_config, mock_runner, mock_ai_provider)
    mock_ai_provider.analyze.return_value = "PASS: Looks good."

    # When
    result = engine.run_check("security_check")

    # Then
    assert result is True