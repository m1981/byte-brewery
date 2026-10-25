"""`git log` as the history reader on throwaway repositories (DES-VCS-065, rules H-01–H-11, H-44, H-45)."""

from __future__ import annotations

import pytest
from conftest import GIT_ENV, Repo

from vcs_lite.core import gitlog
from vcs_lite.core.gitcli import GitCli
from vcs_lite.core.gitlog import GitLog
from vcs_lite.core.log import CommitFile, LogQuery, Ref, RefKind, Scope
from vcs_lite.core.repo import GitError


@pytest.fixture
def log() -> GitLog:
    return GitLog(GitCli(env=GIT_ENV))


def commit(repo: Repo, message: str, *, author: str | None = None, date: str | None = None, file: str | None = None) -> str:
    repo.write(file or f"{len(repo.git('rev-list', '--all').split())}.txt", message + "\n")
    repo.git("add", "-A")
    extra = ([f"--author={author}"] if author else []) + ([f"--date={date}"] if date else [])
    repo.git("commit", "-q", "-m", message, *extra)
    return head(repo)


def head(repo: Repo, rev: str = "HEAD") -> str:
    return repo.git("rev-parse", rev).decode().strip()


def subjects(page) -> list[str]:
    return [c.subject for c in page.commits]


# ---------- reading (H-01, H-02, H-03, H-05) ----------

def test_des_vcs_065_commits_newest_first_with_parents_authors_and_labels(repo, log):
    a = commit(repo, "pierwszy", author="Żaneta <z@example.invalid>")
    b = commit(repo, "drugi")
    repo.git("tag", "-a", "v1", "-m", "v1", a)
    page = log.page(repo.path, LogQuery(), skip=0)
    assert subjects(page) == ["drugi", "pierwszy"] and not page.more
    second, first = page.commits
    assert second.hash == b and second.parents == (a,) and first.parents == ()
    assert first.author == "Żaneta" and first.email == "z@example.invalid"
    assert second.refs == (Ref(RefKind.LOCAL, "main", current=True),) and first.refs == (Ref(RefKind.TAG, "v1"),)


def test_at_vcs_057_stash_and_notes_are_not_history_and_labels_tell_their_kind(repo, log, tmp_path):
    commit(repo, "a")
    bare = tmp_path / "origin.git"
    Repo(tmp_path).git("init", "-q", "--bare", "-b", "main", str(bare))
    repo.git("remote", "add", "origin", str(bare))
    repo.git("push", "-q", "-u", "origin", "main")
    repo.git("remote", "set-head", "origin", "main")
    commit(repo, "b"); commit(repo, "c")
    repo.git("branch", "origin/fake")
    repo.write("0.txt", "zmiana w schowku\n"); repo.git("stash", "-q")
    repo.git("notes", "add", "-m", "notatka", "HEAD")
    page = log.page(repo.path, LogQuery(), skip=0)
    assert subjects(page) == ["c", "b", "a"]                                     # no WIP, index or notes commits
    assert page.commits[0].refs == (Ref(RefKind.LOCAL, "main", current=True), Ref(RefKind.LOCAL, "origin/fake"))
    assert page.commits[2].refs == (Ref(RefKind.REMOTE, "origin/main"),)        # without origin/HEAD
    assert log.unpushed(repo.path) == {head(repo), head(repo, "HEAD~1")}         # H-10
    assert log.count(repo.path, LogQuery()) == 3                                 # H-49


def test_des_vcs_065_no_upstream_or_a_detached_head_has_nothing_unpushed(repo, log):
    commit(repo, "a"); commit(repo, "b")
    assert log.unpushed(repo.path) == set()
    repo.git("checkout", "-q", "--detach", "HEAD~1")
    assert log.unpushed(repo.path) == set()
    assert log.page(repo.path, LogQuery(), skip=0).commits[1].refs == (Ref(RefKind.HEAD, "HEAD"),)


