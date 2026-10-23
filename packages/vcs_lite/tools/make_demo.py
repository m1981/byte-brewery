"""Create demo repositories for the manual checklist in docs/MANUAL-UI.md.

Usage: python tools/make_demo.py <empty folder>

Layout:
  <folder>/root/alpha    every kind of change, an ignored file, a rename, a nested repository, a long docs/plan.md,
                         images, a PDF, a text file and a zip (step 17)
  <folder>/root/beta     clean, tracking <folder>/remotes/beta.git
  <folder>/root/gamma    a merge conflict
  <folder>/root/zdjecia  a plain folder (must not appear in Settings)
  <folder>/root/.ukryte  a hidden repository (must not appear in Settings)
  <folder>/settings.json rootdir = <folder>/root, no repositories chosen yet
"""

from __future__ import annotations

import json
import os
import struct
import subprocess
import sys
import zlib
from pathlib import Path

ENV = {
    **os.environ,
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_AUTHOR_NAME": "Demo",
    "GIT_AUTHOR_EMAIL": "demo@example.invalid",
    "GIT_COMMITTER_NAME": "Demo",
    "GIT_COMMITTER_EMAIL": "demo@example.invalid",
}


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], env=ENV, check=False, capture_output=True)


def write(repo: Path, rel: str, text: str) -> None:
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def new_repo(path: Path) -> Path:
    path.mkdir(parents=True)
    git(path, "init", "-q", "-b", "main")
    # The app commits here with the user's own git config, so give the demo repos a local identity.
    git(path, "config", "user.name", "Demo")
    git(path, "config", "user.email", "demo@example.invalid")
    return path


def commit(repo: Path, message: str) -> None:
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", message)


def png(rgb: tuple[int, int, int], width: int = 160, height: int = 90) -> bytes:
    """A plain one-colour PNG, enough to see that an image opened and which version it is."""
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    rows = b"".join(b"\0" + bytes(rgb) * width for _ in range(height))
    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b"")


def pdf(text: str) -> bytes:
    """A one-page PDF with a line of text."""
    stream = f"BT /F1 24 Tf 40 100 Td ({text}) Tj ET".encode()
    objects = [b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
               b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 360 200] /Contents 4 0 R "
               b"/Resources << /Font << /F1 5 0 R >> >> >>",
               b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream",
               b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    out, offsets = b"%PDF-1.4\n", []
    for number, body in enumerate(objects, 1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % number + body + b"\nendobj\n"
    table = b"".join(b"%010d 00000 n \n" % offset for offset in offsets)
    return (out + b"xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1) + table
            + b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objects) + 1, len(out)))


PLAN = "# Plan\n\n" + "".join(f"## Etap {n}\n\nAkapit {n} o pracy w repozytorium.\n\n" for n in range(1, 31)) + (
    "## Na koniec\n\nTydzień próbny zakończony; żółw idzie w las.\n")


def make_alpha(root: Path) -> None:
    a = new_repo(root / "alpha")
    write(a, "README.md", "# alpha\n")
    write(a, "staged.py", "def f():\n    return 1\n")
    write(a, "both.py", "x = 1\n")
    write(a, "old_name.py", "def moved():\n    pass\n" * 5)
    write(a, ".gitignore", "*.log\nnested/\n")
    write(a, "docs/plan.md", PLAN)   # long enough to see the page scroll to a search match (step 16)
    (a / "logo.png").write_bytes(png((200, 40, 40)))      # step 17: red in HEAD …
    write(a, "notatki.txt", "Notatki bez zmian.\nDruga linia.\n")
    (a / "archiwum.zip").write_bytes(b"PK\x05\x06" + b"\0" * 18)   # an empty zip: opens in its application
    commit(a, "init")
    (a / "logo.png").write_bytes(png((40, 120, 220)))     # … blue in the working copy
    (a / "ikona.png").write_bytes(png((40, 160, 80)))     # green in the index …
    git(a, "add", "ikona.png")
    (a / "ikona.png").write_bytes(png((240, 180, 40)))    # … yellow on disk
    (a / "opis.pdf").write_bytes(pdf("PDF z repo demo"))
    write(a, "README.md", "# alpha\n\nZmiana w kopii roboczej.\n")
    write(a, "staged.py", "def f():\n    return 2\n")
    git(a, "add", "staged.py")
    write(a, "both.py", "x = 2\n")
    git(a, "add", "both.py")
    write(a, "both.py", "x = 3\n")
    git(a, "mv", "old_name.py", "renamed.py")
    write(a, "new/a.txt", "a\n")
    write(a, "new/b.txt", "b\n")
    write(a, "debug.log", "ignored\n")
    nested = new_repo(a / "nested")
    write(nested, "n.txt", "n\n")
    commit(nested, "nested init")


def make_beta(root: Path, remotes: Path) -> None:
    bare = remotes / "beta.git"
    bare.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(bare)], env=ENV, check=True, capture_output=True)
    b = new_repo(root / "beta")
    write(b, "README.md", "# beta\n")
    commit(b, "init")
    git(b, "remote", "add", "origin", str(bare))
    git(b, "push", "-q", "-u", "origin", "main")
    write(b, "notes.md", "do zacommitowania w kroku 11\n")


def make_gamma(root: Path) -> None:
    g = new_repo(root / "gamma")
    write(g, "f.txt", "base\n")
    commit(g, "base")
    git(g, "checkout", "-q", "-b", "other")
    write(g, "f.txt", "other\n")
    commit(g, "other")
    git(g, "checkout", "-q", "main")
    write(g, "f.txt", "main\n")
    commit(g, "main")
    git(g, "merge", "-q", "other")


def main(target: Path) -> None:
    if target.exists() and any(target.iterdir()):
        sys.exit(f"{target} nie jest pusty; podaj pusty folder.")
    root = target / "root"
    make_alpha(root)
    make_beta(root, target / "remotes")
    make_gamma(root)
    (root / "zdjecia").mkdir()
    write(root / "zdjecia", "wakacje.txt", "nie repo\n")
    hidden = new_repo(root / ".ukryte")
    write(hidden, "x.txt", "x\n")
    commit(hidden, "init")
    (target / "settings.json").write_text(json.dumps({"rootdir": str(root), "repos": []}, indent=2), encoding="utf-8")
    print(f"Repozytoria demo: {root}\nUstawienia: {target / 'settings.json'}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(Path(sys.argv[1]).expanduser().resolve())
