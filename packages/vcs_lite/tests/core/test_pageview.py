"""Pages in the browser run as their own short processes (REQ-VCS-031, REQ-VCS-023, DES-VCS-049, DES-VCS-059)."""

from __future__ import annotations

import sys
from pathlib import Path

from vcs_lite.core.difftool import compare
from vcs_lite.core.pageview import MarkdownDiffTool, TextDiffTool


def test_des_vcs_049_runs_the_page_module_with_the_sides_and_titles():
    tool = MarkdownDiffTool(open_browser=False)
    argv = tool.command(Path("/tmp/vcs-lite-x/left/a.md"), Path("/tmp/vcs-lite-x/right/a.md"), "a.md (HEAD)", "a.md (indeks)")
    assert argv[:3] == [sys.executable, "-m", "vcs_lite.core.mdpage"]
    assert argv[3:] == ["/tmp/vcs-lite-x/left/a.md", "/tmp/vcs-lite-x/right/a.md", "a.md (HEAD)", "a.md (indeks)", "--no-open"]


def test_req_vcs_031_images_load_from_the_folder_of_a_working_copy_file(tmp_path):
    work = tmp_path / "repo" / "docs" / "a.md"
    argv = MarkdownDiffTool().command(Path("/tmp/vcs-lite-x/left/a.md"), work, "a.md (indeks)", "a.md (kopia robocza)")
    assert argv[-2:] == ["--base", str(work.parent)]


def test_des_vcs_049_the_page_is_written_without_errors(tmp_path):
    right = tmp_path / "a.md"
    right.write_text("# Plan\n\nNowy akapit.\n", encoding="utf-8")
    result = compare(MarkdownDiffTool(open_browser=False), b"# Plan\n", right, name="a.md",
                     left_title="a.md (HEAD)", right_title="a.md (kopia robocza)")
    assert result.returncode == 0 and not result.failed, result.stderr


def test_des_vcs_049_a_failing_page_is_reported_with_its_error(tmp_path):
    missing = tmp_path / "brak.md"
    result = MarkdownDiffTool(open_browser=False).open(missing, missing, "a", "b").wait()
    assert result.failed and "brak.md" in result.stderr


def test_req_vcs_031_the_chosen_theme_is_passed_when_the_page_opens():
    chosen = ["system"]
    tool = MarkdownDiffTool(open_browser=False, theme=lambda: chosen[0])
    sides = (Path("/tmp/vcs-lite-x/left/a.md"), Path("/tmp/vcs-lite-x/right/a.md"), "a", "b")
    assert "--theme" not in tool.command(*sides)
    chosen[0] = "dark"  # read at every opening, so a change in the settings applies at once
    assert tool.command(*sides)[-2:] == ["--theme", "dark"]


def test_req_vcs_032_the_reader_asks_for_the_reading_mode():
    argv = MarkdownDiffTool(open_browser=False, read=True).command(
        Path("/r/a.md"), Path("/r/a.md"), "a.md (kopia robocza)", "a.md (kopia robocza)")
    assert "--read" in argv


def test_des_vcs_056_reader_at_a_line_passes_it_and_keeps_its_settings():
    reader = MarkdownDiffTool(open_browser=False, read=True, theme=lambda: "dark")
    argv = reader.at_line(12).command(Path("/r/a.md"), Path("/r/a.md"), "a", "a")
    assert argv[-4:] == ["--theme", "dark", "--line", "12"] and "--read" in argv and "--no-open" in argv
    assert "--line" not in reader.command(Path("/r/a.md"), Path("/r/a.md"), "a", "a")


# ---------- text files (DES-VCS-059) ----------

def test_des_vcs_059_text_tool_runs_the_text_page_module():
    argv = TextDiffTool(open_browser=False).command(Path("/tmp/vcs-lite-x/left/a.py"), Path("/repo/a.py"), "a.py (indeks)",
                                                    "a.py (kopia robocza)")
    assert argv[:3] == [sys.executable, "-m", "vcs_lite.core.textpage"] and "--base" not in argv
    assert argv[3:7] == ["/tmp/vcs-lite-x/left/a.py", "/repo/a.py", "a.py (indeks)", "a.py (kopia robocza)"]


def test_des_vcs_059_text_reader_at_a_line_with_the_theme(tmp_path):
    reader = TextDiffTool(open_browser=False, read=True, theme=lambda: "light")
    argv = reader.at_line(7).command(Path("/r/a.py"), Path("/r/a.py"), "a", "a")
    assert "--read" in argv and argv[-4:] == ["--theme", "light", "--line", "7"]


def test_des_vcs_059_the_text_page_is_written_without_errors(tmp_path):
    right = tmp_path / "a.py"
    right.write_text("x = 2\n", encoding="utf-8")
    result = compare(TextDiffTool(open_browser=False), b"x = 1\n", right, name="a.py",
                     left_title="a.py (indeks)", right_title="a.py (kopia robocza)")
    assert result.returncode == 0 and not result.failed, result.stderr
