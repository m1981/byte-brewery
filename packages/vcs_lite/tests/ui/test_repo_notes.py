from pathlib import Path
import tkinter as tk
import pytest


def test_at_vcs_070_notes_save_and_switch_back_in_same_panel(tk_root, tmp_path):
    from vcs_lite.ui.notes import NotesPanel, NoteStore
    store = NoteStore(tmp_path / 'notes')
    panel = NotesPanel(tk_root, store, clipboard=lambda text: None, on_hide=lambda: None)
    a, b = tmp_path / 'a', tmp_path / 'b'
    panel.select_repo(a)
    assert not store.path(a).exists()
    panel.editor.insert('1.0', 'prompt A')
    panel.changed()
    panel.select_repo(b)
    assert store.read(a) == 'prompt A'
    assert panel.editor.get('1.0', 'end-1c') == ''
    panel.select_repo(a)
    assert panel.editor.get('1.0', 'end-1c') == 'prompt A'
    panel.destroy()


def test_req_vcs_046_notes_keep_text_on_save_failure(tk_root, tmp_path, monkeypatch):
    from vcs_lite.ui.notes import NotesPanel, NoteStore
    store = NoteStore(tmp_path / 'notes')
    panel = NotesPanel(tk_root, store, clipboard=lambda text: None, on_hide=lambda: None)
    panel.select_repo(tmp_path / 'repo')
    panel.editor.insert('1.0', 'keep me')
    panel.changed()
    monkeypatch.setattr(store, 'write', lambda *args: (_ for _ in ()).throw(OSError('disk full')))
    assert not panel.flush()
    assert panel.editor.get('1.0', 'end-1c') == 'keep me'
    panel.destroy()


def test_req_vcs_046_atomic_save_and_repo_identity(tmp_path, monkeypatch):
    from vcs_lite.ui.notes import NoteStore
    store = NoteStore(tmp_path / 'notes')
    a, b = tmp_path / 'a' / 'repo', tmp_path / 'b' / 'repo'
    store.write(a, 'Żółw 🐢')
    store.write(b, 'other')
    assert store.read(a) == 'Żółw 🐢' and store.read(b) == 'other'
    monkeypatch.setattr('vcs_lite.ui.notes.os.replace', lambda *args: (_ for _ in ()).throw(OSError('failed')))
    with pytest.raises(OSError):
        store.write(a, 'replacement')
    assert store.read(a) == 'Żółw 🐢'
    assert len(list(store.directory.iterdir())) == 2


def test_req_vcs_046_bad_encoding_does_not_overwrite_note(tk_root, tmp_path):
    from vcs_lite.ui.notes import NoteStore, NotesPanel
    store = NoteStore(tmp_path)
    repo = tmp_path / 'repo'
    store.path(repo).write_bytes(b'\xff')
    panel = NotesPanel(tk_root, store, clipboard=lambda value: None, on_hide=lambda: None)
    panel.select_repo(repo)
    assert str(panel.editor.cget('state')) == 'disabled'
    panel.flush()
    assert 'Nie odczytano' in panel.status.cget('text')
    assert store.path(repo).read_bytes() == b'\xff'
    panel.destroy()


@pytest.mark.parametrize('trigger', ['timer', 'focus_out'])
def test_req_vcs_046_notes_autosave_from_editor_event(tk_root, tmp_path, trigger):
    import time
    from vcs_lite.ui.notes import NotesPanel, NoteStore
    store = NoteStore(tmp_path / 'notes')
    panel = NotesPanel(tk_root, store, clipboard=lambda text: None, on_hide=lambda: None)
    repo = tmp_path / 'repo'
    try:
        panel.select_repo(repo)
        tk_root.update()
        panel.editor.insert('1.0', 'Żółw — szkic')
        tk_root.update()  # deliver <<Modified>>, without calling changed/flush directly
        assert not store.path(repo).exists()
        if trigger == 'focus_out':
            # Isolate FocusOut: the timer must not rescue a broken binding.
            if panel.pending:
                panel.after_cancel(panel.pending)
                panel.pending = None
            panel.editor.event_generate('<FocusOut>')
        deadline = time.monotonic() + (2 if trigger == 'timer' else .3)
        while not store.path(repo).exists() and time.monotonic() < deadline:
            tk_root.update()
            time.sleep(.01)
        assert store.path(repo).read_text(encoding='utf-8') == 'Żółw — szkic'
        assert panel.status.cget('text') == 'Zapisano'
    finally:
        panel.destroy()


def _notes_process(settings, mode):
    import os
    import subprocess
    import sys
    script = Path(__file__).resolve().parents[1] / 'notes_lifecycle.py'
    env = {**os.environ, 'PYTHONPATH': str(script.parent.parent / 'src'),
           'GIT_CONFIG_GLOBAL': os.devnull, 'GIT_CONFIG_NOSYSTEM': '1'}
    result = subprocess.run([sys.executable, str(script), str(settings), mode],
                            env=env, capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'PASS ' + mode in result.stdout


def _notes_settings(repo):
    from vcs_lite.core.settings import Settings, SettingsStore
    settings = repo.path.parent / 'settings.json'
    SettingsStore(settings).save(Settings(rootdir=str(repo.path.parent), repos=('repo',)))
    return settings


def test_at_vcs_070_notes_survive_independent_application_restart(repo):
    settings = _notes_settings(repo)
    _notes_process(settings, 'write')
    _notes_process(settings, 'read')


def test_req_vcs_046_close_failure_keeps_text_and_retry_saves(repo):
    settings = _notes_settings(repo)
    _notes_process(settings, 'failure')
    _notes_process(settings, 'read')
