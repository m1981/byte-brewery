"""Repository scratch notes and their atomic local persistence.

Trace: DES-VCS-080, REQ-VCS-046
"""
from pathlib import Path
import hashlib
import os
import tempfile
import tkinter as tk
from vcs_lite.ui import theme
from vcs_lite.ui.scrolling import ScrollPane


class NoteStore:
    def __init__(self, directory: Path):
        self.directory = directory

    def path(self, repo: Path) -> Path:
        key = hashlib.sha256(os.fsencode(str(repo.resolve()))).hexdigest()
        return self.directory / (key + '.md')

    def read(self, repo: Path) -> str:
        try:
            return self.path(repo).read_text(encoding='utf-8')
        except FileNotFoundError:
            return ''

    def write(self, repo: Path, text: str) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        name = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=self.directory, delete=False) as out:
                name = out.name
                out.write(text)
                out.flush()
                os.fsync(out.fileno())
            os.replace(name, self.path(repo))
        finally:
            if name and os.path.exists(name):
                os.unlink(name)


class NotesPanel(tk.Frame):
    def __init__(self, master, store, *, clipboard, on_hide):
        super().__init__(master, bg=theme.COLORS['bg'], cursor='arrow')
        self.store, self.clipboard = store, clipboard
        self.repo = None
        self.drafts = {}
        self.dirty = set()
        self.states = {}
        self.read_errors = set()
        self.pending = None
        head = tk.Frame(self, bg=theme.COLORS['panel'], height=28)
        head.pack(fill=tk.X)
        head.pack_propagate(False)
        tk.Label(head, text='Notatka', bg=theme.COLORS['panel'], font=theme.font('body')).pack(side=tk.LEFT, padx=10)
        tk.Button(head, text='›', command=on_hide, highlightbackground=theme.COLORS['panel']).pack(side=tk.RIGHT)
        self.copy = tk.Button(head, text='Kopiuj całość', command=self.copy_text, highlightbackground=theme.COLORS['panel'])
        self.copy.pack(side=tk.RIGHT)
        self.context = tk.Label(self, anchor=tk.W, bg=theme.COLORS['bg'], fg=theme.COLORS['dim'], font=theme.font('history_meta'))
        self.context.pack(fill=tk.X, padx=10, pady=4)
        self.status = tk.Label(self, anchor=tk.W, bg=theme.COLORS['panel'], fg=theme.COLORS['dim'], font=theme.font('history_meta'))
        self.status.pack(side=tk.BOTTOM, fill=tk.X)
        scroller = ScrollPane(self, bg=theme.COLORS['bg'])
        scroller.pack(fill=tk.BOTH, expand=True)
        self.editor = tk.Text(scroller, wrap=tk.WORD, undo=True, exportselection=False, width=25,
                              bd=0, highlightthickness=0, padx=12, pady=8, font=theme.font('body'))
        scroller.attach(self.editor)
        self.editor.bind('<<Modified>>', self.changed)
        self.editor.bind('<FocusOut>', lambda e: self.flush())
        self.editor.bind('<<Selection>>', lambda e: self.copy.configure(text='Kopiuj zaznaczenie' if self.editor.tag_ranges('sel') else 'Kopiuj całość'))
        self.editor.configure(state=tk.DISABLED)

    def changed(self, event=None):
        if self.repo is None or self.repo in self.read_errors or not self.editor.edit_modified():
            return
        self.editor.edit_modified(False)
        self.dirty.add(self.repo)
        self.drafts[self.repo] = self.editor.get('1.0', 'end-1c')
        self.status.configure(text='Zapisywanie…', fg=theme.COLORS['dim'])
        if self.pending:
            self.after_cancel(self.pending)
        self.pending = self.after(700, self.flush)

    def flush(self):
        if self.pending:
            self.after_cancel(self.pending)
            self.pending = None
        self.changed()
        if self.pending:
            self.after_cancel(self.pending)
            self.pending = None
        for repo in tuple(self.dirty):
            try:
                if self.store:
                    self.store.write(repo, self.drafts[repo])
                self.dirty.remove(repo)
            except OSError as exc:
                self.status.configure(text=f'Nie zapisano {repo.name}: {exc}', fg=theme.COLORS['del'])
                return False
        if self.repo not in self.read_errors:
            self.status.configure(text='Zapisano' if self.repo else '', fg=theme.COLORS['dim'])
        return True

    def select_repo(self, repo):
        repo = Path(repo).resolve() if repo else None
        if repo == self.repo:
            return
        saved = self.flush()
        if self.repo:
            self.states[self.repo] = (self.editor.index('insert'), self.editor.yview()[0])
        self.repo = repo
        self.editor.configure(state=tk.NORMAL)
        self.editor.delete('1.0', tk.END)
        if repo:
            if repo not in self.drafts:
                try:
                    self.drafts[repo] = self.store.read(repo) if self.store else ''
                except (OSError, UnicodeError) as exc:
                    self.read_errors.add(repo)
                    self.status.configure(text=f'Nie odczytano: {exc}', fg=theme.COLORS['del'])
            self.editor.insert('1.0', self.drafts.get(repo, ''))
        self.editor.edit_reset()
        self.editor.edit_modified(False)
        if repo in self.states:
            cursor, scroll = self.states[repo]
            self.editor.mark_set('insert', cursor)
            self.editor.yview_moveto(scroll)
        self.context.configure(text=repo.name if repo else 'Wybierz repo')
        if repo is None or repo in self.read_errors:
            self.editor.configure(state=tk.DISABLED)
        elif saved:
            self.status.configure(text='Notatka repo' if self.drafts.get(repo) else 'Pusta notatka')

    def copy_text(self):
        if self.editor.tag_ranges('sel'):
            value = self.editor.get('sel.first', 'sel.last')
        else:
            value = self.editor.get('1.0', 'end-1c')
        self.clipboard(value)

    def destroy(self):
        if self.pending:
            self.after_cancel(self.pending)
            self.pending = None
        super().destroy()
