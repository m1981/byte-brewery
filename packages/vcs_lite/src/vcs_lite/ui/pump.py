"""Bridges Worker and the Tk event loop: results are drained on the Tk thread, polling only while work runs.

Trace: DES-VCS-017, REQ-VCS-016, REQ-VCS-101
"""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from typing import Any

from vcs_lite.app.worker import OnDone, Worker


class TkPump:
    """An Executor for AppModel: submits to Worker and polls with after() until nothing is pending."""

    def __init__(self, root: tk.Misc, worker: Worker, interval_ms: int = 50):
        self._root = root
        self._worker = worker
        self._interval_ms = interval_ms
        self._scheduled: str | None = None

    @property
    def polling(self) -> bool:
        return self._scheduled is not None

    def busy(self, key: str) -> bool:
        return self._worker.busy(key)

    def submit(self, key: str, job: Callable[[], Any], on_done: OnDone) -> bool:
        accepted = self._worker.submit(key, job, on_done)
        if accepted and not self.polling:
            self._schedule()
        return accepted

    def _schedule(self) -> None:
        self._scheduled = self._root.after(self._interval_ms, self._poll)

    def _poll(self) -> None:
        self._scheduled = None
        self._worker.drain()
        if self._worker.pending:
            self._schedule()
