"""Lanes of the branch graph, without git and without Tk (DES-VCS-066, rules H-20–H-35, AT-VCS-050–056).

Histories are written child first, as `git log --topo-order` gives them: `("M", "B F2")` is commit M with
the parents B and F2. Hashes are single letters; colours are indexes of the palette.
"""

from __future__ import annotations

import pytest

from vcs_lite.core.graph import PALETTE, Edge, GraphLayout, GraphRow
from vcs_lite.core.log import Commit


def history(*rows: tuple[str, str]) -> list[Commit]:
    return [Commit(name, tuple(parents.split()), "a", "a@x", 0, (), name) for name, parents in rows]


def lay_out(*rows: tuple[str, str]) -> dict[str, GraphRow]:
    commits = history(*rows)
    return dict(zip((c.hash for c in commits), GraphLayout().extend(commits)))


def check_no_line_crosses_a_commit(rows: list[GraphRow]) -> None:
    """H-27: a lane passing a row never runs through that row's commit, and no lane is drawn twice."""
    for row in rows:
        columns = [column for column, _ in row.through]
        assert row.column not in columns and len(columns) == len(set(columns))
        assert all(column != row.column for column, _ in row.joins)


# ---------- straight lines (H-20, H-23, H-29) ----------

def test_at_vcs_050_a_linear_history_is_one_straight_line():
    g = lay_out(("C", "B"), ("B", "A"), ("A", ""))
    assert [(g[x].column, g[x].color) for x in "CBA"] == [(0, 0)] * 3
    assert g["C"].up is None and g["C"].down == 0                 # a tip: nothing above, its line goes down
    assert g["B"].up == 0 and g["B"].down == 0
    assert g["A"].up == 0 and g["A"].down is None                 # the root ends the line (H-29)
    assert all(g[x].width == 1 for x in "CBA")


# ---------- merges and forks (H-21, H-24, H-31) ----------

def test_at_vcs_051_a_merged_branch_gets_its_own_lane_and_colour():
    rows = [("M", "B F2"), ("F2", "F1"), ("F1", "A"), ("B", "A"), ("A", "")]
    g = lay_out(*rows)
    assert (g["M"].column, g["M"].color, g["M"].forks) == (0, 0, ((1, 1),))
    assert [(g[x].column, g[x].color) for x in ("F2", "F1", "B")] == [(1, 1), (1, 1), (0, 0)]
    assert g["F2"].through == ((0, 0),) and g["B"].through == ((1, 1),)
    assert (g["A"].column, g["A"].joins, g["A"].down) == (0, ((1, 1),), None)   # the branch lane ends on A
    check_no_line_crosses_a_commit(list(g.values()))


def test_at_vcs_052_two_unmerged_branches_from_one_commit_meet_on_the_leftmost_lane():
    g = lay_out(("X", "A"), ("B", "A"), ("A", ""))
    assert (g["X"].column, g["B"].column) == (0, 1)
    assert g["B"].color != g["X"].color and g["B"].up is None
    assert (g["A"].column, g["A"].joins, g["A"].up) == (0, ((1, 1),), 0)


def test_at_vcs_053_an_octopus_reuses_the_lane_that_already_waits_for_a_parent():
    rows = [("Y", "P3"), ("O", "P1 P2 P3 P4"), ("P1", "R"), ("P2", "R"), ("P3", "R"), ("P4", "R"), ("R", "")]
    g = lay_out(*rows)
    assert (g["Y"].column, g["O"].column) == (0, 1)
    assert g["O"].forks == ((2, 2), (0, 0), (3, 3))               # P2 new, P3 on Y's lane, P4 new, in parent order
    assert [g[x].column for x in ("P1", "P2", "P3", "P4")] == [1, 2, 0, 3]
    assert g["R"].column == 0 and {c for c, _ in g["R"].joins} == {1, 2, 3}
    check_no_line_crosses_a_commit(list(g.values()))


def test_des_vcs_066_a_merge_of_a_branch_that_forked_far_below():
    rows = [("M", "B X"), ("B", "C"), ("C", "D"), ("X", "D"), ("D", "")]
    g = lay_out(*rows)
    assert g["M"].forks == ((1, 1),) and g["X"].column == 1
    assert g["B"].through == ((1, 1),) and g["C"].through == ((1, 1),)   # the waiting lane passes by B and C
    check_no_line_crosses_a_commit(list(g.values()))


def test_des_vcs_066_a_repeated_parent_counts_once():
    g = lay_out(("M", "A A"), ("A", ""))
    assert g["M"].forks == () and g["M"].down == 0


# ---------- roots and freed lanes (H-28, H-29, H-30, H-31) ----------

