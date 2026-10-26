"""P19 presentation and interaction using explicit file times, independent of test speed."""
import os
from datetime import datetime

import pytest
from test_main_window import root, world  # noqa: F401
from vcs_lite.core.status import Group
from vcs_lite.ui.main_window import MainWindow


@pytest.fixture
def recent(root, world):
    r=world.repo('alpha')
    for p in ['a.txt','z.txt','old.txt','deleted.txt']:
        r.write(p,'before\n')
    r.commit()
    for p in ['a.txt','z.txt','old.txt']:
        r.write(p,'after\nextra\n')
    (r.path/'deleted.txt').unlink()
    now=datetime(2026,10,26,21,19,6)
    world.clock=lambda:now
    for p,age in [('z.txt',300),('a.txt',360),('old.txt',7200)]:
        stamp=int((now.timestamp()-age)*1e9)
        os.utime(r.path/p,ns=(stamp,stamp))
    model=world.start('alpha');window=MainWindow(root,model);world.select('alpha')
    return window,model,r,world


def test_at_vcs_066_sorted_rows_headers_counts_and_nonselectable_separators(recent):
    window,model,r,world=recent;fl=window.file_list
    assert [row.path for row in fl.rows()]==['z.txt','a.txt','old.txt','deleted.txt']
    c=fl.canvas
    assert [c.itemcget(i,'text') for i in c.find_withtag('time_label')]==['5 min temu','2 h temu','Czas nieznany']
    assert '2 pliki' in fl.tooltip_at(fl.rows()[0].top-5)
    fl.select_key((Group.CHANGES,'z.txt'))
    fl.click(fl.rows()[0].top-5)
    assert fl.selected_key==(Group.CHANGES,'z.txt')
    fl.press_down();assert fl.selected_key==(Group.CHANGES,'a.txt')
    before=world.git.call_count
    fl.hover(fl.rows()[0].top+3);fl.render(model)
    assert world.git.call_count==before
    fl.select_key((Group.CHANGES,'z.txt'));fl.press_space();world.worker.settle()
    assert fl.selected_key==(Group.CHANGES,'a.txt')


def test_req_vcs_042_refresh_preserves_selection_and_other_views(recent):
    window,model,r,world=recent;fl=window.file_list
    fl.select_key((Group.CHANGES,'a.txt'))
    stamp=int(datetime(2026,10,26,21,18).timestamp()*1e9);os.utime(r.path/'old.txt',ns=(stamp,stamp))
    model.refresh('alpha');world.worker.settle()
    assert fl.rows()[0].path=='old.txt' and fl.selected_key==(Group.CHANGES,'a.txt')
    for view in ('folders','project'):
        window.set_list_view(view);world.worker.settle()
        assert not fl.canvas.find_withtag('time_label')
        assert not fl.canvas.find_withtag('line_count')


def test_req_vcs_043_columns_stay_aligned_and_narrow_hints_move_to_tooltip(recent):
    window,model,r,world=recent;fl=window.file_list;c=fl.canvas
    row=fl.rows()[0];fl.hover(row.top+3)
    counts=[i for i in c.find_withtag('line_count') if c.type(i)=='text']
    assert counts
    assert {c.itemcget(i,'text') for i in counts} >= {'+2','−1','+0'}
    assert max(c.coords(i)[0] for i in counts)==fl._width()-16
    fl._width=lambda:400
    fl.render(model);fl.hover(fl.rows()[0].top+3)
    assert not c.find_withtag('hint')
    assert 'spacja' in fl.tooltip_at(fl.rows()[0].top+3)
    assert max(c.bbox(i)[2] for i in c.find_withtag('line_count'))<=402


def test_des_vcs_073_model_publishes_details_with_status_only_after_worker(recent):
    window,model,r,world=recent
    change=model.files(Group.CHANGES)[0]
    old=model.change_details(change)
    r.write(change.path,'new\nlines\nhere\n')
    model.refresh('alpha')
    assert model.change_details(change)==old
    world.worker.settle()
    assert model.change_details(change).lines.added==3


def test_des_vcs_074_large_counts_fit_cells_with_full_value_in_tooltip(recent):
    from dataclasses import replace
    from vcs_lite.core.changes import LineStats
    window,model,r,world=recent;fl=window.file_list;c=fl.canvas
    key=(Group.CHANGES,'z.txt')
    model.view('alpha').details[key]=replace(model.view('alpha').details[key],lines=LineStats(12345678,1234567))
    fl.render(model)
    row=fl.rows()[0]
    counts=[i for i in c.find_withtag('line_count') if abs(c.coords(i)[1]-(row.top+12))<1]
    assert len(counts)==2
    assert all(c.bbox(i)[2]-c.bbox(i)[0]<=56 for i in counts)
    assert '12\u202f345\u202f678' in fl.tooltip_at(row.top+3)
