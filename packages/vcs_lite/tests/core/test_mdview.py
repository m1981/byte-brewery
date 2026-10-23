"""The rendered Markdown diff run as its own short process (REQ-VCS-031, DES-VCS-049)."""

from __future__ import annotations

import sys
from pathlib import Path

from vcs_lite.core.difftool import compare
from vcs_lite.core.mdview import MarkdownDiffTool


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
