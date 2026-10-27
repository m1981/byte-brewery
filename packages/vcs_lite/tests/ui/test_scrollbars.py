"""Native scrollbar commands, stable geometry and viewport rendering (P20)."""
import tkinter as tk
from tkinter import ttk

import pytest
from test_file_list_viewport import large_list, text_items  # noqa: F401
from test_main_window import world  # noqa: F401



def command(bar, *args):
    bar.tk.call(bar.cget('command'), *args)


@pytest.mark.parametrize('kind', ['canvas', 'text'])
def test_des_vcs_078_two_way_native_scroll_and_stable_gutter(tk_root, kind):
    from vcs_lite.ui.scrolling import ScrollPane
    top = tk.Toplevel(tk_root)
    top.geometry('400x200')
    pane = ScrollPane(top, bg='white')
    pane.pack(fill=tk.BOTH, expand=True)
    seen = []
    widget = (tk.Canvas(pane, highlightthickness=0, scrollregion=(0, 0, 300, 2000)) if kind == 'canvas'
              else tk.Text(pane, height=3, wrap=tk.WORD))
    if kind == 'text':
        widget.insert('1.0', '\n'.join(str(i) for i in range(200)))
    pane.attach(widget, on_view=lambda *fractions: seen.append(widget.yview()))
    try:
        top.update()
        bar = pane.scrollbar
        assert isinstance(bar, ttk.Scrollbar)
        width = widget.winfo_width()
        assert bar.winfo_y() == 6
        assert pane.winfo_height() - bar.winfo_y() - bar.winfo_height() == 6
        for args in [('moveto', .5), ('scroll', 1, 'pages'), ('scroll', -1, 'units')]:
            command(bar, *args)
            top.update()
            assert bar.get() == pytest.approx(widget.yview())
            assert widget.yview()[0] > 0
        widget.yview_moveto(0)
        top.update()
        assert bar.get()[0] == 0 and len(seen) >= 4
        if kind == 'canvas':
            widget.configure(scrollregion=(0, 0, 300, 200))
        else:
            widget.delete('1.0', tk.END)
        top.update()
        command(bar, 'moveto', 1)
        top.update()
        assert bar.get() == (0, 1)
        assert widget.winfo_width() == width
    finally:
        top.destroy()


def test_at_vcs_069_req_vcs_045_scrollbar_repaints_virtual_rows_and_keeps_header(large_list):
    top, fl, model, view = large_list
    bar = fl.scroller.scrollbar
    header_y = fl.heading.winfo_rooty()
    fl.select_key(fl.rows()[0].key)
    for fraction in (.5, 1, 0):
        command(bar, 'moveto', fraction)
        top.update()
        assert len(fl.canvas.find_all()) < 250
        visible = [r for r in fl.rows() if fl.canvas.canvasy(0) <= r.top < fl.canvas.canvasy(fl.canvas.winfo_height())]
        assert visible and all(r.path in text_items(fl.canvas) for r in visible)
        assert fl.heading.winfo_rooty() == header_y
        assert fl.selected_key == fl.rows()[0].key
        assert bar.get() == pytest.approx(fl.canvas.yview())


def test_req_vcs_045_all_panels_share_native_scroll_contract(tk_root, world):
    from test_history_panel import ManyCommits
    from vcs_lite.app.history import HistorySession
    from vcs_lite.app.search import DEBOUNCE_MS
    from vcs_lite.ui.main_window import MainWindow

    names = [f'repo{i:02}' for i in range(20)]
    repos = [world.repo(name) for name in names]
    repo = repos[0]
    repo.write('matches.txt', 'needle\n' * 100)
    repo.commit('search fixture')
    repo.write('new.txt', 'changed\n')
    model = world.start(*names)
    world.select(names[0])
    history = HistorySession(ManyCommits(700), world.worker, later=world.timers.later, model=model)
    search = world.search_session()
    world.worker.settle()
    top = tk.Toplevel(tk_root)
    top.geometry('1000x760')
    window = MainWindow(top, model, history=history, search=search)
    window.pack(fill=tk.BOTH, expand=True)
    try:
        top.update()
        assert window.sidebar.heading.winfo_height() == window.file_list.heading.winfo_height() == 28
        assert window.sidebar.heading.winfo_rooty() == window.file_list.heading.winfo_rooty()
        panes = [window.sidebar, window.file_list, window.history.commit_list, window.history.details]
        for panel in panes:
            assert isinstance(panel.scroller.scrollbar, ttk.Scrollbar)
            assert panel.scroller.scrollbar.get() == pytest.approx(panel.canvas.yview())
        assert isinstance(window.message_scroller.scrollbar, ttk.Scrollbar)
        assert isinstance(window.banner_scroller.scrollbar, ttk.Scrollbar)
        side = window.sidebar
        command(side.scroller.scrollbar, 'moveto', 1)
        top.update()
        assert side.canvas.canvasy(0) > 0
        last = side.rows()[-1]
        assert last.top < side.canvas.canvasy(side.canvas.winfo_height())
        commits = window.history.commit_list
        command(commits.scroller.scrollbar, 'moveto', .5)
        top.update()
        assert min(commits.drawn) > 0 and len(commits.drawn) < 30
        command(commits.scroller.scrollbar, 'moveto', 1)
        top.update()
        world.worker.settle()
        top.update()
        assert len(history.commits) == 700  # scrollbar reaches the same lazy-load path as wheel
        window._message_focus_in()
        window.message_box.insert('1.0', 'long message\n' * 100)
        top.update()
        command(window.message_scroller.scrollbar, 'moveto', 1)
        top.update()
        assert window.message_box.yview()[0] > .5
        dialog = window.open_settings()
        top.update()
        command(dialog.scroller.scrollbar, 'moveto', 1)
        top.update()
        assert dialog.list_canvas.yview()[0] > 0
        assert dialog.list_canvas.yview() == pytest.approx(dialog.scroller.scrollbar.get())
        dialog.cancel()
        dialog = window.open_search()
        dialog.phrase.set('needle')
        world.timers.advance(DEBOUNCE_MS)
        world.worker.settle()
        top.update()
        result = dialog.results
        command(result.scroller.scrollbar, 'moveto', 1)
        top.update()
        assert result.canvas.yview()[0] > 0
        assert result.canvas.yview() == pytest.approx(result.scroller.scrollbar.get())
        dialog.close()
    finally:
        top.destroy()
