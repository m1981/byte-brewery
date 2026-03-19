from datetime import datetime

from prompt_extractor.models import MessageNode


def test_message_node_minimal():
    node = MessageNode(timestamp=datetime(2026, 1, 1), role="user", text="Hi")
    assert node.role == "user"
    assert node.text == "Hi"
    assert node.image_id is None
    assert node.branch_parent is None
    assert node.children == []


def test_message_node_full():
    node = MessageNode(
        timestamp=datetime(2026, 3, 19, 13, 30, 56),
        role="model",
        text="Response",
        image_id="img123",
        branch_parent={"promptId": "p/1", "displayName": "Topic"},
    )
    assert node.role == "model"
    assert node.text == "Response"
    assert node.image_id == "img123"
    assert node.branch_parent == {"promptId": "p/1", "displayName": "Topic"}


def test_message_node_children_not_shared():
    a = MessageNode(timestamp=datetime(2026, 1, 1), role="user", text="A")
    b = MessageNode(timestamp=datetime(2026, 1, 1), role="user", text="B")
    a.children.append(b)
    c = MessageNode(timestamp=datetime(2026, 1, 1), role="user", text="C")
    assert c.children == []
