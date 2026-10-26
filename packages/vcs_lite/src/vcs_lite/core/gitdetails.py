"""Read changed-file times and line counts without changing the index or running diff plugins.

Trace: DES-VCS-073, REQ-VCS-042, REQ-VCS-043
"""
from __future__ import annotations

import os
import stat
from pathlib import Path

from vcs_lite.core.changes import ChangeDetails, LineStats
from vcs_lite.core.gitcli import GitCli
from vcs_lite.core.status import Group, RepoStatus


def parse_numstat(raw: bytes) -> dict[str, LineStats]:
    """NUL-delimited paths, including the empty-prefix old/new form of renames."""
    records = iter(raw.split(b"\0"))
    result = {}
    for record in records:
        if not record:
            continue
        try:
            added, removed, path = record.split(b"\t", 2)
            if not path:
                next(records)  # old path
                path = next(records)
            if not path:
                raise ValueError("Brak ścieżki numstat")
            lines = LineStats(kind="binary") if added == removed == b"-" else LineStats(int(added), int(removed))
            if lines.added < 0 or lines.removed < 0:
                raise ValueError("Ujemna liczba linii")
            result[os.fsdecode(path)] = lines
        except (ValueError, StopIteration) as exc:
            raise ValueError("Nieprawidłowy wynik git diff --numstat") from exc
    return result


def untracked_lines(path: Path) -> LineStats:
    mode = path.lstat().st_mode
    if stat.S_ISLNK(mode):
        data = os.fsencode(os.readlink(path))
        return LineStats(data.count(b"\n") + bool(data and not data.endswith(b"\n")), 0)
    if not stat.S_ISREG(mode):
        return LineStats(kind="unknown", reason="To nie jest zwykły plik ani dowiązanie.")
    count, last = 0, b""
    with path.open("rb") as source:
        first = source.read(8000)
        if b"\0" in first:
            return LineStats(kind="binary")
        block = first
        while block:
            count += block.count(b"\n")
            last = block[-1:]
            block = source.read(65536)
    return LineStats(count + bool(last and last != b"\n"), 0)


class GitChangeReader:
    def __init__(self, git: GitCli):
        self.git = git

    def _diff(self, root: Path, *args: str) -> tuple[dict[str, LineStats], str]:
        result = self.git.run(root, "diff", "--numstat", "-z", "--no-ext-diff", "--no-textconv", *args,
                              read_only=True)
        if not result.ok:
            return {}, result.message
        try:
            return parse_numstat(result.stdout), ""
        except ValueError as exc:
            return {}, str(exc)

    def read(self, root: Path, status: RepoStatus) -> dict[tuple[Group, str], ChangeDetails]:
        counts = {}
        for group, args in ((Group.STAGED, ("--cached", "--no-renames")),
                            (Group.CHANGES, ("--no-renames",))):
            if status.group(group):
                counts[group] = self._diff(root, *args)
        times = {}
        for change in status.changes:
            if change.path not in times:
                try:
                    times[change.path] = (root / change.path).lstat().st_mtime_ns
                except OSError:
                    times[change.path] = None
        details = {}
        for change in status.changes:
            if change.group is Group.CONFLICTS:
                lines = LineStats(kind="conflict")
            elif change.group is Group.UNVERSIONED:
                try:
                    lines = untracked_lines(root / change.path)
                except OSError as exc:
                    lines = LineStats(kind="unknown", reason=str(exc))
            else:
                entries, error = counts[change.group]
                if change.group is Group.STAGED and change.orig_path and change.code in ("R", "C"):
                    # Compare blobs so moving an unchanged file is 0/0, independent of rename thresholds.
                    entries, error = self._diff(root, f"HEAD:{change.orig_path}", f":{change.path}", "--")
                    lines = next(iter(entries.values()), LineStats())
                else:
                    lines = entries.get(change.path, LineStats(kind="unknown", reason="Brak pliku w wyniku numstat; odśwież listę."))
                if error:
                    lines = LineStats(kind="unknown", reason=error)
            details[change.group, change.path] = ChangeDetails(times[change.path], lines)
        return details
