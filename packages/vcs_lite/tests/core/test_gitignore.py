"""Adding unversioned files and folders to .gitignore (REQ-VCS-030, DES-VCS-048; PROPOZYCJA-gitignore.md, G-01–G-12)."""

from __future__ import annotations

import os

import pytest
from conftest import GIT_ENV

from vcs_lite.core.gitcli import GitCli
from vcs_lite.core.repo import GitRepo
from vcs_lite.core.status import Group


@pytest.fixture
def gr(repo) -> GitRepo:
    repo.write("README.md", "x\n"); repo.commit("init")
    return GitRepo(repo.path, GitCli(env=GIT_ENV))


def unversioned(gr: GitRepo) -> list[str]:
    return [c.path for c in gr.status().group(Group.UNVERSIONED)]


def ignore_file(repo) -> bytes:
    return (repo.path / ".gitignore").read_bytes()


def test_req_vcs_030_g01_one_file_creates_the_gitignore(repo, gr):
    repo.write("a.log", "x\n")
    assert gr.ignore(["a.log"], {}).ok
    assert ignore_file(repo) == b"/a.log\n"
    assert unversioned(gr) == [".gitignore"]


def test_req_vcs_030_g02_missing_final_newline_is_added_first(repo, gr):
    repo.write(".gitignore", "*.tmp"); repo.write("a.log", "x\n")
    gr.ignore(["a.log"], {})
    assert ignore_file(repo) == b"*.tmp\n/a.log\n"


def test_req_vcs_030_g03_a_line_already_there_is_not_added_again(repo, gr):
    repo.write(".gitignore", "/a.log\n"); repo.write("a.log", "x\n")
    assert gr.ignore(["a.log"], {}).ok
    assert ignore_file(repo) == b"/a.log\n"


def test_req_vcs_030_g04_special_characters_are_escaped(repo, gr):
    names = ["#notatka.txt", "!wazne.txt", "plik[1].txt", "a*b.txt", "x "]
    for name in names:
        repo.write(name, "x\n")
    gr.ignore(names, {})
    assert ignore_file(repo).decode().splitlines() == ["/#notatka.txt", "/!wazne.txt", "/plik\\[1\\].txt", "/a\\*b.txt", "/x\\ "]
    assert unversioned(gr) == [".gitignore"]


def test_req_vcs_030_g05_polish_letters_and_spaces(repo, gr):
    repo.write("zdjęcie z wakacji.png", "x\n")
    gr.ignore(["zdjęcie z wakacji.png"], {})
    assert ignore_file(repo) == "/zdjęcie z wakacji.png\n".encode()
    assert unversioned(gr) == [".gitignore"]


def test_req_vcs_030_g06_g07_a_folder_covers_its_files(repo, gr):
    repo.write("new/a.txt", "a\n"); repo.write("new/b.txt", "b\n")
    gr.ignore(["new/a.txt"], {"new": ["new/a.txt", "new/b.txt"]})
    assert ignore_file(repo) == b"/new/\n"
    assert unversioned(gr) == [".gitignore"]


def test_req_vcs_030_g08_folder_with_tracked_files_gets_file_patterns(repo, gr):
    repo.write("mix/tracked.txt", "t\n"); repo.commit("tracked")
    repo.write("mix/u1.txt", "u\n"); repo.write("mix/u2.txt", "u\n")
    gr.ignore([], {"mix": ["mix/u1.txt", "mix/u2.txt"]})
    assert ignore_file(repo) == b"/mix/u1.txt\n/mix/u2.txt\n"
    assert repo.git("ls-files", "mix").decode().split() == ["mix/tracked.txt"]


def test_req_vcs_030_g09_crlf_line_endings_stay_crlf(repo, gr):
    (repo.path / ".gitignore").write_bytes(b"*.tmp\r\n"); repo.write("a.log", "x\n")
    gr.ignore(["a.log"], {})
    assert ignore_file(repo) == b"*.tmp\r\n/a.log\r\n"


@pytest.mark.skipif(os.geteuid() == 0, reason="root writes read-only files")
def test_req_vcs_030_g10_read_only_gitignore_is_an_error_and_stays_unchanged(repo, gr):
    repo.write(".gitignore", "*.tmp\n"); repo.write("a.log", "x\n")
    (repo.path / ".gitignore").chmod(0o444)
    try:
        with pytest.raises(OSError):
            gr.ignore(["a.log"], {})
        assert ignore_file(repo) == b"*.tmp\n"
    finally:
        (repo.path / ".gitignore").chmod(0o644)


def test_req_vcs_030_g11_a_later_pattern_wins_over_an_earlier_negation(repo, gr):
    repo.write(".gitignore", "*.log\n!keep.log\n"); repo.write("keep.log", "x\n")
    assert "keep.log" in unversioned(gr)
    gr.ignore(["keep.log"], {})
    assert "keep.log" not in unversioned(gr)


def test_req_vcs_030_g12_nested_file_goes_to_the_root_gitignore(repo, gr):
    repo.write("a/b/c.tmp", "x\n")
    gr.ignore(["a/b/c.tmp"], {})
    assert ignore_file(repo) == b"/a/b/c.tmp\n"
    assert not (repo.path / "a" / ".gitignore").exists()
