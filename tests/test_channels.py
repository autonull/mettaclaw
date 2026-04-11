import pytest
import channels.embodiment as embodiment
from channels.base import Channel

class MockChannel(Channel):
    def __init__(self, name):
        super().__init__(name)
        self.sent_messages = []

    def start(self):
        self.running = True
        self.connected = True

    def send_message(self, text):
        self.sent_messages.append(text)

@pytest.fixture(autouse=True)
def clean_embodiment():
    embodiment.stop_all()
    # Reset channels dict explicitly for isolation
    embodiment.bus._channels.clear()
    embodiment.bus._active_channel = None
    embodiment.bus._running = False
    yield
    embodiment.stop_all()
    embodiment.bus._channels.clear()

def test_embodiment_registration():
    chan = MockChannel("mock1")
    chan.start()
    embodiment.register_channel("mock1", chan)

    assert "mock1" in embodiment.get_active_channels()

    embodiment.unregister_channel("mock1")
    assert "mock1" not in embodiment.get_active_channels()

def test_embodiment_broadcast():
    chan1 = MockChannel("mock1")
    chan1.start()
    chan2 = MockChannel("mock2")
    chan2.start()

    embodiment.register_channel("mock1", chan1)
    embodiment.register_channel("mock2", chan2)

    embodiment.broadcast("hello world")

    assert chan1.sent_messages == ["hello world"]
    assert chan2.sent_messages == ["hello world"]

def test_embodiment_send_to():
    chan1 = MockChannel("mock1")
    chan1.start()
    chan2 = MockChannel("mock2")
    chan2.start()

    embodiment.register_channel("mock1", chan1)
    embodiment.register_channel("mock2", chan2)

    embodiment.send_to("mock1", "only to 1")

    assert chan1.sent_messages == ["only to 1"]
    assert chan2.sent_messages == []

def test_embodiment_receive():
    chan = MockChannel("mock1")
    chan.start()
    chan.set_last_message("incoming message")
    embodiment.register_channel("mock1", chan)

    msg = embodiment.receive_all()
    assert msg == "incoming message"

    # Second read should be empty as it consumes the message
    assert embodiment.receive_all() == ""

def test_websearch():
    import channels.websearch as websearch
    # Test escaping behavior logic manually

    # Normally this would be integration, but we can verify the search function
    # string assembly gracefully formats results if search_ was mocked.
    def mock_search_(query, max_results=10):
        return [
            {"title": 'Cool "Quotes"', "snippet": "A \n newline"}
        ]

    import types
    import json

    # Store real function to not permanently break module
    real_search_ = websearch.search_
    websearch.search_ = mock_search_

    try:
        res = websearch.search("test")
        # Ensure json stringification happened securely
        assert '"Cool \\"Quotes\\""' in res
        assert '"A \\n newline"' in res
        assert res.startswith("(") and res.endswith(")")
        assert "TITLE:" not in res # Replaced with Result abstraction
    finally:
        websearch.search_ = real_search_

    # Empty test
    def mock_empty(query, max_results=10):
        return []

    websearch.search_ = mock_empty
    try:
        assert websearch.search("test") == "(No_Results)"
    finally:
        websearch.search_ = real_search_
