import json
from pathlib import Path

import pytest

from prompt_extractor.cli import _process_file, _find_files


def _write_json(path: Path, data: dict) -> Path:
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


MINIMAL_DATA = {
    "chunkedPrompt": {
        "chunks": [{"role": "user", "text": "Hello", "createTime": "2026-01-01T00:00:00Z"}]
    }
}


def test_find_files_picks_up_txt_files(tmp_path):
    (tmp_path / "conv.txt").write_text(json.dumps(MINIMAL_DATA))
    files = _find_files(tmp_path)
    assert any(f.name == "conv.txt" for f in files)


def test_find_files_picks_up_json_files(tmp_path):
    (tmp_path / "conv.json").write_text(json.dumps(MINIMAL_DATA))
    files = _find_files(tmp_path)
    assert any(f.name == "conv.json" for f in files)


def test_find_files_skips_subdirectories(tmp_path):
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    (subdir / "nested.json").write_text(json.dumps(MINIMAL_DATA))
    files = _find_files(tmp_path)
    assert all(f.parent == tmp_path for f in files)


def test_find_files_empty_dir_returns_empty(tmp_path):
    assert _find_files(tmp_path) == []


def test_process_file_skips_non_json(tmp_path):
    p = tmp_path / "not_json.txt"
    p.write_text("this is not json")
    result = _process_file(p, "timeline")
    assert result == ""


def test_process_file_html_view(tmp_path):
    p = _write_json(tmp_path / "conv.json", MINIMAL_DATA)
    result = _process_file(p, "html")
    assert "<!DOCTYPE html>" in result
    assert "Hello" in result


def test_load_conversation_returns_name_and_nodes(tmp_path):
    from prompt_extractor.cli import _load_conversation
    p = _write_json(tmp_path / "my_conv.txt", MINIMAL_DATA)
    name, nodes, filepath = _load_conversation(p)
    assert name == "my_conv"
    assert len(nodes) == 1
    assert filepath == str(p)


def test_load_conversation_returns_none_on_invalid(tmp_path):
    from prompt_extractor.cli import _load_conversation
    p = tmp_path / "bad.txt"
    p.write_text("not json")
    assert _load_conversation(p) is None
