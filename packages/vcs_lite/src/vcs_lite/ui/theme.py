"""Every visual value of the reference E-01 in one place; widgets take colours, fonts and spacing only from here.

Source: docs/ui-reference/UI-REFERENCE.md (sections 1, 2, 3, 8) and E-01.html.
Approximations allowed by section 6: sizes rounded to whole points, weights >= 550 drawn bold,
no letter spacing, transparency replaced by computed colours.

Trace: DES-VCS-042, DES-VCS-045, DES-VCS-057, DEC-VCS-097, DEC-VCS-045, DEC-VCS-047, DEC-VCS-049, DEC-VCS-052, DEC-VCS-053, DEC-VCS-068, DEC-VCS-089, DEC-VCS-092
"""

from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass
from tkinter import font as tkfont

COLORS = {
    # tokens (section 1)
    "bg": "#ffffff",
    "chrome": "#ececee",
    "sidebar": "#f2f2f5",
    "line": "#dedee3",
    "ink": "#1d1d1f",
    "dim": "#6e6e73",
    "accent": "#0a66d8",
    "accent_soft": "#e3eefc",
    "mod": "#b4690e",
    "add": "#1f7a3a",
    "del": "#c2302a",
    "ren": "#2a5fb0",
    "unv": "#7a7a80",
    "conf": "#c2302a",
    # single colours (section 1)
    "panel": "#fafafb",               # toolbar and commit panel
    "chip_bg": "#eef0f3",
    "chip_ink": "#3a3a40",            # chip text, badge text
    "title_ink": "#4a4a50",
    "control_border": "#c9c9cf",
    "badge_bg": "#dfe1e6",
    "branch_on_accent": "#dbe8fb",
    "state_clean": "#9fd3ad",
    "state_off": "#c7c7cc",
    "name_off": "#8e8e93",
    "conf_soft": "#fbe3e1",
    # the View switch, P14 (DEC-VCS-092)
    "seg_track": "#e4e4e9", "seg_track_line": "#d4d4da", "seg_thumb": "#ffffff", "seg_thumb_edge": "#cfcfd5",
    "seg_shadow": "#d6d6db", "seg_separator": "#c3c3ca", "seg_hover": "#d9d9df", "seg_ink": "#3a3a40",
    "row_hover": "#f5f7fb",
    "kbd_bg": "#f0f0f3",
    "kbd_border": "#d5d5da",
    "on_accent": "#ffffff",
    "badge_on_accent": "#478ce2",     # white 25 % over accent
    # disabled controls, opacity .45 over the panel (section 1)
    "primary_disabled": "#8eb7eb",
    "secondary_disabled_bg": "#fcfcfc",
    "secondary_disabled_border": "#e4e4e7",
    "secondary_disabled_ink": "#979798",
    # states outside the mock-up (section 8)
    "busy_ring": "#84b2eb",           # white 50 % over accent
    "empty_glyph": "#b9bac0",
    # file list in PyCharm colours (section 9)
    "file_mod": "#002daa",
    "file_ren": "#002daa",
    "file_add": "#0c7216",
    "file_unv": "#a92c3e",
    "file_del": "#6e6e73",
    "folder_icon": "#9aa0ab",
    "folder_act_hover": "#e6e8ee",
    # the search window E-04 (section 10, DEC-VCS-097)
    "hit": "#fde68a", "toggle_on": "#dbe8fb", "toggle_on_edge": "#b9d2f5", "placeholder": "#a0a0a6",
}


@dataclass(frozen=True)
class Type:
    size: int
    weight: str = "normal"
    color: str = COLORS["ink"]
    mono: bool = False
    overstrike: bool = False


