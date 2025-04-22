import unittest
import pytest
import json
import tempfile
import sys
from pathlib import Path
from src.pext import (
    ChatMessageExtractor,
    parse_chat_json,
    extract_prompts,
    format_prompts,
    save_output,
    main
)

class TestChatMessageExtractor(unittest.TestCase):
    def test_extract_second_message(self):
        """Test extracting second message from chats."""
        test_json_data = {
            "chats": [
                {
                    "id": "42687d49-6aa7-4105-bbe5-cf10173a2af3",
                    "title": "Bash: Add Directory to PATH",
                    "messages": [
                        {
                            "role": "system",
                            "content": "Be my helpful female advisor."
                        },
                        {
                            "role": "user",
                            "content": "act as bash expert"
                        }
                    ],
                    "titleSet": "true",
                    "folder": "f67b3b25-e436-4423-b160-212fe81f5e2e"
                },
                {
                    "id": "b5fae9a3-c397-47a7-a88c-c9329c01bb3f",
                    "title": "Tailwind CSS Contradiction Checks",
                    "messages": [
                        {
                            "role": "system",
                            "content": "Be my helpful female advisor."
                        },
                        {
                            "role": "user",
                            "content": "Act as an expert of Tailwind and CSS. "
                        }
                    ],
                    "titleSet": "true",
                    "folder": "f67b3b25-e436-4423-b160-212fe81f5e2e"
                }
            ]
        }

        expected_output = ["act as bash expert", "Act as an expert of Tailwind and CSS. "]
        second_messages = ChatMessageExtractor.extract_second_message(test_json_data)
        self.assertEqual(second_messages, expected_output)

    def test_extract_second_message_single_message(self):
        """Test extracting second message when chat has only one message."""
        test_json_data = {
            "chats": [
                {
                    "id": "chat1",
                    "messages": [
                        {"role": "user", "content": "Is anyone there?"}
                    ]
                }
            ]
        }

        expected_output = [None]  # No second message
        second_messages = ChatMessageExtractor.extract_second_message(test_json_data)
        self.assertEqual(second_messages, expected_output)

    def test_extract_second_message_empty_chat(self):
        """Test extracting second message from empty chat."""
        test_json_data = {
            "chats": [
                {
                    "id": "chat1",
                    "messages": []
                }
            ]
        }

        expected_output = [None]
        second_messages = ChatMessageExtractor.extract_second_message(test_json_data)
        self.assertEqual(second_messages, expected_output)

    def test_extract_second_message_no_chats(self):
        """Test extracting second message when no chats exist."""
        test_json_data = {
            "chats": []
        }

        expected_output = []
        second_messages = ChatMessageExtractor.extract_second_message(test_json_data)
        self.assertEqual(second_messages, expected_output)

    def test_extract_second_message_invalid_structure(self):
        """Test extracting second message with invalid JSON structure."""
        # Test case 1: Missing 'chats' key
        test_json_data1 = {
            "invalid": "structure"
        }
        self.assertEqual(ChatMessageExtractor.extract_second_message(test_json_data1), [])

        # Test case 2: Missing 'messages' key in chat
        test_json_data2 = {
            "chats": [
                {
                    "id": "chat1"
                }
            ]
        }
        self.assertEqual(ChatMessageExtractor.extract_second_message(test_json_data2), [None])

        # Test case 3: Invalid message structure
        test_json_data3 = {
            "chats": [
                {
                    "id": "chat1",
                    "messages": [
                        {"invalid": "message"}
                    ]
                }
            ]
        }
        self.assertEqual(ChatMessageExtractor.extract_second_message(test_json_data3), [None])

        # Test case 4: None input
        self.assertEqual(ChatMessageExtractor.extract_second_message(None), [])

    def test_message_criteria(self):
        """Test message extraction with custom criteria."""
        test_json_data = {
            "chats": [{
                "messages": [
                    {"role": "system", "content": "system msg"},
                    {"role": "user", "content": "user msg"},
                    {"role": "assistant", "content": "assistant msg"}
                ]
            }]
        }
        
        # Only user messages
        user_messages = ChatMessageExtractor.extract_second_message(
            test_json_data,
            lambda msg: msg.get('role') == 'user'
        )
        self.assertEqual(user_messages, [None])  # Only one user message
        
        # Only assistant messages
        assistant_messages = ChatMessageExtractor.extract_second_message(
            test_json_data,
            lambda msg: msg.get('role') == 'assistant'
        )
        self.assertEqual(assistant_messages, [None])  # Only one assistant message

