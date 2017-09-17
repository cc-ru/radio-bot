from logging import getLogger

from radiobot.config import config, get_optint
from radiobot.irc import IRCRadioBot
from radiobot.mpd import Client

logger = getLogger(__name__)


def main():
    mpd_client = Client(config['mpd']['hostname'],
                        config['mpd'].getint('port'),
                        timeout=get_optint('mpd', 'timeout', None))
    bot = IRCRadioBot(config['IRC']['hostname'],
                      config['IRC'].getint('port'),
                      config['IRC']['nickname'],
                      config['IRC']['realname'],
                      config['IRC']['channel'],
                      config['NickServ']['password'],
                      mpd_client,
                      [x.strip() for x in config['IRC']['admins'].split(',')],
                      nickserv_nick=config['NickServ']['nickname'] or None,
                      ssl=config['IRC'].getboolean('tls'))
    bot.start()


if __name__ == '__main__':
    main()
