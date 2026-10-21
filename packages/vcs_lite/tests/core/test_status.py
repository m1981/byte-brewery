"""Status parsing against real git output, one test per row of T-VCS-01."""

from __future__ import annotations

from vcs_lite.core.status import STATUS_ARGS, Group, Side, parse_status


def status(repo):
    return parse_status(repo.git(*STATUS_ARGS))


def only(st, group):
    rows = [c for c in st.changes if c.group is group]
    assert len(rows) == 1, rows
    return rows[0]


def test_t_vcs_01_modified_in_index_is_staged_head_vs_index(repo):
    repo.write("app.py", "a\n"); repo.commit()
    repo.write("app.py", "b\n"); repo.git("add", "app.py")
    c = only(status(repo), Group.STAGED)
    assert (c.path, c.code, c.left, c.right) == ("app.py", "M", Side.HEAD, Side.INDEX)


def test_t_vcs_01_added_is_staged_empty_vs_index(repo):
    repo.write("a.txt", "a\n"); repo.commit()
    repo.write("new.py", "x\n"); repo.git("add", "new.py")
    c = only(status(repo), Group.STAGED)
    assert (c.path, c.code, c.left, c.right) == ("new.py", "A", Side.EMPTY, Side.INDEX)


def test_t_vcs_01_deleted_in_index_is_staged_head_vs_empty(repo):
    repo.write("old.py", "x\n"); repo.commit()
    repo.git("rm", "-q", "old.py")
    c = only(status(repo), Group.STAGED)
    assert (c.path, c.code, c.left, c.right) == ("old.py", "D", Side.HEAD, Side.EMPTY)


def test_t_vcs_01_rename_is_staged_with_original_path(repo):
    repo.write("old.py", "line\n" * 20); repo.commit()
    repo.git("mv", "old.py", "new.py")
    c = only(status(repo), Group.STAGED)
    assert (c.path, c.orig_path, c.code, c.left, c.right) == ("new.py", "old.py", "R", Side.HEAD, Side.INDEX)


def test_t_vcs_01_worktree_modified_is_changes_index_vs_worktree(repo):
    repo.write("app.py", "a\n"); repo.commit()
    repo.write("app.py", "b\n")
    st = status(repo)
    c = only(st, Group.CHANGES)
    assert (c.path, c.code, c.left, c.right) == ("app.py", "M", Side.INDEX, Side.WORKTREE)
    assert st.group(Group.STAGED) == []


def test_t_vcs_01_worktree_deleted_is_changes_index_vs_empty(repo):
    repo.write("app.py", "a\n"); repo.commit()
    (repo.path / "app.py").unlink()
    c = only(status(repo), Group.CHANGES)
    assert (c.path, c.code, c.left, c.right) == ("app.py", "D", Side.INDEX, Side.EMPTY)


def test_t_vcs_01_mm_is_in_staged_and_changes(repo):
    repo.write("app.py", "a\n"); repo.commit()
    repo.write("app.py", "b\n"); repo.git("add", "app.py")
    repo.write("app.py", "c\n")
    st = status(repo)
    staged, changes = only(st, Group.STAGED), only(st, Group.CHANGES)
    assert (staged.left, staged.right) == (Side.HEAD, Side.INDEX)
    assert (changes.left, changes.right) == (Side.INDEX, Side.WORKTREE)


def test_t_vcs_01_untracked_files_are_listed_one_by_one(repo):
    repo.write("a.txt", "a\n"); repo.commit()
    repo.write("new/a.txt", "1\n"); repo.write("new/b.txt", "2\n")
    rows = status(repo).group(Group.UNVERSIONED)
    assert [(c.path, c.left, c.right) for c in rows] == [("new/a.txt", Side.EMPTY, Side.WORKTREE), ("new/b.txt", Side.EMPTY, Side.WORKTREE)]


def test_req_vcs_004_ignored_files_are_not_reported(repo):
    repo.write(".gitignore", "*.log\n"); repo.commit()
    repo.write("debug.log", "x\n")
    assert status(repo).changes == ()


def test_t_vcs_01_conflict_is_listed_without_diff_sides(repo):
    repo.write("f.txt", "base\n"); repo.commit()
    repo.git("checkout", "-q", "-b", "other"); repo.write("f.txt", "other\n"); repo.commit()
    repo.git("checkout", "-q", "main"); repo.write("f.txt", "main\n"); repo.commit()
    repo.git("merge", "-q", "other", check=False)
    st = status(repo)
    c = only(st, Group.CONFLICTS)
    assert (c.path, c.code, c.left, c.right) == ("f.txt", "UU", None, None)
    assert st.has_conflicts


def test_t_vcs_01_repo_without_commits_stages_against_empty(repo):
    repo.write("first.py", "x\n"); repo.git("add", "first.py")
    st = status(repo)
    c = only(st, Group.STAGED)
    assert (c.left, c.right) == (Side.EMPTY, Side.INDEX)
    assert st.oid is None and st.branch == "main"


def test_t_vcs_01_paths_with_spaces_and_polish_letters(repo):
    repo.write("a.txt", "a\n"); repo.commit()
    repo.write("dir z spacją/żółć.txt", "x\n")
    assert [c.path for c in status(repo).changes] == ["dir z spacją/żółć.txt"]


def test_req_vcs_002_branch_upstream_and_ahead_behind_headers():
    raw = b"# branch.oid 1234abcd\0# branch.head main\0# branch.upstream origin/main\0# branch.ab +2 -1\0"
    st = parse_status(raw)
    assert (st.oid, st.branch, st.upstream, st.ahead, st.behind) == ("1234abcd", "main", "origin/main", 2, 1)
    assert not st.detached


def test_uc_vcs_02_detached_head_has_no_branch(repo):
    repo.write("a.txt", "a\n"); repo.commit()
    repo.git("checkout", "-q", "--detach")
    st = status(repo)
    assert st.detached and st.branch is None and st.upstream is None
