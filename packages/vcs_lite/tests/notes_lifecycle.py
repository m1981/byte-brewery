"""Subprocess exercise of the real composition root; only temporary settings are passed in."""
import sys
from pathlib import Path

from vcs_lite.ui.main import build
from vcs_lite.ui.main_window import MainWindow

TEXT = 'Zażółć gęślą jaźń 🐢\nPomysł dla agenta\n'


def run(settings, mode):
    root, model, _ = build(settings)
    root.withdraw()
    try:
        window = next(w for w in root.winfo_children() if isinstance(w, MainWindow))
        panel = window.notes
        panel.clipboard = lambda text: None
        model.select('repo')
        repo = settings.parent / 'repo'
        assert panel.repo == repo.resolve()
        if mode == 'read':
            assert panel.editor.get('1.0', 'end-1c') == TEXT
        else:
            panel.editor.insert('1.0', TEXT)
        close = root.protocol('WM_DELETE_WINDOW')
        if mode == 'failure':
            write = panel.store.write
            def fail(*args):
                raise OSError('simulated disk full')
            panel.store.write = fail
            window.toggle_notes()
            assert window._notes_hidden
            root.tk.call(close)
            assert root.tk.call('info', 'commands', '.') != '', 'window closed despite failed save'
            assert not window._notes_hidden
            assert panel.editor.get('1.0', 'end-1c') == TEXT
            assert 'Nie zapisano' in panel.status.cget('text')
            assert not panel.store.path(repo).exists()
            panel.store.write = write
        root.tk.call(close)
        assert root.tk.call('info', 'commands', '.') == '', 'window did not close after successful save'
        assert panel.store.path(repo).read_text(encoding='utf-8') == TEXT
        print('PASS', mode, flush=True)
    finally:
        if root.tk.call('info', 'commands', '.') != '':
            root.destroy()


if __name__ == '__main__':
    run(Path(sys.argv[1]), sys.argv[2])
