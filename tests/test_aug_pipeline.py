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

# Test data paths - updated to point to new location
TEST_DATA_DIR = Path(__file__).parent / "data"
INPUT_XML = TEST_DATA_DIR / "input.xml"
GOLDEN_CHAT_STATE = TEST_DATA_DIR / "chat_state.json"
GOLDEN_PROMPTS = TEST_DATA_DIR / "prompts.json"
GOLDEN_ANALYZED_PROMPTS = TEST_DATA_DIR / "analyzed_prompts.json"

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs and copy test data."""
    temp_dir = tempfile.mkdtemp()
    
    # Create test data
    test_data = {
        "input.xml": """<?xml version="1.0" encoding="UTF-8"?>
            <root>
                <entry key="CHAT_STATE" value="eyJjb252ZXJzYXRpb25zIjp7fX0=" />
            </root>""",
        "chat_state.json": '{"conversations":{}}',
        "prompts.json": '[]',
        "analyzed_prompts.json": '[]'
    }
    
    # Write test data files
    for filename, content in test_data.items():
        with open(Path(temp_dir) / filename, 'w') as f:
            f.write(content)
    
    yield temp_dir
    shutil.rmtree(temp_dir)

def compare_json_files(file1: Path, file2: Path) -> bool:
    """Compare two JSON files for equality."""
    with open(file1) as f1, open(file2) as f2:
        data1 = json.load(f1)
        data2 = json.load(f2)
        return data1 == data2

class TestAugPipeline:
    def test_validate_input_file(self):
        """Test input file validation."""
        # Test valid XML file
        assert validate_input_file(str(INPUT_XML)) is True

        # Test non-existent file
        assert validate_input_file("nonexistent.xml") is False

        # Test invalid extension
        with tempfile.NamedTemporaryFile(suffix=".txt") as tf:
            assert validate_input_file(tf.name) is False

        # Test empty path
        assert validate_input_file("") is False

    def test_validate_output_dir(self):
        """Test output directory validation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test existing directory
            assert validate_output_dir(temp_dir) is True

            # Test creating new directory
            new_dir = Path(temp_dir) / "new_dir"
            assert validate_output_dir(str(new_dir)) is True
            assert new_dir.exists()

            # Test invalid path (file instead of directory)
            temp_file = Path(temp_dir) / "file.txt"
            temp_file.touch()
            assert validate_output_dir(str(temp_file)) is False

    def test_process_chat_pipeline(self, temp_output_dir):
        """Test the complete pipeline processing."""
        input_xml = Path(temp_output_dir) / "input.xml"
        
        # Run pipeline
        success = process_chat_pipeline(str(input_xml), temp_output_dir)
        assert success is True

        # Check if all output files were created
        output_files = [
            "chat_state.json",
            "prompts.json",
            "analyzed_prompts.json",
            "schema.json"
        ]
        for file in output_files:
            assert Path(temp_output_dir, file).exists()

        # Compare with expected data
        expected_chat_state = {"conversations": {}}
        expected_prompts = []
        expected_analyzed_prompts = []

        with open(Path(temp_output_dir) / "chat_state.json") as f:
            assert json.load(f) == expected_chat_state
        with open(Path(temp_output_dir) / "prompts.json") as f:
            assert json.load(f) == expected_prompts
        with open(Path(temp_output_dir) / "analyzed_prompts.json") as f:
            assert json.load(f) == expected_analyzed_prompts

    def test_pipeline_error_handling(self, temp_output_dir):
        """Test pipeline error handling."""
        # Test with invalid XML file
        with tempfile.NamedTemporaryFile(suffix=".xml") as bad_xml:
            bad_xml.write(b"<invalid>xml</invalid>")
            bad_xml.flush()
            success = process_chat_pipeline(bad_xml.name, temp_output_dir)
            assert success is False

        # Test with non-existent input file
        success = process_chat_pipeline("nonexistent.xml", temp_output_dir)
        assert success is False

        # Test with invalid output directory
        with tempfile.NamedTemporaryFile() as tf:
            success = process_chat_pipeline(str(INPUT_XML), tf.name)
            assert success is False

if __name__ == "__main__":
    pytest.main([__file__])