"""The history panel E-06 drawn from HistorySession (DES-VCS-070, rules H-33, H-34, H-45–H-49, AT-VCS-056, 057, 060)."""

from __future__ import annotations

import tkinter as tk

import pytest
from conftest import Repo
from world import World

from vcs_lite.app.history import HistorySession
from vcs_lite.core.graph import GraphLayout
from vcs_lite.core.log import Commit, LogPage, Ref, RefKind, Scope
from vcs_lite.ui import theme
from vcs_lite.ui.history_panel import LANES, dot_style, graph_width, title_pieces
from vcs_lite.ui.main_window import MainWindow


@pytest.fixture
def root(tk_root):
    frame = tk.Frame(tk_root)
    yield frame
    frame.destroy()


@pytest.fixture
def world(tmp_path) -> World:
    return World(tmp_path)


def fake_commit(name: str, parents: str = "", subject: str | None = None, refs=()) -> Commit:
    return Commit(name, tuple(parents.split()), "Ola", "o@x", 0, tuple(refs), name if subject is None else subject)


class ManyCommits:
    """A reader of a long linear history, without git."""

    def __init__(self, n: int):
        self.commits = tuple(fake_commit(f"c{i:04}", f"c{i + 1:04}" if i + 1 < n else "") for i in range(n))

    def page(self, repo, query, skip):
        return LogPage(self.commits[skip:skip + 500], skip + 500 < len(self.commits))

    def count(self, repo, query):
        return len(self.commits)

    def unpushed(self, repo):
        return set()

    def remote_url(self, repo):
        return None

    def details(self, repo, commit):
        from vcs_lite.core.log import CommitDetails
        return CommitDetails(commit, "", ())


def window_with_history(root, world: World, session: HistorySession | None = None, **extra) -> MainWindow:
    session = session or world.history_session()
    world.worker.settle()
    window = MainWindow(root, world.model, history=session, **extra)
    window.pack()
    root.update_idletasks()
    return window


# ---------- graph column (H-33, H-34) ----------

def test_at_vcs_056_ten_branches_are_clipped_to_eight_columns():
    commits = [fake_commit(f"T{i}", "R") for i in range(10)] + [fake_commit("R")]
    rows = GraphLayout().extend(commits)
    assert LANES == 8 and graph_width(rows) == 8 * 16 + 20
    assert dot_style(rows[7], commits[7]) == (7, "full")
    assert dot_style(rows[8], commits[8]) == (7, "clipped") and dot_style(rows[9], commits[9]) == (7, "clipped")


def test_des_vcs_070_merges_have_hollow_dots_and_a_filtered_list_has_no_lanes():
    merge = fake_commit("M", "A B")
    [row] = GraphLayout().extend([merge])
    assert dot_style(row, merge) == (0, "merge")
    assert dot_style(None, merge) == (0, "merge") and graph_width([]) == 16 + 20


# ---------- a row's text (H-07, H-09, H-10) ----------

def test_at_vcs_057_unpushed_mark_labels_and_subject():
    commit = fake_commit("a", subject="Dodaj historię", refs=(Ref(RefKind.LOCAL, "main", current=True),
                                                             Ref(RefKind.REMOTE, "origin/main"), Ref(RefKind.TAG, "v1")))
    assert title_pieces(commit, unpushed=True) == [("↑", "unpushed"), ("main", "ref_current"), ("origin/main", "ref_remote"),
                                                   ("v1", "ref_tag"), ("Dodaj historię", "subject_out")]
    assert title_pieces(commit, unpushed=False)[-1] == ("Dodaj historię", "subject")
    assert title_pieces(fake_commit("b", subject=""), unpushed=False) == [("(bez opisu)", "subject_empty")]
    detached = fake_commit("c", refs=(Ref(RefKind.HEAD, "HEAD"), Ref(RefKind.LOCAL, "feature")))
    assert title_pieces(detached, unpushed=False)[:2] == [("HEAD", "ref_head"), ("feature", "ref_local")]


# ---------- the panel in the window ----------

def test_des_vcs_070_only_the_visible_rows_are_drawn_and_the_end_reads_more(root, world):
    world.repo("alpha")
    world.start("alpha"); world.select("alpha")
    reader = ManyCommits(700)
    session = HistorySession(reader, world.worker, later=world.timers.later, model=world.model)
    window = window_with_history(root, world, session)
    commits = window.history.commit_list
    commits.canvas.configure(height=240)
    commits.render()
    assert len(session.commits) == 500
    assert 0 < len(commits.drawn) <= 240 // 24 + 2                   # about ten rows, not five hundred
    commits.scroll_to_end()
    world.worker.settle()
    assert len(session.commits) == 700                               # the next page came while near the end
    assert window.history.count_text == "700 commitów"


