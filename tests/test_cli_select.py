import json
from pathlib import Path

import pytest

from prompt_extractor.cli import _find_files, _load_conversation


def _write_json(path: Path, data: dict) -> Path:
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


MINIMAL_DATA_1 = {
    "chunkedPrompt": {
        "chunks": [{"role": "user", "text": "First conversation", "createTime": "2026-01-01T00:00:00Z"}]
    }
}

MINIMAL_DATA_2 = {
    "chunkedPrompt": {
        "chunks": [{"role": "user", "text": "Second conversation", "createTime": "2026-01-02T00:00:00Z"}]
    }
}


def test_list_conversations_shows_numbered_list(tmp_path, capsys):
    """When --select is used without value, list all conversations with numbers."""
    from prompt_extractor.cli import _list_conversations

    _write_json(tmp_path / "conv1.txt", MINIMAL_DATA_1)
    _write_json(tmp_path / "conv2.txt", MINIMAL_DATA_2)

    files = _find_files(tmp_path)
    conversations = [r for f in files if (r := _load_conversation(f)) is not None]

    _list_conversations(conversations)
    captured = capsys.readouterr()

    assert "[1] conv1" in captured.out
    assert "[2] conv2" in captured.out


def test_select_conversation_by_index(tmp_path):
    """Select conversation by numeric index."""
    from prompt_extractor.cli import _select_conversation

    _write_json(tmp_path / "conv1.txt", MINIMAL_DATA_1)
    _write_json(tmp_path / "conv2.txt", MINIMAL_DATA_2)

    files = _find_files(tmp_path)
    conversations = [r for f in files if (r := _load_conversation(f)) is not None]

    selected = _select_conversation(conversations, "1")
    assert selected is not None
    name, nodes, _ = selected
    assert name == "conv1"
    assert nodes[0].text == "First conversation"


def test_select_conversation_by_name(tmp_path):
    """Select conversation by partial name match."""
    from prompt_extractor.cli import _select_conversation

    _write_json(tmp_path / "my_important_chat.txt", MINIMAL_DATA_1)
    _write_json(tmp_path / "other_chat.txt", MINIMAL_DATA_2)

    files = _find_files(tmp_path)
    conversations = [r for f in files if (r := _load_conversation(f)) is not None]

    selected = _select_conversation(conversations, "important")
    assert selected is not None
    name, nodes, _ = selected
    assert name == "my_important_chat"


def test_select_conversation_invalid_index_returns_none(tmp_path):
    """Invalid index returns None."""
    from prompt_extractor.cli import _select_conversation

    _write_json(tmp_path / "conv1.txt", MINIMAL_DATA_1)

    files = _find_files(tmp_path)
    conversations = [r for f in files if (r := _load_conversation(f)) is not None]

    selected = _select_conversation(conversations, "99")
    assert selected is None


def test_select_conversation_no_match_returns_none(tmp_path):
    """No name match returns None."""
    from prompt_extractor.cli import _select_conversation

    _write_json(tmp_path / "conv1.txt", MINIMAL_DATA_1)

    files = _find_files(tmp_path)
    conversations = [r for f in files if (r := _load_conversation(f)) is not None]

    selected = _select_conversation(conversations, "nonexistent")
    assert selected is None
