import json
import pytest
from unittest.mock import patch, MagicMock
from prompt_extractor.tagger import TagManager # We will build this next!

class TestTagManager:

    def test_normal_tagging_saves_to_cache(self, tmp_path, sample_conversations):
        """Happy Path: Uncached prompts trigger the LLM and save to cache."""
        cache_dir = tmp_path / "exports"
        cache_dir.mkdir()

        conversations = [
            ("chat1", sample_conversations["python_main"])
        ]

        # Mock the LLM API call
        with patch("prompt_extractor.tagger.TagManager._call_llm") as mock_llm:
            mock_llm.return_value = ["python", "basics"]

            tagger = TagManager(cache_dir)
            result = tagger.get_tags(conversations)

            # Assertions
            assert mock_llm.call_count == 1
            assert result["chat1"] == ["python", "basics"]

            # Verify cache file was created and written correctly
            cache_file = cache_dir / "chatmap_tags.json"
            assert cache_file.exists()
            saved_cache = json.loads(cache_file.read_text())
            # Cache key should be the prompt text (or hash), not the filename!
            assert "How do I write a Python dictionary?" in saved_cache

    def test_cache_hit_prevents_llm_call(self, tmp_path, sample_conversations):
        """If the prompt is already in the cache, do NOT call the LLM."""
        cache_dir = tmp_path / "exports"
        cache_dir.mkdir()

        # Pre-populate the cache
        cache_file = cache_dir / "chatmap_tags.json"
        cache_file.write_text(json.dumps({
            "Center a div in CSS": ["css", "frontend"]
        }))

        conversations = [("chat_css", sample_conversations["css_main"])]

        with patch("prompt_extractor.tagger.TagManager._call_llm") as mock_llm:
            tagger = TagManager(cache_dir)
            result = tagger.get_tags(conversations)

            # Assertions
            mock_llm.assert_not_called() # Crucial: No API cost incurred!
            assert result["chat_css"] == ["css", "frontend"]

    def test_branch_deduplication(self, tmp_path, sample_conversations):
        """Edge Case: Two files with the exact same first prompt should only trigger ONE API call."""
        cache_dir = tmp_path / "exports"
        cache_dir.mkdir()

        conversations = [
            ("main_file", sample_conversations["python_main"]),
            ("branch_file", sample_conversations["python_branch"])
        ]

        with patch("prompt_extractor.tagger.TagManager._call_llm") as mock_llm:
            mock_llm.return_value = ["python"]

            tagger = TagManager(cache_dir)
            result = tagger.get_tags(conversations)

            # Assertions
            assert mock_llm.call_count == 1 # Only called once despite 2 files!
            assert result["main_file"] == ["python"]
            assert result["branch_file"] == ["python"]

    def test_empty_or_no_user_prompts(self, tmp_path, sample_conversations):
        """Edge Case: Chats with no user prompts should be ignored gracefully."""
        cache_dir = tmp_path / "exports"
        cache_dir.mkdir()

        conversations = [("empty", sample_conversations["empty_chat"])]

        with patch("prompt_extractor.tagger.TagManager._call_llm") as mock_llm:
            tagger = TagManager(cache_dir)
            result = tagger.get_tags(conversations)

            mock_llm.assert_not_called()
            assert result["empty"] == [] # Returns empty list safely

    def test_corrupt_cache_file_recovery(self, tmp_path, sample_conversations):
        """Edge Case: If the JSON cache is corrupted, it should wipe it and start fresh."""
        cache_dir = tmp_path / "exports"
        cache_dir.mkdir()

        cache_file = cache_dir / "chatmap_tags.json"
        cache_file.write_text("{ invalid json syntax ]")

        conversations = [("chat1", sample_conversations["python_main"])]

        with patch("prompt_extractor.tagger.TagManager._call_llm") as mock_llm:
            mock_llm.return_value = ["recovered"]

            tagger = TagManager(cache_dir)
            result = tagger.get_tags(conversations)

            assert result["chat1"] == ["recovered"]
            # Cache should be overwritten with valid JSON
            assert json.loads(cache_file.read_text())

    def test_llm_api_failure_handling(self, tmp_path, sample_conversations):
        """Edge Case: If the LLM API throws an error, don't crash the whole CLI."""
        cache_dir = tmp_path / "exports"
        cache_dir.mkdir()

        conversations = [("chat1", sample_conversations["python_main"])]

        with patch("prompt_extractor.tagger.TagManager._call_llm") as mock_llm:
            # Simulate a network timeout or API error
            mock_llm.side_effect = Exception("API Rate Limit Exceeded")

            tagger = TagManager(cache_dir)
            result = tagger.get_tags(conversations)

            # Should gracefully return empty tags for that chat instead of crashing
            assert result["chat1"] == []