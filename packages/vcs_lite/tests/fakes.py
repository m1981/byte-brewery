"""Test doubles for the app layer: a deterministic worker and a diff tool that records its calls."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from vcs_lite.app.worker import Outcome
from vcs_lite.core.difftool import DiffResult


class ManualWorker:
    """Same contract as Worker, but jobs run only when the test calls settle()."""

    def __init__(self):
        self.queued: list[tuple[str, Callable, Callable]] = []
        self.history: list[str] = []
        self._busy: set[str] = set()

    def busy(self, key: str) -> bool:
        return key in self._busy

    def submit(self, key: str, job: Callable, on_done: Callable) -> bool:
        if key in self._busy:
            return False
        self._busy.add(key)
        self.queued.append((key, job, on_done))
        return True

    def step(self) -> str:
        """Run only the oldest queued job; returns its key."""
        key, job, on_done = self.queued.pop(0)
        self.history.append(key)
        try:
            outcome = Outcome(value=job())
        except Exception as exc:  # noqa: BLE001 - delivered to on_done like the real worker
            outcome = Outcome(error=exc)
        self._busy.discard(key)
        on_done(outcome)
        return key

    def settle(self) -> None:
        """Run queued jobs, including the follow-up jobs they schedule, until nothing is left."""
        while self.queued:
            self.step()


class FakeDiffTool:
    """Stands in for Beyond Compare; optionally edits the right side like a user would."""

    def __init__(self, edit_right: Callable[[Path], None] | None = None):
        self.edit_right = edit_right
        self.calls: list[dict] = []

    def open(self, left: Path, right: Path, left_title: str, right_title: str):
        self.calls.append({"left": left, "right": right, "left_title": left_title, "right_title": right_title,
                           "left_bytes": left.read_bytes(), "right_bytes": right.read_bytes()})
        if self.edit_right:
            self.edit_right(right)
        return self

    def wait(self) -> DiffResult:
        return DiffResult(0, "")
