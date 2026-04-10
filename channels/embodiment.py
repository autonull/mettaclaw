"""
EmbodimentBus - Multi-channel abstraction for MeTTaClaw.
"""
from typing import Dict, List, Optional
import threading

_channels: Dict[str, 'Channel'] = {}
_active_channel: Optional[str] = None
_running = False

def register_channel(name: str, channel_instance):
    _channels[name] = channel_instance

def unregister_channel(name: str):
    if name in _channels:
        del _channels[name]

def start_irc(channel="#metta", server="irc.libera.chat", port=6667, nick="mettaclaw"):
    global _active_channel, _running
    try:
        from channels.irc import IRCChannel
        chan = IRCChannel("irc", channel, server, int(port), nick)
        chan.start()
        register_channel('irc', chan)
        _active_channel = 'irc'
        _running = True
        return True
    except Exception as e:
        print(f"Failed to start IRC: {e}")
        return False

def start_cli(prompt="> ", welcome_msg=None):
    global _active_channel, _running
    try:
        from channels.cli import CLIChannel
        chan = CLIChannel("cli", prompt, welcome_msg)
        chan.start()
        register_channel('cli', chan)
        _active_channel = 'cli'
        _running = True
        return True
    except Exception as e:
        print(f"Failed to start CLI: {e}")
        return False

def start_mattermost(url, channel_id, token):
    global _active_channel, _running
    try:
        from channels.mattermost import MattermostChannel
        chan = MattermostChannel("mattermost", url, channel_id, token)
        chan.start()
        register_channel('mattermost', chan)
        _active_channel = 'mattermost'
        _running = True
        return True
    except Exception as e:
        print(f"Failed to start Mattermost: {e}")
        return False

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
            except:
                pass

def stop_all():
    stop_channel()

def getNextMessage() -> str:
    for name in ['cli', 'irc', 'mattermost']:
        channel = _channels.get(name)
        if channel:
            try:
                msg = channel.get_last_message()
                if msg:
                    return msg
            except Exception:
                pass
    return ""

def receive_all() -> str:
    return getNextMessage()

def broadcast(text: str):
    for name, channel in _channels.items():
        try:
            if channel.is_connected():
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
            if channel.is_connected():
                active.append(name)
        except:
            pass
    return active

def get_active_channel() -> Optional[str]:
    return _active_channel

def is_running() -> bool:
    return _running
