"""Menu Widok → Motyw diffu Markdown (DEC-VCS-083, REQ-VCS-031)."""

from __future__ import annotations

from test_main_window import root, world  # noqa: F401 - shared fixtures

from vcs_lite.ui.main_window import MainWindow


def test_req_vcs_031_the_view_menu_chooses_the_markdown_theme(root, world):  # noqa: F811
    saved = []
    world.save_settings = saved.append
    world.repo("alpha")
    model = world.start("alpha")
    window = MainWindow(root, model)
    top = window.winfo_toplevel()
    assert top.cget("menu") == str(window.menubar)
    assert window.menubar.entrycget(0, "label") == "Widok"
    assert window.view_menu.entrycget(1, "label") == "Motyw diffu Markdown"  # after „Lista plików” (DEC-VCS-091)
    menu = window.theme_menu
    assert [menu.entrycget(i, "label") for i in range(3)] == ["Systemowy", "Jasny", "Ciemny"]
    assert window.markdown_theme.get() == "system"
    menu.invoke(2)
    assert model.markdown_theme == "dark" and saved[-1].markdown_theme == "dark"
