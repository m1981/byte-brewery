"""Entry point and composition root: settings, git, worker, model and the main window.

Trace: DES-VCS-028, DES-VCS-029, DES-VCS-034, DES-VCS-036, DES-VCS-041, REQ-VCS-103
"""

from __future__ import annotations

import argparse
import subprocess
import tkinter as tk
from collections.abc import Sequence
from pathlib import Path
from tkinter import messagebox

from vcs_lite.app.model import AppModel
from vcs_lite.app.worker import Worker
from vcs_lite.core.gitcli import GitCli
from vcs_lite.core.settings import SettingsStore, default_settings_path
from vcs_lite.ui.main_window import MainWindow
from vcs_lite.ui.pump import TkPump
from vcs_lite.ui.tkenv import prepare_tk


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
    pump = TkPump(root, Worker())
    model = AppModel.from_settings(store.load(), git=GitCli(), worker=pump,
                                   confirm=lambda title, message: messagebox.askyesno(title, message, parent=root),
                                   save_settings=store.save)
    MainWindow(root, model, reduce_motion=reduce_motion()).pack(fill=tk.BOTH, expand=True)
    return root, model, pump


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    root, model, _ = build(args.settings)
    model.refresh_all()
    _bring_to_front(root)
    root.mainloop()


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