def test_at_vcs_054_unrelated_histories_and_a_grafted_root_are_drawn_apart():
    g = lay_out(("B", "A"), ("D2", "D1"), ("A", ""), ("D1", ""))
    assert [g[x].column for x in ("B", "D2", "A", "D1")] == [0, 1, 0, 1]
    assert all(not g[x].joins and not g[x].forks for x in g)
    assert g["A"].down is None and g["D1"].down is None


def test_des_vcs_066_a_freed_column_is_free_from_the_next_row_and_gets_a_new_colour():
    rows = [("X", "A"), ("A", ""), ("Y", "Z"), ("Z", "")]
    g = lay_out(*rows)
    assert (g["Y"].column, g["Y"].color) == (0, 1)                # column 0 again, the next colour
    assert g["Y"].width == 1                                       # free columns do not widen the graph


def test_des_vcs_066_a_column_freed_in_a_row_is_not_taken_in_that_row():
    rows = [("X", "A"), ("Y", "A"), ("A", "P Q"), ("P", ""), ("Q", "")]
    g = lay_out(*rows)
    assert g["A"].joins == ((1, 1),) and g["A"].forks == ((2, 2),)   # Q does not take column 1, freed by Y's lane


def test_des_vcs_066_colours_go_round_the_palette():
    tips = [(f"T{i}", "R") for i in range(PALETTE + 1)]
    g = lay_out(*tips, ("R", ""))
    assert [g[f"T{i}"].color for i in range(PALETTE + 1)] == list(range(PALETTE)) + [0]


# ---------- wide graphs and pages (H-32, H-33, H-35) ----------

def test_at_vcs_056_ten_branches_take_ten_columns_and_the_view_clips_them():
    g = lay_out(*[(f"T{i}", "R") for i in range(10)], ("R", ""))
    assert [g[f"T{i}"].column for i in range(10)] == list(range(10))
    assert g["T9"].width == 10 and g["R"].width == 10


def test_at_vcs_055_pages_extend_the_graph_without_changing_drawn_rows():
    rows = [("M", "B F2"), ("F2", "F1"), ("B", "C"), ("C", "D"), ("F1", "D"), ("D", "")]
    commits = history(*rows)
    whole = GraphLayout().extend(commits)
    layout = GraphLayout()
    first = layout.extend(commits[:3])
    assert first[2].through == ((1, 1),)                           # F2's lane runs to the bottom of the page
    assert first + layout.extend(commits[3:]) == whole


@pytest.mark.parametrize("seed", range(3))
def test_des_vcs_066_the_same_log_gives_the_same_graph(seed):
    rows = [("M", "B F2"), ("F2", "F1"), ("F1", "A"), ("B", "A"), ("A", "")]
    assert GraphLayout().extend(history(*rows)) == GraphLayout().extend(history(*rows))


# ---------- whole edges (DEC-VCS-123) ----------

def edges_of(*rows: tuple[str, str]) -> set[Edge]:
    layout = GraphLayout()
    layout.extend(history(*rows))
    return set(layout.edges)


def test_des_vcs_066_edges_run_from_a_commit_to_its_parent_through_one_lane():
    edges = edges_of(("M", "B F2"), ("F2", "F1"), ("F1", "A"), ("B", "A"), ("A", ""))
    assert edges == {Edge(0, 0, 1, 1, 1, 1),     # M to F2: a fork into lane 1
                     Edge(1, 1, 1, 2, 1, 1),     # F2 to F1
                     Edge(0, 0, 0, 3, 0, 0),     # M to B, straight down
                     Edge(3, 0, 0, 4, 0, 0),     # B to A
                     Edge(2, 1, 1, 4, 0, 1)}     # F1 to A: down lane 1, then over to A


def test_des_vcs_066_a_merge_into_a_lane_that_already_waits_gets_its_own_edge():
    edges = edges_of(("Y", "P"), ("O", "Q P"), ("Q", "P"), ("P", ""))
    assert Edge(0, 0, 0, 3, 0, 0) in edges                         # Y down to P
    assert Edge(1, 1, 0, 3, 0, 0) in edges                         # O over to Y's lane, then down to P


def test_at_vcs_055_open_edges_run_to_the_bottom_until_the_parent_comes():
    layout = GraphLayout()
    commits = history(("M", "B F"), ("F", "D"), ("B", "D"), ("D", ""))
    layout.extend(commits[:2])
    assert set(layout.open_edges()) == {Edge(0, 0, 0, None, None, 0), Edge(1, 1, 1, None, None, 1)}
    layout.extend(commits[2:])
    assert layout.open_edges() == [] and Edge(1, 1, 1, 3, 0, 1) in layout.edges
