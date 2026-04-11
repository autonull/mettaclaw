"""
EmbodimentBus - Multi-channel abstraction for MeTTaClaw.
"""
from typing import Dict, List, Optional

_channels: Dict[str, 'Channel'] = {}
_active_channel: Optional[str] = None
_running = False

def register_channel(name: str, channel_instance):
    _channels[name] = channel_instance

def unregister_channel(name: str):
    if name in _channels:
        del _channels[name]

def start_irc(channel="#metta", server="irc.libera.chat", port=6667, nick="mettaclaw"):
    from channels.irc import start_irc as _start_irc
    return _start_irc(channel, server, port, nick)

def start_cli(prompt="> ", welcome_msg=None):
    from channels.cli import start_cli as _start_cli
    return _start_cli(prompt, welcome_msg)

def start_mattermost(url, channel_id, token):
    from channels.mattermost import start_mattermost as _start_mattermost
    return _start_mattermost(url, channel_id, token)

def stop_channel(name: str = None):
    global _running
    if name:
        channel = _channels.get(name)
        if channel:
            channel.stop()
    else:
        _running = False
        for ch_name, channel in _channels.items():
            try:
                channel.stop()
            except Exception:
                pass

def stop_all():
    stop_channel()

def getNextMessage() -> str:
    priority = ['cli', 'irc', 'mattermost']
    other_channels = [k for k in _channels.keys() if k not in priority]
    all_names = priority + other_channels

    for name in all_names:
        channel = _channels.get(name)
        if channel:
            try:
                if name == 'cli' and hasattr(channel, 'get_message_blocking'):
                    msg = channel.get_message_blocking(timeout=0.1)
                    if msg:
                        return msg
                elif hasattr(channel, 'get_last_message'):
                    msg = channel.get_last_message()
                    if msg:
                        return msg
                elif hasattr(channel, 'getLastMessage'):
                    msg = channel.getLastMessage()
                    if msg:
                        return msg
            except Exception:
                pass
    return ""

def receive_all() -> str:
    """MeTTa integration: Get next message from any channel."""
    return getNextMessage()

def broadcast(text: str):
    for name, channel in _channels.items():
        try:
            if hasattr(channel, "is_connected") and channel.is_connected():
                channel.send_message(text)
        except Exception as e:
            print(f"Error sending to {name}: {e}")

def send_all(text: str):
    broadcast(text)
    return None

def send_to(channel_name: str, text: str):
    channel = _channels.get(channel_name)
    if channel:
        try:
            channel.send_message(text)
        except Exception as e:
            print(f"Error sending to {channel_name}: {e}")

def get_active_channels() -> List[str]:
    active = []
    for name, channel in _channels.items():
        try:
            if hasattr(channel, "is_connected") and channel.is_connected():
                active.append(name)
        except Exception:
            pass
    return active

def get_active_channel() -> Optional[str]:
    return _active_channel

def is_running() -> bool:
    return _running
