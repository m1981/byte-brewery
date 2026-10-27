"""Cursor inheritance when Tk's sash cursor has not yet been restored (DES-VCS-069)."""
import tkinter as tk

import pytest
from test_main_window import world  # noqa: F401
from vcs_lite.ui.main_window import MainWindow


def inherited_cursor(widget):
    """Tk's empty cursor inherits from its nearest ancestor with an explicit cursor."""
    while widget is not None:
        cursor = str(widget.cget('cursor'))
        if cursor:
            return cursor
        widget = widget.master
    return ''


@pytest.fixture
def shown(tk_root, world):
    world.repo('alpha')
    model = world.start('alpha')
    world.select('alpha')
    session = world.history_session()
    world.worker.settle()
    top = tk.Toplevel(tk_root)
    top.geometry('1000x760')
    window = MainWindow(top, model, history=session)
    window.pack(fill=tk.BOTH, expand=True)
    top.update()
    try:
        yield window
    finally:
        top.destroy()


@pytest.mark.parametrize('drag', [False, True])
def test_at_vcs_049_req_vcs_036_sash_cursor_does_not_leak_to_content(shown, drag):
    window, split = shown, shown.split
    x, y = split.sash_coord(0)
    x, y = x + 10, y + 2
    assert split.identify(x, y)
    # Run actual Tk class handlers. Moving into a pane need not send Leave to
    # Panedwindow; Tk restores its cursor using a 150 ms timer (panedwindow.tcl).
    split.tk.call('::tk::panedwindow::Motion', str(split), x, y)
    assert str(split.cget('cursor')) == 'sb_v_double_arrow'
    if drag:
        split.tk.call('::tk::panedwindow::MarkSash', str(split), x, y, 1)
        split.tk.call('::tk::panedwindow::DragSash', str(split), x, y - 20, 1)
        split.tk.call('::tk::panedwindow::ReleaseSash', str(split), 1)
    for widget in (window.sidebar.canvas, window.file_list.canvas,
                   window.history.commit_list.canvas, window.history.details.canvas,
                   window.message_scroller.scrollbar):
        assert inherited_cursor(widget) == 'arrow', str(widget)
    assert inherited_cursor(window.message_box) == 'xterm'
    assert all(inherited_cursor(handle) == 'sb_v_double_arrow' for handle in window.history.handles())


def test_des_vcs_069_header_controls_do_not_inherit_the_drag_cursor(shown):
    history = shown.history
    assert inherited_cursor(history.scope) == 'arrow'
    assert inherited_cursor(history._count) == 'arrow'
    assert inherited_cursor(history._path) == 'hand2'
    field = next(w for w in history._header.winfo_children() if type(w) is tk.Frame)
    assert inherited_cursor(field) == 'arrow'
    entry = next(w for w in field.winfo_children() if isinstance(w, tk.Entry))
    assert inherited_cursor(entry) == 'xterm'
    shown.history_drag_start(500, 240)
    shown.history_drag_to(460, total=900)
    shown.history_drag_end(total=900)
    assert inherited_cursor(shown.sidebar.canvas) == 'arrow'
    assert inherited_cursor(history._header) == 'sb_v_double_arrow'
