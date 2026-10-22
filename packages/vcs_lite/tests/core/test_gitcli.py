"""Running git: environment, timeouts, failures (DES-VCS-001..004)."""

from __future__ import annotations

import json
import os
import threading

from conftest import GIT_ENV

from vcs_lite.core.gitcli import GIT_LOG_ENV, GitCli


def cli() -> GitCli:
    return GitCli(env=GIT_ENV)


def test_des_vcs_002_git_never_prompts_in_a_hidden_terminal(repo):
    env = cli().env_for(repo.path, read_only=False, network=False)
    assert env["GIT_TERMINAL_PROMPT"] == "0"
    assert "GIT_OPTIONAL_LOCKS" not in env


def test_des_vcs_002_reads_do_not_take_optional_locks(repo):
    assert cli().env_for(repo.path, read_only=True, network=False)["GIT_OPTIONAL_LOCKS"] == "0"


def test_des_vcs_004_network_calls_use_ssh_batch_mode(repo):
    assert cli().env_for(repo.path, read_only=False, network=True)["GIT_SSH_COMMAND"] == "ssh -o BatchMode=yes"


def test_des_vcs_004_user_ssh_command_in_env_is_kept(repo):
    g = GitCli(env={**GIT_ENV, "GIT_SSH_COMMAND": "ssh -i ~/.ssh/work"})
    assert g.env_for(repo.path, read_only=False, network=True)["GIT_SSH_COMMAND"] == "ssh -i ~/.ssh/work"


def test_des_vcs_004_user_core_ssh_command_is_kept(repo):
    repo.git("config", "core.sshCommand", "ssh -i ~/.ssh/work")
    assert "GIT_SSH_COMMAND" not in cli().env_for(repo.path, read_only=False, network=True)


def test_des_vcs_001_output_is_bytes_and_errors_are_decoded(repo):
    r = cli().run(repo.path, "rev-parse", "--is-inside-work-tree")
    assert r.ok and r.stdout == b"true\n"
    bad = cli().run(repo.path, "no-such-command")
    assert not bad.ok and "no-such-command" in bad.message


def test_des_vcs_001_input_goes_to_stdin(repo):
    r = cli().run(repo.path, "hash-object", "--stdin", input=b"abc")
    assert r.stdout.strip() == b"f2ba8f84ab5c1bce84a7b441cb1959cfc7093b7f"


def test_des_vcs_003_timeout_ends_with_a_message_instead_of_hanging(repo):
    repo.git("config", "alias.slow", "!sleep 5")
    r = cli().run(repo.path, "slow", timeout=0.3)
    assert not r.ok and "limit czasu" in r.message


def test_des_vcs_035_every_call_is_counted(repo):
    g = cli()
    g.run(repo.path, "status")
    g.run(repo.path, "status")
    assert g.call_count == 2


# ---------- git call log (DES-VCS-047) ----------

def test_des_vcs_047_each_call_is_logged_as_a_json_line_without_paths(repo, tmp_path):
    log = tmp_path / "git.log"
    GitCli(env={**GIT_ENV, GIT_LOG_ENV: str(log)}).run(repo.path, "status", "--porcelain")
    [record] = [json.loads(line) for line in log.read_text().splitlines()]
    assert set(record) == {"t", "pid", "cmd"} and record["cmd"] == "status" and record["pid"] == os.getpid()
    assert str(repo.path) not in log.read_text()


def test_des_vcs_047_nothing_is_written_without_the_variable(repo, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    before = set(tmp_path.iterdir())
    g = cli()
    g.run(repo.path, "status")
    assert g.log_path is None and set(tmp_path.iterdir()) == before


def test_des_vcs_047_lines_from_parallel_calls_never_interleave(repo, tmp_path):
    log = tmp_path / "git.log"
    g = GitCli(env={**GIT_ENV, GIT_LOG_ENV: str(log)})
    threads = [threading.Thread(target=lambda: [g.run(repo.path, "version") for _ in range(10)]) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert [json.loads(line)["cmd"] for line in log.read_text().splitlines()] == ["version"] * 40
