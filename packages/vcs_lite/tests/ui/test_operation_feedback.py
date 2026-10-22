"""Error banner (P3) and operation in progress (P4) in the window."""

from __future__ import annotations

from test_main_window import conflicted, root, world  # noqa: F401 - shared fixtures

from vcs_lite.core.status import Group
from vcs_lite.ui.main_window import MainWindow


def test_des_vcs_043_banner_shows_the_failed_operation_and_closes(root, world):  # noqa: F811
    conflicted(world, "gamma")
    model = world.start("gamma")
    window = MainWindow(root, model)
    world.select("gamma")
    assert not window.banner.winfo_ismapped() and window.banner.winfo_manager() == ""
    model.toggle(next(c for c in model.files(Group.CONFLICTS))); world.worker.settle()
    assert window.banner.winfo_manager() == "pack"
    assert window.banner_title.cget("text") == "Oznaczenie jako rozwiązany nie powiodło się"
    assert "linia 1" in window.banner_body.get("1.0", "end-1c")
    window.close_banner()
    assert window.banner.winfo_manager() == "" and model.error is None


def test_des_vcs_043_busy_bar_runs_only_during_an_operation(root, world):  # noqa: F811
    r = world.repo("alpha")
    r.write("a.py", "a\n"); r.git("add", "a.py")
    model = world.start("alpha")
    window = MainWindow(root, model)
    world.select("alpha")
    model.message = "fix"
    model.commit()
    assert window.busy_text.cget("text") == "Zapisywanie commita…"
    assert window.busy_bar.winfo_manager() == "place" and window.busy_animating
    world.worker.settle()
    assert window.busy_text.cget("text") == ""
    assert window.busy_bar.winfo_manager() == "" and not window.busy_animating  # no timer while idle (REQ-VCS-101)


def test_des_vcs_043_reduced_motion_shows_a_still_bar_and_stops_cleanly(root, world):  # noqa: F811
    r = world.repo("alpha")
    r.write("a.py", "a\n"); r.git("add", "a.py")
    model = world.start("alpha")
    window = MainWindow(root, model, reduce_motion=True)
    world.select("alpha")
    model.message = "fix"
    model.commit()
    assert window.busy_bar.winfo_manager() == "place" and window._busy_after is None  # no animation timer
    world.worker.settle()
    assert window.busy_bar.winfo_manager() == "" and not window.busy_animating