def test_des_vcs_065_the_current_branch_leaves_other_branches_out(repo, log):
    commit(repo, "a")
    repo.git("checkout", "-q", "-b", "feature"); commit(repo, "na feature")
    repo.git("checkout", "-q", "main"); commit(repo, "na main")
    assert set(subjects(log.page(repo.path, LogQuery(), skip=0))) == {"na main", "na feature", "a"}
    assert subjects(log.page(repo.path, LogQuery(scope=Scope.CURRENT), skip=0)) == ["na main", "a"]
    assert log.count(repo.path, LogQuery(scope=Scope.CURRENT)) == 2


def test_des_vcs_065_a_child_stays_above_a_parent_with_a_later_date(repo, log):
    commit(repo, "rodzic", date="2030-01-01T10:00:00")
    commit(repo, "dziecko", date="2001-01-01T10:00:00")       # rebase, cherry-pick or a wrong clock
    assert subjects(log.page(repo.path, LogQuery(), skip=0)) == ["dziecko", "rodzic"]


def test_des_vcs_065_pages_of_commits(repo, log, monkeypatch):
    for i in range(7):
        commit(repo, f"c{i}")
    monkeypatch.setattr(gitlog, "PAGE", 3)
    first = log.page(repo.path, LogQuery(), skip=0)
    assert subjects(first) == ["c6", "c5", "c4"] and first.more
    last = log.page(repo.path, LogQuery(), skip=6)
    assert subjects(last) == ["c0"] and not last.more


# ---------- unusual repositories (H-04, H-08, H-09, H-11) ----------

def test_at_vcs_058_a_fresh_repository_has_no_history_and_no_error(repo, log):
    assert log.page(repo.path, LogQuery(), skip=0).commits == ()
    assert log.page(repo.path, LogQuery(scope=Scope.CURRENT), skip=0).commits == ()
    assert log.count(repo.path, LogQuery()) == 0 and log.unpushed(repo.path) == set()


def test_at_vcs_054_a_shallow_clone_ends_on_a_grafted_root(repo, log, tmp_path):
    for i in range(3):
        commit(repo, f"c{i}")
    shallow = tmp_path / "shallow"
    Repo(tmp_path).git("clone", "-q", "--depth", "2", f"file://{repo.path}", str(shallow))
    oldest = log.page(shallow, LogQuery(), skip=0).commits[-1]
    assert oldest.subject == "c1" and oldest.parents == () and oldest.refs == ()


def test_des_vcs_065_unicode_and_an_empty_message(repo, log):
    repo.write("a.txt", "x\n"); repo.git("add", "-A")
    repo.git("commit", "-q", "--allow-empty-message", "-m", "", "--author=Łucja Żółć <l@x>")
    [c] = log.page(repo.path, LogQuery(), skip=0).commits
    assert c.subject == "" and c.author == "Łucja Żółć"


def test_des_vcs_065_git_errors_are_raised(tmp_path, log):
    (tmp_path / "nie-repo").mkdir()
    with pytest.raises(GitError):
        log.page(tmp_path / "nie-repo", LogQuery(), skip=0)


# ---------- the filter (H-44) ----------

def test_at_vcs_059_the_filter_finds_message_author_and_hash(repo, log):
    commit(repo, "fix parser", author="Ola <ola@x>")
    docs = commit(repo, "docs", author="Ola <ola@x>")
    commit(repo, "fix ui", author="Michal <m@x>")
    assert subjects(log.page(repo.path, LogQuery(text="ola"), skip=0)) == ["docs", "fix parser"]
    assert subjects(log.page(repo.path, LogQuery(text="FIX"), skip=0)) == ["fix ui", "fix parser"]
    assert subjects(log.page(repo.path, LogQuery(text=docs[:7]), skip=0)) == ["docs"]
    assert subjects(log.page(repo.path, LogQuery(text="[nie*regex"), skip=0)) == []   # a fixed string, no error


# ---------- details of a commit (H-45) ----------

