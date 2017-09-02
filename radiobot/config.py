from configparser import ConfigParser
from os.path import exists

config = ConfigParser()
read_success = not not config.read('radio-bot.cfg')

for section in {'IRC', 'NickServ'} - set(config.sections()):
    config.add_section(section)

config['IRC'].setdefault('server', 'localhost:6667')
config['IRC'].setdefault('nickname', 'radio-bot')
config['IRC'].setdefault('realname', 'Radio bot')
config['IRC'].setdefault('channel', '#radio')
config['IRC'].setdefault('tls', 'false')

config['NickServ'].setdefault('password', 'secret')
config['NickServ'].setdefault('nickname', '')

if not exists('radio-bot.cfg') or not read_success:
    with open('radio-bot.cfg', 'w') as f:
        config.write(f)
