"""Entry point and composition root: settings, git, worker, model and the main window.

Trace: DES-VCS-062, REQ-VCS-104, DEC-VCS-112, DES-VCS-028, DES-VCS-029, DES-VCS-034, DES-VCS-036, DES-VCS-041, DES-VCS-055, REQ-VCS-033, REQ-VCS-103
"""

from __future__ import annotations

import argparse
import subprocess
import tkinter as tk
from collections.abc import Sequence
from pathlib import Path
from tkinter import messagebox

from vcs_lite.app.model import AppModel
from vcs_lite.app.search import SearchSession
from vcs_lite.app.worker import Worker
from vcs_lite.core.gitcli import GitCli
from vcs_lite.core.gitgrep import GitGrepSearcher
from vcs_lite.core.settings import SettingsStore, default_settings_path
from vcs_lite.ui.main_window import MainWindow
from vcs_lite.ui.pump import TkPump, tk_later
from vcs_lite.ui.tkenv import prepare_tk

WINDOW_ICON = Path(__file__).with_name("icon.png")   # written by tools/make_app.py (DES-VCS-061)


def parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="vcs-lite", description="Lekki panel VCS dla repozytoriów gita.")
    parser.add_argument("--settings", type=Path, default=default_settings_path(),
                        help="plik ustawień (domyślnie w ~/Library/Application Support/vcs-lite)")
    return parser.parse_args(argv)


def build(settings_path: Path) -> tuple[tk.Tk, AppModel, TkPump]:
    """The whole app without starting it; tests/measure_footprint.py measures exactly this (DES-VCS-034)."""
    store = SettingsStore(settings_path)
    prepare_tk()
    root = tk.Tk()
    root.title("vcs-lite")
    root.geometry("960x620")
    set_window_icon(root, WINDOW_ICON)
    pump, git = TkPump(root, Worker()), GitCli()
    model = AppModel.from_settings(store.load(), git=git, worker=pump,
                                   confirm=lambda title, message: ask(root, title, message),
                                   save_settings=store.save)
    search = SearchSession(GitGrepSearcher(git), pump, later=tk_later(root), repo=lambda: model.selected_path,
                           open_match=model.open_match)
    MainWindow(root, model, reduce_motion=reduce_motion(), search=search).pack(fill=tk.BOTH, expand=True)
    return root, model, pump


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    root, model, _ = build(args.settings)
    model.refresh_all()
    _bring_to_front(root)
    root.mainloop()


def set_window_icon(root: tk.Misc, icon: Path) -> bool:
    """The logo in the Dock when vcs-lite starts from a terminal (DEC-VCS-112); Tk copies the image, so no
    reference is kept. A missing or broken file leaves the default icon and never stops the start."""
    if not icon.is_file():
        return False
    try:
        root.iconphoto(True, tk.PhotoImage(master=root, file=str(icon)))
    except tk.TclError:
        return False
    return True


def ask(root: tk.Tk, title: str, message: str) -> bool:
    """P9: paint pending changes (an emptied message field) before the modal question takes over."""
    root.update_idletasks()
    return messagebox.askyesno(title, message, parent=root)


def reduce_motion() -> bool:
    """macOS setting „Ogranicz ruch”; the busy bar then stays still (UI-REFERENCE §8, P4)."""
    try:
        out = subprocess.run(["defaults", "read", "com.apple.universalaccess", "reduceMotion"],
                             capture_output=True, text=True, timeout=2, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return out.stdout.strip() == "1"


def _bring_to_front(root: tk.Tk) -> None:
    """Started from a terminal, the window would otherwise open behind it."""
    root.lift()
    root.attributes("-topmost", True)
    root.after_idle(root.attributes, "-topmost", False)


if __name__ == "__main__":
    main()
