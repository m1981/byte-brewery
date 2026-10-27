"""Selection and contents survive drawing only the viewport (DES-VCS-075)."""
from dataclasses import replace
import tkinter as tk
import time

import pytest
from test_main_window import world  # noqa: F401

from vcs_lite.core.changes import ChangeDetails, LineStats
from vcs_lite.core.status import FileChange, Group, Side
from vcs_lite.ui.file_list import FileList


@pytest.fixture
def large_list(tk_root, world):
    world.repo("alpha")
    model = world.start("alpha")
    world.select("alpha")
    view = model.view("alpha")
    changes = tuple(FileChange(f"file_{i:04}.py", Group.CHANGES, "M", Side.INDEX, Side.WORKTREE)
                    for i in range(3000))
    view.status = replace(view.status, changes=changes)
    # One separator per file: the separator population must also be bounded.
    now = time.time_ns()
    view.details = {(c.group, c.path): ChangeDetails(now - i * 600 * 10**9, LineStats(i, 1))
                    for i, c in enumerate(changes)}
    top = tk.Toplevel(tk_root)
    top.geometry("760x420")
    top.attributes("-topmost", True)
    fl = FileList(top, on_toggle=lambda c: None, on_activate=lambda c: None,
                  on_toggle_folder=lambda g, p: None, on_empty_action=lambda a: None)
    fl.pack(fill=tk.BOTH, expand=True)
    top.update()
    fl.render(model)
    top.update()
    yield top, fl, model, view
    top.destroy()


def text_items(canvas):
    return {canvas.itemcget(i, "text") for i in canvas.find_all() if canvas.type(i) == "text"}


@pytest.mark.parametrize("mode", ["changes", "folders", "project"])
def test_des_vcs_075_viewport_preserves_all_rows_and_selection(large_list, mode):
    top, fl, model, view = large_list
    model.list_view = mode
    fl.render(model)
    top.update()
    assert len(fl.rows()) == (6000 if mode == "project" else 3000)  # status groups + project tree
    assert len(fl.canvas.find_all()) < 250
    for index in (0, len(fl.rows()) // 2, len(fl.rows()) - 1, 0):
        row = fl.rows()[index]
        fl.select_key(row.key)
        top.update()
        assert row.path in text_items(fl.canvas)
        assert fl.selected_key == row.key
        assert len(fl.canvas.find_all()) < 250
        if mode == "changes":
            assert f"+{index:,}".replace(',', '\u202f') in text_items(fl.canvas)
    fl.select_all()
    assert len(fl.selected_keys) == len(fl.rows())
    fl.select_key(fl.rows()[-2].key)
    fl.press_down()
    top.update()
    assert fl.selected_key == fl.rows()[-1].key
    assert fl.rows()[-1].path in text_items(fl.canvas)


def test_req_vcs_105_scroll_resize_and_shrink_repaint_the_current_view(large_list):
    top, fl, model, view = large_list
    c = fl.canvas
    c.yview_moveto(0.5)  # direct Tk scrolling must repaint too
    top.update()
    visible = [r for r in fl.rows() if c.canvasy(0) <= r.top < c.canvasy(c.winfo_height())]
    assert visible and all(r.path in text_items(c) for r in visible)
    assert "file_0000.py" not in text_items(c)
    fl.scroll(-120)
    top.geometry("500x280")
    top.update()
    assert len(c.find_all()) < 150
    c.yview_moveto(1)
    top.update()
    assert "file_2999.py" in text_items(c)
    view.status = replace(view.status, changes=view.status.changes[:2])
    fl.render(model)
    top.update()
    assert "file_0000.py" in text_items(c) and "file_2999.py" not in text_items(c)
    assert c.canvasy(0) == 0


def test_des_vcs_075_commit_with_3000_files_only_draws_visible_names(tk_root):
    from types import SimpleNamespace
    from vcs_lite.core.log import Commit, CommitDetails, CommitFile
    from vcs_lite.ui.history_panel import CommitView
    commit = Commit("abcdef", (), "Demo", "d@x", 0, (), "Large commit")
    files = tuple(CommitFile("A", f"file_{i:04}.py") for i in range(3000))
    session = SimpleNamespace(repo_path=None, selected_commit=commit,
                              details=CommitDetails(commit, "", files, {f.path: LineStats(i + 1, 2) for i, f in enumerate(files)}))
    opened, histories = [], []
    top = tk.Toplevel(tk_root)
    top.geometry("500x300")
    top.attributes("-topmost", True)
    details = CommitView(top, session, on_open_file=lambda c, f: opened.append(f), on_show_history=histories.append)
    details.pack(fill=tk.BOTH, expand=True)
    try:
        top.update()
        details.render()
        c = details.canvas
        assert "+1" in text_items(c) and "−2" in text_items(c)
        assert "+4\u202f501\u202f500 −6\u202f000" in text_items(c)
        assert len(details.file_rows()) == 3000
        assert len(c.find_all()) < 100
        assert "file_0000.py" in text_items(c) and "file_2999.py" not in text_items(c)
        c.yview_moveto(1)
        top.update()
        assert "+3\u202f000" in text_items(c)
        assert "file_2999.py" in text_items(c) and "file_0000.py" not in text_items(c)
        y = int(details.file_rows()[-1][1] + 5 - c.canvasy(0))
        details.double_click(y)
        details.prepare_file_menu(y)[1][2]()
        assert opened == [files[-1]] and histories == [files[-1].path]
        session.details = replace(session.details, files=files[:2])
        details.render()
        top.update()
        assert "file_0000.py" in text_items(c) and "file_2999.py" not in text_items(c)
        assert len(c.find_all()) < 100
    finally:
        top.destroy()
