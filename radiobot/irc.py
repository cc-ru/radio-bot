import ssl as ssllib

from irc.bot import SingleServerIRCBot, ExponentialBackoff
from irc.connection import Factory


class IRCRadioBot(SingleServerIRCBot):

    strategy = ExponentialBackoff(max_interval=180)

    def __init__(self, server, nickname, realname, channel, password,
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
        self.channel_topic = None
        self.nickserv_password = password
        self.nickserv_nick = nickserv_nick or nickname
        self.connection.set_rate_limit(100)

    def on_welcome(self, connection, event):
        connection.privmsg('NickServ', ' '.join('IDENTIFY',
                                                self.nickserv_nick,
                                                self.nickserv_password))
        connection.join(self.channel)