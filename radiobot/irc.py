import ssl as ssllib
from functools import partial
from logging import getLogger

from irc.bot import SingleServerIRCBot, ExponentialBackoff
from irc.connection import Factory

from radiobot.mpd import MPDTrack

logger = getLogger(__name__)


class IRCRadioBot(SingleServerIRCBot):

    strategy = ExponentialBackoff(max_interval=180)

    def __init__(self, hostname, port, nickname, realname, channel, password,
                 mpd_client, admins,
                 nickserv_nick=None, ssl=False):
        server = (hostname, port)
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
        self.previous_topic = None
        self.admins = admins
        self.nickserv_password = password
        self.nickserv_nick = nickserv_nick or nickname
        self.mpd = mpd_client

        self.connection.set_rate_limit(100)

    def start(self):
        logger.info('Starting bot...')
        super().start()

    def on_welcome(self, connection, event):
        logger.info('Connected to the IRC server.')
        if self.nickserv_password:
            connection.privmsg('NickServ', ' '.join(('IDENTIFY',
                                                     self.nickserv_nick,
                                                     self.nickserv_password)))
            logger.info('Sent authentication data for nickname %s',
                        self.nickserv_nick)
        connection.join(self.channel)

        self.reactor.scheduler.execute_every(1, partial(self.update,
                                                        connection))

    def get_current_track(self):
        with self.mpd as mpd:
            return MPDTrack(mpd.status(), mpd.currentsong())

    def update(self, connection):
        current_track = self.get_current_track()

        if current_track != self.previous_track:
            logger.debug('updated track: old=%r, new=%r',
                         self.previous_track,
                         current_track)
            if current_track.state == 'play':
                topic = '\x02Playing:\x02 ' + str(current_track)
            elif current_track.state == 'stop':
                topic = '\x02Radio offline'
            if topic != self.previous_topic:
                logger.debug('updated topic: old=%r, new=%r',
                             self.previous_topic,
                             topic)
                connection.topic(self.channel, topic)
                self.previous_topic = topic

            if current_track.state == 'play':
                connection.privmsg(
                    self.channel,
                    '\x02Now playing:\x02 {artist} — {title}'.format(
                        **current_track
                    )
                )
                connection.privmsg(
                    self.channel,
                    '\x02Album:\x02 {album}'.format(**current_track)
                )
                connection.privmsg(
                    self.channel,
                    '\x02Genre:\x02 {genre}, \x02volume\x02: {volume}%'.format(
                        **current_track
                    )
                )
            elif current_track.state == 'stop':
                connection.privmsg(
                    self.channel,
                    ', '.join(self.admins) + ': \x02\x0307Radio stopped!'
                )

        self.previous_track = current_track

    def on_pubmsg(self, connection, event):
        logger.debug('privmsg: %s', event)
        msg = event.arguments[0]

        if msg == '#current':
            current_track = self.get_current_track()
            if current_track.state == 'play':
                elapsed, total = current_track.time.split(':')
                elapsed, total = int(elapsed), int(total)
                elapsed = ':'.join('{:02d}'.format(x)
                                   for x in divmod(elapsed, 60))
                total = ':'.join('{:02d}'.format(x)
                                 for x in divmod(total, 60))
                connection.privmsg(
                    self.channel,
                    '\x02Now playing:\x02 [{time_elapsed} / {time_total} '
                    '@ {volume}%] {artist} — {title}'.format(
                        time_elapsed=elapsed,
                        time_total=total,
                        **current_track)
                )
                connection.privmsg(
                    self.channel,
                    '\x02Album:\x02 {album}'.format(**current_track)
                )
                connection.privmsg(
                    self.channel,
                    '\x02Genre:\x02 {genre}'.format(**current_track)
                )
            else:
                connection.privmsg(
                    self.channel,
                    '\x02Radio is stopped.'
                )
