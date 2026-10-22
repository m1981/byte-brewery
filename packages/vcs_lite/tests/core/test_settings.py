"""Settings: scanning rootdir and persisting the chosen repositories (DES-VCS-019, DES-VCS-020).

The Settings dialog lists exactly what scan_rootdir returns, and the main window lists exactly
Settings.repos, so the Settings scenarios are checked here at that boundary.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from vcs_lite.core.difftool import BEYOND_COMPARE
from vcs_lite.core.settings import (
    DEFAULT_ROOTDIR,
    RootDirNotFound,
    Settings,
    SettingsError,
    SettingsStore,
    scan_rootdir,
)


def make_repo(path: Path) -> Path:
    (path / ".git").mkdir(parents=True)
    return path


@pytest.fixture
def rootdir(tmp_path: Path) -> Path:
    root = tmp_path / "PycharmProjects"
    root.mkdir()
    return root


# ---------- scanning rootdir ----------

def test_at_vcs_018_only_first_level_repositories_are_listed(rootdir):
    make_repo(rootdir / "docs")
    make_repo(rootdir / "docs" / "sessions")
    assert scan_rootdir(rootdir) == ["docs"]


def test_at_vcs_022_folders_that_are_not_repositories_are_hidden(rootdir):
    make_repo(rootdir / "alpha")
    (rootdir / "zdjecia").mkdir()
    assert scan_rootdir(rootdir) == ["alpha"]


def test_des_vcs_020_hidden_folders_are_skipped(rootdir):
    make_repo(rootdir / ".cache-repo")
    make_repo(rootdir / "visible")
    assert scan_rootdir(rootdir) == ["visible"]


def test_des_vcs_020_worktree_with_git_file_counts_as_repository(rootdir):
    wt = rootdir / "feature-wt"
    wt.mkdir()
    (wt / ".git").write_text("gitdir: /elsewhere/.git/worktrees/feature-wt\n")
    assert scan_rootdir(rootdir) == ["feature-wt"]


def test_des_vcs_020_plain_files_are_ignored_and_names_are_sorted(rootdir):
    for name in ("gamma", "alpha", "beta"):
        make_repo(rootdir / name)
    (rootdir / "notes.txt").write_text("x")
    assert scan_rootdir(rootdir) == ["alpha", "beta", "gamma"]


def test_uc_vcs_01_missing_rootdir_is_reported_with_its_path(tmp_path):
    missing = tmp_path / "nope"
    with pytest.raises(RootDirNotFound, match=str(missing)):
        scan_rootdir(missing)


# ---------- persisting settings ----------

def test_des_vcs_019_defaults_when_no_settings_file_exists(tmp_path):
    settings = SettingsStore(tmp_path / "settings.json").load()
    assert settings == Settings(rootdir=DEFAULT_ROOTDIR, repos=(), diff_tool=BEYOND_COMPARE, show_folders=False)
    assert DEFAULT_ROOTDIR == "~/PycharmProjects"


def test_at_vcs_001_chosen_repositories_survive_a_restart(tmp_path, rootdir):
    for name in ("alpha", "beta", "gamma"):
        make_repo(rootdir / name)
    path = tmp_path / "support" / "settings.json"
    chosen = [n for n in scan_rootdir(rootdir) if n in {"alpha", "gamma"}]
    SettingsStore(path).save(Settings(rootdir=str(rootdir), repos=tuple(chosen)))
    assert SettingsStore(path).load().repos == ("alpha", "gamma")


def test_des_vcs_037_diff_tool_command_is_stored_in_settings(tmp_path):
    path = tmp_path / "settings.json"
    SettingsStore(path).save(Settings(diff_tool=("/usr/local/bin/inny-diff", "{left}", "{right}")))
    assert json.loads(path.read_text())["diff_tool"] == ["/usr/local/bin/inny-diff", "{left}", "{right}"]
    assert SettingsStore(path).load().diff_tool == ("/usr/local/bin/inny-diff", "{left}", "{right}")


def test_des_vcs_019_rootdir_keeps_tilde_and_expands_on_use():
    settings = Settings(rootdir="~/PycharmProjects")
    assert settings.root_path == Path.home() / "PycharmProjects"
    assert settings.repo_path("alpha") == Path.home() / "PycharmProjects" / "alpha"


def test_des_vcs_019_missing_keys_fall_back_to_defaults(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"repos": ["alpha"]}))
    assert SettingsStore(path).load() == Settings(repos=("alpha",))


def test_des_vcs_019_corrupt_file_is_reported_not_silently_reset(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text("{not json")
    with pytest.raises(SettingsError, match=str(path)):
        SettingsStore(path).load()


def test_uc_vcs_01_failed_save_keeps_the_previous_settings(tmp_path):
    folder = tmp_path / "support"
    path = folder / "settings.json"
    store = SettingsStore(path)
    store.save(Settings(repos=("alpha",)))
    folder.chmod(0o500)  # no new files, so the atomic temp file cannot be created
    try:
        with pytest.raises(SettingsError):
            store.save(Settings(repos=("beta",)))
    finally:
        folder.chmod(0o700)
    assert store.load().repos == ("alpha",)


def test_req_vcs_017_saving_settings_writes_nothing_into_repositories(tmp_path, rootdir):
    repo = make_repo(rootdir / "alpha")
    before = sorted(p.name for p in repo.rglob("*"))
    SettingsStore(tmp_path / "settings.json").save(Settings(rootdir=str(rootdir), repos=("alpha",)))
    assert sorted(p.name for p in repo.rglob("*")) == before


@pytest.mark.parametrize("data", [{"repos": "alpha"}, {"rootdir": 5}, {"diff_tool": [1, 2]}, {"show_folders": "yes"}, ["not", "an", "object"]])
def test_des_vcs_019_values_of_the_wrong_type_are_reported(tmp_path, data):
    path = tmp_path / "settings.json"
    path.write_text(json.dumps(data))
    with pytest.raises(SettingsError, match=str(path)):
        SettingsStore(path).load()


def test_req_vcs_025_folder_view_choice_is_stored(tmp_path):
    path = tmp_path / "settings.json"
    SettingsStore(path).save(Settings(show_folders=True))
    assert json.loads(path.read_text())["show_folders"] is True
    assert SettingsStore(path).load().show_folders is True
