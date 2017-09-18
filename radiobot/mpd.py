from collections.abc import Mapping
from logging import getLogger

import mpd
from mpd import MPDClient

logger = getLogger(__name__)


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
            except (ConnectionError, mpd.ConnectionError) as exc:
                logger.debug('Ignored exception', exc_info=exc)
            self.connected = False
            logger.debug('Disconnected from mpd.')

    def open(self):
        if not self.connected:
            self.client = MPDClient()
            self.client.timeout = self.timeout
            self.client.connect(self.hostname, self.port)
            self.connected = True
            logger.debug('Connected to mpd.')

    def __enter__(self):
        self.open()
        return self.client

    def __exit__(self, *args):
        self.close()
        return False


class MPDTrack(Mapping):
    attributes = ['volume',
                  'repeat',
                  'random',
                  'single',
                  'consume',
                  'playlist',
                  'playlist_length',
                  'mix_ramp',
                  'state',
                  'song',
                  'song_id',
                  'time',
                  'elapsed',
                  'bitrate',
                  'format',
                  'id',
                  'pos',
                  'name',
                  'genre',
                  'date',
                  'track',
                  'album',
                  'title',
                  'album_artist',
                  'artist',
                  'file']

    def __init__(self, status, current):
        self.volume = int(status['volume'])
        self.repeat = bool(int(status['repeat']))
        self.random = bool(int(status['random']))
        self.single = bool(int(status['single']))
        self.consume = bool(int(status['consume']))
        self.playlist = int(status['playlist'])
        self.playlist_length = int(status['playlistlength'])
        self.mix_ramp = float(status['mixrampdb'])
        self.state = status['state']
        self.song = bool(int(status['song'])) if 'song' in status else None
        self.song_id = int(status['songid']) if 'songid' in status else None
        self.time = status['time'] if 'time' in status else '0:0'
        self.elapsed = (float(status['elapsed'])
                        if 'elapsed' in status else None)
        self.bitrate = int(status['bitrate']) if 'bitrate' in status else None
        self.format = status.get('audio')

        self.file = current.get('file')
        self.artist = current.get('artist')
        self.album_artist = current.get('albumartist')
        self.title = current.get('title')
        self.album = current.get('album')
        self.track = current.get('track')
        self.date = current.get('date')
        self.genre = current.get('genre')
        self.name = current.get('name')
        self.pos = int(current['pos']) if 'pos' in current else None
        self.id = int(current['id']) if 'id' in current else None

    def __eq__(self, other):
        if not isinstance(other, MPDTrack):
            return False

        return all(getattr(self, x) == getattr(other, x)
                   for x in ['volume',
                             'file',
                             'artist',
                             'album',
                             'title',
                             'name'])

    def __ne__(self, other):
        return not (self == other)

    def __str__(self):
        if self.state == 'play':
            return '{artist} — {title}'.format(**self)
        elif self.state == 'stop':
            return 'radio is stopped'

    def __iter__(self):
        return iter(self.attributes)

    def __len__(self):
        return len(self.attributes)

    def __getitem__(self, key):
        return getattr(self, key)

    def __repr__(self):
        return 'MPDTrack<' + ', '.join(
            x + '=' + repr(getattr(self, x))
            for x in self.attributes
        ) + '>'
