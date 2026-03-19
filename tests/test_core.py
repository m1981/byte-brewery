import pytest
from prompt_extractor.core import extract_user_prompts, format_to_markdown

@pytest.fixture
def sample_json_data():
    return {
        "chunkedPrompt": {
            "chunks": [
                {"role": "user", "text": "First prompt"},
                {"role": "model", "text": "Model response"},
                {"role": "user", "text": "Second prompt"},
                {"role": "user", "driveImage": {"id": "123"}} # No text, should be ignored
            ]
        }
    }

def test_extract_user_prompts_success(sample_json_data):
    prompts = extract_user_prompts(sample_json_data)
    assert len(prompts) == 2
    assert prompts[0] == "First prompt"
    assert prompts[1] == "Second prompt"

def test_extract_user_prompts_missing_keys():
    assert extract_user_prompts({}) == []
    assert extract_user_prompts({"chunkedPrompt": {}}) == []

def test_format_to_markdown():
    prompts = ["Prompt A", "Prompt B"]
    filename = "test.json"
    expected_output = (
        "# File: test.json\n\n"
        "## Prompt 1\nPrompt A\n\n"
        "## Prompt 2\nPrompt B\n"
    )
    assert format_to_markdown(filename, prompts) == expected_output