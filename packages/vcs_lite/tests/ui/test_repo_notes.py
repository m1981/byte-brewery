from pathlib import Path
import tkinter as tk
import pytest


def test_at_vcs_070_notes_save_switch_and_reopen(tk_root, tmp_path):
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