class TestPromptExtraction:
    @pytest.fixture
    def sample_chat_data(self):
        return {
            "messages": [
                {"role": "system", "content": "System message"},
                {"role": "human", "content": "Human message 1"},
                {"role": "assistant", "content": "Assistant response"},
                {"role": "human", "content": "Human message 2"}
            ],
            "metadata": {
                "timestamp": "2023-01-01T12:00:00Z",
                "conversation_id": "test-123"
            }
        }

    def test_extract_prompts(self, sample_chat_data):
        """Test prompt extraction with metadata."""
        prompts = extract_prompts(sample_chat_data)
        assert len(prompts) == 2
        assert prompts[0]["content"] == "Human message 1"
        assert prompts[0]["timestamp"] == "2023-01-01T12:00:00Z"
        assert prompts[0]["conversation_id"] == "test-123"

    def test_extract_prompts_missing_metadata(self):
        """Test prompt extraction with missing metadata."""
        chat_data = {
            "messages": [
                {"role": "human", "content": "Hello"}
            ]
        }
        prompts = extract_prompts(chat_data)
        assert len(prompts) == 1
        assert prompts[0]["timestamp"] is None
        assert prompts[0]["conversation_id"] is None

    @pytest.mark.parametrize("format_type,expected_start", [
        ("json", "["),
        ("csv", "content"),
        ("text", "Human message")
    ])
    def test_format_prompts(self, sample_chat_data, format_type, expected_start):
        """Test different prompt formats."""
        prompts = extract_prompts(sample_chat_data)
        formatted = format_prompts(prompts, format_type, True, True)
        assert formatted.startswith(expected_start)
        
    def test_format_prompts_csv_options(self, sample_chat_data):
        """Test CSV formatting with different options."""
        prompts = extract_prompts(sample_chat_data)
        
        # Basic CSV
        basic = format_prompts(prompts, "csv")
        assert "content" in basic
        assert "timestamp" not in basic
        
        # With timestamps
        with_time = format_prompts(prompts, "csv", include_timestamps=True)
        assert "timestamp" in with_time
        
        # With conversation ID
        with_id = format_prompts(prompts, "csv", include_conversation_id=True)
        assert "conversation_id" in with_id

    def test_save_output(self, tmp_path):
        """Test saving output to file and stdout."""
        content = "Test content"
        
        # Test file output
        output_file = tmp_path / "test_output.txt"
        save_output(content, output_file)
        assert output_file.read_text() == content
        
        # Test stdout (captured by pytest)
        save_output(content, None)
        # Note: stdout capture is handled by pytest

    def test_main_error_handling(self, tmp_path):
        """Test main function error handling."""
        # Test nonexistent file
        with pytest.raises(SystemExit):
            sys.argv = ["pext", "nonexistent.json"]
            main()
        
        # Test invalid JSON
        invalid_json = tmp_path / "invalid.json"
        invalid_json.write_text("invalid json")
        with pytest.raises(SystemExit):
            sys.argv = ["pext", str(invalid_json)]
            main()

    def test_main_success(self, tmp_path, sample_chat_data):
        """Test successful main execution."""
        # Create input file
        input_file = tmp_path / "input.json"
        input_file.write_text(json.dumps(sample_chat_data))
        
        # Create output file
        output_file = tmp_path / "output.txt"
        
        # Test with various formats
        for fmt in ["text", "json", "csv"]:
            sys.argv = [
                "pext",
                str(input_file),
                "--output", str(output_file),
                "--format", fmt,
                "--timestamps",
                "--conversation-id"
            ]
            main()
            assert output_file.exists()
            assert output_file.stat().st_size > 0

if __name__ == "__main__":
    pytest.main([__file__])