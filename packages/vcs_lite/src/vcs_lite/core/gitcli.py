"""The only place that runs git: environment, timeouts, decoding, failures as results.

Trace: DES-VCS-001, DES-VCS-002, DES-VCS-003, DES-VCS-004, DES-VCS-035, DES-VCS-047, REQ-VCS-101, REQ-VCS-010, REQ-VCS-014, REQ-VCS-017
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

LOCAL_TIMEOUT = 30.0
NETWORK_TIMEOUT = 120.0
BATCH_SSH = "ssh -o BatchMode=yes"
GIT_LOG_ENV = "VCS_LITE_GIT_LOG"  # path of the git call log; unset means no log (DES-VCS-047)


@dataclass(frozen=True)
class GitResult:
    args: tuple[str, ...]
    returncode: int
    stdout: bytes
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0

    @property
    def message(self) -> str:
        """What to show the user: stderr, or stdout when git wrote its explanation there."""
        return (self.stderr.strip() or self.stdout.decode("utf-8", errors="replace").strip())


class GitCli:
    def __init__(self, git: str = "git", env: Mapping[str, str] | None = None):
        self.git = git
        self.base_env = dict(os.environ if env is None else env)
        self.call_count = 0
        self.log_path = self.base_env.get(GIT_LOG_ENV) or None

    def env_for(self, repo: Path, *, read_only: bool, network: bool) -> dict[str, str]:
        env = {**self.base_env, "GIT_TERMINAL_PROMPT": "0"}
        if read_only:
            env["GIT_OPTIONAL_LOCKS"] = "0"  # `git status` must not rewrite the index
        if network and "GIT_SSH_COMMAND" not in env and not self._has_core_ssh_command(repo):
            env["GIT_SSH_COMMAND"] = BATCH_SSH  # fail instead of waiting for a key passphrase
        return env

    def _has_core_ssh_command(self, repo: Path) -> bool:
        return bool(self.run(repo, "config", "--get", "core.sshCommand", read_only=True).stdout.strip())

    def run(self, repo: Path, *args: str, input: bytes | None = None, read_only: bool = False,
            network: bool = False, timeout: float | None = None) -> GitResult:
        env = self.env_for(repo, read_only=read_only, network=network)
        argv = [self.git, "-C", str(repo), "-c", "core.quotepath=false", *args]
        limit = timeout if timeout is not None else (NETWORK_TIMEOUT if network else LOCAL_TIMEOUT)
        self.call_count += 1
        if self.log_path:
            append_log(self.log_path, {"t": time.monotonic(), "pid": os.getpid(), "cmd": args[0] if args else ""})
        try:
            proc = subprocess.run(argv, input=input, stdin=None if input is not None else subprocess.DEVNULL,
                                  capture_output=True, env=env, timeout=limit, check=False)
        except subprocess.TimeoutExpired:
            return GitResult(args, -1, b"", f"git {' '.join(args)}: przekroczony limit czasu {limit:g} s")
        except OSError as exc:
            return GitResult(args, 127, b"", f"Nie można uruchomić {self.git}: {exc.strerror or exc}")
        return GitResult(args, proc.returncode, proc.stdout, proc.stderr.decode("utf-8", errors="replace"))


def append_log(path: str, record: dict) -> None:
    """One JSON line in one O_APPEND write, so lines from threads and processes never interleave."""
    fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
    try:
        os.write(fd, (json.dumps(record) + "\n").encode("utf-8"))
    finally:
        os.close(fd)
