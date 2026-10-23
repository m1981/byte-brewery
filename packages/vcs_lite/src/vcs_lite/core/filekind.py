"""What kind of file a path is, which decides where it opens (REQ-VCS-034, DEC-VCS-098, DEC-VCS-100).

The kind comes from the extension alone, so the change list, the project tree and the search window agree.
Whether an unchanged file can be shown as text is read from its first bytes, like git does.

Trace: DES-VCS-060, DES-VCS-008, REQ-VCS-034, REQ-VCS-007, DEC-VCS-099, DEC-VCS-100
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path

TEXT_LIMIT = 2 * 1024 * 1024   # larger files get no page (DEC-VCS-099, DEC-VCS-105)
SNIFF = 8000                   # bytes git looks at for a NUL


class Kind(Enum):
    MARKDOWN = "markdown"
    IMAGE = "image"
    PDF = "pdf"
    OTHER = "other"

    @property
    def shown_as_file(self) -> bool:
        """The browser shows the file itself; there is no page of differences (DEC-VCS-100)."""
        return self in (Kind.IMAGE, Kind.PDF)


EXTENSIONS = {".md": Kind.MARKDOWN, ".pdf": Kind.PDF,
              **{ext: Kind.IMAGE for ext in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp", ".ico")}}


def kind_of(path: str) -> Kind:
    return EXTENSIONS.get(Path(path).suffix.lower(), Kind.OTHER)


def is_text(path: Path) -> bool:
    """A regular file up to 2 MB without a NUL byte in its first 8000 bytes."""
    try:
        if not path.is_file() or path.stat().st_size > TEXT_LIMIT:
            return False
        with path.open("rb") as handle:
            return b"\0" not in handle.read(SNIFF)
    except OSError:
        return False
