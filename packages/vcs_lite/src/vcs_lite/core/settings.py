"""Which repositories are watched: scanning rootdir and persisting the choice.

Trace: DES-VCS-019, DES-VCS-020, DES-VCS-037, DES-VCS-045, REQ-VCS-001, REQ-VCS-025, REQ-VCS-017, DEC-VCS-007, DEC-VCS-016, DEC-VCS-027
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from vcs_lite.core.difftool import BEYOND_COMPARE

DEFAULT_ROOTDIR = "~/PycharmProjects"


def default_settings_path() -> Path:
    return Path.home() / "Library" / "Application Support" / "vcs-lite" / "settings.json"


class SettingsError(Exception):
    """Settings could not be read or written."""


class RootDirNotFound(SettingsError):
    def __init__(self, rootdir: Path):
        super().__init__(f"Katalog z repozytoriami nie istnieje: {rootdir}")
        self.rootdir = rootdir


@dataclass(frozen=True)
class Settings:
    rootdir: str = DEFAULT_ROOTDIR
    repos: tuple[str, ...] = ()
    diff_tool: tuple[str, ...] = BEYOND_COMPARE
    show_folders: bool = False

    @property
    def root_path(self) -> Path:
        return Path(self.rootdir).expanduser()

    def repo_path(self, name: str) -> Path:
        return self.root_path / name

    def to_dict(self) -> dict[str, Any]:
        return {"rootdir": self.rootdir, "repos": list(self.repos), "diff_tool": list(self.diff_tool),
                "show_folders": self.show_folders}

    @classmethod
    def from_dict(cls, data: Any) -> Settings:
        """Missing keys take defaults; values of the wrong type raise ValueError."""
        if not isinstance(data, dict):
            raise ValueError("oczekiwano obiektu JSON")
        defaults = cls()
        rootdir = data.get("rootdir", defaults.rootdir)
        if not isinstance(rootdir, str):
            raise ValueError("„rootdir” musi być tekstem")
        show_folders = data.get("show_folders", defaults.show_folders)
        if not isinstance(show_folders, bool):
            raise ValueError("„show_folders” musi być wartością true albo false")
        return cls(
            rootdir=rootdir,
            repos=_strings(data, "repos", defaults.repos),
            diff_tool=_strings(data, "diff_tool", defaults.diff_tool),
            show_folders=show_folders,
        )


def _strings(data: dict[str, Any], key: str, default: tuple[str, ...]) -> tuple[str, ...]:
    value = data.get(key, list(default))
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"„{key}” musi być listą tekstów")
    return tuple(value)


def _is_repository(folder: Path) -> bool:
    return (folder / ".git").exists()  # a directory, or a file in a linked worktree


def scan_rootdir(rootdir: Path) -> list[str]:
    """Names of first-level, non-hidden folders of rootdir that are git repositories."""
    if not rootdir.is_dir():
        raise RootDirNotFound(rootdir)
    return sorted(
        entry.name
        for entry in rootdir.iterdir()
        if entry.is_dir() and not entry.name.startswith(".") and _is_repository(entry)
    )


class SettingsStore:
    def __init__(self, path: Path):
        self.path = path

    def load(self) -> Settings:
        if not self.path.exists():
            return Settings()
        try:
            return Settings.from_dict(json.loads(self.path.read_text(encoding="utf-8")))
        except (OSError, ValueError) as exc:  # json.JSONDecodeError is a ValueError
            raise SettingsError(f"Nie można odczytać ustawień {self.path}: {exc}") from exc

    def save(self, settings: Settings) -> None:
        payload = json.dumps(settings.to_dict(), ensure_ascii=False, indent=2)
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._write_atomically(payload)
        except OSError as exc:
            raise SettingsError(f"Nie można zapisać ustawień {self.path}: {exc}") from exc

    def _write_atomically(self, payload: str) -> None:
        fd, tmp = tempfile.mkstemp(dir=self.path.parent, prefix=".settings-", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(payload)
            os.replace(tmp, self.path)
        except BaseException:
            Path(tmp).unlink(missing_ok=True)
            raise
