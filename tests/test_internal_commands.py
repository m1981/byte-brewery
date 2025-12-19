import pytest
import sys
import logging
from unittest.mock import MagicMock, patch
from aireview.core import (
    Config,
    ShellCommandRunner,
    ReviewEngine,
    CheckDefinition,
    ContextDefinition,
    CommandError  # <--- Import the new exception
)


# ==========================================
# 1. COMMAND RUNNER TESTS (Low Level)
# ==========================================

def test_runner_executes_valid_internal_command():
    """Test that internal:push_diff triggers the python logic."""
    runner = ShellCommandRunner()

    # Mock the internal method so we don't actually run git
    with patch.object(runner, '_run_internal_push_diff', return_value="DIFF CONTENT") as mock_method:
        result = runner.run("internal:push_diff")

        assert result == "DIFF CONTENT"
        mock_method.assert_called_once()


def test_runner_rejects_unknown_internal_command():
    """Test that internal:typo returns a clear error message."""
    runner = ShellCommandRunner()

    # Expect an exception now, not a string return
    with pytest.raises(CommandError) as excinfo:
        runner.run("internal:format_disk")

    assert "Unknown internal command 'internal:format_disk'" in str(excinfo.value)
    assert "Available commands: internal:push_diff" in str(excinfo.value)

def test_runner_treats_old_syntax_as_shell():
    """Test that @push_diff is NOT intercepted and falls through to shell (where it fails)."""
    runner = ShellCommandRunner()

    # We expect subprocess to try running '@push_diff' and fail
    with patch("subprocess.run") as mock_sub:
        mock_sub.side_effect = OSError("Command not found")  # Simulate shell failure

        # This should NOT trigger _run_internal_push_diff
        with patch.object(runner, '_run_internal_push_diff') as mock_internal:
            try:
                runner.run("@push_diff")
            except (OSError, CommandError):
                pass # Expected failure

            mock_internal.assert_not_called()


# ==========================================
# 2. CONFIGURATION TESTS (Validation)
# ==========================================

def test_config_does_not_inject_magic_defaults():
    """
    STRICT MODE TEST:
    Ensure we DO NOT automatically inject 'push_diff'.
    The user must define it explicitly.
    """
    data = {"checks": []}
    config = Config.from_dict(data)

    # Assert that 'push_diff' is NOT magically added
    assert "push_diff" not in config.definitions


def test_config_validation_detects_command_in_context_list(caplog):
    """
    Test that putting 'internal:push_diff' directly in the context list
    raises a helpful error telling the user to define it first.
    """
    data = {
        "checks": [{
            "id": "bad_check",
            "context": ["internal:push_diff"]  # WRONG: Should be an ID
        }]
    }

    with pytest.raises(SystemExit):
        Config.from_dict(data)

    # Updated assertion to match the new generic hint
    assert "Did you mean to define a context with cmd: 'internal:push_diff'?" in caplog.text


def test_config_validation_detects_old_syntax_in_context_list(caplog):
    """Test that putting '@push_diff' in context list raises a hint."""
    data = {
        "checks": [{
            "id": "old_check",
            "context": ["@push_diff"]  # WRONG
        }]
    }

    with pytest.raises(SystemExit):
        Config.from_dict(data)

    # Updated assertion to match the new generic hint
    assert "Did you mean to define a context with cmd: '@push_diff'?" in caplog.text


def test_config_validation_detects_missing_push_diff_id(caplog):
    """Test specific hint when user uses 'push_diff' ID but forgot to define it."""
    data = {
        "checks": [{
            "id": "check1",
            "context": ["push_diff"]  # ID exists in checks...
        }],
        "definitions": []  # ...but missing in definitions!
    }

    with pytest.raises(SystemExit):
        Config.from_dict(data)

    assert "You must define 'push_diff' in 'definitions'" in caplog.text


# ==========================================
# 3. ENGINE TESTS (Integration)
# ==========================================

def test_engine_handles_empty_internal_context(capsys):
    """Test that the engine prints the specific hint for internal:push_diff."""

    # Setup Config (Explicitly defining the internal command now)
    config = Config(
        definitions={"my_diff": ContextDefinition("my_diff", "tag", "internal:push_diff")},
        prompts={},
        checks=[CheckDefinition("c1", "p1", "gpt-4", ["my_diff"])]
    )

    # Setup Runner to return empty string
    runner = ShellCommandRunner()
    with patch.object(runner, '_run_internal_push_diff', return_value=""):
        engine = ReviewEngine(config, runner, MagicMock())
        engine.run_check("c1")

        # Check stdout for the hint
        captured = capsys.readouterr()
        assert "No staged changes found" in captured.out

def test_engine_aborts_on_command_error(capsys):
    """Test that if a command fails (raises CommandError), the check aborts immediately."""
    config = Config(
        definitions={"bad_cmd": ContextDefinition("bad_cmd", "tag", "internal:bad")},
        prompts={},
        checks=[CheckDefinition("c1", "p1", "gpt-4", ["bad_cmd"])]
    )

    runner = ShellCommandRunner()
    # We don't need to patch run, because run() naturally raises CommandError for bad internal commands

    engine = ReviewEngine(config, runner, MagicMock())
    result = engine.run_check("c1")

    assert result is False
    captured = capsys.readouterr()
    assert "Error gathering context" in captured.out
    assert "Unknown internal command" in captured.out