TYPE = {
    # section 2
    "body": Type(13),
    "toolbar_repo": Type(15, "bold"),
    "chip": Type(12, color=COLORS["chip_ink"]),
    "side_header": Type(11, "bold", COLORS["dim"]),
    "side_name": Type(13, "bold"),
    "side_branch": Type(12, color=COLORS["dim"]),
    "badge": Type(12, "bold", COLORS["chip_ink"]),
    "group_header": Type(11, "bold", COLORS["dim"]),
    "group_count": Type(11, color=COLORS["dim"]),
    "file_name": Type(13, color=COLORS["file_mod"]),         # coloured by status (section 9)
    "file_name_del": Type(13, color=COLORS["file_del"], overstrike=True),
    "file_folder": Type(12, color=COLORS["dim"]),
    "folder_name": Type(13),
    "folder_count": Type(12, color=COLORS["dim"]),
    "folder_changes": Type(12, color=COLORS["mod"]),
    "segment": Type(12, color=COLORS["seg_ink"]),   # the View switch (DEC-VCS-092)  # changes inside a folder of the project tree (DEC-VCS-089)
    "folder_act": Type(16),
    "hint": Type(12, color=COLORS["dim"]),
    "kbd": Type(11, mono=True),
    "message": Type(13),
    "reason": Type(12, color=COLORS["dim"]),
    "statusbar": Type(12, color=COLORS["dim"]),
    # section 8
    "banner_title": Type(13, "bold", COLORS["conf"]),
    "banner_body": Type(12, mono=True),
    "busy_text": Type(12, color=COLORS["dim"]),
    "conflict_chip": Type(12, "bold", COLORS["conf"]),
    "merge_chip": Type(12, "bold", COLORS["accent"]),
    "empty_glyph": Type(26, color=COLORS["empty_glyph"]),
    "empty_head": Type(15, "bold"),
    "empty_sub": Type(13, color=COLORS["dim"]),
    "path": Type(12, color=COLORS["dim"], mono=True),
    "dialog_title": Type(15, "bold"),
    "dialog_note": Type(12, color=COLORS["dim"]),
    # section 10
    "toggle": Type(12, "bold", COLORS["chip_ink"]),
    "toggle_mono": Type(12, "bold", COLORS["chip_ink"], mono=True),
    "placeholder": Type(13, color=COLORS["placeholder"]),
}

# Section 3, in points. Pairs are (horizontal, vertical) unless named otherwise.
SPACE = {
    "titlebar_height": 38,
    "toolbar_pad": (14, 10), "toolbar_gap": 10,
    "chip_pad": (9, 2), "chip_gap": 6,
    "sidebar_width": 230, "sidebar_pad": (8, 10), "sidebar_item_gap": 2,
    "side_header_pad": (8, 6),
    "repo_item_pad": (8, 7), "repo_item_gap": 8, "repo_item_radius": 7, "repo_dot_column": 10,
    "state_dot": 9,
    "badge_min_width": 22, "badge_pad": (7, 1),
    "side_foot_pad": 8,
    "files_pad_top": 6,
    # file list (section 9)
    "group_header": (6, 15, 3),        # top, text line, bottom: 24
    "group_side": 16, "group_count_gap": 8,
    "row_height": 24, "row_side": 16, "hint_gap": 16,
    "indent_flat": 28, "indent_chevron": 28, "chevron_width": 12, "indent_icon": 46, "indent_child": 68,
    "folder_icon": (16, 13), "suffix_gap": 8,
    "folder_act": 20, "folder_act_radius": 5,
    "commit_pad": (14, 12), "commit_gap": (12, 8),
    "message_height": 64, "message_pad": (10, 8), "message_radius": 8,
    "commit_buttons_gap": 6,
    "reason_gap": 6,
    "statusbar_pad": (14, 6), "statusbar_gap": 14,
    "kbd_pad": (4, 0), "kbd_radius": 4,
    "line": 1,
    # section 8
    "seg_height": 24, "seg_pad": 2, "seg_item_pad": 12, "seg_separator": 10, "seg_label_gap": 8,
    "banner_margin": (12, 8, 4), "banner_pad": (12, 8), "banner_pad_right": 10, "banner_radius": 8, "banner_edge": 3, "banner_lines": 4,
    "busy_bar_height": 2, "busy_bar_share": 0.3, "busy_bar_period_ms": 1200,
    "empty_pad": (24, 40), "empty_gap": 6, "empty_text_width": 46,
    "dialog_width": 420, "dialog_list_height": 220,
    # section 10
    "search_window": (720, 420), "search_bar_pad": (14, 10), "search_gap": 10, "search_field_pad": (8, 4),
    "toggle": (24, 20), "toggle_radius": 5, "mask_width": 150, "mask_label_gap": 6,
    "where_share": 0.45, "where_gap": 12, "line_number_gap": 4, "results_pad_top": 4,
}

MONO_FAMILY = "Menlo"

_fonts: dict[str, tkfont.Font] = {}


def font(role: str) -> tkfont.Font:
    """A Tk font for a TYPE role, created once (needs a Tk root)."""
    if role not in _fonts:
        t = TYPE[role]
        family = MONO_FAMILY if t.mono else tkfont.nametofont("TkDefaultFont").actual("family")
        _fonts[role] = tkfont.Font(family=family, size=t.size, weight=t.weight, overstrike=t.overstrike)
    return _fonts[role]


def label(parent: tk.Misc, role: str, text: str = "", bg: str = COLORS["bg"], **options) -> tk.Label:
    t = TYPE[role]
    return tk.Label(parent, text=text, font=font(role), fg=t.color, bg=bg, bd=0, padx=0, pady=0, **options)
