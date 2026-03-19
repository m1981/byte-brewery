import pytest
from prompt_extractor.models import UserPrompt, BranchInfo
from prompt_extractor.core import extract_user_prompts, format_to_markdown


@pytest.fixture
def sample_json_data():
    return {
        "chunkedPrompt": {
            "chunks": [
                {"role": "user", "text": "First prompt"},
                {"role": "model", "text": "Model response"},
                {
                    "role": "user",
                    "text": "Branched prompt",
                    "branchParent": {
                        "promptId": "prompts/123",
                        "displayName": "Original Topic"
                    }
                },
                {"role": "user", "driveImage": {"id": "123"}}  # Ignored
            ]
        }
    }


def test_extract_user_prompts_success(sample_json_data):
    prompts = extract_user_prompts(sample_json_data)

    assert len(prompts) == 2

    # Check first prompt (no branch)
    assert prompts[0].text == "First prompt"
    assert prompts[0].branch_info is None

    # Check second prompt (with branch)
    assert prompts[1].text == "Branched prompt"
    assert prompts[1].branch_info is not None
    assert prompts[1].branch_info.prompt_id == "prompts/123"
    assert prompts[1].branch_info.display_name == "Original Topic"


def test_format_to_markdown():
    prompts = [
        UserPrompt(text="Prompt A"),
        UserPrompt(
            text="Prompt B",
            branch_info=BranchInfo(prompt_id="p/1", display_name="Topic A")
        )
    ]

    expected_output = (
        "# File: test.json\n\n"
        "## Prompt 1\n"
        "Prompt A\n\n"
        "## Prompt 2\n"
        "> 🌿 **Branched from:** Topic A (`p/1`)\n\n"
        "Prompt B\n"
    )

    assert format_to_markdown("test.json", prompts) == expected_output