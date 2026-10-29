"""Read-only audit of baseline code using disposable repos, notes and a fake clipboard."""
import argparse, json, os, subprocess, sys, tempfile, time
from pathlib import Path
from datetime import datetime
p=argparse.ArgumentParser();p.add_argument('--base',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
pkg=a.base.resolve()/'packages/vcs_lite';a.output=a.output.resolve();sys.path.insert(0,str(pkg/'src'))
os.environ.update(GIT_CONFIG_GLOBAL=os.devnull,GIT_CONFIG_NOSYSTEM='1',GIT_AUTHOR_NAME='Audit',GIT_AUTHOR_EMAIL='audit@example.invalid',GIT_COMMITTER_NAME='Audit',GIT_COMMITTER_EMAIL='audit@example.invalid')
from vcs_lite.core.gitcli import GitCli
from vcs_lite.core.gitlog import GitLog
from vcs_lite.core.log import LogQuery
from vcs_lite.core.changes import LineStats
records=[]
def record(name, expected, actual):
 records.append({'name':name,'expected':expected,'actual':actual,'pass':actual==expected})
with tempfile.TemporaryDirectory(prefix='vcs-stage4-probes-') as temp:
 folder=Path(temp);repo=folder/'repo';repo.mkdir()
 def git(*args):return subprocess.check_output(['git','-C',str(repo),*args],stderr=subprocess.PIPE).decode().strip()
 git('init','-q','-b','main')
 (repo/'a.txt').write_text('one\ntwo\n');git('add','.');git('commit','-qm','root')
 (repo/'a.txt').write_text('one\nthree\nfour\n');git('commit','-qam','change')
 git('checkout','-qb','side');(repo/'side.txt').write_text('side\n');git('add','.');git('commit','-qm','side')
 git('checkout','-q','main');(repo/'main.txt').write_text('main\n');git('add','.');git('commit','-qm','main')
 git('merge','-q','--no-ff','-m','merge','side');git('commit','-q','--allow-empty','-m','empty')
 (repo/'binary.dat').write_bytes(b'\0binary');git('add','.');git('commit','-qm','binary')
 git('mv','a.txt','renamed.txt');git('commit','-qm','rename')
 reader=GitLog(GitCli());commits=reader.page(repo,LogQuery(),0).commits
 totals=reader.commit_totals(repo,commits)
 for c in commits:
  d=reader.details(repo,c);expect=[sum(v.added for v in d.lines.values()),sum(v.removed for v in d.lines.values())]
  actual=totals.get(c.hash);record('totals_'+c.subject,expect,list(actual) if actual is not None else None)
 # Git allows ASCII RS in a pathname; log records use the same byte as separator.
 (repo/'odd\x1e.txt').write_text('x\ny\n');git('add','.');git('commit','-qm','record-separator-path')
 c=reader.page(repo,LogQuery(),0).commits[0]
 actual=reader.commit_totals(repo,(c,)).get(c.hash)
 record('totals_record_separator_path',[2,0],list(actual) if actual is not None else None)
 from vcs_lite.ui.main import build
 from vcs_lite.ui.main_window import MainWindow
 from vcs_lite.ui.notes import NotesPanel,NoteStore
 from vcs_lite.ui.widgets import draw_compact_counts
 from vcs_lite.ui import theme
 import tkinter as tk
 root,model,pump=build(folder/'settings.json');root.title('vcs-lite — przegląd, dane tymczasowe')
 root.update();window=next(x for x in root.winfo_children() if isinstance(x,MainWindow));panel=window.notes
 notes_a,notes_b=folder/'notes-a',folder/'notes-b';panel.select_repo(notes_a);root.update()
 def wait(seconds):
  end=time.monotonic()+seconds
  while time.monotonic()<end:root.update();time.sleep(.01)
 def edit(text):
  panel.editor.delete('1.0','end');panel.editor.insert('1.0',text);root.update()
 record('no_file_before_edit',False,panel.store.path(notes_a).exists())
 edit('auto Żółw');wait(.85);record('timer_saved','auto Żółw',panel.store.read(notes_a))
 edit('focus-save');panel.editor.event_generate('<FocusOut>');root.update()
 record('focus_out_saved','focus-save',panel.store.read(notes_a))
 captured=[];panel.clipboard=captured.append;panel.editor.tag_add('sel','1.0','1.5');panel.copy_text();panel.editor.tag_remove('sel','1.0','end');panel.copy_text()
 record('copy_selection_and_whole',['focus','focus-save'],captured)
 edit('\n'.join(str(i) for i in range(150)));panel.flush();panel.editor.mark_set('insert','70.0');panel.editor.yview_moveto(.5);root.update()
 expected=[panel.editor.index('insert'),round(panel.editor.yview()[0],3)]
 panel.select_repo(notes_b);root.update();panel.select_repo(notes_a);root.update()
 record('cursor_scroll_restored',expected,[panel.editor.index('insert'),round(panel.editor.yview()[0],3)])
 fresh=NotesPanel(root,NoteStore(panel.store.directory),clipboard=lambda _:None,on_hide=lambda:None);fresh.select_repo(notes_a)
 record('new_panel_reads_disk',panel.store.read(notes_a),fresh.editor.get('1.0','end-1c'));fresh.destroy()
 record('settings_adjacent_notes',str(folder/'notes'),str(panel.store.directory))
 root.update();record('notes_details_x_aligned',window.notes.winfo_rootx(),window.history.details.winfo_rootx())
 canvas=tk.Canvas(root)
 for name,lines,expected in [('text',LineStats(334,34),['−34','+334']),('zero',LineStats(),['−0','+0']),('binary',LineStats(kind='binary'),['binarne']),('unknown',LineStats(kind='unknown'),['—']),('conflict',LineStats(kind='conflict'),['konflikt'])]:
  canvas.delete('all');draw_compact_counts(canvas,lines,250,20)
  ids=canvas.find_all();record('renderer_'+name,expected,[canvas.itemcget(i,'text') for i in ids])
  if name=='text':
   record('renderer_colors',[theme.COLORS['del'],theme.COLORS['add']],[canvas.itemcget(i,'fill') for i in ids])
   font=theme.font('line_count');gap=round(canvas.coords(ids[0])[0]-font.measure('−34')-canvas.coords(ids[1])[0],1);record('renderer_gap',5.0,gap)
  if name=='zero':record('renderer_zero_colors',[theme.COLORS['dim']]*2,[canvas.itemcget(i,'fill') for i in ids])
 edit('pending close');original_write=panel.store.write
 def fail(*args):raise OSError('audit disk full')
 panel.store.write=fail
 root.tk.call(root.protocol('WM_DELETE_WINDOW'))
 record('close_error_keeps_window',True,bool(root.winfo_exists()))
 record('close_error_visible',True,'Nie zapisano' in panel.status.cget('text'))
 record('close_error_keeps_text','pending close',panel.editor.get('1.0','end-1c'))
 panel.store.write=original_write;root.tk.call(root.protocol('WM_DELETE_WINDOW'))
 record('successful_close_saved','pending close',NoteStore(folder/'notes').read(notes_a))
report={'baseline':'c19208dd4ce797ec5183c3127e832c5282a30aba','date':datetime.now().astimezone().isoformat(),'kind':'audit probes, not previously existing regression tests','records':records,'failed':[x['name'] for x in records if not x['pass']]}
(a.output/'probes.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
for r in records:print(r['name'], 'PASS' if r['pass'] else 'FAIL', '' if r['pass'] else repr(r['actual']))
