"""Double Shift, recognised without Tk so it can be tested with a clock (DES-VCS-057).

A tap is Shift pressed and released with no other key and no click in between, so capital letters and
Shift-clicks (REQ-VCS-029) never count. Two taps fire when the second starts at most 350 ms after the first
ended; left and right Shift count alike.

Trace: DES-VCS-057, REQ-VCS-033, DEC-VCS-097
"""

from __future__ import annotations

import time
from collections.abc import Callable

DOUBLE_SHIFT_MS = 350
SHIFTS = frozenset({"Shift_L", "Shift_R"})


def _now_ms() -> float:
    return time.monotonic() * 1000


class DoubleShift:
    def __init__(self, on_double: Callable[[], None], clock: Callable[[], float] = _now_ms):
        self._on_double, self._clock = on_double, clock
        self._down = False                 # Shift is held
        self._alone = False                # nothing else happened since it went down
        self._pressed_at = 0.0
        self._last_tap: float | None = None   # when the previous tap ended

    def press(self, keysym: str) -> None:
        if keysym not in SHIFTS:
            self.other()
        elif not self._down:               # a held key may repeat its press
            self._down, self._alone, self._pressed_at = True, True, self._clock()

    def release(self, keysym: str) -> None:
        if keysym not in SHIFTS or not self._down:
            return
        self._down = False
        if not self._alone:
            return
        if self._last_tap is not None and self._pressed_at - self._last_tap <= DOUBLE_SHIFT_MS:
            self._last_tap = None
            self._on_double()
        else:
            self._last_tap = self._clock()

    def other(self) -> None:
        """Any other key or a click: the current press is no tap, and no pair is pending."""
        self._alone, self._last_tap = False, None