def test_at_vcs_060_files_of_a_commit_a_merge_and_the_root(repo, log):
    repo.write("a.py", "a\n"); repo.write("stary.md", "s\n"); repo.write("nazwa.py", "n\n" * 20)
    root = commit(repo, "root", file="a.py")
    repo.git("checkout", "-q", "-b", "feature")
    repo.write("f.txt", "f\n"); feature = commit(repo, "feature", file="f.txt")
    repo.git("checkout", "-q", "main")
    repo.write("a.py", "b\n"); repo.git("rm", "-q", "stary.md"); repo.git("mv", "nazwa.py", "imie.py")
    repo.git("commit", "-q", "-am", "zmiany\n\nDłuższy opis\nw dwóch liniach.")
    changes = head(repo)
    repo.git("merge", "-q", "--no-ff", "-m", "merge feature", "feature")
    page = {c.hash: c for c in log.page(repo.path, LogQuery(), skip=0).commits}
    details = log.details(repo.path, page[changes])
    assert details.body == "Dłuższy opis\nw dwóch liniach."
    assert set(details.files) == {CommitFile("M", "a.py"), CommitFile("D", "stary.md"),
                                  CommitFile("R", "imie.py", "nazwa.py")}
    merge = log.details(repo.path, page[head(repo)])
    assert merge.files == (CommitFile("A", "f.txt"),) and merge.body == ""      # against the first parent
    first = log.details(repo.path, page[root])
    assert {f.status for f in first.files} == {"A"} and len(first.files) == 3
    assert log.details(repo.path, page[feature]).files == (CommitFile("A", "f.txt"),)


# ---------- the history of a path (H-50–H-56, DES-VCS-071) ----------

def renamed_file(repo: Repo) -> dict[str, str]:
    """a.txt in two commits, renamed to b.txt, changed once more; other files in between."""
    hashes = {}
    repo.write("a.txt", "1\n2\n3\n4\n5\n"); hashes["pierwszy"] = commit(repo, "pierwszy", file="a.txt")
    commit(repo, "inny plik", file="inny.txt")
    repo.write("a.txt", "1\n2\n3\n4\n5\n6\n"); hashes["drugi"] = commit(repo, "drugi", file="a.txt")
    repo.git("mv", "a.txt", "b.txt"); repo.git("commit", "-q", "-m", "zmiana nazwy"); hashes["nazwa"] = head(repo)
    repo.write("docs/plan.md", "plan\n"); commit(repo, "plan", file="docs/plan.md")
    repo.write("b.txt", "1\n2\n3\n4\n5\n6\n7\n"); hashes["czwarty"] = commit(repo, "czwarty", file="b.txt")
    return hashes


def test_at_vcs_061_a_file_history_follows_renames_and_knows_the_name_in_each_commit(repo, log):
    hashes = renamed_file(repo)
    page = log.page(repo.path, LogQuery(path="b.txt"), skip=0)
    assert subjects(page) == ["czwarty", "zmiana nazwy", "drugi", "pierwszy"] and not page.more
    assert page.paths[hashes["pierwszy"]] == CommitFile("A", "a.txt")
    assert page.paths[hashes["nazwa"]] == CommitFile("R", "b.txt", "a.txt")
    assert page.paths[hashes["czwarty"]] == CommitFile("M", "b.txt")


def test_at_vcs_062_a_folder_history_and_a_path_with_the_text_filter(repo, log):
    renamed_file(repo)
    repo.write("docs/inne.md", "x\n"); commit(repo, "inne docs", file="docs/inne.md")
    assert subjects(log.page(repo.path, LogQuery(path="docs", folder=True), skip=0)) == ["inne docs", "plan"]
    assert subjects(log.page(repo.path, LogQuery(text="drugi", path="b.txt"), skip=0)) == ["drugi"]
    assert subjects(log.page(repo.path, LogQuery(text="plan", path="b.txt"), skip=0)) == []


def test_des_vcs_071_special_characters_in_a_path_are_literal(repo, log):
    repo.write("d/[x].txt", "1\n"); commit(repo, "nawiasy", file="d/[x].txt")
    repo.write("d/x.txt", "1\n"); commit(repo, "bez nawiasów", file="d/x.txt")
    assert subjects(log.page(repo.path, LogQuery(path="d/[x].txt"), skip=0)) == ["nawiasy"]
