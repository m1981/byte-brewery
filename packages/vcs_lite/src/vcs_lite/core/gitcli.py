"""The only place that runs git: environment, timeouts, decoding, failures as results.

Trace: DES-VCS-001, DES-VCS-002, DES-VCS-003, DES-VCS-004, DES-VCS-035, DES-VCS-047, DES-VCS-053, REQ-VCS-033, REQ-VCS-101, REQ-VCS-010, REQ-VCS-014, REQ-VCS-017
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import tempfile
import threading
import time
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
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
    stopped: bool = False  # a stream left before git finished, so git was ended on purpose (DES-VCS-053)

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

    def _prepare(self, repo: Path, args: tuple[str, ...], *, read_only: bool, network: bool,
                 timeout: float | None) -> tuple[list[str], dict[str, str], float]:
        """argv, environment and time limit of one call, which is counted and logged here (DES-VCS-047)."""
        env = self.env_for(repo, read_only=read_only, network=network)
        argv = [self.git, "-C", str(repo), "-c", "core.quotepath=false", *args]
        limit = timeout if timeout is not None else (NETWORK_TIMEOUT if network else LOCAL_TIMEOUT)
        self.call_count += 1
        if self.log_path:
            append_log(self.log_path, {"t": time.monotonic(), "pid": os.getpid(), "cmd": args[0] if args else ""})
        return argv, env, limit

    def _timed_out(self, args: tuple[str, ...], limit: float) -> GitResult:
        return GitResult(args, -1, b"", f"git {' '.join(args)}: przekroczony limit czasu {limit:g} s")

    def _not_started(self, args: tuple[str, ...], exc: OSError) -> GitResult:
        return GitResult(args, 127, b"", f"Nie można uruchomić {self.git}: {exc.strerror or exc}")

    def run(self, repo: Path, *args: str, input: bytes | None = None, read_only: bool = False,
            network: bool = False, timeout: float | None = None) -> GitResult:
        argv, env, limit = self._prepare(repo, args, read_only=read_only, network=network, timeout=timeout)
        try:
            proc = subprocess.run(argv, input=input, stdin=None if input is not None else subprocess.DEVNULL,
                                  capture_output=True, env=env, timeout=limit, check=False)
        except subprocess.TimeoutExpired:
            return self._timed_out(args, limit)
        except OSError as exc:
            return self._not_started(args, exc)
        return GitResult(args, proc.returncode, proc.stdout, proc.stderr.decode("utf-8", errors="replace"))

    @contextmanager
    def stream(self, repo: Path, *args: str, timeout: float | None = None) -> Iterator[GitStream]:
        """A read whose output lines arrive while git still writes them (DES-VCS-053). Leaving the block before
        the end ends git; afterwards `result` holds the exit code and stderr. Stderr goes to a temporary
        file, so a full stderr pipe can never block git while only stdout is read."""
        argv, env, limit = self._prepare(repo, args, read_only=True, network=False, timeout=timeout)
        with tempfile.TemporaryFile() as err:
            try:
                proc = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=err, env=env,
                                        start_new_session=True)  # its own group: ending git ends its children
            except OSError as exc:
                stream = GitStream(None)
                stream.result = self._not_started(args, exc)
                yield stream
                return
            expired = threading.Event()
            timer = threading.Timer(limit, lambda: (expired.set(), _kill_group(proc)))
            timer.start()
            stream = GitStream(proc)
            try:
                yield stream
            finally:
                timer.cancel()
                stopped = not stream.exhausted and proc.poll() is None
                if stopped:
                    _kill_group(proc)
                proc.stdout.close()
                proc.wait()
                err.seek(0)
                message = err.read().decode("utf-8", errors="replace")
                stream.result = (self._timed_out(args, limit) if expired.is_set() else
                                 GitResult(args, proc.returncode, b"", message, stopped=stopped))


class GitStream:
    """Output lines of a running git, without their newline; `result` is set once the stream is closed."""

    def __init__(self, proc: subprocess.Popen | None):
        self._proc = proc
        self.exhausted = proc is None   # every line was read, so git ends on its own
        self.result: GitResult | None = None

    def __iter__(self) -> Iterator[bytes]:
        if self._proc is None:
            return
        for line in self._proc.stdout:
            yield line[:-1] if line.endswith(b"\n") else line
        self.exhausted = True

    @property
    def process_finished(self) -> bool:
        return self._proc is None or self._proc.poll() is not None


def _kill_group(proc: subprocess.Popen) -> None:
    """SIGKILL to git and whatever it started (an alias, a hook), so nothing keeps its output pipe open."""
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):  # already gone; macOS answers EPERM for a group of zombies
        pass


def append_log(path: str, record: dict) -> None:
    """One JSON line in one O_APPEND write, so lines from threads and processes never interleave."""
    fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
    try:
        os.write(fd, (json.dumps(record) + "\n").encode("utf-8"))
    finally:
        os.close(fd)
