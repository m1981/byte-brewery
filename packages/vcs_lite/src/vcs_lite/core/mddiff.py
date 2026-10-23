"""Markdown compared as a document: blocks aligned first, then words inside changed blocks.

A block is one paragraph-sized piece: heading, paragraph, list item (its first paragraph, without the nested
list), table row, code block, front matter or rule. Blocks are equal when their text is equal after collapsing
whitespace, so re-wrapped lines are not a change. Inside a changed stretch, blocks of the same kind are paired
by similarity; changed words are wrapped in private-use sentinels that the page renderer turns into <ins>/<del>.

Trace: DES-VCS-049, DES-VCS-056, REQ-VCS-031, REQ-VCS-033, DEC-VCS-078, DEC-VCS-081, DEC-VCS-088
"""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field
from enum import Enum

from markdown_it import MarkdownIt

# Sentinels survive Markdown rendering as plain characters; nothing in a real file uses them.
INS_START, INS_END, DEL_START, DEL_END = "", "", "", ""

# Words for the inline diff: links, images and code spans stay whole (a mark inside them would break them);
# punctuation and <br> stand apart, so "robocza." → "ostateczna." and "stara<br>D2" → "nowa<br>D2" change one word.
WORD = re.compile(r"\s*(?:!?\[[^\]]*\]\([^)]*\)|`[^`]*`|<br\s*/?>|[^\s.,;:!?<]+|<|[.,;:!?]+)", re.IGNORECASE)
BR_TAG = re.compile(r"<br\s*/?>", re.IGNORECASE)
TASK = re.compile(r"^\[([ xX])\](?=\s)")
PAIRING = 0.5            # blocks this similar are one changed block, not a removal and an addition
PAIRING_LIMIT = 4000     # old × new blocks in one changed stretch; above it everything is removed and added

def _line_break_tag(state, silent: bool) -> bool:
    """<br> is the one HTML tag kept: Markdown has no other line break inside a table cell (DEC-VCS-088).
    As a parser rule, it stays literal inside code; any other tag stays text (`html` is off)."""
    match = BR_TAG.match(state.src, state.pos) if state.src[state.pos] == "<" else None
    if not match:
        return False
    if not silent:
        state.push("hardbreak", "br", 0)
    state.pos = match.end()
    return True


MARKDOWN = MarkdownIt("commonmark", {"html": False}).enable("table").enable("strikethrough")
MARKDOWN.inline.ruler.before("html_inline", "line_break_tag", _line_break_tag)


class State(Enum):
    SAME = "same"
    ADD = "add"
    DEL = "del"
    MOD = "mod"


@dataclass(frozen=True)
class Block:
    kind: str                  # heading, paragraph, item, header, row, code, meta, hr
    src: str                   # inline Markdown, code text or front matter
    key: str                   # equality: whitespace collapsed (code and front matter compared exactly)
    depth: int = 0             # list nesting
    ordered: bool = False
    number: str = ""           # ordered list item number
    tag: str = ""              # h1–h6, or the code language
    cells: tuple[str, ...] = ()  # table rows
    table: int = 0             # rows of one table share it
    quote: int = 0             # blockquote nesting
    line: int = field(default=0, compare=False)   # first and last line in the file, 1-based (DES-VCS-056)
    end: int = field(default=0, compare=False)


@dataclass(frozen=True)
class Change:
    state: State
    block: Block               # the block shown: the new one, or the old one when removed
    old: Block | None = None   # the old block of a modified pair
    marked: str | None = None  # new inline source with word sentinels (text blocks of a modified pair)


def parse_blocks(text: str) -> list[Block]:
    meta, body = _split_front_matter(text)
    offset = text[: len(text) - len(body)].count("\n")   # lines before the body: front matter and blank lines
    blocks = [Block("meta", meta, meta, line=1, end=meta.count("\n") + 3)] if meta is not None else []
    tokens = MARKDOWN.parse(body)
    lists: list[bool] = []          # ordered flags of the open lists
    quote = table = 0
    item_number: str | None = None  # set by an item opening, taken by its first paragraph
    for index, tok in enumerate(tokens):
        kind = tok.type
        if kind in ("bullet_list_open", "ordered_list_open"):
            lists.append(kind == "ordered_list_open")
        elif kind in ("bullet_list_close", "ordered_list_close"):
            lists.pop()
        elif kind in ("blockquote_open", "blockquote_close"):
            quote += tok.nesting
        elif kind == "list_item_open":
            item_number = tok.info
        elif kind == "paragraph_open":
            content = tokens[index + 1].content
            if item_number is None:
                blocks.append(Block("paragraph", content, _collapse(content), len(lists), quote=quote, **_source_lines(tok, offset)))
            else:
                content = TASK.sub(lambda m: "☐" if m[1] == " " else "☑", content)
                blocks.append(Block("item", content, _collapse(content), len(lists), lists[-1], item_number,
                                    quote=quote, **_source_lines(tok, offset)))
                item_number = None
        elif kind == "heading_open":
            content = tokens[index + 1].content
            blocks.append(Block("heading", content, f"{tok.tag} {_collapse(content)}", len(lists), tag=tok.tag,
                                quote=quote, **_source_lines(tok, offset)))
        elif kind in ("fence", "code_block"):
            blocks.append(Block("code", tok.content, tok.content, len(lists), tag=tok.info.strip(), quote=quote,
                                **_source_lines(tok, offset)))
            item_number = None
        elif kind == "hr":
            blocks.append(Block("hr", "", "---", quote=quote, **_source_lines(tok, offset)))
        elif kind == "tr_open":
            header = tokens[index - 1].type == "thead_open"
            if header:
                table += 1
            cells = tuple(_row_cells(tokens, index))
            blocks.append(Block("header" if header else "row", " | ".join(cells), _collapse(" | ".join(cells)),
                                cells=cells, table=table, quote=quote, **_source_lines(tok, offset)))
    return blocks


