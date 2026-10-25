"""Lanes of the branch graph: which column and colour each commit and line takes (DES-VCS-066).

Commits come child first (`git log --topo-order`). A lane is a column waiting for one commit. A commit
stands on the leftmost lane waiting for it; the other lanes waiting for it end there. Its first parent
takes over its lane, so first-parent lines are straight; other parents go to a lane already waiting for
them or to the first free column (P. Vigier, "Commit graph drawing algorithms", 2019). A lane keeps its
column until it reaches its commit, so no line runs through another commit. The state outlives a page,
so the next page continues the drawing (H-32). Rows hold only columns and colour indexes: the panel
turns them into points and decides about clipping (H-33) and filtering (H-34).

Trace: DES-VCS-066, REQ-VCS-038, DEC-VCS-117, DEC-VCS-120, DEC-VCS-123
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from vcs_lite.core.log import Commit

PALETTE = 8   # colours of the lanes, in turn (H-31)

Line = tuple[int, int]   # (column, colour)


@dataclass(frozen=True)
class GraphRow:
    column: int
    color: int
    up: int | None              # colour of the lane coming down into the commit, None for a branch tip
    down: int | None            # colour of the line to the first parent, None for a root
    joins: tuple[Line, ...]     # other lanes that end on the commit: from their column at the top
    forks: tuple[Line, ...]     # lanes of further parents: to their column at the bottom
    through: tuple[Line, ...]   # lanes passing the row from top to bottom
    width: int                  # columns the row uses


@dataclass(frozen=True)
class Edge:
    """A line from a commit to its parent (DEC-VCS-123): it leaves the child's column for the lane's at
    once, runs down the lane, and enters the parent's column on the last row. `to_row` is None while the
    parent is not read yet (H-32)."""

    from_row: int
    from_col: int
    lane: int
    to_row: int | None
    to_col: int | None
    color: int


@dataclass
class _Lane:
    waits_for: str
    color: int
    starts: list[tuple[int, int]]   # (row, column) of each commit whose edge runs down this lane


class GraphLayout:
    def __init__(self) -> None:
        self._lanes: list[_Lane | None] = []
        self._colors = 0
        self._row = 0
        self.edges: list[Edge] = []     # finished edges, in the order their parents came

    def extend(self, commits: Iterable[Commit]) -> list[GraphRow]:
        return [self._place(commit) for commit in commits]

    def open_edges(self) -> list[Edge]:
        """Edges whose parents are not read yet: they run to the bottom of the list."""
        return [Edge(row, column, lane, None, None, waiting.color)
                for lane, waiting in enumerate(self._lanes) if waiting is not None for row, column in waiting.starts]

    def _new_color(self) -> int:
        color = self._colors % PALETTE
        self._colors += 1
        return color

    def _free_column(self, taken: set[int]) -> int:
        for column, lane in enumerate(self._lanes):
            if lane is None and column not in taken:
                return column
        self._lanes.append(None)
        return len(self._lanes) - 1

    def _place(self, commit: Commit) -> GraphRow:
        lanes = self._lanes
        waiting = [i for i, lane in enumerate(lanes) if lane is not None and lane.waits_for == commit.hash]
        through = tuple((i, lane.color) for i, lane in enumerate(lanes) if lane is not None and i not in waiting)
        freed = set(waiting[1:])                       # free again only from the next row (H-28)
        if waiting:
            column = waiting[0]
            color = up = lanes[column].color
        else:
            column, up = self._free_column(set()), None
            color = self._new_color()
        joins = tuple((i, lanes[i].color) for i in waiting[1:])
        row_index = self._row
        self._row += 1
        for i in waiting:
            self.edges += [Edge(row, col, i, row_index, column, lanes[i].color) for row, col in lanes[i].starts]
            lanes[i] = None

        parents = list(dict.fromkeys(commit.parents))
        down = None
        if parents:
            lanes[column] = _Lane(parents[0], color, [(row_index, column)])
            down = color
        else:
            freed.add(column)                          # a root ends its lane (H-29)
        forks = []
        for parent in parents[1:]:
            existing = next((i for i, lane in enumerate(lanes) if lane is not None and lane.waits_for == parent), None)
            if existing is None:
                existing = self._free_column(freed | {column})
                lanes[existing] = _Lane(parent, self._new_color(), [])
            lanes[existing].starts.append((row_index, column))
            forks.append((existing, lanes[existing].color))

        while lanes and lanes[-1] is None:             # free columns on the right do not widen the graph
            lanes.pop()
        used = [column, *(i for i, _ in through), *(i for i, _ in joins), *(i for i, _ in forks)]
        return GraphRow(column, color, up, down, joins, tuple(forks), through, max(used) + 1)
