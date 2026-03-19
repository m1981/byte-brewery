from datetime import datetime, timezone

import pytest

from prompt_extractor.core import (
    build_threads,
    format_timeline,
    format_tree,
    parse_chunks,
)
from prompt_extractor.models import MessageNode


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def simple_chunks():
    return {
        "chunkedPrompt": {
            "chunks": [
                {
                    "role": "user",
                    "text": "First prompt",
                    "createTime": "2026-03-19T13:30:56.796Z",
                },
                {
                    "role": "model",
                    "text": "Model response",
                    "createTime": "2026-03-19T13:31:05.664Z",
                },
            ]
        }
    }


@pytest.fixture
def chunks_with_thought():
    return {
        "chunkedPrompt": {
            "chunks": [
                {
                    "role": "user",
                    "text": "User message",
                    "createTime": "2026-03-19T13:30:00.000Z",
                },
                {
                    "role": "model",
                    "text": "Internal thinking",
                    "isThought": True,
                    "createTime": "2026-03-19T13:30:01.000Z",
                },
                {
                    "role": "model",
                    "text": "Visible response",
                    "createTime": "2026-03-19T13:30:02.000Z",
                },
            ]
        }
    }


@pytest.fixture
def chunks_with_image_and_branch():
    return {
        "chunkedPrompt": {
            "chunks": [
                {
                    "role": "user",
                    "text": "Original question",
                    "createTime": "2026-03-19T13:30:00.000Z",
                },
                {
                    "role": "model",
                    "text": "First answer",
                    "createTime": "2026-03-19T13:30:05.000Z",
                },
                {
                    "role": "user",
                    "driveImage": {"id": "img-abc"},
                    "createTime": "2026-03-19T13:31:00.000Z",
                },
                {
                    "role": "user",
                    "text": "Branched follow-up",
                    "branchParent": {
                        "promptId": "prompts/xyz",
                        "displayName": "Original question",
                    },
                    "createTime": "2026-03-19T13:31:00.001Z",
                },
                {
                    "role": "model",
                    "text": "Branch answer",
                    "createTime": "2026-03-19T13:31:10.000Z",
                },
            ]
        }
    }


# ---------------------------------------------------------------------------
# parse_chunks
# ---------------------------------------------------------------------------

def test_parse_chunks_filters_thought(chunks_with_thought):
    nodes = parse_chunks(chunks_with_thought)
    texts = [n.text for n in nodes]
    assert "Internal thinking" not in texts
    assert "Visible response" in texts


def test_parse_chunks_filters_empty_chunks():
    data = {
        "chunkedPrompt": {
            "chunks": [
                {"role": "user", "text": ""},        # no text, no image
                {"role": "model", "createTime": ""},   # no text, no image
                {"role": "user", "text": "Hello", "createTime": "2026-01-01T00:00:00Z"},
            ]
        }
    }
    nodes = parse_chunks(data)
    assert len(nodes) == 1
    assert nodes[0].text == "Hello"


def test_parse_chunks_extracts_image_id():
    data = {
        "chunkedPrompt": {
            "chunks": [
                {
                    "role": "user",
                    "driveImage": {"id": "img-123"},
                    "createTime": "2026-01-01T00:00:00Z",
                }
            ]
        }
    }
    nodes = parse_chunks(data)
    assert len(nodes) == 1
    assert nodes[0].image_id == "img-123"
    assert nodes[0].text == ""


def test_parse_chunks_sorts_chronologically():
    data = {
        "chunkedPrompt": {
            "chunks": [
                {"role": "model", "text": "B", "createTime": "2026-01-01T00:00:02Z"},
                {"role": "user", "text": "A", "createTime": "2026-01-01T00:00:01Z"},
            ]
        }
    }
    nodes = parse_chunks(data)
    assert nodes[0].text == "A"
    assert nodes[1].text == "B"


def test_parse_chunks_captures_branch_parent(chunks_with_image_and_branch):
    nodes = parse_chunks(chunks_with_image_and_branch)
    branched = [n for n in nodes if n.branch_parent]
    assert len(branched) == 1
    assert branched[0].branch_parent["promptId"] == "prompts/xyz"
    assert branched[0].branch_parent["displayName"] == "Original question"


