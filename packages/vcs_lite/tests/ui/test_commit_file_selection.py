"""Persistent file selection and scroll through a real history refresh (REQ-VCS-044)."""
import tkinter as tk

import pytest
from test_main_window import world  # noqa: F401
from vcs_lite.ui.main_window import MainWindow
from vcs_lite.ui import theme


@pytest.fixture
def review(tk_root, world):
    repo = world.repo("alpha")
    world.repo("beta")
    for i in range(80):
        repo.write(f"file_{i:03}.py", "text\n")
    repo.commit("many files")
    model = world.start("alpha", "beta")
    world.select("alpha")
    session = world.history_session()
    world.worker.settle()
    top = tk.Toplevel(tk_root)
    top.geometry("1100x820")
    window = MainWindow(top, model, history=session)
    window.pack(fill=tk.BOTH, expand=True)
    top.update()
    details = window.history.details
    details.canvas.yview_moveto(1)
    top.update()
    yield top, details, session, model, world
    top.destroy()


def last_y(details):
    return int(details.file_rows()[-1][1] + 5 - details.canvas.canvasy(0))


def test_at_vcs_068_clicked_file_survives_hover_diff_and_redraw(review, monkeypatch):
    top, details, session, model, world = review
    y = last_y(details)
    details.click(20, y)
    assert details.selected_path == "file_079.py"
    details._set_hover(-1)
    details.render()
    chosen = details.canvas.find_withtag("selected_commit_file")
    assert len(chosen) == 1
    assert details.canvas.itemcget(chosen[0], "fill") == theme.COLORS["accent_soft"]
    details.double_click(y)
    world.worker.settle()
    top.update()
    assert details.selected_path == "file_079.py"
    assert world.tool.calls[-1]["right_title"].startswith("file_079.py")
    monkeypatch.setattr(tk.Menu, "tk_popup", lambda *args: None)
    details.open_file_menu(last_y(details) - 24, 0, 0)
    assert details.selected_path == "file_078.py"


def test_req_vcs_044_refresh_never_collapses_details_or_scroll(review):
    top, details, session, model, world = review
    before = details.canvas.canvasy(0)
    assert before > 0
    seen = []
    def observe():
        top.update_idletasks()
        seen.append((session.details, details.canvas.canvasy(0)))
    session.subscribe(observe)
    model.refresh("alpha")  # the same path used after focus returns
    world.worker.settle()
    top.update()
    assert seen and all(d is not None and abs(y - before) < 2 for d, y in seen)


def test_req_vcs_044_selection_survives_refresh_but_new_context_resets(review):
    top, details, session, model, world = review
    details.click(20, last_y(details))
    model.refresh("alpha")
    world.worker.settle()
    top.update()
    assert details.selected_path == "file_079.py" and details.canvas.canvasy(0) > 0
    session.select(1)
    world.worker.settle()
    top.update()
    assert details.selected_path is None and details.canvas.canvasy(0) == 0
    session.select(0)
    world.worker.settle()
    top.update()
    details.click(20, details.file_rows()[0][1] + 5)
    assert details.selected_path == "file_000.py"
    world.select("beta")
    top.update()
    assert details.selected_path is None and details.canvas.canvasy(0) == 0
