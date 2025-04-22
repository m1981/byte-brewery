
import pytest
import json
from pathlib import Path
import tempfile
import shutil
from augment_ai.aug_pipeline import (
    validate_input_file,
    validate_output_dir,
    process_chat_pipeline
)

# Test data paths
TEST_DATA_DIR = Path(__file__).parent / "data"

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

def compare_json_files(file1: Path, file2: Path) -> bool:
    """Compare two JSON files for equality."""
    with open(file1) as f1, open(file2) as f2:
        data1 = json.load(f1)
        data2 = json.load(f2)
        return data1 == data2

class TestAugPipeline:
    def test_integration_with_analyzed_prompts(self, temp_output_dir):
        """Integration test comparing pipeline output with specific analyzed prompts data."""
        # Setup test input XML with known content
        input_xml_content = """<?xml version="1.0" encoding="UTF-8"?>
            <root>
                <entry key="CHAT_STATE" value="eyJjb252ZXJzYXRpb25zIjp7ImNvbnYxIjp7ImNoYXRIaXN0b3J5IjpbeyJyZXF1ZXN0X21lc3NhZ2UiOiJIZWxsbyBBSSIsInJlcXVlc3RfaWQiOiIxMjMiLCJ0aW1lc3RhbXAiOiIyMDI0LTAxLTAxVDAwOjAwOjAwWiJ9XX19fQ==" />
            </root>"""
        
        input_xml_path = Path(temp_output_dir) / "integration_input.xml"
        input_xml_path.write_text(input_xml_content)

        # Create expected analyzed prompts data
        expected_analyzed_prompts = {
            "conv1": [
                {
                    "meaningful_content": "Hello AI",
                    "original_length": 8,
                    "processed_length": 8
                }
            ]
        }

        # Ensure TEST_DATA_DIR exists
        TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)
        
        expected_file = TEST_DATA_DIR / "analyzed_prompts.json"
        with open(expected_file, 'w') as f:
            json.dump(expected_analyzed_prompts, f, indent=2)

        # Run pipeline
        success = process_chat_pipeline(str(input_xml_path), temp_output_dir)
        assert success is True

        # Compare output with expected data
        output_file = Path(temp_output_dir) / "analyzed_prompts.json"
        assert compare_json_files(output_file, expected_file), \
            "Pipeline output doesn't match expected analyzed prompts"

        # Verify the content explicitly
        with open(output_file) as f:
            actual_output = json.load(f)
            assert actual_output == expected_analyzed_prompts, \
                "Content mismatch in analyzed prompts"