def test_parse_chunks_handles_invalid_data():
    assert parse_chunks({}) == []
    assert parse_chunks({"chunkedPrompt": None}) == []


def test_parse_chunks_parses_timestamp(simple_chunks):
    nodes = parse_chunks(simple_chunks)
    expected = datetime(2026, 3, 19, 13, 30, 56, 796000, tzinfo=timezone.utc)
    assert nodes[0].timestamp == expected


# ---------------------------------------------------------------------------
# build_threads
# ---------------------------------------------------------------------------

def _make_node(text, ts_offset=0, branch_name=None):
    bp = {"promptId": "p/1", "displayName": branch_name} if branch_name else None
    return MessageNode(
        timestamp=datetime(2026, 1, 1, 0, 0, ts_offset, tzinfo=timezone.utc),
        role="user",
        text=text,
        branch_parent=bp,
    )


def test_build_threads_empty():
    threads = build_threads([])
    assert threads == [(None, [])]


def test_build_threads_single_thread():
    nodes = [_make_node("A"), _make_node("B")]
    threads = build_threads(nodes)
    assert len(threads) == 1
    assert threads[0][0] is None
    assert [n.text for n in threads[0][1]] == ["A", "B"]


def test_build_threads_splits_on_branch():
    nodes = [
        _make_node("A"),
        _make_node("B"),
        _make_node("C", branch_name="Original"),
        _make_node("D"),
    ]
    threads = build_threads(nodes)
    assert len(threads) == 2
    assert threads[0][0] is None
    assert [n.text for n in threads[0][1]] == ["A", "B"]
    assert threads[1][0] == "Original"
    assert [n.text for n in threads[1][1]] == ["C", "D"]


def test_build_threads_multiple_branches():
    nodes = [
        _make_node("A"),
        _make_node("B", branch_name="Root"),
        _make_node("C", branch_name="Branch1"),
    ]
    threads = build_threads(nodes)
    assert len(threads) == 3
    assert threads[0][0] is None
    assert threads[1][0] == "Root"
    assert threads[2][0] == "Branch1"


# ---------------------------------------------------------------------------
# format_timeline
# ---------------------------------------------------------------------------

def test_format_timeline_header():
    nodes = [_make_node("Hello")]
    output = format_timeline(nodes)
    assert "# Conversation Timeline" in output


def test_format_timeline_includes_text():
    nodes = [_make_node("Hello world")]
    output = format_timeline(nodes)
    assert "Hello world" in output


def test_format_timeline_shows_role():
    nodes = [
        MessageNode(
            timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
            role="model",
            text="Answer",
        )
    ]
    output = format_timeline(nodes)
    assert "Model" in output


def test_format_timeline_branch_rewind_marker():
    nodes = [
        _make_node("Before"),
        _make_node("Branched", branch_name="Previous Topic"),
    ]
    output = format_timeline(nodes)
    assert "TIMELINE BRANCH (Rewind)" in output
    assert 'Branched from: "Previous Topic"' in output


def test_format_timeline_shows_image_id():
    node = MessageNode(
        timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
        role="user",
        text="",
        image_id="abc-123",
    )
    output = format_timeline([node])
    assert "[Attached Image ID: abc-123]" in output


# ---------------------------------------------------------------------------
# format_tree
# ---------------------------------------------------------------------------

def test_format_tree_header():
    output = format_tree([(None, [_make_node("Hi")])])
    assert "# Conversation Threads" in output


def test_format_tree_main_thread_label():
    output = format_tree([(None, [_make_node("Hi")])])
    assert "Main Thread" in output


def test_format_tree_branch_label():
    threads = [
        (None, [_make_node("A")]),
        ("Original", [_make_node("B")]),
    ]
    output = format_tree(threads)
    assert "Branch 1" in output
    assert 'Branched from: "Original"' in output


def test_format_tree_skips_empty_threads():
    threads = [(None, []), ("X", [_make_node("B")])]
    output = format_tree(threads)
    assert "Main Thread" not in output
    assert "Branch 1" in output
