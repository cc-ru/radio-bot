import ssl as ssllib
from functools import partial

from irc.bot import SingleServerIRCBot, ExponentialBackoff
from irc.connection import Factory

from radiobot.mpd import MPDTrack


class IRCRadioBot(SingleServerIRCBot):

    strategy = ExponentialBackoff(max_interval=180)

    def __init__(self, server, nickname, realname, channel, password,
                 mpd_client,
                 nickserv_nick=None, ssl=False):
        if ssl:
            super().__init__([server], nickname, realname,
                             recon=self.strategy,
                             connect_factory=Factory(
                                 wrapper=ssllib.wrap_socket
                             ))
        else:
            super().__init__([server], nickname, realname,
                             recon=self.strategy)
        self.channel = channel
        self.previous_track = None
        self.nickserv_password = password
        self.nickserv_nick = nickserv_nick or nickname
        self.mpd = mpd_client

        self.connection.set_rate_limit(100)

    def on_welcome(self, connection, event):
        connection.privmsg('NickServ', ' '.join('IDENTIFY',
                                                self.nickserv_nick,
                                                self.nickserv_password))
        connection.join(self.channel)

        sekf.reactor.scheduler.execute_every(1, partial(self.update,
                                                        connection))

    def get_current_track(self):
        with self.mpd as mpd:
            return MPDTrack(mpd.status(), mpd.currentsong())
    
    def update(self, connection):
        current_track = self.get_current_track()

        if current_track != self.previous_track:
            topic = 'Playing: ' + str(current_track)
            connection.topic(self.channel, topic)

            connection.privmsg(
                self.channel,
                '\x02Now playing:\x02 [{name}] {artist} — {title}'.format(
                    name=current_track.name,
                    artist=current_track.artist,
                    title=current_track.title
                )
            )
            connection.privmsg(
                self.channel,
                '\x02Album:\x02 {album}'.format(album=current_track.album)
            )
            connection.privmsg(
                self.channel,
                '\x02Genre:\x02 {genre}, \x02volume\x02: {volume}'
            )

        self.previous_track = current_track
