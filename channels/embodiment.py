"""
EmbodimentBus - Multi-channel abstraction for MeTTaClaw.
"""
from typing import Dict, List, Optional

class EmbodimentBus:
    """Central message bus managing multiple communication channels."""
    def __init__(self):
        self._channels: Dict[str, 'Channel'] = {}
        self._active_channel: Optional[str] = None
        self._running = False

    def register_channel(self, name: str, channel_instance):
        self._channels[name] = channel_instance

    def unregister_channel(self, name: str):
        if name in self._channels:
            del self._channels[name]

    def stop_channel(self, name: str = None):
        if name:
            channel = self._channels.get(name)
            if channel:
                channel.stop()
        else:
            self._running = False
            for ch_name, channel in self._channels.items():
                try:
                    channel.stop()
                except Exception:
                    pass

    def stop_all(self):
        self.stop_channel()

    def receive_all(self) -> str:
        """MeTTa integration: Get next message from any channel."""
        priority = ['cli', 'irc', 'mattermost']
        other_channels = [k for k in self._channels.keys() if k not in priority]

        for name in priority + other_channels:
            channel = self._channels.get(name)
            if channel and hasattr(channel, 'get_last_message'):
                try:
                    msg = channel.get_last_message()
                    if msg:
                        return msg
                except Exception:
                    pass
        return ""

    def send_all(self, text: str):
        """Broadcasts a message to all connected channels."""
        for name, channel in self._channels.items():
            try:
                if hasattr(channel, "is_connected") and channel.is_connected():
                    channel.send_message(text)
            except Exception as e:
                print(f"Error sending to {name}: {e}")
        return None

    def send_to(self, channel_name: str, text: str):
        channel = self._channels.get(channel_name)
        if channel:
            try:
                channel.send_message(text)
            except Exception as e:
                print(f"Error sending to {channel_name}: {e}")

    def get_active_channels(self) -> List[str]:
        active = []
        for name, channel in self._channels.items():
            try:
                if hasattr(channel, "is_connected") and channel.is_connected():
                    active.append(name)
            except Exception:
                pass
        return active

    def is_running(self) -> bool:
        return self._running

    def set_running(self, state: bool):
        self._running = state

    def set_active_channel(self, channel: str):
        self._active_channel = channel


# Singleton instance
bus = EmbodimentBus()

# Legacy module-level API delegating to the bus instance
def register_channel(name: str, channel_instance): bus.register_channel(name, channel_instance)
def unregister_channel(name: str): bus.unregister_channel(name)
def stop_channel(name: str = None): bus.stop_channel(name)
def stop_all(): bus.stop_all()
def receive_all() -> str: return bus.receive_all()
def send_all(text: str): return bus.send_all(text)
def broadcast(text: str): return bus.send_all(text)
def send_to(channel_name: str, text: str): bus.send_to(channel_name, text)
def get_active_channels() -> List[str]: return bus.get_active_channels()
def get_active_channel() -> Optional[str]: return bus._active_channel
def is_running() -> bool: return bus.is_running()

# Specific start functions
def start_irc(channel="#metta", server="irc.libera.chat", port=6667, nick="mettaclaw"):
    from channels.irc import start_irc as _start_irc
    return _start_irc(channel, server, port, nick)

def start_cli(prompt="> ", welcome_msg=None):
    from channels.cli import start_cli as _start_cli
    return _start_cli(prompt, welcome_msg)

def start_mattermost(url, channel_id, token):
    from channels.mattermost import start_mattermost as _start_mattermost
    return _start_mattermost(url, channel_id, token)

# Required overrides for module imports that interact with bus internal state
def _set_active_channel(name: str):
    bus.set_active_channel(name)
def _set_running(state: bool):
    bus.set_running(state)
