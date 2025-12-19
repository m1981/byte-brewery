import os
import sys
import pytest
import subprocess
from unittest.mock import MagicMock, patch, mock_open, ANY

# STANDARD IMPORT - Works because we added 'src' to pythonpath in pyproject.toml
from aireview.core import (
    Config,
    ContextDefinition,
    CheckDefinition,
    ShellCommandRunner,
    OpenAIProvider,
    ReviewEngine,
    main,
    load_config
)


# ==========================================
# 1. DOMAIN & CONFIG TESTS
# ==========================================

def test_config_from_dict_valid():
    data = {
        "definitions": [{"id": "d1", "tag": "t1", "cmd": "ls"}],
        "checks": [{"id": "c1", "system_prompt": "p1", "model": "m1", "context": ["d1"]}]
    }
    config = Config.from_dict(data)
    assert len(config.definitions) == 1
    assert config.definitions["d1"].cmd == "ls"
    assert config.checks[0].model == "m1"


def test_config_from_dict_malformed_definition():
    data = {
        "definitions": [
            {"id": "d1", "cmd": "ls"},
            {"cmd": "ls"},
            {"id": "d2"}
        ],
        "checks": []
    }
    config = Config.from_dict(data)
    assert len(config.definitions) == 1
    assert "d1" in config.definitions


def test_config_from_dict_malformed_check():
    data = {
        "definitions": [],
        "checks": [
            {"id": "c1"},
            {"system_prompt": "foo"}
        ]
    }
    config = Config.from_dict(data)
    assert len(config.checks) == 1
    assert config.checks[0].id == "c1"
    assert config.checks[0].model == "gpt-3.5-turbo"


# ==========================================
# 2. SHELL COMMAND RUNNER TESTS
# ==========================================

def test_shell_runner_success():
    runner = ShellCommandRunner()
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = " output "
        result = runner.run("echo hello")

        mock_run.assert_called_once_with(
            "echo hello",
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        assert result == "output"


def test_shell_runner_empty_command():
    runner = ShellCommandRunner()
    assert runner.run("") == ""
    assert runner.run("   ") == ""
    assert runner.run(None) == ""


def test_shell_runner_failure():
    runner = ShellCommandRunner()
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1, cmd="bad", stderr="oops"
        )
        result = runner.run("bad")

        assert "ERROR executing 'bad':" in result
        assert "oops" in result


def test_shell_runner_file_not_found():
    runner = ShellCommandRunner()
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError()
        result = runner.run("missing_shell")
        assert "ERROR: Shell environment issue." in result


# ==========================================
# 3. OPENAI PROVIDER TESTS
# ==========================================

def test_openai_provider_init_missing_package():
    with patch.dict(sys.modules, {'openai': None}):
        with pytest.raises(SystemExit) as exc:
            OpenAIProvider("key")
        assert exc.value.code == 1


def test_openai_provider_analyze_success():
    with patch("openai.OpenAI") as mock_client_cls:
        mock_client = mock_client_cls.return_value
        mock_client.chat.completions.create.return_value.choices = [
            MagicMock(message=MagicMock(content="AI_RESPONSE"))
        ]

        provider = OpenAIProvider("fake-key")
        response = provider.analyze("gpt-4", "sys_prompt", "user_code")

        assert response == "AI_RESPONSE"

        call_args = mock_client.chat.completions.create.call_args
        assert call_args.kwargs['model'] == "gpt-4"
        messages = call_args.kwargs['messages']
        assert messages[0] == {"role": "system", "content": "sys_prompt"}
        assert messages[1] == {"role": "user", "content": "user_code"}


def test_openai_provider_analyze_error():
    with patch("openai.OpenAI") as mock_client_cls:
        mock_client = mock_client_cls.return_value
        mock_client.chat.completions.create.side_effect = Exception("API Down")

        provider = OpenAIProvider("k")
        response = provider.analyze("m", "s", "u")
        assert "AI API ERROR: API Down" in response


# ==========================================
# 4. REVIEW ENGINE TESTS
# ==========================================

@pytest.fixture
def mock_runner():
    runner = MagicMock()
    runner.run.side_effect = lambda cmd: f"output_of_{cmd}"
    return runner


@pytest.fixture
def mock_ai():
    ai = MagicMock()
    ai.analyze.return_value = "PASS"
    return ai


@pytest.fixture
def sample_config():
    return Config(
        definitions={
            "d1": ContextDefinition("d1", "tag1", "cmd1"),
            "d2": ContextDefinition("d2", "tag2", "cmd2")
        },
        checks=[
            CheckDefinition("c1", "prompt1", "model1", ["d1", "d2"]),
            CheckDefinition("c2", "prompt2", "model2", ["missing_def"])
        ]
    )


def test_engine_build_context(sample_config, mock_runner, mock_ai):
    engine = ReviewEngine(sample_config, mock_runner, mock_ai)
    context = engine.build_context("c1")

    assert "<tag1>\noutput_of_cmd1\n</tag1>" in context
    assert "<tag2>\noutput_of_cmd2\n</tag2>" in context


def test_engine_build_context_missing_def(sample_config, mock_runner, mock_ai):
    engine = ReviewEngine(sample_config, mock_runner, mock_ai)
    context = engine.build_context("c2")

    assert "<!-- Warning: Context 'missing_def' not defined -->" in context


