"""External diff tool port and command-template adapter (DES-VCS-036..039)."""

from __future__ import annotations

import json
import stat
import sys
import textwrap
from pathlib import Path

import pytest

from vcs_lite.core.difftool import (
    BEYOND_COMPARE,
    CommandTemplateDiffTool,
    DiffResult,
    DiffToolError,
    compare,
)


class FakeTool:
    """Stands in for Beyond Compare: records what it was given and what it saw on disk."""

    def __init__(self, result: DiffResult = DiffResult(0, "")):
        self.result = result
        self.calls: list[dict] = []

    def open(self, left: Path, right: Path, left_title: str, right_title: str):
        self.calls.append({
            "left": left, "right": right, "left_title": left_title, "right_title": right_title,
            "left_text": left.read_text(encoding="utf-8"), "right_text": right.read_text(encoding="utf-8"),
            "left_writable": bool(left.stat().st_mode & stat.S_IWUSR),
        })
        return self

    def wait(self) -> DiffResult:
        return self.result


@pytest.fixture
def recorder(tmp_path: Path) -> tuple[list[str], Path]:
    """A real CLI tool: a Python script that writes its arguments to a JSON file."""
    out = tmp_path / "args.json"
    script = tmp_path / "fake_diff.py"
    script.write_text(textwrap.dedent(f"""
        import json, sys
        json.dump(sys.argv[1:], open({str(out)!r}, "w"))
    """), encoding="utf-8")
    return [sys.executable, str(script)], out


def test_des_vcs_037_template_fills_paths_and_titles():
    tool = CommandTemplateDiffTool(["diff-x", "{left}", "{right}", "-t1={left_title}", "-t2={right_title}"])
    assert tool.command(Path("/a/L"), Path("/b/R"), "app.py (HEAD)", "app.py (index)") == [
        "diff-x", "/a/L", "/b/R", "-t1=app.py (HEAD)", "-t2=app.py (index)"]


def test_des_vcs_037_titles_with_braces_are_inserted_literally():
    tool = CommandTemplateDiffTool(["d", "{left_title}"])
    assert tool.command(Path("l"), Path("r"), "x{right}y", "-") == ["d", "x{right}y"]


def test_des_vcs_037_default_command_is_beyond_compare():
    assert BEYOND_COMPARE[0] == "/Applications/Beyond Compare.app/Contents/MacOS/bcomp"
    assert "{left}" in BEYOND_COMPARE and "{right}" in BEYOND_COMPARE


def test_des_vcs_036_any_cli_tool_can_be_plugged_in(recorder, tmp_path):
    argv, out = recorder
    left, right = tmp_path / "l.txt", tmp_path / "r.txt"
    left.write_text("a\n"); right.write_text("b\n")
    result = CommandTemplateDiffTool([*argv, "{left}", "{right}"]).open(left, right, "L", "R").wait()
    assert result == DiffResult(0, "")
    assert json.loads(out.read_text()) == [str(left), str(right)]


def test_des_vcs_039_missing_tool_error_names_the_command(tmp_path):
    tool = CommandTemplateDiffTool(["/nonexistent/inny-diff", "{left}", "{right}"])
    with pytest.raises(DiffToolError, match="/nonexistent/inny-diff"):
        tool.open(tmp_path / "l", tmp_path / "r", "L", "R")


def test_des_vcs_039_exit_code_and_stderr_are_reported(tmp_path):
    script = tmp_path / "boom.py"
    script.write_text("import sys\nsys.stderr.write('boom')\nsys.exit(3)\n", encoding="utf-8")
    result = CommandTemplateDiffTool([sys.executable, str(script), "{left}"]).open(tmp_path / "l", tmp_path / "r", "L", "R").wait()
    assert result == DiffResult(3, "boom") and result.failed


def test_des_vcs_039_nonzero_exit_without_stderr_is_not_a_failure():
    # Diff tools signal "files differ" with a non-zero code (Beyond Compare uses several such codes).
    assert not DiffResult(11, "").failed


def test_des_vcs_038_git_sides_are_read_only_temp_files_with_the_file_name(tmp_path):
    tool = FakeTool()
    compare(tool, b"old\n", b"new\n", name="app.py", left_title="HEAD", right_title="index")
    call = tool.calls[0]
    assert (call["left_text"], call["right_text"]) == ("old\n", "new\n")
    assert call["left"].name == call["right"].name == "app.py"
    assert not call["left_writable"]


def test_req_vcs_023_worktree_side_is_passed_as_the_real_file(tmp_path):
    work = tmp_path / "app.py"
    work.write_text("edited\n")
    tool = FakeTool()
    compare(tool, b"index\n", work, name="app.py", left_title="index", right_title="worktree")
    assert tool.calls[0]["right"] == work  # editable in the tool, DEC-VCS-039


def test_des_vcs_038_temp_files_are_removed_after_the_tool_exits(tmp_path):
    tool = FakeTool(DiffResult(0, ""))
    compare(tool, b"a", b"b", name="f.txt", left_title="L", right_title="R")
    assert not tool.calls[0]["left"].exists() and not tool.calls[0]["right"].exists()


def test_des_vcs_038_temp_files_are_removed_when_the_tool_cannot_start(tmp_path):
    seen: list[Path] = []

    class Broken:
        def open(self, left, right, left_title, right_title):
            seen.append(left)
            raise DiffToolError("cannot start")

    with pytest.raises(DiffToolError):
        compare(Broken(), b"a", b"b", name="f.txt", left_title="L", right_title="R")
    assert seen and not seen[0].exists()


def test_des_vcs_038_empty_side_is_an_empty_file(tmp_path):
    tool = FakeTool()
    compare(tool, b"", b"x\n", name="new.py", left_title="empty", right_title="index")
    assert tool.calls[0]["left_text"] == ""
    assert tool.calls[0]["right_text"] == "x\n"
