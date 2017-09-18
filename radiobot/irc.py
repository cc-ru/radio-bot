import ssl as ssllib
from functools import partial
from logging import getLogger

from irc.bot import SingleServerIRCBot, ExponentialBackoff
from irc.connection import Factory

from radiobot.config import config
from radiobot.mpd import MPDTrack

logger = getLogger(__name__)


def get_nick(event):
    return event.source.split('!', 1)[0]


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
        self.votes = 0
        self.voters = {}
        self.poll_remaining = -1
        self.poll_time = config['poll'].getint('poll time')
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

    def reply(self, connection, event, msg):
        connection.privmsg(self.channel,
                           get_nick(event) + ': ' + msg)

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

    def reset_poll(self):
        self.votes = 0
        self.poll_remaining = -1
        self.voters = {}

    def update_poll(self, connection):
        if self.poll_remaining < 0:
            return

        self.poll_remaining -= 1
        if self.poll_remaining < 0:
            connection.privmsg(self.channel,
                               '\x02Poll closed.')
            if self.votes < 0:
                connection.privmsg(self.channel,
                                   'The current track is going to be '
                                   '\x02skipped\x02.')
                with self.mpd as mpd:
                    mpd.next()
                self.update(connection)
            else:
                connection.privmsg(self.channel,
                                   'The current track is going to \x02continue '
                                   'playing\x02.')
            self.votes = 0

    def update(self, connection):
        current_track = self.get_current_track()
        self.update_poll(connection)

        if current_track.state == 'play':
            color_off = '\x0f'
            if self.votes > 0:
                color_on = '\x0303'
            elif self.votes < 0:
                color_on = '\x0305'
            else:
                color_on = ''
                color_off = ''

            topic = ('\x02Playing:\x02 '
                     '[{color_on}{votes}{color_off}] '
                     '{current_track!s}').format(
                         color_on=color_on,
                         votes=self.votes,
                         color_off=color_off,
                         current_track=current_track
                     )
        elif current_track.state == 'stop':
            topic = '\x02Radio offline'

        if topic != self.previous_topic:
            logger.debug('updated topic: old=%r, new=%r',
                         self.previous_topic,
                         topic)
            connection.topic(self.channel, topic)
            self.previous_topic = topic

        if current_track != self.previous_track:
            logger.debug('updated track: old=%r, new=%r',
                         self.previous_track,
                         current_track)
            self.reset_poll()

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
        elif msg == '#rip' or self.poll_remaining > -1 and msg == '#unrip':
            if self.previous_track.state == 'stop':
                connection.privmsg(self.channel,
                                   '\x02Radio is stopped\x02.')
                return

            if event.source in self.voters:
                if self.voters[event.source] == msg:
                    self.reply(connection, event,
                               '\x02You have already voted\x02.')
                    return
                else:
                    self.votes += (-1 if self.voters[event.source] == '#unrip'
                                   else 1)

            if msg == '#rip':
                self.votes -= 1
            else:
                self.votes += 1

            self.voters[event.source] = msg

            if self.poll_remaining == -1:
                connection.privmsg(self.channel,
                                   '\x02Song skip requested!\x02 '
                                   'You have \x02{poll_time} seconds\x02 to '
                                   'cast you vote. Use commands '
                                   '\x1f#unrip\x1f and \x1f#rip\x1f to '
                                   'vote!'.format(poll_time=self.poll_time))
                self.poll_remaining = self.poll_time

            self.reply(connection, event,
                       '\x02Your vote has been saved.\x02')
            self.update(connection)
