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
    embodiment._channels.clear()
    embodiment._active_channel = None
    embodiment._running = False
    yield
    embodiment.stop_all()
    embodiment._channels.clear()

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
