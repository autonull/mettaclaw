import threading

class Channel:
    def __init__(self, name):
        self.name = name
        self.running = False
        self.connected = False
        self.last_message = ""
        self.msg_lock = threading.Lock()

    def start(self):
        raise NotImplementedError

    def stop(self):
        self.running = False
        self.connected = False

    def send_message(self, text):
        raise NotImplementedError

    def get_last_message(self):
        with self.msg_lock:
            msg = self.last_message
            self.last_message = ""
            return msg

    def set_last_message(self, msg):
        with self.msg_lock:
            if not self.last_message:
                self.last_message = msg
            else:
                self.last_message += " | " + msg

    def is_connected(self):
        return self.connected and self.running
