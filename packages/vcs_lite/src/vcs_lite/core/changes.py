"""Changed-file metadata and pure time grouping, independent of Git and Tk.

Trace: DES-VCS-072, REQ-VCS-042, REQ-VCS-043
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime

from vcs_lite.core.status import FileChange


@dataclass(frozen=True)
class LineStats:
    added: int = 0
    removed: int = 0
    kind: str = "text"  # text, binary, conflict, unknown, loading
    reason: str = ""


@dataclass(frozen=True)
class ChangeDetails:
    mtime_ns: int | None = None
    lines: LineStats = field(default_factory=lambda: LineStats(kind="loading"))


@dataclass(frozen=True)
class TimeGroup:
    files: tuple[FileChange, ...]
    newest: int | None
    oldest: int | None


def time_groups(changes: list[FileChange], details: Callable[[FileChange], ChangeDetails]) -> list[TimeGroup]:
    dated = [(c, details(c).mtime_ns) for c in changes]
    dated.sort(key=lambda pair: (pair[1] is None, -(pair[1] or 0), pair[0].path))
    groups: list[list[tuple[FileChange, int | None]]] = []
    for change, stamp in dated:
        previous = groups[-1][-1][1] if groups else None
        newest = groups[-1][0][1] if groups else None
        if (not groups or (stamp is None) != (previous is None)
                or (stamp is not None and (previous - stamp > 300 * 10**9 or newest - stamp > 900 * 10**9))):
            groups.append([])
        groups[-1].append((change, stamp))
    return [TimeGroup(tuple(c for c, _ in g), g[0][1], g[-1][1]) for g in groups]


def relative_time(stamp: int | None, now: datetime) -> str:
    if stamp is None:
        return "Czas nieznany"
    seconds = now.timestamp() - stamp / 10**9
    if seconds < 0:
        return "czas z przyszłości"
    if seconds < 60:
        return "przed chwilą"
    if seconds < 3600:
        return f"{int(seconds // 60)} min temu"
    if seconds < 86400:
        return f"{int(seconds // 3600)} h temu"
    if seconds < 7 * 86400:
        days = int(seconds // 86400)
        return "1 dzień temu" if days == 1 else f"{days} dni temu"
    date = datetime.fromtimestamp(stamp / 10**9, tz=now.tzinfo)
    return date.strftime("%d.%m" if date.year == now.year else "%d.%m.%Y")


def time_range(group: TimeGroup) -> str:
    if group.newest is None:
        return "Czas zapisu niedostępny (plik usunięty lub błąd odczytu metadanych)."
    def full(stamp):
        return datetime.fromtimestamp(stamp / 10**9).astimezone().strftime("%d.%m.%Y %H:%M:%S %Z")
    return f"Ostatnie zapisy na dysku: {full(group.oldest)} — {full(group.newest)}."
