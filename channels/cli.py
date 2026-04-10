import sys
import threading
from channels.base import Channel

class CLIChannel(Channel):
    def __init__(self, name, prompt="> ", welcome_msg=None):
        super().__init__(name)
        self.prompt = prompt
        self.welcome_msg = welcome_msg
        self.input_buffer = ""
        self.input_ready = threading.Event()
        self.thread = None

    def start(self):
        self.running = True
        self.connected = True
        if self.welcome_msg:
            print(self.welcome_msg)
        self.thread = threading.Thread(target=self._input_thread, daemon=True, name="CLI-Input")
        self.thread.start()

    def _input_thread(self):
        while self.running:
            try:
                if sys.stdin.isatty():
                    print(self.prompt, end='', flush=True)
                line = sys.stdin.readline()
                if line:
                    self.input_buffer = line.rstrip('\n')
                    self.input_ready.set()
                else:
                    break
            except Exception:
                break

    def stop(self):
        super().stop()
        self.input_ready.set()

    def send_message(self, text):
        with self.msg_lock:
            print(text)
            if self.running and sys.stdin.isatty():
                print(self.prompt, end='', flush=True)

    def get_last_message(self, timeout=0.1):
        if self.input_ready.wait(timeout):
            self.input_ready.clear()
            msg = self.input_buffer
            self.input_buffer = ""
            return msg
        return ""
