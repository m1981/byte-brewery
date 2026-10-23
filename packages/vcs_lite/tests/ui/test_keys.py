"""Double Shift recognised without Tk, with an injected clock (DES-VCS-057)."""

from __future__ import annotations

import pytest

from vcs_lite.ui.keys import DOUBLE_SHIFT_MS, DoubleShift


class Clock:
    def __init__(self):
        self.ms = 0.0

    def __call__(self) -> float:
        return self.ms


@pytest.fixture
def keys():
    clock, fired = Clock(), []
    return DoubleShift(lambda: fired.append(clock.ms), clock=clock), clock, fired


def tap(shift: DoubleShift, clock: Clock, *, after: float = 0, hold: float = 40, keysym: str = "Shift_L") -> None:
    clock.ms += after
    shift.press(keysym)
    clock.ms += hold
    shift.release(keysym)


def test_des_vcs_057_two_quick_taps_fire_once(keys):
    shift, clock, fired = keys
    tap(shift, clock)
    tap(shift, clock, after=DOUBLE_SHIFT_MS)
    assert len(fired) == 1
    tap(shift, clock, after=100)   # a third tap starts a new pair
    assert len(fired) == 1


def test_des_vcs_057_left_and_right_shift_count_alike(keys):
    shift, clock, fired = keys
    tap(shift, clock, keysym="Shift_L")
    tap(shift, clock, after=100, keysym="Shift_R")
    assert len(fired) == 1


def test_des_vcs_057_a_slow_second_tap_does_not_fire(keys):
    shift, clock, fired = keys
    tap(shift, clock)
    tap(shift, clock, after=DOUBLE_SHIFT_MS + 1)
    assert fired == []
    tap(shift, clock, after=100)   # but it can begin the next pair
    assert len(fired) == 1


def test_des_vcs_057_shift_with_a_letter_is_not_a_tap(keys):
    shift, clock, fired = keys
    tap(shift, clock)
    shift.press("Shift_L"); shift.press("A"); shift.release("A"); shift.release("Shift_L")   # a capital letter
    tap(shift, clock, after=50)
    assert fired == []


def test_des_vcs_057_a_click_between_taps_breaks_the_pair(keys):
    shift, clock, fired = keys
    tap(shift, clock)
    shift.other()
    tap(shift, clock, after=50)
    assert fired == []


def test_des_vcs_057_shift_click_is_not_a_tap(keys):
    shift, clock, fired = keys
    shift.press("Shift_L"); shift.other(); shift.release("Shift_L")    # Shift-click in the file list
    tap(shift, clock, after=50)
    assert fired == []


def test_des_vcs_057_other_keys_alone_do_nothing(keys):
    shift, clock, fired = keys
    for key in ("a", "Return", "Meta_L"):
        shift.press(key); shift.release(key)
    assert fired == []
