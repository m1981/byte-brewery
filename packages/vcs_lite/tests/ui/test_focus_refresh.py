"""Refresh when the user comes back to the window from another app (REQ-VCS-015, DES-VCS-018, DEC-VCS-059).

Tk does not deliver focus events to the hidden test window, so each test checks that the events are
bound and then runs their handlers; the real switch between apps is checked by hand (MANUAL-UI.md, step 12).
"""

from __future__ import annotations

import time

from test_main_window import root, world  # noqa: F401 - shared fixtures

from vcs_lite.ui.main_window import FOCUS_REFRESH_MS, MainWindow


def shown(root, world):  # noqa: F811
    model = world.start("alpha")
    window = MainWindow(root, model)
    world.select("alpha")
    refreshes = []
    model.refresh_all = lambda: refreshes.append(time.monotonic())
    return window, refreshes


def leave_app(window, root, monkeypatch):  # noqa: F811
    monkeypatch.setattr(window, "focus_get", lambda: None)  # no widget of ours has the focus
    window.on_focus_out()
    root.update()


def wait(root, seconds):  # noqa: F811
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        root.update()
        time.sleep(0.01)


def test_des_vcs_018_focus_events_of_the_window_are_bound(root, world):  # noqa: F811
    world.repo("alpha")
    window, _ = shown(root, world)
    top = window.winfo_toplevel()
    assert top.bind("<FocusIn>") and top.bind("<FocusOut>")


def test_req_vcs_015_coming_back_from_another_app_refreshes_once_after_300_ms(root, world, monkeypatch):  # noqa: F811
    world.repo("alpha")
    window, refreshes = shown(root, world)
    leave_app(window, root, monkeypatch)
    start = time.monotonic()
    window.on_focus_in(); window.on_focus_in(); window.on_focus_in()  # several events on the way back
    assert FOCUS_REFRESH_MS == 300 and refreshes == []
    wait(root, 0.5)
    assert len(refreshes) == 1 and refreshes[0] - start >= 0.29
    assert not window.focus_refresh_pending  # nothing left scheduled while idle (REQ-VCS-101)


def test_des_vcs_018_moving_the_focus_inside_the_window_does_not_refresh(root, world, monkeypatch):  # noqa: F811
    world.repo("alpha")
    window, refreshes = shown(root, world)
    monkeypatch.setattr(window, "focus_get", lambda: window.message_box)  # focus went to another widget of ours
    window.on_focus_out()
    root.update()
    window.on_focus_in()
    assert not window.focus_refresh_pending
    wait(root, 0.4)
    assert refreshes == []