def test_engine_run_check_pass(sample_config, mock_runner, mock_ai):
    engine = ReviewEngine(sample_config, mock_runner, mock_ai)
    result = engine.run_check("c1")

    assert result is True
    mock_ai.analyze.assert_called_with("model1", "prompt1", ANY)


def test_engine_run_check_fail(sample_config, mock_runner, mock_ai):
    mock_ai.analyze.return_value = "FAIL: Bad code"
    engine = ReviewEngine(sample_config, mock_runner, mock_ai)
    result = engine.run_check("c1")

    assert result is False


def test_engine_run_check_fail_case_insensitive(sample_config, mock_runner, mock_ai):
    mock_ai.analyze.return_value = "fail: Bad code"
    engine = ReviewEngine(sample_config, mock_runner, mock_ai)
    assert engine.run_check("c1") is False


def test_engine_run_check_dry_run_override(sample_config, mock_runner, mock_ai):
    mock_ai.analyze.return_value = "DRY RUN: Would FAIL"
    engine = ReviewEngine(sample_config, mock_runner, mock_ai)
    assert engine.run_check("c1") is True


def test_engine_run_check_empty_context(sample_config, mock_runner, mock_ai):
    # Even if runner returns empty string, the engine wraps it in XML tags.
    # So context is NOT empty, and AI IS called.
    mock_runner.run.return_value = ""
    engine = ReviewEngine(sample_config, mock_runner, mock_ai)

    result = engine.run_check("c1")
    assert result is True
    # FIXED: AI IS called because context contains XML tags
    mock_ai.analyze.assert_called()

def test_engine_run_check_exception(sample_config, mock_runner, mock_ai):
    mock_runner.run.side_effect = Exception("Boom")
    engine = ReviewEngine(sample_config, mock_runner, mock_ai)

    result = engine.run_check("c1")
    assert result is False


def test_engine_check_not_found(sample_config, mock_runner, mock_ai):
    engine = ReviewEngine(sample_config, mock_runner, mock_ai)
    assert engine.run_check("non_existent") is False


# ==========================================
# 5. CLI TESTS
# ==========================================

def test_load_config_creates_default():
    with patch("os.path.exists", return_value=False), \
            patch("builtins.open", mock_open(read_data="checks: []")) as m_open:
        config = load_config("dummy.yaml")

        m_open.assert_any_call("dummy.yaml", 'w')
        assert isinstance(config, Config)


def test_load_config_io_error():
    with patch("os.path.exists", return_value=False), \
            patch("builtins.open", side_effect=IOError("Perm denied")):
        with pytest.raises(SystemExit) as exc:
            load_config("dummy.yaml")
        assert exc.value.code == 1


def test_load_config_invalid_yaml():
    with patch("os.path.exists", return_value=True), \
            patch("builtins.open", mock_open(read_data="{invalid_yaml")):
        with pytest.raises(SystemExit) as exc:
            load_config("dummy.yaml")
        assert exc.value.code == 1


def test_main_no_args():
    with patch("sys.argv", ["aireview.py"]):
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 1


def test_main_init():
    # We patch the string path now because 'aireview' is resolvable via pythonpath
    with patch("sys.argv", ["aireview.py", "init"]), \
            patch("aireview.core.load_config") as mock_load:
        main()
        mock_load.assert_called_once()


def test_main_validate():
    with patch("sys.argv", ["aireview.py", "validate"]), \
            patch("aireview.core.load_config"):
        main()


def test_main_run_dry_run_success():
    mock_cfg = Config(definitions={}, checks=[
        CheckDefinition("c1", "p", "m", [])
    ])

    with patch("sys.argv", ["aireview.py", "run", "--dry-run"]), \
            patch("aireview.core.load_config", return_value=mock_cfg), \
            patch("aireview.core.ShellCommandRunner"), \
            patch("aireview.core.MockAIProvider") as MockAI:
        MockAI.return_value.analyze.return_value = "PASS"

        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 0


def test_main_run_fail():
    # FIXED: Added a dummy definition so context is not empty.
    # If context is empty, the engine skips the AI call and returns True (Pass).
    mock_cfg = Config(
        definitions={"d1": ContextDefinition("d1", "t", "c")},
        checks=[CheckDefinition("c1", "p", "m", ["d1"])]
    )

    with patch("sys.argv", ["aireview.py", "run", "--dry-run"]), \
            patch("aireview.core.load_config", return_value=mock_cfg), \
            patch("aireview.core.ShellCommandRunner"), \
            patch("aireview.core.MockAIProvider") as MockAI:
        MockAI.return_value.analyze.return_value = "FAIL"

        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 1


# def test_main_run_missing_api_key():
#     # 1. Capture the mutmut variable if it exists
#     mutmut_env = {}
#     if 'MUTANT_UNDER_TEST' in os.environ:
#         mutmut_env['MUTANT_UNDER_TEST'] = os.environ['MUTANT_UNDER_TEST']
#
#     with patch("sys.argv", ["aireview.py", "run"]), \
#             patch("aireview.core.load_config"), \
#             patch.dict(os.environ, mutmut_env, clear=True): # 2. Restore it into the cleared env
#         with pytest.raises(SystemExit) as exc:
#             main()
#         assert exc.value.code == 1


def test_main_run_specific_check_not_found():
    mock_cfg = Config(definitions={}, checks=[])

    with patch("sys.argv", ["aireview.py", "run", "--check", "missing"]), \
            patch("aireview.core.load_config", return_value=mock_cfg), \
            patch.dict(os.environ, {"OPENAI_API_KEY": "sk-..."}):
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 1