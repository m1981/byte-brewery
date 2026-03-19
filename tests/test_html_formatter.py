from datetime import datetime, timezone

import pytest

from prompt_extractor.html_formatter import format_html
from prompt_extractor.models import MessageNode


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _node(text, role="user", ts=0, branch_name=None, image_id=None):
    bp = {"promptId": "p/1", "displayName": branch_name} if branch_name else None
    return MessageNode(
        timestamp=datetime(2026, 1, 1, 0, 0, ts, tzinfo=timezone.utc),
        role=role,
        text=text,
        image_id=image_id,
        branch_parent=bp,
    )


# ---------------------------------------------------------------------------
# Structure
# ---------------------------------------------------------------------------

def test_format_html_is_valid_document():
    output = format_html([("test.txt", [_node("Hi")])])
    assert "<!DOCTYPE html>" in output
    assert "<html" in output
    assert "</html>" in output


def test_format_html_contains_lane_per_conversation():
    convs = [("a.txt", [_node("A")]), ("b.txt", [_node("B")])]
    output = format_html(convs)
    assert output.count('class="lane"') == 2


def test_format_html_shows_lane_headers():
    output = format_html([("my_conv.txt", [_node("Hi")])])
    assert "my_conv.txt" in output


def test_format_html_empty_conversations_renders():
    output = format_html([])
    assert "<!DOCTYPE html>" in output


# ---------------------------------------------------------------------------
# Message rendering
# ---------------------------------------------------------------------------

def test_format_html_shows_message_text():
    output = format_html([("f.txt", [_node("Hello world")])])
    assert "Hello world" in output


def test_format_html_escapes_html_in_text():
    output = format_html([("f.txt", [_node("<b>bold</b>")])])
    assert "<b>bold</b>" not in output
    assert "&lt;b&gt;" in output


def test_format_html_user_message_has_user_class():
    output = format_html([("f.txt", [_node("Hi", role="user")])])
    assert 'message user' in output


def test_format_html_model_message_has_model_class():
    output = format_html([("f.txt", [_node("Hi", role="model")])])
    assert 'message model' in output


def test_format_html_shows_image_id():
    node = MessageNode(
        timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
        role="user",
        text="",
        image_id="img-abc-123",
    )
    output = format_html([("f.txt", [node])])
    assert "img-abc-123" in output


def test_format_html_shows_timestamp():
    node = MessageNode(
        timestamp=datetime(2026, 1, 1, 13, 30, 56, tzinfo=timezone.utc),
        role="user",
        text="Hi",
    )
    output = format_html([("f.txt", [node])])
    assert "13:30:56" in output


# ---------------------------------------------------------------------------
# Branch markers
# ---------------------------------------------------------------------------

def test_format_html_shows_branch_marker():
    nodes = [_node("Original"), _node("Branched", branch_name="Original Topic")]
    output = format_html([("f.txt", nodes)])
    assert "branch-marker" in output
    assert "Original Topic" in output


def test_format_html_escapes_branch_name():
    nodes = [_node("X", branch_name='<b>evil</b>')]
    output = format_html([("f.txt", nodes)])
    assert "<b>evil</b>" not in output
    assert "&lt;b&gt;" in output


def test_format_html_branch_marker_before_message():
    nodes = [_node("Branched", branch_name="Root")]
    output = format_html([("f.txt", nodes)])
    branch_pos = output.index("branch-marker")
    msg_pos = output.index("message user")
    assert branch_pos < msg_pos
