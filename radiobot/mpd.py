import mpd
from mpd import MPDClient


class Client:
    def __init__(self, hostname, port, *,
                 timeout=None):
        self.client = None
        self.timeout = timeout
        self.hostname = hostname
        self.port = port
        self.connected = False

    def close(self):
        if self.connected:
            try:
                self.client.close()
                self.client.disconnect()
            except (ConnectionError, mpd.ConnectionError):
                pass
            self.connected = False

    def open(self):
        if not self.connected:
            self.client = MPDClient()
            self.client.timeout = self.timeout
            self.client.connect(self.hostname, self.port)
            self.connected = True

    def __enter__(self):
        self.open()
        return self.client

    def __exit__(self, *args):
        self.close()
        return False


class MPDTrack:
    def __init__(self, status):
        self.volume = int(status['volume'])
        self.repeat = bool(int(status['repeat']))
        self.random = bool(int(status['random']))
        self.single = bool(int(status['single']))
        self.consume = bool(int(status['consume']))
        self.playlist = int(status['playlist'])
        self.playlist_length = int(status['playlistlength'])
        self.mix_ramp = float(status['mixrampdb'])
        self.state = status['state']
        self.song = bool(int(status['song']))
        self.song_id = int(status['songid'])
        self.time = status['time']  # ?
        self.elapsed = float(status['elapsed'])
        self.bitrate = int(status['bitrate'])
        self.format = status['audio']