def test_des_vcs_070_click_keys_filter_and_scope_drive_the_session(root, world):
    alpha = world.repo("alpha")
    alpha.write("a.txt", "a\n"); alpha.commit("drugi")
    world.start("alpha"); world.select("alpha")
    window = window_with_history(root, world)
    panel, session = window.history, window.history.session
    assert [c.subject for c in session.commits] == ["drugi", "init"] and session.selected == 0
    panel.commit_list.click(24 + 5); world.worker.settle()
    assert session.selected == 1 and panel.details.title_text == "init"
    panel.commit_list.press_up(); world.worker.settle()
    assert session.selected == 0
    panel.filter.set("init")
    assert world.timers.pending == 1                                 # waits for a pause in typing (H-44)
    world.timers.advance(250); world.worker.settle()
    assert [c.subject for c in session.commits] == ["init"]
    panel.scope.click(panel.scope.winfo_reqwidth() - 5)              # „Bieżąca”
    world.worker.settle()
    assert session.query.scope is Scope.CURRENT


def test_des_vcs_070_the_placeholder_replaces_the_list(root, world):
    fresh = Repo(world.root / "fresh"); fresh.path.mkdir(); fresh.git("init", "-q", "-b", "main")
    world.start("fresh"); world.select("fresh")
    window = window_with_history(root, world)
    assert window.history.commit_list.placeholder_text == "Repo nie ma jeszcze commitów."


def test_at_vcs_060_details_files_open_the_diff_and_the_menu_copies_the_address(root, world):
    alpha = world.repo("alpha")
    alpha.git("remote", "add", "origin", "git@github.com:m1981/app.git")
    alpha.write("a.py", "stare\n"); alpha.commit("pierwszy")
    alpha.write("a.py", "nowe\n"); alpha.commit("drugi")
    world.start("alpha"); world.select("alpha")
    copied, opened = [], []
    window = window_with_history(root, world, clipboard=copied.append, open_url=opened.append)
    panel = window.history
    details = panel.details
    assert details.title_text == "drugi" and [f.path for f, _ in details.file_rows()] == ["a.py"]
    _, top = details.file_rows()[0]
    details.double_click(top + 5); world.worker.settle()
    call = world.tool.calls[-1]
    assert (call["left_bytes"], call["right_bytes"]) == (b"stare\n", b"nowe\n")
    head = panel.session.selected_commit
    labels = [(label, enabled) for label, enabled, _ in panel.commit_list.prepare_menu(0)]
    assert labels == [("Kopiuj hash", True), ("Kopiuj adres commita", True), ("Otwórz w przeglądarce", True)]
    for _, _, command in panel.commit_list.prepare_menu(0):
        command()
    url = f"https://github.com/m1981/app/commit/{head.hash}"
    assert copied == [head.hash, url] and opened == [url]


def test_des_vcs_070_without_a_known_host_the_address_items_are_inactive(root, world):
    world.repo("alpha")
    world.start("alpha"); world.select("alpha")
    window = window_with_history(root, world)
    labels = [(label, enabled) for label, enabled, _ in window.history.commit_list.prepare_menu(0)]
    assert labels == [("Kopiuj hash", True), ("Kopiuj adres commita", False), ("Otwórz w przeglądarce", False)]


def test_des_vcs_070_new_colours_are_in_the_theme():
    assert [theme.COLORS[f"lane_{i}"] for i in range(3)] == ["#0a66d8", "#1f9e5a", "#c56a12"]


# ---------- smooth edges (DEC-VCS-123) ----------

