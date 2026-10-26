"""P17/P19: deterministic time groups and read-only Git line statistics."""
import hashlib
import os
from datetime import datetime, timezone

import pytest

from conftest import GIT_ENV
from vcs_lite.core.changes import ChangeDetails, LineStats, time_groups, relative_time
from vcs_lite.core.gitdetails import GitChangeReader, parse_numstat
from vcs_lite.core.gitcli import GitCli, GitResult
from vcs_lite.core.repo import GitRepo
from vcs_lite.core.status import FileChange, Group, Side


def change(path):
    return FileChange(path, Group.CHANGES, 'M', Side.INDEX, Side.WORKTREE)


def test_at_vcs_064_orders_ties_missing_and_splits_gap_and_span():
    seconds = {'z': 2000, 'a': 2000, 'b': 1700, 'c': 1400, 'd': 1100, 'e': 1000, 'f': 699}
    items = [change(p) for p in ['missing-z', 'f', 'd', 'z', 'c', 'a', 'b', 'e', 'missing-a']]
    info = {c.path: ChangeDetails(seconds[c.path] * 10**9) for c in items if c.path in seconds}
    groups = time_groups(items, lambda c: info.get(c.path, ChangeDetails()))
    assert [[c.path for c in g.files] for g in groups] == [['a','z','b','c','d'], ['e'], ['f'], ['missing-a','missing-z']]
    assert (groups[0].newest, groups[0].oldest) == (2000*10**9, 1100*10**9)
    assert groups[-1].newest is None


@pytest.mark.parametrize('seconds,label', [(0,'przed chwilą'),(59,'przed chwilą'),(60,'1 min temu'),
    (3599,'59 min temu'),(3600,'1 h temu'),(86399,'23 h temu'),(86400,'1 dzień temu'),
    (6*86400,'6 dni temu'),(7*86400,'19.10'),(-1,'czas z przyszłości')])
def test_req_vcs_042_relative_age_boundaries(seconds, label):
    now = datetime(2026,10,26,12,tzinfo=timezone.utc)
    assert relative_time(int((now.timestamp()-seconds)*10**9), now) == label
    assert relative_time(None, now) == 'Czas nieznany'
    assert relative_time(int(datetime(2025,1,1,tzinfo=timezone.utc).timestamp()*10**9),now) == '01.01.2025'


def test_des_vcs_073_numstat_handles_tabs_newlines_renames_and_binary():
    out = parse_numstat(b'12\t3\ta\tb\n.txt\0-\t-\tb.bin\0' b'0\t0\t\0old\t.txt\0new\n.txt\0')
    assert out['a\tb\n.txt'] == LineStats(12,3)
    assert out['b.bin'].kind == 'binary'
    assert out['new\n.txt'] == LineStats(0,0)
    with pytest.raises(ValueError):
        parse_numstat(b'12\tbad\tfile\0')


def read(repo):
    git = GitCli(env=GIT_ENV)
    status = GitRepo(repo.path, git).status()
    return status, GitChangeReader(git).read(repo.path, status)


