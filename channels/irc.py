import socket
import threading
import random
from channels.base import Channel

class IRCChannel(Channel):
    def __init__(self, name, channel, server="irc.libera.chat", port=6667, nick="mettaclaw"):
        super().__init__(name)
        self.irc_channel = channel
        self.server = server
        self.port = port
        self.nick = f"{nick}{random.randint(1000, 9999)}"
        self.sock = None
        self.sock_lock = threading.Lock()
        self.thread = None

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._irc_loop, daemon=True)
        self.thread.start()

    def _send(self, cmd):
        with self.sock_lock:
            if self.sock:
                self.sock.sendall((cmd + "\r\n").encode())

    def _irc_loop(self):
        sock = socket.socket()
        try:
            sock.connect((self.server, self.port))
            self.sock = sock
            self._send(f"NICK {self.nick}")
            self._send(f"USER {self.nick} 0 * :{self.nick}")

            while self.running:
                try:
                    data = sock.recv(4096).decode(errors="ignore")
                except OSError:
                    break
                if not data:
                    break

                for line in data.split("\r\n"):
                    if not line:
                        continue
                    if line.startswith("PING"):
                        self._send(f"PONG {line.split()[1]}")
                    parts = line.split()
                    if len(parts) > 1 and parts[1] == "001":
                        self.connected = True
                        self._send(f"JOIN {self.irc_channel}")
                    elif line.startswith(":") and " PRIVMSG " in line:
                        try:
                            prefix, trailing = line[1:].split(" PRIVMSG ", 1)
                            msg_nick = prefix.split("!", 1)[0]

                            if " :" not in trailing:
                                continue

                            msg = trailing.split(" :", 1)[1]
                            self.set_last_message(f"{msg_nick}: {msg}")
                        except Exception:
                            pass
        except Exception as e:
            print(f"IRC Error: {e}")
        finally:
            with self.sock_lock:
                if self.sock:
                    try:
                        self.sock.close()
                    except Exception:
                        pass
                self.sock = None
            self.connected = False

    def stop(self):
        super().stop()
        with self.sock_lock:
            if self.sock:
                try:
                    self.sock.close()
                except Exception:
                    pass

    def send_message(self, text):
        if self.connected:
            self._send(f"PRIVMSG {self.irc_channel} :{text}")

def start_irc(channel, server="irc.libera.chat", port=6667, nick="mettaclaw"):
    import channels.embodiment as embodiment
    chan = IRCChannel("irc", channel, server, int(port), nick)
    chan.start()
    embodiment.register_channel("irc", chan)
    embodiment._active_channel = "irc"
    embodiment._running = True
    return True
