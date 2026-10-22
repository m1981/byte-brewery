"""Operations on one repository: diff sides, stage, unstage, commit, push, pull."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from conftest import GIT_ENV, Repo

from vcs_lite.core.gitcli import GitCli
from vcs_lite.core.repo import GitRepo, UnresolvedConflict
from vcs_lite.core.status import Group


@pytest.fixture
def gr(repo) -> GitRepo:
    return GitRepo(repo.path, GitCli(env=GIT_ENV))


def entry(gr: GitRepo, group: Group, path: str):
    return next(c for c in gr.status().group(group) if c.path == path)


@pytest.fixture
def remote(tmp_path, repo):
    """A bare origin with main pushed and tracked."""
    bare = tmp_path / "origin.git"
    Repo(tmp_path).git("init", "-q", "--bare", "-b", "main", str(bare))
    repo.write("a.txt", "a\n"); repo.commit("init")
    repo.git("remote", "add", "origin", str(bare))
    repo.git("push", "-q", "-u", "origin", "main")
    return bare


def other_clone(tmp_path, bare) -> Repo:
    clone = Repo(tmp_path / "other")
    Repo(tmp_path).git("clone", "-q", str(bare), str(clone.path))
    return clone


# ---------- diff sides (DES-VCS-007) ----------

def test_des_vcs_007_staged_sides_are_head_and_index(repo, gr):
    repo.write("app.py", "old\n"); repo.commit()
    repo.write("app.py", "new\n"); repo.git("add", "app.py"); repo.write("app.py", "work\n")
    assert gr.sides(entry(gr, Group.STAGED, "app.py")) == (b"old\n", b"new\n")
    assert gr.sides(entry(gr, Group.CHANGES, "app.py")) == (b"new\n", repo.path / "app.py")


def test_des_vcs_007_rename_reads_head_from_original_path(repo, gr):
    repo.write("old.py", "body\n" * 10); repo.commit()
    repo.git("mv", "old.py", "new.py")
    assert gr.sides(entry(gr, Group.STAGED, "new.py")) == (b"body\n" * 10, b"body\n" * 10)


def test_des_vcs_007_empty_sides_for_new_and_deleted_files(repo, gr):
    repo.write("gone.py", "x\n"); repo.commit()
    repo.git("rm", "-q", "gone.py"); repo.write("fresh.py", "y\n")
    assert gr.sides(entry(gr, Group.STAGED, "gone.py")) == (b"x\n", b"")
    assert gr.sides(entry(gr, Group.UNVERSIONED, "fresh.py")) == (b"", repo.path / "fresh.py")


# ---------- stage and unstage (DES-VCS-011, DES-VCS-012) ----------

def test_at_vcs_008_stage_records_the_whole_file(repo, gr):
    repo.write("app.py", "".join(f"{i}\n" for i in range(50))); repo.commit()
    lines = [f"{i}\n" for i in range(50)]; lines[1] = "zmiana A\n"; lines[48] = "zmiana B\n"
    repo.write("app.py", "".join(lines))
    assert gr.stage(entry(gr, Group.CHANGES, "app.py")).ok
    st = gr.status()
    assert [c.path for c in st.group(Group.STAGED)] == ["app.py"] and st.group(Group.CHANGES) == []
    index = repo.git("cat-file", "blob", ":app.py").decode()
    assert "zmiana A" in index and "zmiana B" in index


def test_req_vcs_005_stage_records_a_deletion(repo, gr):
    repo.write("app.py", "x\n"); repo.commit()
    (repo.path / "app.py").unlink()
    gr.stage(entry(gr, Group.CHANGES, "app.py"))
    assert entry(gr, Group.STAGED, "app.py").code == "D"


def test_req_vcs_005_stage_adds_an_unversioned_file(repo, gr):
    repo.write("a.txt", "a\n"); repo.commit(); repo.write("new.py", "n\n")
    gr.stage(entry(gr, Group.UNVERSIONED, "new.py"))
    assert entry(gr, Group.STAGED, "new.py").code == "A"


def test_at_vcs_009_unstaging_a_rename_restores_both_paths(repo, gr):
    repo.write("old.py", "body\n" * 10); repo.commit()
    repo.git("mv", "old.py", "new.py")
    assert gr.unstage(entry(gr, Group.STAGED, "new.py")).ok
    st = gr.status()
    assert st.group(Group.STAGED) == []
    assert [c.path for c in st.group(Group.UNVERSIONED)] == ["new.py"]
    assert [(c.path, c.code) for c in st.group(Group.CHANGES)] == [("old.py", "D")]


def test_des_vcs_012_unstage_in_a_repo_without_commits(repo, gr):
    repo.write("first.py", "x\n"); repo.git("add", "first.py")
    assert gr.unstage(entry(gr, Group.STAGED, "first.py")).ok
    assert [c.path for c in gr.status().group(Group.UNVERSIONED)] == ["first.py"]


# ---------- commit (DES-VCS-013) ----------

def test_req_vcs_009_commit_contains_only_staged_changes(repo, gr):
    repo.write("a.py", "a\n"); repo.write("b.py", "b\n"); repo.commit()
    repo.write("a.py", "a2\n"); repo.write("b.py", "b2\n"); repo.git("add", "a.py")
    assert gr.commit("fix a\n\nszczegóły z \"cudzysłowem\"").ok
    assert repo.git("log", "-1", "--format=%B").decode().strip() == 'fix a\n\nszczegóły z "cudzysłowem"'
    assert repo.git("show", "--name-only", "--format=", "HEAD").decode().split() == ["a.py"]
    assert [c.path for c in gr.status().group(Group.CHANGES)] == ["b.py"]


def test_req_vcs_010_hook_rejection_returns_its_output_and_keeps_the_index(repo, gr):
    repo.write("a.py", "a\n"); repo.commit()
    hook = repo.path / ".git" / "hooks" / "pre-commit"
    hook.write_text("#!/bin/sh\necho 'lint failed' >&2\nexit 1\n"); hook.chmod(0o755)
    repo.write("a.py", "a2\n"); repo.git("add", "a.py")
    count = repo.git("rev-list", "--count", "HEAD")
    r = gr.commit("fix a")
    assert not r.ok and "lint failed" in r.message
    assert repo.git("rev-list", "--count", "HEAD") == count
    assert [c.path for c in gr.status().group(Group.STAGED)] == ["a.py"]


# ---------- push and pull (DES-VCS-014, DES-VCS-015) ----------

def test_at_vcs_013_commit_and_push_reaches_the_upstream(repo, gr, remote):
    repo.write("a.txt", "a2\n"); repo.git("add", "a.txt")
    assert gr.commit("fix a").ok and gr.push().ok
    assert repo.git("--git-dir", str(remote), "log", "-1", "--format=%s", "main").strip() == b"fix a"


def test_at_vcs_014_rejected_push_keeps_the_commit_and_does_not_pull(tmp_path, repo, gr, remote):
    other = other_clone(tmp_path, remote)
    other.write("b.txt", "b\n"); other.commit("remote fix"); other.git("push", "-q")
    repo.write("a.txt", "a2\n"); repo.git("add", "a.txt"); gr.commit("fix a")
    head = repo.git("rev-parse", "HEAD")
    r = gr.push()
    assert not r.ok and "rejected" in r.message
    assert repo.git("rev-parse", "HEAD") == head
    assert repo.git("log", "-1", "--format=%s").strip() == b"fix a"


def test_req_vcs_013_push_can_set_the_upstream(tmp_path, repo, gr, remote):
    repo.git("checkout", "-q", "-b", "feature"); repo.write("f.txt", "f\n"); repo.commit("feat")
    assert gr.status().upstream is None
    assert gr.push(set_upstream=True).ok
    assert gr.status().upstream == "origin/feature"


def test_at_vcs_020_pull_fast_forwards_to_the_upstream(tmp_path, repo, gr, remote):
    other = other_clone(tmp_path, remote)
    other.write("b.txt", "b\n"); other.commit("remote fix"); other.git("push", "-q")
    assert gr.pull().ok
    assert repo.git("log", "-1", "--format=%s").strip() == b"remote fix"


def test_at_vcs_021_pull_with_diverged_branches_changes_nothing(tmp_path, repo, gr, remote):
    other = other_clone(tmp_path, remote)
    other.write("b.txt", "b\n"); other.commit("remote fix"); other.git("push", "-q")
    repo.write("c.txt", "c\n"); repo.commit("local fix")
    head = repo.git("rev-parse", "HEAD")
    r = gr.pull()
    assert not r.ok and "fast-forward" in r.message.lower()
    assert repo.git("rev-parse", "HEAD") == head
    assert repo.git("rev-list", "--merges", "--count", "HEAD").strip() == b"0"


# ---------- read-only browsing (REQ-VCS-017) ----------

def _snapshot(root: Path) -> dict[str, str]:
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file()}


def test_at_vcs_017_browsing_does_not_change_the_repository(repo, gr):
    repo.write("a.py", "a\n"); repo.write("b.py", "b\n"); repo.commit()
    repo.write("a.py", "a2\n"); repo.git("add", "a.py"); repo.write("b.py", "b2\n"); repo.write("n.py", "n\n")
    before = _snapshot(repo.path)
    for _ in range(3):
        for change in gr.status().changes:
            gr.sides(change)
    assert _snapshot(repo.path) == before


# ---------- marking a conflict as resolved (REQ-VCS-024, DES-VCS-044) ----------

def conflicted(repo, main_text="main\n", other_text="other\n", delete_on_other=False):
    """Merge `other` into `main` so that f.txt ends up in conflict."""
    repo.write("f.txt", "base\n"); repo.commit("base")
    repo.git("checkout", "-q", "-b", "other")
    if delete_on_other:
        repo.git("rm", "-q", "f.txt"); repo.git("commit", "-q", "-m", "delete")
    else:
        repo.write("f.txt", other_text); repo.commit("other")
    repo.git("checkout", "-q", "main"); repo.write("f.txt", main_text); repo.commit("main")
    repo.git("merge", "-q", "other", check=False)


def test_req_vcs_024_resolved_conflict_is_marked_with_git_add(repo, gr):
    conflicted(repo)
    repo.write("f.txt", "main and other\n")
    assert gr.mark_resolved(entry(gr, Group.CONFLICTS, "f.txt")).ok
    st = gr.status()
    assert not st.has_conflicts and [c.path for c in st.group(Group.STAGED)] == ["f.txt"]


def test_req_vcs_024_file_with_markers_is_not_marked_and_names_the_line(repo, gr):
    conflicted(repo)
    calls = gr.git.call_count
    with pytest.raises(UnresolvedConflict, match=r"f\.txt.*linia 1"):
        gr.mark_resolved(entry(gr, Group.CONFLICTS, "f.txt"))
    assert gr.git.call_count == calls + 1  # only the status lookup above; no git add
    assert gr.status().has_conflicts


def test_req_vcs_024_diff3_base_marker_also_blocks(repo, gr):
    conflicted(repo)
    repo.write("f.txt", "ours\n||||||| base\nbase\n")
    with pytest.raises(UnresolvedConflict, match="linia 2"):
        gr.mark_resolved(entry(gr, Group.CONFLICTS, "f.txt"))


def test_req_vcs_024_markdown_heading_underline_is_not_a_marker(repo, gr):
    conflicted(repo)
    repo.write("f.txt", "Tytuł\n=======\n\nTreść po scaleniu.\n")
    assert gr.mark_resolved(entry(gr, Group.CONFLICTS, "f.txt")).ok
    assert not gr.status().has_conflicts


def test_req_vcs_024_conflict_resolved_by_deleting_the_file_uses_git_rm(repo, gr):
    conflicted(repo, delete_on_other=True)
    (repo.path / "f.txt").unlink()
    assert gr.mark_resolved(entry(gr, Group.CONFLICTS, "f.txt")).ok
    st = gr.status()
    assert not st.has_conflicts and [(c.path, c.code) for c in st.group(Group.STAGED)] == [("f.txt", "D")]



# ---------- whole folders (REQ-VCS-026) ----------

def test_req_vcs_026_stage_all_adds_every_file_in_one_git_call(repo, gr):
    repo.write("a.txt", "a\n"); repo.commit()
    repo.write("spec/a.json", "1\n"); repo.write("spec/b.json", "2\n")
    changes = gr.status().group(Group.UNVERSIONED)
    calls = gr.git.call_count
    assert gr.stage_all(changes).ok
    assert gr.git.call_count == calls + 1
    assert [c.path for c in gr.status().group(Group.STAGED)] == ["spec/a.json", "spec/b.json"]


def test_req_vcs_026_unstage_all_restores_renames_too(repo, gr):
    repo.write("d/old.py", "x\n" * 10); repo.write("d/k.py", "k\n"); repo.commit()
    repo.git("mv", "d/old.py", "d/new.py"); repo.write("d/k.py", "k2\n"); repo.git("add", "d/k.py")
    assert gr.unstage_all(gr.status().group(Group.STAGED)).ok
    st = gr.status()
    assert st.group(Group.STAGED) == []
    assert sorted(c.path for c in st.group(Group.UNVERSIONED)) == ["d/new.py"]


# ---------- merge in progress (DES-VCS-046, REQ-VCS-027) ----------

def test_des_vcs_046_status_reports_a_merge_in_progress(repo, gr):
    repo.write("a.txt", "a\n"); repo.commit("init")
    assert not gr.status().merging
    conflicted(repo)
    assert gr.status().merging


def test_des_vcs_046_merge_is_found_through_a_git_file(tmp_path):
    Repo(tmp_path).git("init", "-q", "-b", "main", "--separate-git-dir", str(tmp_path / "store"), str(tmp_path / "wt"))
    r = Repo(tmp_path / "wt")
    conflicted(r)
    assert (r.path / ".git").is_file()
    assert GitRepo(r.path, GitCli(env=GIT_ENV)).status().merging


def test_req_vcs_027_commit_concludes_a_merge_resolved_to_head(repo, gr):
    conflicted(repo)
    repo.write("f.txt", "main\n")
    assert gr.mark_resolved(entry(gr, Group.CONFLICTS, "f.txt")).ok
    st = gr.status()
    assert st.changes == () and st.merging
    assert gr.commit("Merge branch 'other'").ok
    assert len(repo.git("log", "-1", "--format=%P").split()) == 2
    assert not gr.status().merging
