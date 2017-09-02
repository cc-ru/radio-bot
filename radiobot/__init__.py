from radiobot.config import config
from radiobot.irc import IRCRadioBot
from radiobot.mpd import Client


def main():
    mpd_client = Client()
    bot = IRCRadioBot(config['IRC']['server'],
                      config['IRC']['nickname'],
                      config['IRC']['realname'],
                      config['IRC']['channel'],
                      config['NickServ']['password'],
                      mpd_client,
                      nickserv_nick=config['NickServ']['nickname'] or None,
                      ssl=config['IRC'].getboolean('tls'))
    bot.start()


if __name__ == '__main__':
    main()
