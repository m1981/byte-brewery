"""The View switch in the toolbar and the View menu (REQ-VCS-025, DEC-VCS-091, DEC-VCS-092)."""

from __future__ import annotations

from test_main_window import root, world  # noqa: F401 - shared fixtures

from vcs_lite.ui.main_window import MainWindow


def test_req_vcs_025_the_switch_replaces_the_folder_checkbox_and_sits_before_pull(root, world):  # noqa: F811
    world.repo("alpha")
    window = MainWindow(root, world.start("alpha"))
    assert not hasattr(window, "folders_check")
    order = window.view_switch.master.pack_slaves()  # packed from the right: Odśwież, Pull, switch, label
    assert order.index(window.pull_button) < order.index(window.view_switch) < order.index(window.view_label)
    assert window.view_label.cget("text") == "Widok" and window.view_switch.value == "changes"


def test_req_vcs_025_choosing_a_view_in_the_switch_or_the_menu_is_saved(root, world):  # noqa: F811
    saved = []
    world.save_settings = saved.append
    world.repo("alpha")
    model = world.start("alpha")
    window = MainWindow(root, model)
    switch = window.view_switch
    switch.click(int(switch.coords(switch.find_withtag("label")[1])[0]))
    assert model.list_view == "folders" and saved[-1].list_view == "folders"
    menu = window.list_view_menu
    assert [menu.entrycget(i, "label") for i in range(3)] == ["Zmiany", "Foldery", "Projekt"]
    menu.invoke(2)
    assert model.list_view == "project" and switch.value == "project"
    assert window.view_menu.entrycget(0, "label") == "Lista plików"


def test_req_vcs_025_hovering_an_option_explains_it(root, world):  # noqa: F811
    world.repo("alpha")
    window = MainWindow(root, world.start("alpha"))
    switch = window.view_switch
    tips = []
    for x in [int(switch.coords(label)[0]) for label in switch.find_withtag("label")]:  # before redraws renew the items
        switch.hover(x)
        tips.append(window.view_tip())
    assert tips == ["Tylko zmienione pliki", "Zmienione pliki pogrupowane w folderach", "Zmiany i wszystkie pliki projektu"]
