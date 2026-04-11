import threading
import json
import time
import requests
import websocket
from channels.base import Channel

class MattermostChannel(Channel):
    def __init__(self, name, url, channel_id, token):
        super().__init__(name)
        self.url = url
        self.channel_id = channel_id
        self.token = token
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.bot_user_id = None
        self.ws = None
        self.ws_lock = threading.Lock()
        self.thread = None

    def _get_bot_user_id(self):
        r = requests.get(f"{self.url}/api/v4/users/me", headers=self.headers)
        r.raise_for_status()
        return r.json()["id"]

    def _get_display_name(self, user_id):
        r = requests.get(f"{self.url}/api/v4/users/{user_id}", headers=self.headers)
        r.raise_for_status()
        u = r.json()
        if u.get("first_name") or u.get("last_name"):
            return f"{u.get('first_name','')} {u.get('last_name','')}".strip()
        return u["username"]

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._ws_loop, daemon=True)
        self.thread.start()

    def _ws_loop(self):
        try:
            self.bot_user_id = self._get_bot_user_id()
        except Exception as e:
            print(f"Failed to get Mattermost bot user ID: {e}")
            self.running = False
            return

        ws_url = self.url.replace("https", "wss").replace("http", "ws") + "/api/v4/websocket"
        ws = websocket.WebSocket()
        try:
            ws.connect(ws_url, header=[f"Authorization: Bearer {self.token}"])
        except Exception as e:
            print(f"Mattermost WS connection failed: {e}")
            self.running = False
            return

        self.ws = ws
        self.connected = True
        last_ping = time.time()

        while self.running:
            try:
                if time.time() - last_ping > 25:
                    ws.ping()
                    last_ping = time.time()

                ws.settimeout(1)
                event = json.loads(ws.recv())

                if event.get("event") == "posted":
                    post = json.loads(event["data"]["post"])
                    if post["channel_id"] == self.channel_id and post["user_id"] != self.bot_user_id:
                        try:
                            name = self._get_display_name(post["user_id"])
                        except Exception:
                            name = "unknown"
                        self.set_last_message(f"{name}: {post['message']}")

            except websocket.WebSocketTimeoutException:
                continue
            except Exception as e:
                print(f"Mattermost WS error: {e}")
                break

        ws.close()
        self.connected = False

    def stop(self):
        super().stop()
        if self.ws:
            try:
                self.ws.close()
            except Exception:
                pass

    def send_message(self, text):
        text = text.replace("\\n", "\n")
        if not self.connected:
            return
        try:
            requests.post(
                f"{self.url}/api/v4/posts",
                headers=self.headers,
                json={"channel_id": self.channel_id, "message": text}
            )
        except Exception as e:
            print(f"Error sending to Mattermost: {e}")

def start_mattermost(url, channel_id, token):
    import channels.embodiment as embodiment
    chan = MattermostChannel("mattermost", url, channel_id, token)
    chan.start()
    embodiment.register_channel("mattermost", chan)
    embodiment._active_channel = "mattermost"
    embodiment._running = True
    return True
