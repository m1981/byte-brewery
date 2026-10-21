"""Make Tk start inside a venv made from uv's Python, which cannot find init.tcl on its own.

Trace: DES-VCS-041, OBS-VCS-009, REQ-VCS-103
"""

from __future__ import annotations

import os
import sys
from collections.abc import Mapping
from pathlib import Path


def tcl_tk_paths(env: Mapping[str, str], base_prefix: Path) -> dict[str, str]:
    """Variables to add so Tcl and Tk load their libraries from the base Python; never overrides the user."""
    wanted = {"TCL_LIBRARY": base_prefix / "lib" / "tcl8.6", "TK_LIBRARY": base_prefix / "lib" / "tk8.6"}
    return {name: str(path) for name, path in wanted.items() if name not in env and path.is_dir()}


def prepare_tk() -> None:
    """Call before the first tkinter.Tk()."""
    os.environ.update(tcl_tk_paths(os.environ, Path(sys.base_prefix)))
