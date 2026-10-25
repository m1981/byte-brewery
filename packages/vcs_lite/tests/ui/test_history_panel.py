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