def test_at_vcs_065_counts_each_diff_side_and_preserves_index(repo):
    repo.write('both.txt','a\nb\n'); repo.write('gone.txt','x\ny'); repo.write('old\tname.txt','same\n'*8)
    repo.commit()
    repo.write('both.txt','a\nb\nc\n'); repo.git('add','both.txt')
    repo.write('both.txt','a\nc\n')
    repo.git('mv','old\tname.txt','new\nname.txt')
    (repo.path/'gone.txt').unlink()
    repo.write('fresh.txt','one\ntwo'); repo.write('empty.txt','')
    (repo.path/'binary').write_bytes(b'a\0b\n')
    (repo.path/'link').symlink_to('missing-target')
    before=hashlib.sha256((repo.path/'.git/index').read_bytes()).digest()
    _, info=read(repo)
    assert info[Group.STAGED,'both.txt'].lines == LineStats(1,0)
    assert info[Group.CHANGES,'both.txt'].lines == LineStats(0,1)
    assert info[Group.STAGED,'new\nname.txt'].lines == LineStats(0,0)
    assert info[Group.CHANGES,'gone.txt'].lines == LineStats(0,2)
    assert info[Group.CHANGES,'gone.txt'].mtime_ns is None
    assert info[Group.UNVERSIONED,'fresh.txt'].lines == LineStats(2,0)
    assert info[Group.UNVERSIONED,'empty.txt'].lines == LineStats(0,0)
    assert info[Group.UNVERSIONED,'link'].lines == LineStats(1,0)
    assert info[Group.UNVERSIONED,'binary'].lines.kind == 'binary'
    assert info[Group.STAGED,'both.txt'].mtime_ns == info[Group.CHANGES,'both.txt'].mtime_ns
    assert hashlib.sha256((repo.path/'.git/index').read_bytes()).digest() == before
    repo.write('new\nname.txt','same\n'*8+'extra\n');repo.git('add','--','new\nname.txt')
    assert read(repo)[1][Group.STAGED,'new\nname.txt'].lines == LineStats(1,0)


def test_req_vcs_043_initial_repo_binary_attributes_mode_and_intent_to_add(repo):
    repo.write('first','first\n'); repo.git('add','first')
    assert read(repo)[1][Group.STAGED,'first'].lines == LineStats(1,0)
    repo.write('.gitattributes','*.bin -diff\n'); repo.write('data.bin','old\n');repo.commit()
    repo.write('data.bin','new\n'); (repo.path/'first').chmod(0o755)
    repo.write('intent','a\nb\n');repo.git('add','-N','intent')
    info=read(repo)[1]
    assert info[Group.CHANGES,'data.bin'].lines.kind == 'binary'
    assert info[Group.CHANGES,'first'].lines == LineStats(0,0)
    assert info[Group.CHANGES,'intent'].lines == LineStats(2,0)


def test_req_vcs_043_conflicts_and_errors_are_never_zero(repo):
    repo.write('x','one\n');repo.commit();repo.write('x','two\n')
    status=GitRepo(repo.path,GitCli(env=GIT_ENV)).status()
    class Broken(GitCli):
        def run(self,*args,**kwargs):
            return GitResult(('diff',),1,b'','read failed')
    details=GitChangeReader(Broken()).read(repo.path,status)
    assert details[Group.CHANGES,'x'].lines.kind == 'unknown'
    assert 'read failed' in details[Group.CHANGES,'x'].lines.reason
    from dataclasses import replace
    c=FileChange('x',Group.CONFLICTS,'UU',None,None)
    info=GitChangeReader(Broken()).read(repo.path,replace(status,changes=(c,)))
    assert info[Group.CONFLICTS,'x'].lines.kind == 'conflict'


def test_des_vcs_073_external_diff_and_textconv_are_not_executed(repo):
    marker=repo.path/'called'
    script=repo.path/'external.sh';script.write_text('#!/bin/sh\ntouch "'+str(marker)+'"\n');script.chmod(0o755)
    repo.git('config','diff.external',str(script));repo.git('config','diff.custom.textconv',str(script))
    repo.write('.gitattributes','*.txt diff=custom\n');repo.write('a.txt','one\n');repo.commit();repo.write('a.txt','two\n')
    assert read(repo)[1][Group.CHANGES,'a.txt'].lines == LineStats(1,1)
    assert not marker.exists()


def test_req_vcs_043_disappearing_untracked_file_keeps_other_results(repo):
    repo.write('vanished','a\n');repo.write('kept','b\n')
    git=GitCli(env=GIT_ENV);status=GitRepo(repo.path,git).status()
    (repo.path/'vanished').unlink()
    info=GitChangeReader(git).read(repo.path,status)
    assert info[Group.UNVERSIONED,'vanished'].lines.kind == 'unknown'
    assert info[Group.UNVERSIONED,'vanished'].lines.reason
    assert info[Group.UNVERSIONED,'kept'].lines == LineStats(1,0)
