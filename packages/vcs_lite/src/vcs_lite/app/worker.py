"""Runs operations off the UI thread, at most one per key; results are handed back by drain().

Trace: DES-VCS-016, DES-VCS-017, REQ-VCS-016, REQ-VCS-101
"""

from __future__ import annotations

import queue
import threading
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class Outcome:
    value: Any = None
    error: BaseException | None = None


OnDone = Callable[[Outcome], None]


class Executor(Protocol):
    def busy(self, key: str) -> bool: ...

    def submit(self, key: str, job: Callable[[], Any], on_done: OnDone) -> bool: ...


class Worker:
    """A key stays busy until its result is drained, so on_done may safely schedule a follow-up."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._busy: set[str] = set()
        self._finished: queue.SimpleQueue[tuple[str, OnDone, Outcome]] = queue.SimpleQueue()

    def busy(self, key: str) -> bool:
        with self._lock:
            return key in self._busy

    @property
    def pending(self) -> bool:
        """True while any job runs or waits to be drained; the UI polls only then (REQ-VCS-101)."""
        with self._lock:
            return bool(self._busy)

    def ready(self) -> bool:
        return not self._finished.empty()

    def submit(self, key: str, job: Callable[[], Any], on_done: OnDone) -> bool:
        with self._lock:
            if key in self._busy:
                return False
            self._busy.add(key)
        threading.Thread(target=self._run, args=(key, job, on_done), daemon=True).start()
        return True

    def _run(self, key: str, job: Callable[[], Any], on_done: OnDone) -> None:
        try:
            outcome = Outcome(value=job())
        except Exception as exc:  # noqa: BLE001 - every failure goes back to the UI thread
            outcome = Outcome(error=exc)
        self._finished.put((key, on_done, outcome))

    def drain(self) -> int:
        """Deliver finished results on the calling (UI) thread; returns how many were delivered."""
        delivered = 0
        while True:
            try:
                key, on_done, outcome = self._finished.get_nowait()
            except queue.Empty:
                return delivered
            with self._lock:
                self._busy.discard(key)
            on_done(outcome)
            delivered += 1