def mark_words(old: str, new: str) -> str:
    """The new inline source with removed words kept and changed words wrapped in sentinels."""
    a, b = WORD.findall(old), WORD.findall(new)
    matcher = difflib.SequenceMatcher(None, [w.strip() for w in a], [w.strip() for w in b], autojunk=False)
    parts = []
    for op, i1, i2, j1, j2 in matcher.get_opcodes():
        if op == "equal":
            parts.append("".join(b[j1:j2]))
            continue
        if i2 > i1:
            parts.append(_leading_space(a[i1]) + DEL_START + "".join(a[i1:i2]).strip() + DEL_END)
        if j2 > j1:
            space = _leading_space(b[j1]) or (" " if i2 > i1 else "")  # a replaced first word: old and new apart
            parts.append(space + INS_START + "".join(b[j1:j2]).strip() + INS_END)
    return "".join(parts)


def diff_blocks(old_text: str, new_text: str) -> list[Change]:
    old, new = parse_blocks(old_text), parse_blocks(new_text)
    matcher = difflib.SequenceMatcher(None, [b.key for b in old], [b.key for b in new], autojunk=False)
    changes: list[Change] = []
    for op, i1, i2, j1, j2 in matcher.get_opcodes():
        if op == "equal":
            changes += [Change(State.SAME, block) for block in new[j1:j2]]
        else:
            changes += _pair(old[i1:i2], new[j1:j2])
    return changes


def _pair(old: list[Block], new: list[Block]) -> list[Change]:
    """Pair similar blocks of the same kind, keeping the order (the best total similarity wins)."""
    if len(old) * len(new) > PAIRING_LIMIT:
        return [Change(State.DEL, b) for b in old] + [Change(State.ADD, b) for b in new]
    sim = [[_similarity(o, n) for n in new] for o in old]
    best = [[0.0] * (len(new) + 1) for _ in range(len(old) + 1)]
    for i in range(len(old) - 1, -1, -1):
        for j in range(len(new) - 1, -1, -1):
            paired = best[i + 1][j + 1] + sim[i][j] if sim[i][j] >= PAIRING else -1.0
            best[i][j] = max(best[i + 1][j], best[i][j + 1], paired)
    changes, i, j = [], 0, 0
    while i < len(old) or j < len(new):
        if i < len(old) and j < len(new) and sim[i][j] >= PAIRING and best[i][j] == best[i + 1][j + 1] + sim[i][j]:
            changes.append(_modified(old[i], new[j]))
            i, j = i + 1, j + 1
        elif i < len(old) and (j == len(new) or best[i][j] == best[i + 1][j]):
            changes.append(Change(State.DEL, old[i]))
            i += 1
        else:
            changes.append(Change(State.ADD, new[j]))
            j += 1
    return changes


def _modified(old: Block, new: Block) -> Change:
    marked = None if new.kind in ("code", "meta", "hr") else mark_words(old.src, new.src)
    return Change(State.MOD, new, old, marked)


def _similarity(a: Block, b: Block) -> float:
    if a.kind != b.kind:
        return 0.0
    return difflib.SequenceMatcher(None, a.key, b.key, autojunk=False).ratio()


def _source_lines(tok, offset: int) -> dict[str, int]:
    """First and last line of a block token in the file; markdown-it counts from the body, 0-based, end excluded."""
    return {"line": offset + tok.map[0] + 1, "end": offset + tok.map[1]} if tok.map else {}


def _split_front_matter(text: str) -> tuple[str | None, str]:
    if text.startswith("---\n"):
        end = text.find("\n---", 4)
        if end != -1:
            return text[4:end], text[end + 4:].lstrip("\n")
    return None, text


def _row_cells(tokens, start: int) -> list[str]:
    cells = []
    for tok in tokens[start + 1:]:
        if tok.type == "tr_close":
            break
        if tok.type == "inline":
            cells.append(tok.content)
    return cells


def _collapse(text: str) -> str:
    return " ".join(text.split())


def _leading_space(token: str) -> str:
    return token[: len(token) - len(token.lstrip())]