def test_des_vcs_070_a_change_of_column_is_one_curve_over_a_whole_row():
    from vcs_lite.core.graph import Edge
    from vcs_lite.ui.history_panel import edge_paths
    x0, x1 = 12, 28
    fork = edge_paths(Edge(0, 0, 1, 3, 1, 1), bottom=1000)
    assert fork == [([x0, 12, x0, 24, x1, 24, x1, 36], True), ([x1, 36, x1, 84], False)]
    join = edge_paths(Edge(2, 1, 1, 4, 0, 1), bottom=1000)
    assert join == [([x1, 60, x1, 84], False), ([x1, 84, x1, 96, x0, 96, x0, 108], True)]
    assert edge_paths(Edge(0, 0, 0, 3, 0, 0), bottom=1000) == [([x0, 12, x0, 84], False)]
    assert edge_paths(Edge(1, 1, 0, 2, 0, 0), bottom=1000) == [([x1, 36, x1, 48, x0, 48, x0, 60], True)]
    assert edge_paths(Edge(5, 0, 0, None, None, 0), bottom=200) == [([x0, 132, x0, 200], False)]
    assert edge_paths(Edge(0, 0, 8, 3, 8, 0), bottom=1000) == []      # a clipped lane is not drawn (H-33)


# ---------- „Pokaż historię” (H-50–H-56) ----------

def test_at_vcs_061_show_history_from_the_file_list_and_open_a_commit_of_the_file(root, world):
    alpha = world.repo("alpha")
    alpha.write("a.txt", "1\n"); alpha.commit("pierwszy")
    alpha.git("mv", "a.txt", "b.txt"); alpha.commit("nazwa")
    alpha.write("b.txt", "2\n")                                     # b.txt in Changes
    world.start("alpha"); world.select("alpha")
    window = window_with_history(root, world)
    from vcs_lite.core.status import Group
    fl = window.file_list
    row = next(r for r in fl.rows() if r.path == "b.txt" and r.group is Group.CHANGES)
    menu = {label: (enabled, command) for label, enabled, command in fl.prepare_menu(row.top + 5)}
    assert menu["Pokaż historię"][0]
    menu["Pokaż historię"][1](); world.worker.settle()
    panel, session = window.history, window.history.session
    assert [c.subject for c in session.commits] == ["nazwa", "pierwszy"] and panel.path_text == "Plik: b.txt ✕"
    panel.commit_list.double_click(24 + 5); world.worker.settle()         # the oldest commit
    call = world.tool.calls[-1]
    assert call["right_title"].startswith("a.txt (") and call["left_title"] == "a.txt (pusty)"
    panel.clear_path(); world.worker.settle()
    assert panel.path_text == "" and len(session.rows) == 3


def test_at_vcs_063_unversioned_has_no_history_and_files_of_a_commit_have_it(root, world):
    alpha = world.repo("alpha")
    alpha.write("a.py", "a\n"); alpha.commit("z a.py")
    alpha.write("nowy.txt", "n\n")
    world.start("alpha"); world.select("alpha")
    window = window_with_history(root, world)
    from vcs_lite.core.status import Group
    fl = window.file_list
    row = next(r for r in fl.rows() if r.group is Group.UNVERSIONED)
    assert not {label: enabled for label, enabled, _ in fl.prepare_menu(row.top + 5)}["Pokaż historię"]
    details = window.history.details
    _, top = details.file_rows()[0]
    menu = {label: (enabled, command) for label, enabled, command in details.prepare_file_menu(top + 5)}
    assert set(menu) == {"Porównaj", "Pokaż historię"}
    menu["Pokaż historię"][1](); world.worker.settle()
    assert window.history.session.query.path == "a.py" and window.history.path_text == "Plik: a.py ✕"


@pytest.mark.parametrize('missing', [False, True])
def test_req_vcs_040_history_passes_whole_commit_totals_to_E(root, world, monkeypatch, missing):
    from vcs_lite.core.gitlog import GitLog
    alpha = world.repo('alpha')
    alpha.write('a.txt', 'old\n'); alpha.commit('before')
    alpha.write('a.txt', 'new\nextra\n')
    alpha.write('b.txt', 'other\n'); alpha.commit('after')
    if missing:
        monkeypatch.setattr(GitLog, 'commit_totals', lambda *args: {})
    world.start('alpha'); world.select('alpha')
    window = window_with_history(root, world)
    session = window.history.session
    # A path-filtered history must still show whole-commit totals, including b.txt.
    session.show_path('a.txt', folder=False); world.worker.settle()
    listing = window.history.commit_list
    listing.render()
    c = listing.canvas
    first = [i for i in c.find_withtag('commit_totals') if c.coords(i)[1] == 12]
    assert [c.itemcget(i, 'text') for i in first] == (['—'] if missing else ['−1', '+3'])
    assert [c.itemcget(i, 'fill') for i in first] == (
        [theme.COLORS['dim']] if missing else [theme.COLORS['del'], theme.COLORS['add']])
