import pytest
from datetime import datetime, timezone
from prompt_extractor.models import MessageNode


@pytest.fixture
def node_factory():
    """Helper to quickly build MessageNodes for testing."""

    def _make_node(role: str, text: str, minutes_offset: int = 0):
        # Use a fixed base time for deterministic testing
        base_time = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
        # We can't easily add minutes to a datetime without timedelta,
        # but for simplicity in the factory, we'll just use a static time
        # or you can import timedelta.
        from datetime import timedelta
        ts = base_time + timedelta(minutes=minutes_offset)
        return MessageNode(timestamp=ts, role=role, text=text)

    return _make_node


@pytest.fixture
def sample_conversations(node_factory):
    """Provides a dictionary of pre-configured conversation scenarios."""

    # 1. Normal chat
    chat_python = [
        node_factory("user", "How do I write a Python dictionary?"),
        node_factory("model", "Use curly braces {}")
    ]

    # 2. Branch of chat_python (Identical first prompt!)
    chat_python_branch = [
        node_factory("user", "How do I write a Python dictionary?"),  # Same text
        node_factory("model", "Here is an advanced example...")
    ]

    # 3. Completely different chat
    chat_css = [
        node_factory("user", "Center a div in CSS"),
        node_factory("model", "Use flexbox.")
    ]

    # 4. Edge case: No user prompts at all (e.g., system message only)
    chat_empty = [
        node_factory("model", "System initialized.")
    ]

    return {
        "python_main": chat_python,
        "python_branch": chat_python_branch,
        "css_main": chat_css,
        "empty_chat": chat_empty
    }