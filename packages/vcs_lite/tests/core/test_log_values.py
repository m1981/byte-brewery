"""Values of the history and the parsers of git's output, without git (DES-VCS-064, rules H-07, H-09)."""

from __future__ import annotations

from vcs_lite.core.log import (Commit, CommitFile, LogQuery, Ref, RefKind, Scope, parse_log, parse_name_status,
                               parse_refs)


def record(hash_: str, parents: str = "", author: str = "Ola", email: str = "ola@x", time: int = 100,
           refs: str = "", subject: str = "s") -> bytes:
    return "\x1f".join([hash_, parents, author, email, str(time), refs, subject]).encode() + b"\0"


# ---------- labels (H-07) ----------

def test_des_vcs_064_labels_of_full_decoration():
    refs = parse_refs("HEAD -> refs/heads/main, refs/remotes/origin/main, refs/remotes/origin/HEAD, "
                      "tag: refs/tags/v1, refs/heads/origin/fake")
    assert refs == (Ref(RefKind.LOCAL, "main", current=True), Ref(RefKind.REMOTE, "origin/main"),
                    Ref(RefKind.TAG, "v1"), Ref(RefKind.LOCAL, "origin/fake"))


def test_des_vcs_064_detached_head_grafted_and_unknown_refs():
    assert parse_refs("HEAD, tag: refs/tags/v1") == (Ref(RefKind.HEAD, "HEAD"), Ref(RefKind.TAG, "v1"))
    assert parse_refs("grafted") == ()
    assert parse_refs("refs/stash, refs/notes/commits") == ()
    assert parse_refs("") == ()


# ---------- commits (H-01, H-09) ----------

def test_des_vcs_064_log_records_become_commits():
    raw = record("b" * 40, "a" * 40 + " " + "c" * 40, "Żaneta", "z@x", 1700000000, "HEAD -> refs/heads/main", "Łączenie")
    raw += record("a" * 40, "", subject="")
    first, root = parse_log(raw)
    assert first == Commit("b" * 40, ("a" * 40, "c" * 40), "Żaneta", "z@x", 1700000000,
                           (Ref(RefKind.LOCAL, "main", current=True),), "Łączenie")
    assert first.short == "bbbbbbb" and first.merge
    assert root.parents == () and not root.merge and root.subject == ""


def test_des_vcs_064_broken_bytes_are_replaced_and_a_repeated_parent_counts_once():
    raw = "\x1f".join(["b" * 40, "a" * 40 + " " + "a" * 40, "x", "x", "1", "", ""]).encode()
    raw += b"za\xbf" + b"\0"
    [commit] = parse_log(raw)
    assert commit.subject == "za�" and commit.parents == ("a" * 40,)          # H-26, H-09
    assert parse_log(b"") == []


# ---------- files of a commit (H-45) ----------

def test_des_vcs_064_name_status_with_renames():
    raw = b"M\0a.py\0A\0nowy.txt\0D\0stary.md\0R087\0old/name.py\0new/name.py\0T\0link\0"
    assert parse_name_status(raw) == (CommitFile("M", "a.py"), CommitFile("A", "nowy.txt"), CommitFile("D", "stary.md"),
                                      CommitFile("R", "new/name.py", "old/name.py"), CommitFile("T", "link"))
    assert parse_name_status(b"") == ()


# ---------- the query ----------

def test_des_vcs_064_a_query_filters_only_with_text():
    assert not LogQuery().filtered and LogQuery().scope is Scope.ALL
    assert not LogQuery(text="  ").filtered and LogQuery(text=" fix ").filtered
    assert LogQuery(text=" fix ").phrase == "fix"
